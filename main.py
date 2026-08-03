import os
import requests
import pandas as pd
from datetime import datetime
from pypdf import PdfReader
import io

def analizar_pdf_adjunto(url_pdf):
    """
    Descarga y lee de forma segura un documento PDF adjunto utilizando pypdf
    para extraer exigencias técnicas clave.
    """
    try:
        response = requests.get(url_pdf, timeout=10)
        if response.status_code == 200:
            with io.BytesIO(response.content) as f:
                reader = PdfReader(f)
                texto_pdf = ""
                # Leer hasta las primeras 5 páginas para extraer especificaciones clave
                for page in reader.pages[:5]:
                    texto_pdf += page.extract_text() or ""
            return texto_pdf.lower()
    except Exception as e:
        print(f"No se pudo procesar el PDF adjunto: {e}")
    return ""

def evaluar_portafolio_y_normativa(row):
    texto = str(row.get('Nombre', '')) + " " + str(row.get('Descripcion', ''))
    
    # Si la API entrega algún enlace a documentos adjuntos, se puede analizar aquí
    url_documento = row.get('Enlace', '') # O campo equivalente según la respuesta de la API
    if url_documento and url_documento.endswith('.pdf'):
        texto_pdf = analizar_pdf_adjunto(url_documento)
        texto += " " + texto_pdf
        
    texto = texto.lower()
    
    sugerencia_producto = "Revisión general de portafolio Signify"
    cumplimiento_ds1 = "Requiere revisión de fotometría (FHS = 0%)"
    
    if 'vial' in texto or 'alumbrado' in texto or 'farola' in texto or 'autopista' in texto or 'postacion' in texto:
        sugerencia_producto = "Luminaria Vial LED (Ej: Philips Luma / RoadGrade) + Telegestión Interact City"
        cumplimiento_ds1 = "Aplica DS1: Temperatura de color máx. 3000K/2700K y FHS 0% obligatorio."
    elif 'estadio' in texto or 'cancha' in texto or 'deportivo' in texto:
        sugerencia_producto = "Proyectores de altas prestaciones (Ej: Philips ArenaVision) + Control DMX"
        cumplimiento_ds1 = "Aplica DS1: Direccionamiento estricto para evitar deslumbramiento celeste."
    elif 'fachada' in texto or 'monumento' in texto or 'arquitectonico' in texto:
        sugerencia_producto = "Iluminación Arquitectónica LED (Color Kinetics) con control dinámico"
        cumplimiento_ds1 = "Aplica DS1: Respetar límites de luminancia nocturna y apagado programado."
    elif 'telegestion' in texto or 'smart city' in texto:
        sugerencia_producto = "Sistema de Control Centralizado Interact City / NEMA-Zhaga"
        cumplimiento_ds1 = "Aplica DS1: Compatible con regulación automatizada de flujo en horario nocturno."
    else:
        sugerencia_producto = "Luminaria LED General / CoreLine"
        cumplimiento_ds1 = "Verificar bases técnicas para norma de emisión lumínica."
        
    return pd.Series([sugerencia_producto, cumplimiento_ds1])

def enviar_alerta_telegram(mensaje):
    """
    Envía una notificación automática a Telegram si las credenciales están configuradas en GitHub Secrets.
    """
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
    
    if response.status_code == 200:
        data = response.json()
        print("Procesando licitaciones y analizando bases...")
        
        licitaciones = data.get('Listado', [])
        if licitaciones:
            df = pd.DataFrame(licitaciones)
            
            keywords = [
                'iluminacion', 'iluminación', 'luminaria', 'luminarias', 
                'led', 'alumbrado', 'foco', 'proyector', 'proyectores', 
                'farola', 'vial', 'optica', 'óptica', 'postacion', 'postación',
                'fotometria', 'fotometría', 'telegestion', 'telegestión',
                'smart city', 'estadio', 'cancha', 'polideportivo', 'deportivo',
                'fachada', 'monumento', 'concesion', 'concesión', 'mop',
                'red vial', 'autopista', 'soportes'
            ]
            
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
                df_filtrado[['Propuesta_Portafolio_Philips', 'Auditoria_Normativa_DS1']] = df_filtrado.apply(evaluar_portafolio_y_normativa, axis=1)
                df_filtrado.to_excel(output_path, index=False)
                
                mensaje_alerta = f"💡 *AGLILUZ - Nuevas Licitaciones Detectadas*\n\nSe han filtrado {len(df_filtrado)} oportunidades de iluminación listas para evaluar con el portafolio Philips y norma DS1."
                enviar_alerta_telegram(mensaje_alerta)
                
                print(f"¡Éxito! Se procesaron {len(df_filtrado)} oportunidades con análisis técnico y de PDFs.")
            else:
                print("No se encontraron licitaciones nuevas con los criterios en esta ejecución.")
                df.head(0).to_excel(output_path, index=False)
        else:
            print("No se encontraron licitaciones en el listado general.")
    else:
        print(f"Error al conectar con la API: {response.status_code}")

if __name__ == '__main__':
    main()
