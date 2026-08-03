import streamlit as st
import pandas as pd
import os

# Configuración de la página web
st.set_page_config(
    page_title="AgliLuz - Inteligencia Comercial Signify",
    page_icon="💡",
    layout="wide"
)

# Título y descripción principal
st.title("💡 AgliLuz: Plataforma Online de Inteligencia y Análisis de Licitaciones")
st.markdown("Sistema autónomo de consulta, análisis de bases técnicas y mapeo de competencia para **Signify Chile**.")

# Cargar el archivo de historial generado por el agente
historial_path = 'agliluz/historial_licitaciones.xlsx'

@st.cache_data
def cargar_datos():
    os.makedirs('agliluz', exist_ok=True)
    if os.path.exists(historial_path):
        try:
            df = pd.read_excel(historial_path)
            if not df.empty and len(df.columns) > 2:
                return df
        except Exception:
            pass
    
    # Dataset por defecto para que la app cargue de inmediato con total elegancia
    return pd.DataFrame({
        'CodigoExterno': ['2378-40-LR25', '858-190-LR25', '4483-17-LR26'],
        'Nombre': [
            '[Ejemplo] Recambio de Luminarias Alumbrado Público Comuna', 
            '[Ejemplo] Mejoramiento Iluminación Estadio Municipal', 
            '[Ejemplo] Suministro de Proyectores Deportivos IND'
        ],
        'Nivel_Compatibilidad': ['Alta', 'Alta', 'Alta'],
        'Signify_Equivalente': [
            'RoadFlair / Xceed Pro (Vial Alta Eficiencia)', 
            'Arena X (Proyector Deportivo Alta Gama)', 
            'Arena X / Proyectores Deportivos Alta Gama'
        ],
        'Requerimiento_Potencia': ['100 W', '1000 W', '1200 W'],
        'Requerimiento_Flujo_Luminoso': ['12000 lm', '130000 lm', '150000 lm'],
        'Certificaciones_Exigidas': ['Certificación SEC | Decreto Supremo N°1', 'Decreto Supremo N°1 (Norma Lumínica)', 'Certificación SEC | DS1'],
        'Proveedor_Adjudicado': ['Philips / Signify (Ejemplo)', 'Proveedor Competencia A', 'En proceso / Evaluando bases'],
        'Monto_Adjudicado_CLP': [45000000, 120000000, 85000000],
        'Cantidad_Unidades': [180, 24, 30],
        'Categoria_Proyecto': ['Iluminación Vial', 'Iluminación Deportiva / IND', 'Iluminación Deportiva / IND'],
        'Marcas_Competencia_Detectadas': ['Philips / Signify', 'GE Lighting', 'Pendiente en Actas'],
        'Pautas_Y_Puntajes_Evaluacion': ['Ponderación: 60% Precio, 40% Técnico', 'Evaluación integral por puntaje', 'Bases administrativas y técnicas revisadas']
    })

df = cargar_datos()

is_demo = '2378-40-LR25' in df['CodigoExterno'].values and len(df) <= 3
if is_demo:
    st.info("ℹ️ **Modo Demostración Activo:** Estás viendo datos de ejemplo en tu plataforma online. En cuanto ejecutes tu flujo en GitHub Actions, se sincronizarán los procesos reales de Mercado Público automáticamente.")

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.header("🔍 Filtros de Consulta")

compatibilidades = ['Todas'] + list(df['Nivel_Compatibilidad'].dropna().unique()) if 'Nivel_Compatibilidad' in df.columns else ['Todas']
filtro_comp = st.sidebar.selectbox("Nivel de Compatibilidad Técnica", compatibilidades)

categorias = ['Todas'] + list(df['Categoria_Proyecto'].dropna().unique()) if 'Categoria_Proyecto' in df.columns else ['Todas']
filtro_cat = st.sidebar.selectbox("Categoría de Proyecto", categorias)

busqueda = st.sidebar.text_input("Buscar por ID (ej. 4483-17-LR26), Comprador o Palabra Clave")

# Aplicar filtros
df_filtrado = df.copy()
if filtro_comp != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Nivel_Compatibilidad'] == filtro_comp]
if filtro_cat != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Categoria_Proyecto'] == filtro_cat]
if busqueda:
    mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(busqueda, case=False, na=False)).any(axis=1)
    df_filtrado = df_filtrado[mask]

# --- MÉTRICAS EJECUTIVAS SUPERIORES ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Procesos Analizados", len(df))
with col2:
    st.metric("Procesos Filtrados Activos", len(df_filtrado))
with col3:
    monto_total = df['Monto_Adjudicado_CLP'].sum() if 'Monto_Adjudicado_CLP' in df.columns else 0
    st.metric("Volumen Mercado (CLP)", f"${monto_total:,.0f}")
with col4:
    altas = len(df[df['Nivel_Compatibilidad'] == 'Alta']) if 'Nivel_Compatibilidad' in df.columns else 0
    st.metric("Oportunidades Alta Compatibilidad", altas)

st.markdown("---")

# --- TABS DE NAVEGACIÓN WEB ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard de Licitaciones", "🏆 Mapa de Competencia y Adjudicadas", "💡 Portafolio Signify Chile"])

with tab1:
    st.subheader("Listado Detallado y Requerimientos Técnicos Extraídos")
    st.markdown("Consulta rápida de potencias, flujos lumínicos, IP, IK, garantías y certificaciones extraídas de las bases.")
    
    columnas_mostrar = [col for col in ['CodigoExterno', 'Nombre', 'Nivel_Compatibilidad', 'Signify_Equivalente', 'Requerimiento_Potencia', 'Requerimiento_Flujo_Luminoso', 'Certificaciones_Exigidas'] if col in df_filtrado.columns]
    st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True)

    if not df_filtrado.empty:
        st.markdown("### 🔍 Vista de Detalle Técnico por Licitación")
        selected_id = st.selectbox("Selecciona un Código Externo para ver su análisis profundo:", df_filtrado['CodigoExterno'].unique())
        row_detalle = df_filtrado[df_filtrado['CodigoExterno'] == selected_id].iloc[0]
        
        dcol1, dcol2 = st.columns(2)
        with dcol1:
            st.info(f"**Nombre:** {row_detalle.get('Nombre', 'N/A')}")
            st.write(f"**Proveedor Adjudicado:** {row_detalle.get('Proveedor_Adjudicado', 'N/A')}")
            st.write(f"**Monto Adjudicado:** ${row_detalle.get('Monto_Adjudicado_CLP', 0):,.0f} CLP")
            st.write(f"**Categoría:** {row_detalle.get('Categoria_Proyecto', 'N/A')}")
            st.write(f"**Solución Signify Sugerida:** {row_detalle.get('Signify_Equivalente', 'N/A')}")
        with dcol2:
            st.success(f"**Potencia Requerida:** {row_detalle.get('Requerimiento_Potencia', 'N/A')}")
            st.success(f"**Flujo Luminoso:** {row_detalle.get('Requerimiento_Flujo_Luminoso', 'N/A')}")
            st.success(f"**Certificaciones Exigidas:** {row_detalle.get('Certificaciones_Exigidas', 'N/A')}")

with tab2:
    st.subheader("Análisis de Competencia y Marcas Adjudicadas")
    st.markdown("Identificación de marcas competidoras, montos y pautas de evaluación detectadas en actas.")
    
    cols_mapa = [col for col in ['CodigoExterno', 'Nombre', 'Proveedor_Adjudicado', 'Marcas_Competencia_Detectadas', 'Monto_Adjudicado_CLP', 'Pautas_Y_Puntajes_Evaluacion'] if col in df.columns]
    st.dataframe(df[cols_mapa], use_container_width=True)

with tab3:
    st.subheader("Matriz Estratégica - Portafolio Signify Chile")
    st.markdown("Familias de referencia oficial para cruce de licitaciones:")
    
    portafolio_df = pd.DataFrame({
        "Familia_Signify": ["RoadFlair", "Xceed Pro", "Tango Pro", "ActiStar", "Arena X", "GreenVision Solar"],
        "Aplicacion": ["Vial Alta Eficiencia", "Vial / Autopistas", "Arquitectónica / Proyectores", "Industrial / General", "Estadios y Canchas Deportivas", "Solar Fotovoltaica Autónoma"],
        "Estrategia_Chile": [
            "Liderazgo en vías urbanas e interurbanas", 
            "Alto flujo lumínico y robustez vial", 
            "Control estricto DS1 y diseño de fachadas", 
            "Versatilidad e industrial general", 
            "Máximo rendimiento para recintos deportivos", 
            "Sostenibilidad sin red eléctrica"
        ]
    })
    st.table(portafolio_df)
