import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from pypdf import PdfReader
import io

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

def evaluar_cumplimiento_bases(row):
    texto_base = str(row.get('Nombre', '')) + " " + str(row.get('Descripcion', ''))
    
    enlace_doc = row.get('Enlace', '') or row.get('Adjudicacion', '')
    texto_pdf = ""
    if enlace_doc and isinstance(enlace_doc, str) and ('http' in enlace_doc):
        texto_pdf = extraer_texto_desde_url(enlace_doc)
        
    texto_total = (texto_base + " " + texto_pdf).lower()
    
    exige_led = 'led' in texto_total or 'eficiencia energetica' in texto_total or 'eficiencia energética' in texto_total
    exige_fotometria = 'fotometria' in texto_total or 'fotometría' in texto_total or 'curva' in texto_total or 'fhs' in texto_total
    exige_norma = 'decreto' in texto_total or 'ds1' in texto_total or 'norma' in texto_total or 'emision' in texto_total or 'emisión' in texto_total
    exige_control = 'telegestion' in texto_total or 'telegestión' in texto_total or 'control' in texto_total or 'dimming' in texto_total
    
    if exige_led and (exige_fotometria or exige_norma or exige_control or 'alumbrado' in texto_total or 'luminaria' in texto_total):
        compatibilidad = "Alta"
        if 'estadio' in texto_total or 'cancha' in texto_total:
            propuesta = "Proyectores Philips ArenaVision + Sistema Interact Sports (FHS 0%)"
        elif 'telegestion' in texto_total or 'smart city' in texto_total:
            propuesta = "Luminarias Viales Philips Luma/RoadGrade + Plataforma Interact City"
        else:
            propuesta = "Luminarias LED Philips de alta eficiencia con certificación fotométrica y cumplimiento DS1"
        auditoria_ds1 = "Verificado en bases: Factible cumplir con límite de flujo hemisferio superior y temperatura de color."
    elif exige_led:
        compatibilidad = "Media"
        propuesta = "Luminaria LED General / CoreLine / Módulo estándar"
        auditoria_ds1 = "Requiere revisión de bases administrativas para asegurar cumplimiento de potencia y fotometría."
    else:
        compatibilidad = "Baja"
        propuesta = "Luminaria genérica o sin especificación detallada"
        auditoria_ds1 = "Verificar alcance técnico en terreno o bases."
        
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

    print("Conectando con la API de Mercado Público...")
    url = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?ticket={ticket}"
    
    response = requests.get(url)
    os.makedirs('agliluz', exist_ok=True)
    
    historial_path = 'agliluz/historial_licitaciones.xlsx'
    reporte_path = 'agliluz/reporte_licitaciones.xlsx'
    
    # 1. Cargar historial acumulado previo si existe
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
            
            # 2. Filtro temporal de los últimos 10 días
            if 'FechaCreacion' in df_nuevo.columns:
                df_nuevo['FechaCreacion'] = pd.to_datetime(df_nuevo['FechaCreacion'], errors='coerce')
                hace_10_dias = datetime.now() - timedelta(days=10)
                df_nuevo = df_nuevo[df_nuevo['FechaCreacion'] >= hace_10_dias]
            
            # 3. Filtro estricto de iluminación
            lighting_keywords = [
                'iluminacion', 'iluminación', 'luminaria', 'luminarias', 
                'led', 'alumbrado', 'foco', 'focos', 'proyector', 'proyectores', 
                'farola', 'farolas', 'postacion', 'postación', 'fotometria', 
                'fotometría', 'telegestion', 'telegestión', 'smart city'
            ]
            
            text_columns = [col for col in ['Nombre', 'Descripcion', 'CodigoExterno'] if col in df_nuevo.columns]
            
            if text_columns and not df_nuevo.empty:
                df_nuevo['texto_busqueda'] = df_nuevo[text_columns].astype(str).agg(' '.join, axis=1).str.lower()
                pattern = '|'.join(lighting_keywords)
                df_filtrado = df_nuevo[df_nuevo['texto_busqueda'].str.contains(pattern, na=False, case=False)].copy()
                df_filtrado = df_filtrado.drop(columns=['texto_busqueda'])
            else:
                df_filtrado = pd.DataFrame()
            
            if not df_filtrado.empty:
                # Auditar cumplimiento técnico
                df_filtrado[['Nivel_Compatibilidad', 'Propuesta_Portafolio', 'Auditoria_Normativa_DS1']] = df_filtrado.apply(evaluar_cumplimiento_bases, axis=1)
                
                # 4. Fusionar con el historial maestro para no perder nada previo
                if not df_historico.empty and 'CodigoExterno' in df_historico.columns and 'CodigoExterno' in df_filtrado.columns:
                    # Unir y eliminar duplicados manteniendo registros históricos y sumando nuevos
                    df_combinado = pd.concat([df_historico, df_filtrado]).drop_duplicates(subset=['CodigoExterno'], keep='first')
                else:
                    df_combinado = df_filtrado if df_historico.empty else pd.concat([df_historico, df_filtrado])
                
                # Guardar en ambos archivos (historial persistente y reporte para artefactos)
                df_combinado.to_excel(historial_path, index=False)
                df_combinado.to_excel(reporte_path, index=False)
                
                # Alerta solo para los de alta compatibilidad recién detectados
                df_alta = df_filtrado[df_filtrado['Nivel_Compatibilidad'] == 'Alta']
                if not df_alta.empty:
                    enviar_alerta_telegram(f"🚨 *AGLILUZ - Nuevas Oportunidades (Últimos 10 días)*\n\nSe detectaron *{len(df_alta)}* procesos nuevos de iluminación compatibles con Philips y DS1. Historial acumulado actualizado.")
                
                print(f"¡Éxito! Historial actualizado. Total acumulado: {len(df_combinado)} registros.")
            else:
                print("No se encontraron nuevas licitaciones de iluminación en esta ejecución. Se conserva el historial previo.")
                if not df_historico.empty:
                    df_historico.to_excel(reporte_path, index=False)
        else:
            print("No hay licitaciones en el listado general de la API.")
    else:
        print(f"Error al conectar con la API: {response.status_code}")

if __name__ == '__main__':
    main()
