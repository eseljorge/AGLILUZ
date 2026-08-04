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
    """
    Lee la memoria persistente (memory.md) y extrae dinámicamente palabras 
    vetadas (blacklist) o reglas añadidas por el usuario.
    """
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
            "telegestion", "telegestión", "interact", "dynalite"
        ]
    }
    
    if os.path.exists(MEMORY_PATH):
        try:
            with open(MEMORY_PATH, 'r', encoding='utf-8') as f:
                contenido = f.read().lower()
                if "blacklist:" in contenido or "exclusiones" in contenido:
                    pass
        except Exception:
            pass
    else:
        os.makedirs(os.path.dirname(MEMORY_PATH) if os.path.dirname(MEMORY_PATH) else '.', exist_ok=True)
        with open(MEMORY_PATH, 'w', encoding='utf-8') as f:
            f.write("# 🧠 Memory.md - AgliLuz (Memoria Persistente de Aprendizaje)\n\n## 1. Blacklist Dinámica\n- telemedicina\n- pantallas led comerciales\n")
            
    return default_config

def extraer_texto_desde_url(url):
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', '').lower():
            with io.BytesIO(response.content) as f:
                reader = PdfReader(f)
                texto_completo = ""
                for page in reader.pages[:20]:
                    texto_completo += page.extract_text() or ""
            return texto_completo.lower()
    except Exception:
        pass
    return ""

def extraer_detalle_profundo_web(codigo_externo):
    """
    Entra a la ficha de Mercado Público mediante Playwright para extraer 
    recuadros internos (Cuadro de ofertas, marcas y telegestión).
    """
    url_ficha = f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?id={codigo_externo}"
    resultado_web = {
        "Competencia_Web": "No especificado en ficha web",
        "Detalle_Ofertas_Web": "Sin cuadro de ofertas abierto"
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url_ficha, timeout=35000)
            page.wait_for_load_state('domcontentloaded', timeout=15000)
            
            texto_ficha = page.inner_text('body').lower()
            
            if "cuadro de ofertas" in texto_ficha or "oferta" in texto_ficha:
                resultado_web["Detalle_Ofertas_Web"] = "Cuadro de ofertas detectado y procesado desde la web"
            
            if "ge lighting" in texto_ficha:
                resultado_web["Competencia_Web"] = "GE Lighting"
            elif "osram" in texto_ficha or "ledvance" in texto_ficha:
                resultado_web["Competencia_Web"] = "Osram / Ledvance"
            elif "cree" in texto_ficha:
                resultado_web["Competencia_Web"] = "Cree Lighting"
            elif "philips" in texto_ficha:
                resultado_web["Competencia_Web"] = "Philips / Signify"
            else:
                resultado_web["Competencia_Web"] = "Competencia Local / Alternativa"
                
            browser.close()
    except Exception as e:
        print(f"Nota Playwright en {codigo_externo}: {e}")
        
    return resultado_web

def extraer_parametros_tecnicos_bases(texto):
    potencias = re.findall(r'(\d+[\.,]?\d*)\s*(?:w|watt|watts)', texto, re.IGNORECASE)
    potencia_str = ", ".join(sorted(list(set(potencias)))) + " W" if potencias else "No especificado en bases"

    flujos = re.findall(r'(\d+[\.,]?\d*)\s*(?:lm|lumenes|lúmenes)', texto, re.IGNORECASE)
    flujo_str = ", ".join(sorted(list(set(flujos)))) + " lm" if flujos else "No especificado en bases"

    ip_match = re.findall(r'ip\s*([0-6][5678])', texto, re.IGNORECASE)
    ip_str = "IP" + ", ".join(sorted(list(set(ip_match)))) if ip_match else "No especificado"

    ik_match = re.findall(r'ik\s*([0-1][0-9])', texto, re.IGNORECASE)
    ik_str = "IK" + ", ".join(sorted(list(set(ik_match)))) if ik_match else "No especificado"

    certificaciones = []
    if 'sec' in texto: certificaciones.append("Certificación SEC (Chile)")
    if 'ds1' in texto or 'decreto supremo' in texto or 'norma lumínica' in texto: certificaciones.append("Decreto Supremo N°1 (Norma Lumínica Chile)")
    cert_str = " | ".join(certificaciones) if certificaciones else "Normativa estándar de licitación"

    telegestion_detectada = []
    if 'telegestion' in texto or 'telegestión' in texto: telegestion_detectada.append("Exige Telegestión")
    if 'zhaga' in texto: telegestion_detectada.append("Zócalo Zhaga")
    if 'nema' in texto: telegestion_detectada.append("Zócalo NEMA")
    if 'interact' in texto: telegestion_detectada.append("Plataforma Interact")
    if 'dynalite' in texto: telegestion_detectada.append("Sistema Dynalite")
    
    otros_str = " | ".join(telegestion_detectada) if telegestion_detectada else "Sin requerimientos de control específicos"

    return potencia_str, flujo_str, ip_str, ik_str, cert_str, otros_str

def procesar_inteligencia_avanzada(row):
    codigo = str(row.get('CodigoExterno', ''))
    texto_base = str(row.get('Nombre', '')) + " " + str(row.get('Descripcion', ''))
    
    documentos = row.get('Documentos', [])
    texto_documentos_adjuntos = ""
    if isinstance(documentos, list):
        for doc in documentos:
            url_doc = doc.get('UrlDocumento', '') or doc.get('URL', '')
            if url_doc and isinstance(url_doc, str) and url_doc.startswith('http'):
                texto_documentos_adjuntos += " " + extraer_texto_desde_url(url_doc)

    datos_web = extraer_detalle_profundo_web(codigo)

    adjudicacion_info = row.get('Adjudicacion', {})
    proveedor_adjudicado = "No especificado / En proceso"
    monto_adjudicado = 0
    cantidad_items = 0
    
    if isinstance(adjudicacion_info, dict):
        items_adj = adjudicacion_info.get('Items', [])
        proveedores = adjudicacion_info.get('Proveedor', [])
        if proveedores and isinstance(proveedores, list):
            proveedor_adjudicado = proveedores[0].get('Nombre', 'Proveedor Externo')
        if items_adj and isinstance(items_adj, list):
            for item in items_adj:
                cantidad_items += float(item.get('Cantidad', 0) or 0)
                monto_adjudicado += float(item.get('Total', 0) or 0)

    texto_total = (texto_base + " " + texto_documentos_adjuntos).lower()
    
    potencia, flujo, ip, ik, certs, control_reqs = extraer_parametros_tecnicos_bases(texto_total)
    marcas_detectadas = datos_web.get("Competencia_Web", "Marca Alternativa")

    pauta_evaluacion = "Evaluada según criterios técnicos, económicos y plazo."
    if 'puntaje' in texto_total or 'evaluacion' in texto_total:
        pauta_evaluacion = "Pauta encontrada en Actas: Criterios ponderados (Precio, Técnica, Experiencia)."

    es_ind = 'ind' in texto_total or 'instituto nacional de deporte' in texto_total or 'instituto nacional del deporte' in texto_total
    
    if 'estadio' in texto_total or 'cancha' in texto_total or 'deportivo' in texto_total or es_ind:
        signify_equivalente = "Arena X + Interact Sports (Proyectores Deportivos)"
        categoria = "Iluminación Deportiva / IND"
    elif 'solar' in texto_total or 'fotovoltaica' in texto_total:
        signify_equivalente = "GreenVision Solar (Autónoma / Vial)"
        categoria = "Iluminación Solar"
    elif 'vial' in texto_total or 'autopista' in texto_total or 'carretera' in texto_total:
        signify_equivalente = "RoadFlair / Xceed Pro + Interact City (Telegestión Vial)"
        categoria = "Iluminación Vial"
    elif 'arquitectonico' in texto_total or 'fachada' in texto_total:
        signify_equivalente = "Tango Pro / Color Kinetics + Dynalite (Control Dinámico)"
        categoria = "Iluminación Arquitectónica"
    else:
        signify_equivalente = "ActiStar / CoreLine (Industrial y General)"
        categoria = "Iluminación General / Industrial"
        
    return pd.Series([
        proveedor_adjudicado, monto_adjudicado, cantidad_items, categoria, 
        signify_equivalente, marcas_detectadas, pauta_evaluacion, 
        potencia, flujo, ip, ik, certs, control_reqs
    ])

def main():
    ticket = os.environ.get('TICKET_MP')
    if not ticket:
        print("Error: TICKET_MP no está configurado.")
        return

    reglas_memoria = cargar_memoria_persistente()

    print("Conectando con la API de Mercado Público...")
    url = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?ticket={ticket}"
    
    response = requests.get(url)
    os.makedirs('agliluz', exist_ok=True)
    
    historial_path = 'agliluz/historial_licitaciones.xlsx'
    dashboard_path = 'agliluz/dashboard_inteligencia_mercado.xlsx'
    
    df_historico = pd.DataFrame()
    if os.path.exists(historial_path):
        try:
            df_historico = pd.read_excel(historial_path)
            print(f"Historial maestro cargado: {len(df_historico)} registros previos.")
        except Exception:
            pass

    df_filtrado = pd.DataFrame()
    if response.status_code == 200:
        data = response.json()
        licitaciones = data.get('Listado', [])
        if licitaciones:
            df_nuevo = pd.DataFrame(licitaciones)
            
            if 'FechaCreacion' in df_nuevo.columns:
                df_nuevo['FechaCreacion'] = pd.to_datetime(df_nuevo['FechaCreacion'], errors='coerce')
                desde_enero_2026 = datetime(2026, 1, 1)
                df_nuevo = df_nuevo[df_nuevo['FechaCreacion'] >= desde_enero_2026]
            
            target_keywords = reglas_memoria.get("whitelist_objetivos", [])
            text_columns = [col for col in ['Nombre', 'Descripcion', 'CodigoExterno', 'Comprador'] if col in df_nuevo.columns]
            
            if text_columns and not df_nuevo.empty:
                df_nuevo['texto_busqueda'] = df_nuevo[text_columns].astype(str).agg(' '.join, axis=1).str.lower()
                pattern = '|'.join(target_keywords)
                
                codigos_objetivo = ['2378-40-lr25', '858-190-lr25', '4483-17-lr26']
                
                mask_keywords = df_nuevo['texto_busqueda'].str.contains(pattern, na=False, case=False)
                mask_codigos = df_nuevo['CodigoExterno'].astype(str).str.lower().isin(codigos_objetivo)
                mask_ind = df_nuevo['texto_busqueda'].str.contains('ind|instituto nacional', na=False, case=False)
                
                df_filtrado = df_nuevo[mask_keywords | mask_codigos | mask_ind].copy()
                df_filtrado = df_filtrado.drop(columns=['texto_busqueda'])
            
            if not df_filtrado.empty:
                blacklist = reglas_memoria.get("blacklist", [])
                cols_disponibles = [c for c in ['Nombre', 'Descripcion'] if c in df_filtrado.columns]
                if cols_disponibles:
                    for palabra in blacklist:
                        mask = False
                        for col in cols_disponibles:
                            mask = mask | df_filtrado[col].astype(str).str.lower().str.contains(palabra, na=False)
                        df_filtrado = df_filtrado[~mask]

            if not df_filtrado.empty:
                cols_resultado = [
                    'Proveedor_Adjudicado', 'Monto_Adjudicado_CLP', 'Cantidad_Unidades', 
                    'Categoria_Proyecto', 'Signify_Equivalente', 'Marcas_Competencia_Detectadas', 
                    'Pautas_Y_Puntajes_Evaluacion', 'Requerimiento_Potencia', 'Requerimiento_Flujo_Luminoso', 
                    'Requerimiento_IP', 'Requerimiento_IK', 'Certificaciones_Exigidas', 'Sistemas_Control_Telegestion'
                ]
                print("Iniciando extracción profunda con Playwright y análisis de Telegestión...")
                df_filtrado[cols_resultado] = df_filtrado.apply(procesar_inteligencia_avanzada, axis=1)

    # LIMPIEZA AUTOMÁTICA DE DATOS DE EJEMPLO
    if not df_filtrado.empty:
        if not df_historico.empty:
            cols_check = [c for c in ['Nombre', 'CodigoExterno'] if c in df_historico.columns]
            if cols_check:
                mask_ejemplo = False
                for c in cols_check:
                    mask_ejemplo = mask_ejemplo | df_historico[c].astype(str).str.contains('Ejemplo|ejemplo|\[Ejemplo\]', na=False, regex=True)
                df_historico = df_historico[~mask_ejemplo]
            
            # Combinar datos nuevos (prioridad) con históricos limpios
            df_combinado = pd.concat([df_filtrado, df_historico]).drop_duplicates(subset=['CodigoExterno'], keep='first')
        else:
            df_combinado = df_filtrado
    else:
        # Si no hubo filtrado nuevo, al menos limpiamos el histórico
        if not df_historico.empty:
            cols_check = [c for c in ['Nombre', 'CodigoExterno'] if c in df_historico.columns]
            if cols_check:
                mask_ejemplo = False
                for c in cols_check:
                    mask_ejemplo = mask_ejemplo | df_historico[c].astype(str).str.contains('Ejemplo|ejemplo|\[Ejemplo\]', na=False, regex=True)
                df_historico = df_historico[~mask_ejemplo]
        df_combinado = df_historico

    if df_combinado.empty:
        df_combinado = pd.DataFrame(columns=[
            'CodigoExterno', 'Nombre', 'Signify_Equivalente', 'Requerimiento_Potencia', 
            'Requerimiento_Flujo_Luminoso', 'Certificaciones_Exigidas', 'Sistemas_Control_Telegestion',
            'Proveedor_Adjudicado', 'Monto_Adjudicado_CLP', 'Cantidad_Unidades', 'Categoria_Proyecto'
        ])

    df_combinado.to_excel(historial_path, index=False)
    
    with pd.ExcelWriter(dashboard_path, engine='openpyxl') as writer:
        df_combinado.to_excel(writer, sheet_name='Dashboard_General', index=False)
        if 'Proveedor_Adjudicado' in df_combinado.columns:
            cols_mapa = [col for col in ['CodigoExterno', 'Nombre', 'Proveedor_Adjudicado', 'Monto_Adjudicado_CLP', 'Sistemas_Control_Telegestion', 'Signify_Equivalente'] if col in df_combinado.columns]
            df_combinado[cols_mapa].to_excel(writer, sheet_name='Mapa_Competencia_Adjudicadas', index=False)
        
        portafolio_signify = pd.DataFrame({
            "Familia_Signify": ["RoadFlair + Interact City", "Arena X + Interact Sports", "Tango Pro + Dynalite", "Color Kinetics", "GreenVision Solar"],
            "Aplicacion": ["Vial Inteligente y Telegestión", "Estadios y Recintos Deportivos", "Arquitectónica y Control Dinámico", "Fachadas y Iluminación Monumental", "Autónoma Fotovoltaica"],
            "Estrategia_Chile": ["Liderazgo en smart cities y control centralizado", "Máximo rendimiento y conectividad deportiva", "Control avanzado de escenas y tonos", "Cumplimiento estricto DS1 y diseño", "Sostenibilidad sin red eléctrica"]
        })
        portafolio_signify.to_excel(writer, sheet_name='Portafolio_Signify_Chile', index=False)

    print(f"¡Proceso finalizado con éxito! Total registros analizados: {len(df_combinado)}")

if __name__ == '__main__':
    main()
