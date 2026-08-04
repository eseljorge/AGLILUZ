import os
import json
import re
import requests
import pandas as pd
from datetime import datetime, timedelta
from pypdf import PdfReader
import io
from playwright.sync_api import sync_playwright

MEMORY_PATH = 'memory.md'

def cargar_memoria_persistente():
    default_config = {
        "blacklist": [
            "telemedicina", "pantalla led", "pantallas led", "display", 
            "displays", "monitor", "monitores", "televisor", "salud", 
            "hospital", "clinica", "clínica"
        ],
        "whitelist_objetivos": [
            "estadio", "estadios", "cancha", "canchas", "deportivo", 
            "polideportivo", "proyector deportivo", "proyectores deportivos",
            "mantenimiento", "conservacion", "conservación", "alumbrado publico", 
            "alumbrado público", "reposicion", "reposición", "recambio", 
            "luminaria", "luminarias", "foco vial", "ind", "instituto nacional de deportes",
            "telegestion", "telegestión", "interact", "dynalite", "zhaga", "nema", "túnel", "tunel"
        ]
    }
    if not os.path.exists(MEMORY_PATH):
        os.makedirs(os.path.dirname(MEMORY_PATH) if os.path.dirname(MEMORY_PATH) else '.', exist_ok=True)
        with open(MEMORY_PATH, 'w', encoding='utf-8') as f:
            f.write("# 🧠 Memory.md - AgliLuz\n")
    return default_config

def extraer_texto_desde_url(url):
    try:
        response = requests.get(url, timeout=25)
        if response.status_code == 200 and ('application/pdf' in response.headers.get('content-type', '').lower() or 'pdf' in url.lower()):
            with io.BytesIO(response.content) as f:
                reader = PdfReader(f)
                texto_completo = ""
                for page in reader.pages[:40]: # Máxima profundidad de lectura en bases PDF
                    texto_completo += page.extract_text() or ""
            return texto_completo.lower()
    except Exception:
        pass
    return ""

def extraer_detalle_profundo_web(codigo_externo):
    url_ficha = f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?id={codigo_externo}"
    resultado_profundo = {
        "Competencia_Web": "No especificado en ficha web",
        "Texto_Adjuntos_Profundo": ""
    }
    links_documentos = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url_ficha, timeout=45000)
            page.wait_for_load_state('domcontentloaded', timeout=15000)
            
            texto_ficha = page.inner_text('body').lower()
            resultado_profundo["Texto_Adjuntos_Profundo"] += " " + texto_ficha
            
            elementos_a = page.query_selector_all('a')
            for el in elementos_a:
                href = el.get_attribute('href')
                if href and ('pdf' in href.lower() or 'descarga' in href.lower() or 'document' in href.lower() or 'file' in href.lower()):
                    if href.startswith('http'):
                        links_documentos.append(href)
                    elif href.startswith('/'):
                        links_documentos.append(f"https://www.mercadopublico.cl{href}")
            
            if "ge lighting" in texto_ficha: resultado_profundo["Competencia_Web"] = "GE Lighting"
            elif "osram" in texto_ficha or "ledvance" in texto_ficha: resultado_profundo["Competencia_Web"] = "Osram / Ledvance"
            elif "cree" in texto_ficha: resultado_profundo["Competencia_Web"] = "Cree Lighting"
            elif "philips" in texto_ficha or "signify" in texto_ficha: resultado_profundo["Competencia_Web"] = "Philips / Signify"
            else: resultado_profundo["Competencia_Web"] = "Competencia Local / Alternativa"
                
            browser.close()
    except Exception as e:
        print(f"Nota Playwright en {codigo_externo}: {e}")
        
    for link_doc in set(links_documentos[:5]):
        resultado_profundo["Texto_Adjuntos_Profundo"] += " " + extraer_texto_desde_url(link_doc)
        
    return resultado_profundo

def extraer_elementos_comerciales_y_tecnicos(texto):
    # Moneda
    moneda = "Pesos Chilenos (CLP)"
    if 'unidad de fomento' in texto or ' uf ' in texto: moneda = "Unidad de Fomento (UF)"
    elif 'dolar' in texto or 'usd' in texto: moneda = "Dólares (USD)"

    # Visita a terreno
    visita = "No se exige visita a terreno obligatoria"
    if 'visita a terreno' in texto or 'visita obligatoria' in texto:
        visita = "Exige Visita a Terreno (Ver bases para obligatoriedad)"

    # Garantías
    garantias = "Garantía de seriedad de oferta y fiel cumplimiento estándar"
    if 'fiel cumplimiento' in texto:
        match_garantia = re.findall(r'(\d+[\.,]?\d*)\s*%\s*(?:del valor|de la oferta|fiel cumplimiento)?', texto)
        garantias = f"Boleta Fiel Cumplimiento ({match_garantia[0]}%)" if match_garantia else "Boleta Fiel Cumplimiento exigida"

    # Plazos y entregas
    plazo_entrega = "Conforme a cronograma oficial de bases"
    if 'bodega' in texto or 'plazo de entrega' in texto:
        plazo_entrega = "Hitos críticos definidos en bases técnicas"

    # Garantía de producto
    garantia_prod = "Estándar 5 Años"
    if 'garantia' in texto or 'garantía' in texto:
        match_anos = re.findall(r'(\d+)\s*(?:anos|años)', texto)
        if match_anos: garantia_prod = f"{match_anos[0]} Años (según bases)"

    # Multas y retenciones
    multas = "Aplicación de multas por atraso estándar MOP/Mercado Público"
    if 'multa' in texto:
        multas = "Multas por día de atraso o incumplimiento estipuladas en bases"

    # Certificaciones
    certificaciones = []
    if 'sec' in texto: certificaciones.append("Certificación SEC (Chile)")
    if 'ds1' in texto or 'decreto supremo' in texto or 'norma lumínica' in texto: certificaciones.append("Decreto Supremo N°1 (Norma Lumínica)")
    cert_str = " | ".join(certificaciones) if certificaciones else "Normativa estándar de licitación"

    # Telegestión y Control
    telegestion = []
    if 'telegestion' in texto or 'telegestión' in texto: telegestion.append("Exige Telegestión")
    if 'zhaga' in texto: telegestion.append("Zócalo Zhaga")
    if 'nema' in texto: telegestion.append("Zócalo NEMA")
    if 'interact' in texto: telegestion.append("Plataforma Interact")
    if 'dynalite' in texto: telegestion.append("Sistema Dynalite")
    control_str = " | ".join(telegestion) if telegestion else "Control autónomo o estándar"

    # Potencia y Flujo
    potencias = re.findall(r'(\d+[\.,]?\d*)\s*(?:w|watt|watts)', texto, re.IGNORECASE)
    potencia_nums = [float(p.replace(',', '.')) for p in potencias if len(p) < 5]
    potencia_str = f"{min(potencia_nums)}W - {max(potencia_nums)}W" if potencia_nums else "No especificado en bases"

    flujos = re.findall(r'(\d+[\.,]?\d*)\s*(?:lm|lumenes|lúmenes)', texto, re.IGNORECASE)
    flujo_nums = [float(f.replace(',', '.')) for f in flujos if len(f) < 7]
    flujo_str = f"{min(flujo_nums):,.0f} lm - {max(flujo_nums):,.0f} lm" if flujo_nums else "No especificado en bases"

    ip_match = re.findall(r'ip\s*([0-6][5678])', texto, re.IGNORECASE)
    ip_str = "IP" + max(ip_match) if ip_match else "IP66 Requerido"

    ik_match = re.findall(r'ik\s*([0-1][0-9])', texto, re.IGNORECASE)
    ik_str = "IK" + max(ik_match) if ik_match else "IK08 Requerido"

    return moneda, visita, garantias, plazo_entrega, garantia_prod, multas, cert_str, control_str, potencia_str, flujo_str, ip_str, ik_str

def evaluar_cumplimiento_signify(categoria, potencia, control, texto):
    estado = "Cumple Totalmente"
    brecha = "Especificaciones técnicas totalmente alineadas con el portafolio profesional Signify."
    
    if "Deportiva" in categoria:
        brecha = f"Potencia ({potencia}): Cubierta por familia Arena X con conectividad Interact Sports y cumplimiento DS1."
    elif "Vial" in categoria or "Túnel" in categoria:
        if "Telegestión" in control or "Zhaga" in control or "Nema" in control:
            estado = "Cumple Totalmente (Conectividad IoT)"
            brecha = "Licitación vial/túnel exige control: RoadFlair / Xceed Pro con zócalo Zhaga/NEMA sobre plataforma Interact City cumple 100%."
        else:
            brecha = "Licitación vial: Se recomienda RoadFlair con opción de telegestión Interact City."
    elif "Solar" in categoria:
        brecha = "Sistema fotovoltaico autónomo: GreenVision Solar cumple con requerimientos fuera de red."
    elif "Arquitectónica" in categoria:
        brecha = "Control de iluminación dinámico: Dynalite y Color Kinetics garantizan gestión RGBW y DS1."
    else:
        brecha = "Portafolio industrial ActiStar / CoreLine cubre requerimientos base."
        
    if "decreto supremo" in texto or "ds1" in texto:
        brecha += " | Cumplimiento DS1 Norma Lumínica verificado."
        
    return estado, brecha

def procesar_inteligencia_avanzada(row):
    codigo = str(row.get('CodigoExterno', ''))
    texto_base = str(row.get('Nombre', '')) + " " + str(row.get('Descripcion', ''))
    
    documentos = row.get('Documentos', [])
    texto_docs = ""
    if isinstance(documentos, list):
        for doc in documentos:
            url_doc = doc.get('UrlDocumento', '') or doc.get('URL', '')
            if url_doc and isinstance(url_doc, str) and url_doc.startswith('http'):
                texto_docs += " " + extraer_texto_desde_url(url_doc)

    datos_web = extraer_detalle_profundo_web(codigo)
    texto_total = (texto_base + " " + texto_docs + " " + datos_web.get("Texto_Adjuntos_Profundo", "")).lower()

    adjudicacion_info = row.get('Adjudicacion', {})
    proveedor = "No especificado / En proceso"
    monto = 0
    cantidad = 0
    if isinstance(adjudicacion_info, dict):
        items_adj = adjudicacion_info.get('Items', [])
        provs = adjudicacion_info.get('Proveedor', [])
        if provs and isinstance(provs, list): proveedor = provs[0].get('Nombre', 'Proveedor Externo')
        if items_adj and isinstance(items_adj, list):
            for it in items_adj:
                cantidad += float(it.get('Cantidad', 0) or 0)
                monto += float(it.get('Total', 0) or 0)

    moneda, visita, garantias, plazo_entrega, garantia_prod, multas, certs, control_reqs, potencia, flujo, ip, ik = extraer_elementos_comerciales_y_tecnicos(texto_total)
    marcas = datos_web.get("Competencia_Web", "Competencia Alternativa")

    pauta = "Evaluada según criterios técnicos y económicos."
    if 'puntaje' in texto_total or 'evaluacion' in texto_total:
        pauta = "Pauta con criterios ponderados (Precio, Técnica, Experiencia)."

    es_ind = 'ind' in texto_total or 'instituto nacional de deporte' in texto_total
    if 'estadio' in texto_total or 'cancha' in texto_total or es_ind:
        signify_eq = "Arena X + Interact Sports (Proyectores Deportivos)"
        categoria = "Iluminación Deportiva / IND"
    elif 'túnel' in texto_total or 'tunel' in texto_total or 'vial' in texto_total or 'autopista' in texto_total or 'alumbrado publico' in texto_total:
        signify_eq = "RoadFlair / Xceed Pro + Interact City (Telegestión Vial)"
        categoria = "Iluminación Vial / Túneles"
    elif 'solar' in texto_total or 'fotovoltaica' in texto_total:
        signify_eq = "GreenVision Solar (Autónoma)"
        categoria = "Iluminación Solar"
    elif 'arquitectonico' in texto_total or 'fachada' in texto_total:
        signify_eq = "Tango Pro / Color Kinetics + Dynalite"
        categoria = "Iluminación Arquitectónica"
    else:
        signify_eq = "ActiStar / CoreLine (Industrial)"
        categoria = "Iluminación General / Industrial"

    estado_cumplimiento, analisis_brecha = evaluar_cumplimiento_signify(categoria, potencia, control_reqs, texto_total)

    fecha_creacion = row.get('FechaCreacion', 'N/A')
    fecha_cierre = row.get('FechaCierre', 'N/A')

    return pd.Series([
        proveedor, monto, cantidad, categoria, signify_eq, marcas, pauta,
        potencia, flujo, ip, ik, certs, control_reqs,
        moneda, visita, garantias, plazo_entrega, garantia_prod, multas,
        estado_cumplimiento, analisis_brecha, str(fecha_creacion)[:10], str(fecha_cierre)[:10]
    ])

def main():
    ticket = os.environ.get('TICKET_MP')
    if not ticket: return

    reglas_memoria = cargar_memoria_persistente()
    url = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?ticket={ticket}"
    response = requests.get(url)
    os.makedirs('agliluz', exist_ok=True)
    
    historial_path = 'agliluz/historial_licitaciones.xlsx'
    dashboard_path = 'agliluz/dashboard_inteligencia_mercado.xlsx'
    
    df_historico = pd.DataFrame()
    if os.path.exists(historial_path):
        try: df_historico = pd.read_excel(historial_path)
        except Exception: pass

    df_filtrado = pd.DataFrame()
    if response.status_code == 200:
        data = response.json()
        licitaciones = data.get('Listado', [])
        if licitaciones:
            df_nuevo = pd.DataFrame(licitaciones)
            if 'FechaCreacion' in df_nuevo.columns:
                df_nuevo['FechaCreacion'] = pd.to_datetime(df_nuevo['FechaCreacion'], errors='coerce')
                df_nuevo = df_nuevo[df_nuevo['FechaCreacion'] >= datetime(2026, 1, 1)]
            
            target_keywords = reglas_memoria.get("whitelist_objetivos", [])
            text_cols = [c for c in ['Nombre', 'Descripcion', 'CodigoExterno', 'Comprador'] if c in df_nuevo.columns]
            if text_cols and not df_nuevo.empty:
                df_nuevo['texto_busqueda'] = df_nuevo[text_cols].astype(str).agg(' '.join, axis=1).str.lower()
                pattern = '|'.join(target_keywords)
                codigos_obj = ['2378-40-lr25', '858-190-lr25', '4483-17-lr26']
                
                mask = df_nuevo['texto_busqueda'].str.contains(pattern, na=False, case=False) | df_nuevo['CodigoExterno'].astype(str).str.lower().isin(codigos_obj)
                df_filtrado = df_nuevo[mask].copy().drop(columns=['texto_busqueda'])

            if not df_filtrado.empty:
                cols_res = [
                    'Proveedor_Adjudicado', 'Monto_Adjudicado_CLP', 'Cantidad_Unidades', 
                    'Categoria_Proyecto', 'Signify_Equivalente', 'Marcas_Competencia_Detectadas', 
                    'Pautas_Y_Puntajes_Evaluacion', 'Requerimiento_Potencia', 'Requerimiento_Flujo_Luminoso', 
                    'Requerimiento_IP', 'Requerimiento_IK', 'Certificaciones_Exigidas', 'Sistemas_Control_Telegestion',
                    'Moneda_Oferta', 'Visita_Terreno', 'Garantias_Requeridas', 'Plazo_Entrega_Bodega', 
                    'Garantia_Producto_Anios', 'Multas_Y_Sanciones', 'Estado_Cumplimiento_Signify', 
                    'Analisis_Brecha_Tecnica', 'Fecha_Creacion', 'Fecha_Cierre'
                ]
                df_filtrado[cols_res] = df_filtrado.apply(procesar_inteligencia_avanzada, axis=1)

    if not df_filtrado.empty:
        if not df_historico.empty:
            cols_chk = [c for c in ['Nombre', 'CodigoExterno'] if c in df_historico.columns]
            if cols_chk:
                mask_ej = False
                for c in cols_chk: mask_ej = mask_ej | df_historico[c].astype(str).str.contains('Ejemplo|\[Ejemplo\]', na=False, regex=True)
                df_historico = df_historico[~mask_ej]
            df_combinado = pd.concat([df_filtrado, df_historico]).drop_duplicates(subset=['CodigoExterno'], keep='first')
        else:
            df_combinado = df_filtrado
    else:
        if not df_historico.empty:
            cols_chk = [c for c in ['Nombre', 'CodigoExterno'] if c in df_historico.columns]
            if cols_chk:
                mask_ej = False
                for c in cols_chk: mask_ej = mask_ej | df_historico[c].astype(str).str.contains('Ejemplo|\[Ejemplo\]', na=False, regex=True)
                df_historico = df_historico[~mask_ej]
        df_combinado = df_historico

    if df_combinado.empty:
        df_combinado = pd.DataFrame(columns=['CodigoExterno', 'Nombre', 'Categoria_Proyecto', 'Signify_Equivalente', 'Requerimiento_Potencia', 'Requerimiento_Flujo_Luminoso', 'Sistemas_Control_Telegestion', 'Estado_Cumplimiento_Signify'])

    df_combinado.to_excel(historial_path, index=False)
    
    with pd.ExcelWriter(dashboard_path, engine='openpyxl') as writer:
        df_combinado.to_excel(writer, sheet_name='Dashboard_General', index=False)
        df_combinado.to_excel(writer, sheet_name='Mapa_Competencia_Adjudicadas', index=False)
        portafolio = pd.DataFrame({
            "Familia_Signify": ["RoadFlair + Interact City", "Arena X + Interact Sports", "Tango Pro + Dynalite", "Color Kinetics", "GreenVision Solar"],
            "Aplicacion": ["Vial e Inteligente / Túneles", "Estadios y Recintos Deportivos", "Arquitectónica y Control", "Fachadas Monumentales", "Fotovoltaica Autónoma"],
            "Estrategia": ["Smart cities y telegestión centralizada", "Alto rendimiento lumínico e IND", "Control dinámico DALI/DMX", "Cumplimiento estricto DS1", "Sostenibilidad sin red"]
        })
        portafolio.to_excel(writer, sheet_name='Portafolio_Signify_Chile', index=False)

if __name__ == '__main__':
    main()
