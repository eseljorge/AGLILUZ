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
        print("Conexión exitosa. Procesando datos...")
        
        licitaciones = data.get('Listado', [])
        if licitaciones:
            df = pd.DataFrame(licitaciones)
            output_path = 'agliluz/reporte_licitaciones.xlsx'
            df.to_excel(output_path, index=False)
            print(f"Reporte guardado exitosamente en {output_path}")
        else:
            print("No se encontraron licitaciones en esta ejecución.")
            with open('agliluz/resumen.txt', 'w') as f:
                f.write(f"Ejecución realizada sin registros el {datetime.now()}")
    else:
        print(f"Error al conectar con la API: {response.status_code}")
        # Guardar archivo de respaldo para evitar que la tarea falle por carpeta vacía
        with open('agliluz/error_log.txt', 'w') as f:
            f.write(f"Error API code: {response.status_code} - {datetime.now()}")

if __name__ == '__main__':
    main()
