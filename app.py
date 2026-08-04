import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="AgliLuz: Inteligencia y Análisis de Licitaciones",
    page_icon="💡",
    layout="wide"
)

# Estilo visual limpio y profesional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

st.markdown("# 💡 AgliLuz: Plataforma Online de Inteligencia y Análisis de Licitaciones")
st.markdown("Sistema autónomo de análisis técnico, bases comerciales y mapeo de competencia para **Signify Chile**.")

# Carga de datos reales desde el repositorio o modo demo
HISTORIAL_PATH = 'agliluz/historial_licitaciones.xlsx'

@st.cache_data
def cargar_datos():
    if os.path.exists(HISTORIAL_PATH):
        try:
            df = pd.read_excel(HISTORIAL_PATH)
            if not df.empty and 'CodigoExterno' in df.columns:
                # Verificar si son datos reales o ejemplos antiguos
                if not df['CodigoExterno'].astype(str).str.contains('Ejemplo', case=False).all():
                    return df, False
        except Exception:
            pass
    
    # Datos de demostración estructurados con formato profesional en caso de no existir archivo local
    data_demo = pd.DataFrame({
        'CodigoExterno': ['TÚNEL-LO-RUIZ-2026', '858-190-LR25', '4483-17-LR26'],
        'Nombre': ['[Ejemplo] Túnel Lo Ruiz - Alumbrado y Control Telensa', '[Ejemplo] Mejoramiento Iluminación Estadio Municipal', '[Ejemplo] Suministro de Proyectores Deportivos IND'],
        'Categoria_Proyecto': ['Iluminación Vial / Túneles', 'Iluminación Deportiva / IND', 'Iluminación Deportiva / IND'],
        'Signify_Equivalente': ['RoadFlair / Xceed Pro + Interact City', 'Arena X + Interact Sports', 'Arena X + Interact Sports'],
        'Requerimiento_Potencia': ['100W - 150W', 'Not Specified', 'Not Specified'],
        'Requerimiento_Flujo_Luminoso': ['12,000 lm', 'Not Specified', 'Not Specified'],
        'Certificaciones_Exigidas': ['Certificación SEC | DS1 (Norma Lumínica)', 'Normativa estándar', 'Normativa estándar'],
        'Sistemas_Control_Telegestion': ['Exige Telegestión / Zócalo Zhaga', 'Sin requerimientos', 'Sin requerimientos'],
        'Estado_Cumplimiento_Signify': ['Cumple Totalmente (Conectividad IoT)', 'Cumple Totalmente', 'Cumple Totalmente'],
        'Analisis_Brecha_Tecnica': ['Túnel y vial: RoadFlair con zócalo Zhaga/NEMA sobre plataforma Interact City cumple 100%.', 'Estadio municipal: Arena X cumple requerimientos de rendimiento.', 'Proyecto IND: Arena X cumple rendimiento y DS1.'],
        'Proveedor_Adjudicado': ['En proceso / Licitación Privada', 'Proveedor Externo A', 'Proveedor Externo B'],
        'Monto_Adjudicado_CLP': [0, 45000000, 120000000],
        'Cantidad_Unidades': [50, 120, 240],
        'Moneda_Oferta': ['Unidad de Fomento (UF)', 'CLP', 'CLP'],
        'Fecha_Presentacion': ['2026-05-07', '2026-03-15', '2026-04-10'],
        'Fecha_Adjudicacion_Proyectada': ['2026-08-03', '2026-04-01', '2026-05-01'],
        'Visita_Terreno': ['No hay por parte del cliente, si se requiere ir solos', 'Obligatoria', 'Facultativa'],
        'Garantias_Requeridas': ['Boleta Fiel Cumplimiento 10%', 'Boleta Fiel Cumplimiento 5%', 'Boleta Seriedad Oferta'],
        'Plazo_Entrega_Bodega': ['Primer día hábil de mayo de 2028', '30 días corridos', '45 días corridos'],
        'Garantia_Producto_Anios': ['5 Años + mediciones anuales', '5 Años', '5 Años']
    })
    return data_demo, True

df_licitaciones, es_demo = cargar_datos()

if es_demo:
    st.info("ℹ️ **Modo Demostración Activo:** Estás viendo datos de ejemplo estructurados con el formato de fichas comerciales. En cuanto ejecutes tu flujo en GitHub Actions, se sincronizarán los procesos reales.")

# Métricas principales
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Procesos Analizados", len(df_licitaciones))
with col2:
    st.metric("Procesos Filtrados Activos", len(df_licitaciones))
with col3:
    volumen_total = df_licitaciones['Monto_Adjudicado_CLP'].sum() if 'Monto_Adjudicado_CLP' in df_licitaciones.columns else 0
    st.metric("Volumen Mercado (CLP)", f"${volumen_total:,.0f}")
with col4:
    st.metric("Oportunidades Alta Compatibilidad", len(df_licitaciones))

st.markdown("---")

# Pestañas principales de la aplicación
tab1, tab2, tab3 = st.tabs(["📊 Dashboard de Licitaciones", "🏆 Mapa de Competencia y Adjudicadas", "💡 Portafolio Signify Chile"])

with tab1:
    st.subheader("Listado Detallado y Requerimientos Técnicos Extraídos")
    st.markdown("Consulta rápida de potencias, flujos lumínicos, IP, IK, garantías y cumplimiento técnico extraído de las bases.")
    
    # Tabla interactiva principal
    columnas_mostrar = [c for c in ['CodigoExterno', 'Nombre', 'Categoria_Proyecto', 'Signify_Equivalente', 'Requerimiento_Potencia', 'Estado_Cumplimiento_Signify'] if c in df_licitaciones.columns]
    st.dataframe(df_licitaciones[columnas_mostrar], use_container_width=True)
    
    st.markdown("---")
    st.subheader("🔍 Vista de Detalle Técnico y Comercial por Licitación")
    st.markdown("Selecciona un Código Externo para desplegar la ficha completa con plazos, monedas, garantías y requerimientos idénticos a tus plantillas de control:")
    
    if not df_licitaciones.empty:
        codigos_disponibles = df_licitaciones['CodigoExterno'].tolist()
        codigo_seleccionado = st.selectbox("Selecciona un Código Externo para ver su análisis profundo:", codigos_disponibles)
        
        # Filtrar el registro seleccionado
        registro = df_licitaciones[df_licitaciones['CodigoExterno'] == codigo_seleccionado].iloc[0]
        
        # Despliegue en formato de tarjeta estructurada tipo ficha comercial
        st.markdown(f"### 📄 Ficha de Proceso: {registro.get('Nombre', 'Sin Nombre')}")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**ID / Código Externo:** `{registro.get('CodigoExterno', 'N/A')}`")
            st.markdown(f"**Categoría:** {registro.get('Categoria_Proyecto', 'N/A')}")
            st.markdown(f"**Proveedor Adjudicado:** {registro.get('Proveedor_Adjudicado', 'N/A')}")
            st.markdown(f"**Monto Adjudicado:** ${registro.get('Monto_Adjudicado_CLP', 0):,.0f} CLP")
            st.markdown(f"**Moneda de la Oferta:** {registro.get('Moneda_Oferta', 'Unidad de Fomento (UF)')}")
            st.markdown(f"**Fecha Presentación de Oferta:** {registro.get('Fecha_Presentacion', 'N/A')}")
            st.markdown(f"**Fecha Adjudicación Proyectada:** {registro.get('Fecha_Adjudicacion_Proyectada', 'N/A')}")
            st.markdown(f"**Visita a Terreno:** {registro.get('Visita_Terreno', 'N/A')}")
            
        with col_b:
            st.markdown(f"**Equivalente Signify:** `{registro.get('Signify_Equivalente', 'N/A')}`")
            st.markdown(f"**Estado de Cumplimiento:** {registro.get('Estado_Cumplimiento_Signify', 'N/A')}")
            st.markdown(f"**Potencia Requerida:** {registro.get('Requerimiento_Potencia', 'N/A')}")
            st.markdown(f"**Flujo Lumínico:** {registro.get('Requerimiento_Flujo_Luminoso', 'N/A')}")
            st.markdown(f"**Certificaciones / Normativa:** {registro.get('Certificaciones_Exigidas', 'N/A')}")
            st.markdown(f"**Sistemas de Control / Telegestión:** {registro.get('Sistemas_Control_Telegestion', 'N/A')}")
            st.markdown(f"**Garantías Requeridas:** {registro.get('Garantias_Requeridas', 'N/A')}")
            st.markdown(f"**Garantía de Producto:** {registro.get('Garantia_Producto_Anios', 'N/A')}")

        st.markdown("#### 📋 Análisis de Brecha y Requerimientos Críticos (Plazos y Entregas)")
        st.info(f"**Análisis Técnico y Comercial:** {registro.get('Analisis_Brecha_Tecnica', 'Sin observaciones')}")
        
        if 'Plazo_Entrega_Bodega' in registro:
            st.success(f"**Hito Clave / Plazo Crítico:** Disponibilidad en bodega / Hitos: {registro.get('Plazo_Entrega_Bodega', 'N/A')}")

with tab2:
    st.subheader("🏆 Mapa de Competencia y Adjudicadas")
    cols_mapa = [c for c in ['CodigoExterno', 'Nombre', 'Proveedor_Adjudicado', 'Monto_Adjudicado_CLP', 'Estado_Cumplimiento_Signify', 'Signify_Equivalente'] if c in df_licitaciones.columns]
    st.dataframe(df_licitaciones[cols_mapa], use_container_width=True)

with tab3:
    st.subheader("💡 Portafolio Oficial Signify Chile")
    st.markdown("Líneas de productos y soluciones integrales integradas para cruce automático con licitaciones:")
    portafolio_df = pd.DataFrame({
        "Familia_Signify": ["RoadFlair + Interact City", "Arena X + Interact Sports", "Tango Pro + Dynalite", "Color Kinetics", "GreenVision Solar"],
        "Aplicacion": ["Vial Inteligente y Telegestión", "Estadios y Recintos Deportivos", "Arquitectónica y Control Dinámico", "Fachadas y Iluminación Monumental", "Autónoma Fotovoltaica"],
        "Estrategia_Chile": ["Liderazgo en smart cities y control centralizado", "Máximo rendimiento y conectividad deportiva", "Control avanzado de escenas y tonos", "Cumplimiento estricto DS1 y diseño", "Sostenibilidad sin red eléctrica"]
    })
    st.dataframe(portafolio_df, use_container_width=True)
