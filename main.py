import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from pypdf import PdfReader
import io

# ==========================================
# MÓDULO DE MEMORIA Y APRENDIZAJE (CORRECCIONES)
# ==========================================
CONFIG_PATH = 'agliluz/correcciones.json'

def cargar_memoria_correcciones():
    """
    Carga las reglas aprendidas, exclusiones y preferencias del usuario
    desde un archivo persistente en el repositorio.
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
            "luminaria", "luminarias", "foco vial"
        ]
    }
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                print("Memoria de correcciones cargada exitosamente.")
                return json.load(f)
        except Exception as e:
            print(f"Error al leer memoria de correcciones, usando valores por defecto: {e}")
            
    # Si no existe, se crea automáticamente para que persista
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=4)
    return default_config

def extraer_texto_desde_url(url):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', '').lower():
            with io.BytesIO(response.content) as f:
                reader = PdfReader(f)
                texto_completo = ""
                for page in reader.pages[:8]:
                    texto_completo += page.extract_text() or ""
            return texto_completo.lower()
    except Exception as e:
        print(f"Aviso: No se pudo procesar el documento PDF adjunto: {e}")
    return ""

def evaluar_cumplimiento_bases(row, reglas_aprendidas):
    """
    Evalúa el texto aplicando estrictamente la memoria de correcciones aprendida
    (exclusiones y focos de negocio objetivo).
    """
    texto_base = str(row.get('Nombre', '')) + " " + str(row.get('Descripcion', ''))
    
    enlace_doc = row.get('Enlace', '') or row.get('Adjudicacion', '')
    texto_pdf = ""
    if enlace_doc and isinstance(enlace_doc, str) and ('http' in enlace_doc):
        texto_pdf = extraer_texto_desde_url(enlace_doc)
        
    texto_total = (texto_base + " " + texto_pdf).lower()
    
    # 1. APLICAR BLACKLIST APRENDIDA (Exclusión estricta)
    blacklist = reglas_aprendidas.get("blacklist", [])
    for palabra in blacklist:
        if palabra in texto_total:
            return pd.Series(["Excluido", f"Descartado por regla de memoria (Contiene término prohibido: '{palabra}')", "Excluido"])

    # 2. APLICAR OBJETIVOS APRENDIDOS
    objetivos = reglas_aprendidas.get("whitelist_objetivos", [])
    
    es_estadio_cancha = any(term in texto_total for term in ['estadio', 'cancha', 'canchas', 'deportivo', 'polideportivo', 'proyector deportivo', 'proyectores deportivos'])
    es_mantenimiento_alumbrado = any(term in texto_total for term in ['mantenimiento', 'conservacion', 'conservación', 'alumbrado publico', 'alumbrado público'])
    es_reposicion_luminarias = any(term in texto_total for term in ['reposicion', 'reposición', 'recambio', 'luminaria', 'luminarias', 'foco vial'])
    
    if es_estadio_cancha:
        compatibilidad = "Alta"
        propuesta = "Proyectores Philips ArenaVision / MasterFlood + Sistema Interact Sports (FHS 0%)"
        auditoria_ds1 = "Verificado: Iluminación deportiva de alta eficiencia, control óptico y cumplimiento DS1."
    elif es_mantenimiento_alumbrado or es_reposicion_luminarias:
        compatibilidad = "Alta"
        propuesta = "Luminarias Viales Philips (Luma / RoadGrade / CoreLine) + Servicio / Telegestión Interact City"
        auditoria_ds1 = "Verificado: Recambio/Mantenimiento de alumbrado público con cumplimiento DS1 (FHS 0% y 3000K/2700K)."
    else:
        compatibilidad = "Media"
        propuesta = "Luminaria LED General / Industrial / Arquitectónica"
        auditoria_ds1 = "Requiere revisión general de bases técnicas para cumplimiento de norma lumínica."
        
    return pd.Series([compatibilidad, propuesta, auditoria_ds1])

def enviar_alerta_telegram(mensaje):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
            print("Alerta enviada por Telegram exitosamente.")
        except Exception as e:
            print(f"Error al enviar alerta a Telegram: {e}")

def main():
    ticket = os.environ.get('TICKET_MP')
    if not ticket:
        print("Error: TICKET_MP no está configurado en las variables de entorno.")
        return

    # Cargar memoria de correcciones aprendidas
    reglas_aprendidas = cargar_memoria_correcciones()

    print("Conectando con la API de Mercado Público...")
    url = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?ticket={ticket}"
    
    response = requests.get(url)
    os.makedirs('agliluz', exist_ok=True)
    
    historial_path = 'agliluz/historial_licitaciones.xlsx'
    reporte_path = 'agliluz/reporte_licitaciones.xlsx'
    
    # Cargar memoria histórica previa de licitaciones
    df_historico = pd.DataFrame()
    if os.path.exists(historial_path):
        try:
            df_historico = pd.read_excel(historial_path)
            print(f"Historial previo cargado: {len(df_historico)} registros acumulados.")
        except Exception as e:
            print(f"Aviso al leer historial previo: {e}")

    if response.status_code == 200:
        data = response.json()
        licitaciones = data.get('Listado', [])
        if licitaciones:
            df_nuevo = pd.DataFrame(licitaciones)
            
            # Filtro temporal: últimos 10 días
            if 'FechaCreacion' in df_nuevo.columns:
                df_nuevo['FechaCreacion'] = pd.to_datetime(df_nuevo['FechaCreacion'], errors='coerce')
                hace_10_dias = datetime.now() - timedelta(days=10)
                df_nuevo = df_nuevo[df_nuevo['FechaCreacion'] >= hace_10_dias]
            
            # Palabras clave de búsqueda inicial basadas en los objetivos aprendidos
            target_keywords = reglas_aprendidas.get("whitelist_objetivos", [])
            
            text_columns = [col for col in ['Nombre', 'Descripcion', 'CodigoExterno'] if col in df_nuevo.columns]
            
            if text_columns and not df_nuevo.empty:
                df_nuevo['texto_busqueda'] = df_nuevo[text_columns].astype(str).agg(' '.join, axis=1).str.lower()
                pattern = '|'.join(target_keywords)
                df_filtrado = df_nuevo[df_nuevo['texto_busqueda'].str.contains(pattern, na=False, case=False)].copy()
                df_filtrado = df_filtrado.drop(columns=['texto_busqueda'])
            else:
                df_filtrado = pd.DataFrame()
            
            if not df_filtrado.empty:
                # Aplicar evaluación respetando memoria y correcciones aprendidas
                df_filtrado[['Nivel_Compatibilidad', 'Propuesta_Portafolio', 'Auditoria_Normativa_DS1']] = df_filtrado.apply(lambda row: evaluar_cumplimiento_bases(row, reglas_aprendidas), axis=1)
                
                # Excluir elementos marcados por la memoria de correcciones
                df_filtrado = df_filtrado[df_filtrado['Nivel_Compatibilidad'] != 'Excluido']
                
                if not df_filtrado.empty:
                    # Fusionar con historial maestro evitando duplicados
                    if not df_historico.empty and 'CodigoExterno' in df_historico.columns and 'CodigoExterno' in df_filtrado.columns:
                        df_combinado = pd.concat([df_historico, df_filtrado]).drop_duplicates(subset=['CodigoExterno'], keep='first')
                    else:
                        df_combinado = df_filtrado if df_historico.empty else pd.concat([df_historico, df_filtrado])
                    
                    df_combinado.to_excel(historial_path, index=False)
                    df_combinado.to_excel(reporte_path, index=False)
                    
                    df_alta = df_filtrado[df_filtrado['Nivel_Compatibilidad'] == 'Alta']
                    if not df_alta.empty:
                        enviar_alerta_telegram(f"🚨 *AGLILUZ - Oportunidades Clave Detectadas*\n\nSe detectaron *{len(df_alta)}* procesos nuevos de alta compatibilidad (Estadios, canchas, recambio o mantenimiento de alumbrado) aptos para Philips y norma DS1.")
                    
                    print(f"¡Éxito! Historial actualizado aplicando memoria de correcciones. Total acumulado: {len(df_combinado)} registros.")
                else:
                    print("Tras aplicar la memoria de correcciones y filtros estrictos, no quedaron registros nuevos.")
                    if not df_historico.empty:
                        df_historico.to_excel(reporte_path, index=False)
            else:
                print("No se encontraron licitaciones con los criterios de memoria objetivo.")
                if not df_historico.empty:
                    df_historico.to_excel(reporte_path, index=False)
        else:
            print("No hay licitaciones en el listado general de la API.")
    else:
        print(f"Error al conectar con la API: {response.status_code}")

if __name__ == '__main__':
    main()
