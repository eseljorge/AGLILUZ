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
    if os.path.exists(historial_path):
        try:
            return pd.read_excel(historial_path)
        except Exception:
            pass
    
    # Estructura por defecto para que la app cargue de inmediato de forma impecable
    return pd.DataFrame(columns=[
        'CodigoExterno', 'Nombre', 'Nivel_Compatibilidad', 'Signify_Equivalente', 
        'Requerimiento_Potencia', 'Requerimiento_Flujo_Luminoso', 'Certificaciones_Exigidas',
        'Proveedor_Adjudicado', 'Monto_Adjudicado_CLP', 'Cantidad_Unidades', 'Categoria_Proyecto',
        'Marcas_Competencia_Detectadas', 'Pautas_Y_Puntajes_Evaluacion'
    ])

df = cargar_datos()

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.header("🔍 Filtros de Consulta")

compatibilidades = ['Todas'] + list(df['Nivel_Compatibilidad'].dropna().unique()) if 'Nivel_Compatibilidad' in df.columns else ['Todas']
filtro_comp = st.sidebar.selectbox("Nivel de Compatibilidad Técnica", compatibilidades)

categorias = ['Todas'] + list(df['Categoria_Proyecto'].dropna().unique()) if 'Categoria_Proyecto' in df.columns else ['Todas']
filtro_cat = st.sidebar.selectbox("Categoría de Proyecto", categorias)

busqueda = st.sidebar.text_input("Buscar por ID (ej. 4483-17-LR26), Comprador o Palabra Clave")

# Aplicar filtros
df_filtrado = df.copy()
if not df_filtrado.empty and 'Nivel_Compatibilidad' in df_filtrado.columns and filtro_comp != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Nivel_Compatibilidad'] == filtro_comp]
if not df_filtrado.empty and 'Categoria_Proyecto' in df_filtrado.columns and filtro_cat != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Categoria_Proyecto'] == filtro_cat]
if busqueda and not df_filtrado.empty:
    mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(busqueda, case=False, na=False)).any(axis=1)
    df_filtrado = df_filtrado[mask]

# --- MÉTRICAS EJECUTIVAS SUPERIORES ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Procesos Analizados", len(df))
with col2:
    st.metric("Procesos Filtrados Activos", len(df_filtrado))
with col3:
    monto_total = df['Monto_Adjudicado_CLP'].sum() if 'Monto_Adjudicado_CLP' in df.columns and not df.empty else 0
    st.metric("Volumen Mercado (CLP)", f"${monto_total:,.0f}")
with col4:
    altas = len(df[df['Nivel_Compatibilidad'] == 'Alta']) if 'Nivel_Compatibilidad' in df.columns and not df.empty else 0
    st.metric("Oportunidades Alta Compatibilidad", altas)

st.markdown("---")

if df.empty or len(df.columns) <= 3:
    st.info("ℹ️ **Plataforma en línea conectada exitosamente.** El agente recopilará los procesos en su próxima ejecución automática en GitHub Actions y se reflejarán aquí en tiempo real.")
else:
    # --- TABS DE NAVEGACIÓN WEB ---
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard de Licitaciones", "🏆 Mapa de Competencia y Adjudicadas", "💡 Portafolio Signify Chile"])

    with tab1:
        st.subheader("Listado Detallado y Requerimientos Técnicos Extraídos")
        st.markdown("Consulta rápida de potencias, flujos lumínicos, IP, IK, garantías y certificaciones extraídas de las bases.")
        
        columnas_mostrar = [col for col in ['CodigoExterno', 'Nombre', 'Nivel_Compatibilidad', 'Signify_Equivalente', 'Requerimiento_Potencia', 'Requerimiento_Flujo_Luminoso', 'Certificaciones_Exigidas'] if col in df_filtrado.columns]
        st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True)

        if not df_filtrado.empty and 'CodigoExterno' in df_filtrado.columns:
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
                st.success(f"**Protección IP / IK:** {row_detalle.get('Requerimiento_IP', 'N/A')} / {row_detalle.get('Requerimiento_IK', 'N/A')}")
                st.success(f"**Temperatura de Color (CCT):** {row_detalle.get('Requerimiento_CCT_Kelvin', 'N/A')}")
                st.warning(f"**Certificaciones Exigidas:** {row_detalle.get('Certificaciones_Exigidas', 'N/A')}")

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
