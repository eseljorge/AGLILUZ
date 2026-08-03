import os
import requests
import pandas as pd
from datetime import datetime

def main():
    ticket = os.environ.get('TICKET_MP')
    if not ticket:
        print("Error: TICKET_MP no está configurado en las variables de entorno.")
        return

    print("Conectando con la API de Mercado Público...")
    url = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?ticket={ticket}"
    
    response = requests.get(url)
    
    # Crear directorio de salida requerido
    os.makedirs('agliluz', exist_ok=True)
    
    if response.status_code == 200:
        data = response.json()
        print("Conexión exitosa. Aplicando filtro inteligente de iluminación y proyectos...")
        
        licitaciones = data.get('Listado', [])
        if licitaciones:
            df = pd.DataFrame(licitaciones)
            
            # Palabras clave ampliadas para cubrir alumbrado, vialidad, smart cities, estadios y arquitectura
            keywords = [
                'iluminacion', 'iluminación', 'luminaria', 'luminarias', 
                'led', 'alumbrado', 'foco', 'proyector', 'proyectores', 
                'farola', 'vial', 'optica', 'óptica', 'postacion', 'postación',
                'fotometria', 'fotometría', 'telegestion', 'telegestión',
                'smart city', 'estadio', 'cancha', 'polideportivo', 'deportivo',
                'fachada', 'monumento', 'concesion', 'concesión', 'mop',
                'red vial', 'autopista', 'soportes', 'torre de iluminacion'
            ]
            
            # Identificar columnas de texto disponibles en la respuesta de la API
            text_columns = [col for col in ['Nombre', 'Descripcion', 'CodigoExterno'] if col in df.columns]
            
            if text_columns:
                # Unificar texto en minúsculas para realizar una búsqueda robusta
                df['texto_busqueda'] = df[text_columns].astype(str).agg(' '.join, axis=1).str.lower()
                
                # Crear patrón de búsqueda con las palabras clave
                pattern = '|'.join(keywords)
                df_filtrado = df[df['texto_busqueda'].str.contains(pattern, na=False, case=False)].copy()
                
                # Limpiar columna temporal
                df_filtrado = df_filtrado.drop(columns=['texto_busqueda'])
            else:
                df_filtrado = df
            
            output_path = 'agliluz/reporte_licitaciones.xlsx'
            
            if not df_filtrado.empty:
                df_filtrado.to_excel(output_path, index=False)
                print(f"¡Éxito! Se filtraron e identificaron {len(df_filtrado)} oportunidades de iluminación y proyectos asociados.")
            else:
                print("No se encontraron licitaciones nuevas con los criterios ampliados en esta ejecución.")
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
