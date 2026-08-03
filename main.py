import os
import json
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
            "luminaria", "luminarias", "foco vial"
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
        response = requests.get(url, timeout=15)
        if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', '').lower():
            with io.BytesIO(response.content) as f:
                reader = PdfReader(f)
                texto_completo = ""
                for page in reader.pages[:8]:
                    texto_completo += page.extract_text() or ""
            return texto_completo.lower()
    except Exception:
        pass
    return ""

def procesar_datos_adjudicacion(row):
    texto_base = str(row.get('Nombre', '')) + " " + str(row.get('Descripcion', ''))
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

    texto_total = texto_base.lower()
    
    if 'estadio' in texto_total or 'cancha' in texto_total or 'deportivo' in texto_total:
        signify_equivalente = "Arena X (Proyector Deportivo Alta Gama)"
        categoria = "Iluminación Deportiva"
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
        
    return pd.Series([proveedor_adjudicado, monto_adjudicado, cantidad_items, categoria, signify_equivalente])

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
            text_columns = [col for col in ['Nombre', 'Descripcion', 'CodigoExterno'] if col in df_nuevo.columns]
            
            if text_columns and not df_nuevo.empty:
                df_nuevo['texto_busqueda'] = df_nuevo[text_columns].astype(str).agg(' '.join, axis=1).str.lower()
                pattern = '|'.join(target_keywords)
                df_filtrado = df_nuevo[df_nuevo['texto_busqueda'].str.contains(pattern, na=False, case=False)].copy()
                df_filtrado = df_filtrado.drop(columns=['texto_busqueda'])
            else:
                df_filtrado = pd.DataFrame()
            
            # FILTRO DE EXCLUSIÓN (BLACKLIST) SEGURO ANTE COLUMNAS FALTANTES
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
                df_filtrado[['Proveedor_Adjudicado', 'Monto_Adjudicado_CLP', 'Cantidad_Unidades', 'Categoria_Proyecto', 'Signify_Equivalente']] = df_filtrado.apply(procesar_datos_adjudicacion, axis=1)
                
                if not df_historico.empty and 'CodigoExterno' in df_historico.columns and 'CodigoExterno' in df_filtrado.columns:
                    df_combinado = pd.concat([df_historico, df_filtrado]).drop_duplicates(subset=['CodigoExterno'], keep='first')
                else:
                    df_combinado = df_filtrado if df_historico.empty else pd.concat([df_historico, df_filtrado])
                
                df_combinado.to_excel(historial_path, index=False)
                
                with pd.ExcelWriter(dashboard_path, engine='openpyxl') as writer:
                    df_combinado.to_excel(writer, sheet_name='Dashboard_General', index=False)
                    
                    if 'Proveedor_Adjudicado' in df_combinado.columns:
                        cols_mapa = [col for col in ['CodigoExterno', 'Nombre', 'Proveedor_Adjudicado', 'Monto_Adjudicado_CLP', 'Cantidad_Unidades', 'Signify_Equivalente'] if col in df_combinado.columns]
                        df_combinado[cols_mapa].to_excel(writer, sheet_name='Mapa_Competencia_Adjudicadas', index=False)
                    
                    portafolio_signify = pd.DataFrame({
                        "Familia_Signify": ["RoadFlair", "Xceed Pro", "Tango Pro", "ActiStar", "Arena X", "GreenVision Solar"],
                        "Aplicacion": ["Vial Alta Eficiencia", "Vial / Autopistas", "Arquitectónica / Proyectores", "Industrial / General", "Estadios y Canchas Deportivas", "Solar Fotovoltaica Autónoma"],
                        "Estrategia_Chile": ["Liderazgo en vías urbanas e interurbanas", "Alto flujo lumínico y robustez vial", "Control estricto DS1 y diseño de fachadas", "Versatilidad e industrial general", "Máximo rendimiento para recintos deportivos", "Sostenibilidad sin red eléctrica"]
                    })
                    portafolio_signify.to_excel(writer, sheet_name='Portafolio_Signify_Chile', index=False)

                print("¡Dashboard Ejecutivo de Inteligencia de Mercado generado con éxito!")
            else:
                print("No se encontraron registros nuevos tras aplicar filtros y memoria histórica.")
        else:
            print("No hay licitaciones en la respuesta general de la API.")
    else:
        print(f"Error al conectar con la API: {response.status_code}")

if __name__ == '__main__':
    main()
