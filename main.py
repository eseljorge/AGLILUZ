import os
import json
import re
import requests
import pandas as pd
from datetime import datetime, timedelta
from pypdf import PdfReader
import io

CONFIG_PATH = 'agliluz/correcciones.json'

def cargar_memoria_correcciones():
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
            "luminaria", "luminarias", "foco vial", "ind", "instituto nacional de deportes"
        ]
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=4)
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

def extraer_parametros_tecnicos_bases(texto):
    potencias = re.findall(r'(\d+[\.,]?\d*)\s*(?:w|watt|watts)', texto, re.IGNORECASE)
    potencia_str = ", ".join(sorted(list(set(potencias)))) + " W" if potencias else "No especificado en bases"

    flujos = re.findall(r'(\d+[\.,]?\d*)\s*(?:lm|lumenes|lúmenes)', texto, re.IGNORECASE)
    flujo_str = ", ".join(sorted(list(set(flujos)))) + " lm" if flujos else "No especificado en bases"

    cri_match = re.findall(r'(?:cri|ra)\s*[:>]?\s*(\d+)', texto, re.IGNORECASE)
    cri_str = "CRI " + ", ".join(sorted(list(set(cri_match)))) if cri_match else "No especificado"

    ip_match = re.findall(r'ip\s*([0-6][5678])', texto, re.IGNORECASE)
    ip_str = "IP" + ", ".join(sorted(list(set(ip_match)))) if ip_match else "No especificado"

    ik_match = re.findall(r'ik\s*([0-1][0-9])', texto, re.IGNORECASE)
    ik_str = "IK" + ", ".join(sorted(list(set(ik_match)))) if ik_match else "No especificado"

    cct_match = re.findall(r'(\d{3,4})\s*k\b', texto, re.IGNORECASE)
    cct_str = ", ".join(sorted(list(set(cct_match)))) + "K" if cct_match else "No especificado"

    garantia_match = re.findall(r'(\d+)\s*(?:años|ano|anos)\s*de\s*garantía', texto, re.IGNORECASE)
    garantia_str = ", ".join(sorted(list(set(garantia_match)))) + " años" if garantia_match else "No especificado"

    surge_match = re.findall(r'(\d+)\s*kv\b', texto, re.IGNORECASE)
    surge_str = ", ".join(sorted(list(set(surge_match)))) + " kV" if surge_match else "No especificado"

    certificaciones = []
    if 'sec' in texto: certificaciones.append("Certificación SEC (Chile)")
    if 'ds1' in texto or 'decreto supremo' in texto or 'norma lumínica' in texto: certificaciones.append("Decreto Supremo N°1 (Norma Lumínica Chile)")
    if 'iso' in texto: certificaciones.append("Norma ISO")
    if 'ce' in texto: certificaciones.append("Marcado CE / RoHs")
    cert_str = " | ".join(certificaciones) if certificaciones else "Normativa estándar de licitación"

    otros_elementos = []
    if 'fotometria' in texto or 'fotometría' in texto: otros_elementos.append("Exige Estudio Fotométrico")
    if 'telegestion' in texto or 'telegestión' in texto or 'zhaga' in texto or 'nema' in texto: otros_elementos.append("Telegestión / Zócalo NEMA o Zhaga")
    if 'driver' in texto or 'alimentador' in texto: otros_elementos.append("Especifica Driver / LED Driver")
    otros_str = " | ".join(otros_elementos) if otros_elementos else "Sin requerimientos adicionales específicos"

    return potencia_str, flujo_str, cri_str, ip_str, ik_str, cct_str, garantia_str, surge_str, cert_str, otros_str

def procesar_inteligencia_avanzada(row):
    texto_base = str(row.get('Nombre', '')) + " " + str(row.get('Descripcion', ''))
    
    documentos = row.get('Documentos', [])
    texto_documentos_adjuntos = ""
    
    if isinstance(documentos, list):
        for doc in documentos:
            url_doc = doc.get('UrlDocumento', '') or doc.get('URL', '')
            if url_doc and isinstance(url_doc, str) and url_doc.startswith('http'):
                texto_documentos_adjuntos += " " + extraer_texto_desde_url(url_doc)

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
    
    potencia, flujo, cri, ip, ik, cct, garantia, surge, certs, otros_reqs = extraer_parametros_tecnicos_bases(texto_total)

    marcas_detectadas = "No especificado en actas"
    if 'philips' in texto_total:
        marcas_detectadas = "Philips / Signify"
    elif 'ge' in texto_total:
        marcas_detectadas = "GE Lighting"
    elif 'osram' in texto_total or 'ledvance' in texto_total:
        marcas_detectadas = "Osram / Ledvance"
    elif 'cree' in texto_total:
        marcas_detectadas = "Cree Lighting"
    else:
        marcas_detectadas = "Marca Alternativa / Competencia Local"

    pauta_evaluacion = "Evaluada según criterios técnicos, económicos y plazo."
    if 'puntaje' in texto_total or 'evaluacion' in texto_total or 'nota' in texto_total:
        pauta_evaluacion = "Pauta encontrada en Actas: Criterios ponderados (Precio, Especificaciones Técnicas, Experiencia)."

    es_ind = 'ind' in texto_total or 'instituto nacional de deporte' in texto_total or 'instituto nacional del deporte' in texto_total
    
    if 'estadio' in texto_total or 'cancha' in texto_total or 'deportivo' in texto_total or es_ind:
        signify_equivalente = "Arena X / Proyectores Deportivos Alta Gama"
        categoria = "Iluminación Deportiva / IND"
    elif 'solar' in texto_total or 'fotovoltaica' in texto_total:
        signify_equivalente = "GreenVision Solar (Autónoma / Vial)"
        categoria = "Iluminación Solar"
    elif 'vial' in texto_total or 'autopista' in texto_total or 'carretera' in texto_total:
        signify_equivalente = "RoadFlair / Xceed Pro (Vial Alta Eficiencia)"
        categoria = "Iluminación Vial"
    elif 'arquitectonico' in texto_total or 'fachada' in texto_total:
        signify_equivalente = "Tango Pro / Color Kinetics (Arquitectónica)"
        categoria = "Iluminación Arquitectónica"
    else:
        signify_equivalente = "ActiStar / CoreLine (Industrial y General)"
        categoria = "Iluminación General / Industrial"
        
    return pd.Series([
        proveedor_adjudicado, monto_adjudicado, cantidad_items, categoria, 
        signify_equivalente, marcas_detectadas, pauta_evaluacion, 
        potencia, flujo, cri, ip, ik, cct, garantia, surge, certs, otros_reqs
    ])

def main():
    ticket = os.environ.get('TICKET_MP')
    if not ticket:
        print("Error: TICKET_MP no está configurado.")
        return

    reglas_aprendidas = cargar_memoria_correcciones()

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
            
            target_keywords = reglas_aprendidas.get("whitelist_objetivos", [])
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
                blacklist = reglas_aprendidas.get("blacklist", [])
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
                    'Requerimiento_CRI', 'Requerimiento_IP', 'Requerimiento_IK', 'Requerimiento_CCT_Kelvin',
                    'Requerimiento_Garantia', 'Requerimiento_Proteccion_kV', 'Certificaciones_Exigidas', 'Otros_Requerimientos_Tecnicos'
                ]
                df_filtrado[cols_resultado] = df_filtrado.apply(procesar_inteligencia_avanzada, axis=1)

    if not df_filtrado.empty:
        if not df_historico.empty and 'CodigoExterno' in df_historico.columns and 'CodigoExterno' in df_filtrado.columns:
            df_combinado = pd.concat([df_historico, df_filtrado]).drop_duplicates(subset=['CodigoExterno'], keep='first')
        else:
            df_combinado = df_filtrado
    else:
        df_combinado = df_historico

    if df_combinado.empty:
        df_combinado = pd.DataFrame(columns=[
            'CodigoExterno', 'Nombre', 'Nivel_Compatibilidad', 'Signify_Equivalente', 
            'Requerimiento_Potencia', 'Requerimiento_Flujo_Luminoso', 'Certificaciones_Exigidas',
            'Proveedor_Adjudicado', 'Monto_Adjudicado_CLP', 'Cantidad_Unidades', 'Categoria_Proyecto'
        ])

    df_combinado.to_excel(historial_path, index=False)
    
    with pd.ExcelWriter(dashboard_path, engine='openpyxl') as writer:
        df_combinado.to_excel(writer, sheet_name='Dashboard_General', index=False)
        if 'Proveedor_Adjudicado' in df_combinado.columns:
            cols_mapa = [col for col in ['CodigoExterno', 'Nombre', 'Proveedor_Adjudicado', 'Monto_Adjudicado_CLP', 'Requerimiento_Potencia', 'Requerimiento_Flujo_Luminoso', 'Certificaciones_Exigidas', 'Signify_Equivalente'] if col in df_combinado.columns]
            df_combinado[cols_mapa].to_excel(writer, sheet_name='Mapa_Competencia_Adjudicadas', index=False)
        
        portafolio_signify = pd.DataFrame({
            "Familia_Signify": ["RoadFlair", "Xceed Pro", "Tango Pro", "ActiStar", "Arena X", "GreenVision Solar"],
            "Aplicacion": ["Vial Alta Eficiencia", "Vial / Autopistas", "Arquitectónica / Proyectores", "Industrial / General", "Estadios y Canchas Deportivas", "Solar Fotovoltaica Autónoma"],
            "Estrategia_Chile": ["Liderazgo en vías urbanas e interurbanas", "Alto flujo lumínico y robustez vial", "Control estricto DS1 y diseño de fachadas", "Versatilidad e industrial general", "Máximo rendimiento para recintos deportivos", "Sostenibilidad sin red eléctrica"]
        })
        portafolio_signify.to_excel(writer, sheet_name='Portafolio_Signify_Chile', index=False)

    print(f"¡Proceso finalizado! Total registros en historial: {len(df_combinado)}")

if __name__ == '__main__':
    main()
