import os
import requests
import pandas as pd
from datetime import datetime

def evaluar_portafolio_y_normativa(row):
    """
    Función inteligente que analiza el título y descripción de la licitación
    para sugerir una solución base del portafolio y verificar cumplimiento normativo DS1.
    """
    texto = str(row.get('Nombre', '')) + " " + str(row.get('Descripcion', ''))
    texto = texto.lower()
    
    sugerencia_producto = "Revisión general de portafolio Signify"
    cumplimiento_ds1 = "Requiere revisión de fotometría (Control de flujo al Hemisferio Superior FHS = 0%)"
    
    # Cruce con líneas de producto y aplicaciones específicas
    if 'vial' in texto or 'alumbrado' in texto or 'farola' in texto or 'autopista' in texto or 'postacion' in texto:
        sugerencia_producto = "Luminaria Vial LED (Ej: Philips Luma / RoadGrade) con opción de Telegestión Interact City"
        cumplimiento_ds1 = "Aplica DS1: Exigir temperatura de color cálida (máx. 3000K o 2700K según zona de protección astronómica) y FHS 0%."
    elif 'estadio' in texto or 'cancha' in texto or 'deportivo' in texto or 'polideportivo' in texto:
        sugerencia_producto = "Proyectores de altas prestaciones (Ej: Philips ArenaVision / Color Kinetics) con control DMX/Interact Sports"
        cumplimiento_ds1 = "Aplica DS1: Direccionamiento estricto de proyectores para evitar deslumbramiento y emisión hacia el cielo."
    elif 'fachada' in texto or 'monumento' in texto or 'arquitectonico' in texto or 'arquitectónico' in texto:
        sugerencia_producto = "Iluminación Arquitectónica LED (Ej: Color Kinetics / Architectural Flood) con control dinámico"
        cumplimiento_ds1 = "Aplica DS1: Respetar límites de brillo y apagado en horario nocturno según normativa local."
    elif 'telegestion' in texto or 'telegestión' in texto or 'smart city' in texto:
        sugerencia_producto = "Sistema de Control Centralizado Interact City / Nodes Zhaga/NEMA"
        cumplimiento_ds1 = "Aplica DS1: Compatible con reducción de flujo nocturno automatizada para cumplimiento normativo."
    else:
        sugerencia_producto = "Luminaria LED General / CoreLine / Proyectores modulares"
        cumplimiento_ds1 = "Verificar bases técnicas para cumplimiento de norma de emisión lumínica."
        
    return pd.Series([sugerencia_producto, cumplimiento_ds1])

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
        print("Conexión exitosa. Filtrando y evaluando con portafolio técnico...")
        
        licitaciones = data.get('Listado', [])
        if licitaciones:
            df = pd.DataFrame(licitaciones)
            
            # Palabras clave del rubro
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
                # Aplicar la evaluación automática de portafolio y cumplimiento DS1
                df_filtrado[['Propuesta_Portafolio_Philips', 'Auditoria_Normativa_DS1']] = df_filtrado.apply(evaluar_portafolio_y_normativa, axis=1)
                
                df_filtrado.to_excel(output_path, index=False)
                print(f"¡Éxito! Se procesaron {len(df_filtrado)} oportunidades con evaluación técnica integrada.")
            else:
                print("No se encontraron licitaciones nuevas con los criterios en esta ejecución.")
                df.head(0).to_excel(output_path, index=False)
                with open('agliluz/resumen.txt', 'w') as f:
                    f.write(f"Ejecución limpia sin coincidencias el {datetime.now()}")
        else:
            print("No se encontraron licitaciones en el listado general de la API.")
            with open('agliluz/resumen.txt', 'w') as f:
                f.write(f"Ejecución sin registros generales el {datetime.now()}")
    else:
        print(f"Error al conectar con la API: {response.status_code}")
        with open('agliluz/error_log.txt', 'w') as f:
            f.write(f"Error API code: {response.status_code} - {datetime.now()}")

if __name__ == '__main__':
    main()
