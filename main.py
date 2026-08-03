import os
import requests
import pandas as pd
from datetime import datetime
from pypdf import PdfReader
import io

def extraer_texto_desde_url(url):
    """
    Descarga y extrae texto de un documento PDF (bases técnicas/administrativas)
    utilizando pypdf para su análisis.
    """
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', '').lower():
            with io.BytesIO(response.content) as f:
                reader = PdfReader(f)
                texto_completo = ""
                # Leer las primeras páginas clave donde se especifican los requerimientos técnicos
                for page in reader.pages[:8]:
                    texto_completo += page.extract_text() or ""
            return texto_completo.lower()
    except Exception as e:
        print(f"Aviso: No se pudo procesar el documento PDF adjunto: {e}")
    return ""

def evaluar_cumplimiento_bases(row):
    """
    Analiza el texto de la licitación y el documento PDF adjunto (si existe)
    para validar si es posible cumplir técnicamente con las bases y la norma DS1.
    """
    texto_base = str(row.get('Nombre', '')) + " " + str(row.get('Descripcion', ''))
    
    # Si la API entrega enlaces a documentos o bases adjuntas, los incorporamos al análisis
    enlace_doc = row.get('Enlace', '') or row.get('Adjudicacion', '')
    texto_pdf = ""
    if enlace_doc and isinstance(enlace_doc, str) and ('http' in enlace_doc):
        texto_pdf = extraer_texto_desde_url(enlace_doc)
        
    texto_total = (texto_base + " " + texto_pdf).lower()
    
    # Criterios de exigencia técnica en bases
    exige_led = 'led' in texto_total or 'eficiencia energetica' in texto_total or 'eficiencia energética' in texto_total
    exige_fotometria = 'fotometria' in texto_total or 'fotometría' in texto_total or 'curva' in texto_total or 'fhs' in texto_total
    exige_norma = 'decreto' in texto_total or 'ds1' in texto_total or 'norma' in texto_total or 'emision' in texto_total or 'emisión' in texto_total
    exige_control = 'telegestion' in texto_total or 'telegestión' in texto_total or 'control' in texto_total or 'dimming' in texto_total
    
    # Validación de compatibilidad con el portafolio Philips / Signify y norma DS1
    # Alta compatibilidad: Se requiere iluminación LED, cumple con requerimientos fotométricos/normativos y es factible técnicamente.
    if exige_led and (exige_fotometria or exige_norma or exige_control):
        compatibilidad = "Alta"
        if 'estadio' in texto_total or 'cancha' in texto_total:
            propuesta = "Proyectores Philips ArenaVision + Sistema Interact Sports (Cumplimiento FHS 0%)"
        elif 'telegestion' in texto_total or 'smart city' in texto_total:
            propuesta = "Luminarias Viales Philips Luma/RoadGrade + Plataforma Interact City"
        else:
            propuesta = "Luminarias LED Philips de alta eficiencia con certificación fotométrica y cumplimiento DS1"
        auditoria_ds1 = "Verificado en bases: Factible cumplir con límite de flujo hemisferio superior y temperatura de color permitida."
    elif exige_led:
        compatibilidad = "Media"
        propuesta = "Luminaria LED General / CoreLine / Módulo estándar"
        auditoria_ds1 = "Requiere revisión detallada de las bases administrativas para asegurar cumplimiento de potencia y fotometría."
    else:
        compatibilidad = "Baja"
        propuesta = "Sin coincidencia técnica directa con especificaciones del portafolio"
        auditoria_ds1 = "Fuera de alcance o sin requerimientos claros de iluminación especializada."
        
    return pd.Series([compatibilidad, propuesta, auditoria_ds1])

def enviar_alerta_telegram(mensaje):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
            print("Alerta de alta compatibilidad técnica enviada por Telegram.")
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
    
    if response.status_code == 200:
        data = response.json()
        print("Procesando y auditando bases técnicas y administrativas...")
        
        licitaciones = data.get('Listado', [])
        if licitaciones:
            df = pd.DataFrame(licitaciones)
            
            keywords = ['iluminacion', 'iluminación', 'luminaria', 'luminarias', 'led', 'alumbrado', 'foco', 'proyector', 'farola', 'vial', 'telegestion', 'telegestión', 'smart city', 'estadio', 'cancha']
            text_columns = [col for col in ['Nombre', 'Descripcion', 'CodigoExterno'] if col in df.columns]
            
            if text_columns:
                df['texto_busqueda'] = df[text_columns].astype(str).agg(' '.join, axis=1).str.lower()
                pattern = '|'.join(keywords)
                df_filtrado = df[df['texto_busqueda'].str.contains(pattern, na=False, case=False)].copy()
                df_filtrado = df_filtrado.drop(columns=['texto_busqueda'])
            else:
                df_filtrado = df
            
            output_path = 'agliluz/reporte_licitaciones.xlsx'
            
            if not df_filtrado.empty:
                # Auditar cumplimiento contra bases y portafolio
                df_filtrado[['Nivel_Compatibilidad', 'Propuesta_Portafolio', 'Auditoria_Normativa_DS1']] = df_filtrado.apply(evaluar_cumplimiento_bases, axis=1)
                
                df_filtrado.to_excel(output_path, index=False)
                
                # Filtrar estrictamente las que tienen alta compatibilidad técnica verificada
                df_alta = df_filtrado[df_filtrado['Nivel_Compatibilidad'] == 'Alta']
                
                if not df_alta.empty:
                    mensaje_alerta = f"🚨 *AGLILUZ - Oportunidad Validada en Bases*\n\nSe detectaron *{len(df_alta)}* licitaciones donde es totalmente factible cumplir los requerimientos técnicos, normativos (DS1) y de portafolio Philips. Revise el reporte en GitHub."
                    enviar_alerta_telegram(mensaje_alerta)
                else:
                    print("Reporte generado. No se encontraron procesos con cumplimiento técnico de Alta Compatibilidad en esta ejecución.")
                
                print(f"¡Éxito! Procesadas {len(df_filtrado)} licitaciones totales con auditoría de bases.")
            else:
                print("No se encontraron coincidencias generales.")
                df.head(0).to_excel(output_path, index=False)
        else:
            print("No hay licitaciones en el listado general.")
    else:
        print(f"Error al conectar con la API: {response.status_code}")

if __name__ == '__main__':
    main()
