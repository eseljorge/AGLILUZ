import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="AgliLuz | Enterprise Intelligence & Tender Analytics",
    page_icon="💡",
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #f8fafc; color: #1e293b; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .executive-header { background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); padding: 2.5rem 2rem; border-radius: 12px; color: #ffffff; margin-bottom: 2rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .executive-header h1 { color: #ffffff; font-size: 2.2rem; font-weight: 700; margin-bottom: 0.5rem; }
    .executive-header p { color: #93c5fd; font-size: 1.1rem; margin-bottom: 0; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="executive-header">
        <h1>💡 AgliLuz Enterprise Intelligence</h1>
        <p>Plataforma Autónoma de Análisis Técnico, Scoring de Relevancia y Mapeo Comercial | Signify Chile</p>
    </div>
""", unsafe_allow_html=True)

HISTORIAL_PATH = 'agliluz/historial_licitaciones.xlsx'

@st.cache_data
def cargar_datos():
    if os.path.exists(HISTORIAL_PATH):
        try:
            df = pd.read_excel(HISTORIAL_PATH)
            if not df.empty and 'CodigoExterno' in df.columns:
                return df, False
        except Exception:
            pass
    
    # Datos de demostración robustos
    data_demo = pd.DataFrame({
        'CodigoExterno': ['TÚNEL-LO-RUIZ-2026', '858-190-LR25', '4483-17-LR26'],
        'Nombre': ['[Ejemplo] Túnel Lo Ruiz - Alumbrado y Control Telensa', '[Ejemplo] Mejoramiento Iluminación Estadio Municipal', '[Ejemplo] Suministro de Proyectores Deportivos IND'],
        'Categoria_Proyecto': ['Iluminación Vial / Pública', 'Iluminación Deportiva', 'Iluminación Deportiva'],
        'Signify_Equivalente': ['RoadFlair / Xceed Pro + Interact City', 'Arena X + Interact Sports', 'Arena X + Interact Sports'],
        'Cantidad_Unidades': [150, 80, 220],
        'Requerimiento_Potencia': ['100W - 150W', '1000W - 1200W', '800W - 1000W'],
        'Requerimiento_Flujo_Luminoso': ['12,000 lm - 18,000 lm', '120,000 lm - 150,000 lm', '95,000 lm - 120,000 lm'],
        'Requerimiento_IP': ['IP66', 'IP66', 'IP66'],
        'Requerimiento_IK': ['IK08', 'IK08', 'IK08'],
        'Sistemas_Control_Telegestion': ['Telegestión | Zócalo Zhaga', 'Control estándar', 'Interact Sports'],
        'Certificaciones_Exigidas': ['SEC | Decreto Supremo N°1 (DS1)', 'SEC', 'SEC | DS1'],
        'Proveedor_Adjudicado': ['En curso / Vigente', 'Proveedor Externo A', 'Proveedor Externo B'],
        'Monto_Propuesta_CLP': [250000000, 50000000, 130000000],
        'Monto_Adjudicado_CLP': [0, 45000000, 120000000],
        'Score_Relevancia': [95, 85, 90],
        'Estado_Cumplimiento_Signify': ['Cumple Totalmente (Alta Prioridad)', 'Cumple Totalmente', 'Cumple Totalmente'],
        'Analisis_Brecha_Tecnica': ['Score: 95 | Luminarias detectadas: 150', 'Score: 85 | Luminarias detectadas: 80', 'Score: 90 | Luminarias detectadas: 220'],
        'Fecha_Creacion': ['2026-08-01', '2026-02-10', '2026-03-15'],
        'Fecha_Cierre': ['2026-08-15', '2026-03-15', '2026-04-10']
    })
    return data_demo, True

df_licitaciones, es_demo = cargar_datos()

if es_demo:
    st.info("ℹ️ **Modo Demostración Activo:** Ejecuta tu workflow en GitHub Actions para cargar los datos reales procesados.")

# Métricas Ejecutivas
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Procesos Filtrados", len(df_licitaciones))
with c2:
    volumen_total = df_licitaciones['Monto_Propuesta_CLP'].sum() if 'Monto_Propuesta_CLP' in df_licitaciones.columns else 0
    st.metric("Volumen Mercado", f"${volumen_total:,.0f} CLP")
with c3:
    total_luminarias = df_licitaciones['Cantidad_Unidades'].sum() if 'Cantidad_Unidades' in df_licitaciones.columns else 0
    st.metric("Total Luminarias en Licitación", f"{total_luminarias:,.0f} un.")
with c4:
    score_promedio = df_licitaciones['Score_Relevancia'].mean() if 'Score_Relevancia' in df_licitaciones.columns else 0
    st.metric("Score Promedio Relevancia", f"{score_promedio:.1f} pts")

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Dashboard Ejecutivo de Licitaciones", "🏆 Mapa de Competencia y Adjudicadas", "💡 Portafolio Tecnológico Signify"])

with tab1:
    st.subheader("Listado Estratégico y Parámetros Técnicos Extraídos")
    st.markdown("Proyectos de iluminación pura filtrados, con cantidad de unidades, potencias y flujos extraídos:")
    
    cols_t1 = [c for c in ['CodigoExterno', 'Nombre', 'Categoria_Proyecto', 'Cantidad_Unidades', 'Requerimiento_Potencia', 'Requerimiento_Flujo_Luminoso', 'Sistemas_Control_Telegestion', 'Score_Relevancia'] if c in df_licitaciones.columns]
    st.dataframe(df_licitaciones[cols_t1], use_container_width=True)
    
    st.markdown("---")
    st.subheader("🔍 Ficha de Auditoría Técnica y Comercial por Proyecto")
    
    if not df_licitaciones.empty:
        codigos = df_licitaciones['CodigoExterno'].tolist()
        sel_codigo = st.selectbox("Seleccione Código de Licitación:", codigos, key="sel_codigo_exec")
        
        reg = df_licitaciones[df_licitaciones['CodigoExterno'] == sel_codigo].iloc[0]
        
        st.markdown(f"### 🏢 Ficha de Proyecto: {reg.get('Nombre', 'Sin Nombre')}")
        
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("#### 📋 Condiciones Comerciales y Económicas")
            st.markdown(f"**Código Externo:** `{reg.get('CodigoExterno', 'N/A')}`")
            st.markdown(f"**Categoría:** {reg.get('Categoria_Proyecto', 'N/A')}")
            st.markdown(f"**Proveedor Adjudicado:** {reg.get('Proveedor_Adjudicado', 'N/A')}")
            st.markdown(f"**Monto Propuesta / Presupuesto:** **${reg.get('Monto_Propuesta_CLP', 0):,.0f} CLP**")
            st.markdown(f"**Fechas (Creación / Cierre):** {reg.get('Fecha_Creacion', 'N/A')} al {reg.get('Fecha_Cierre', 'N/A')}")
            
        with col_right:
            st.markdown("#### ⚡ Especificaciones Técnicas y IoT")
            st.markdown(f"**Solución Signify Equivalente:** `{reg.get('Signify_Equivalente', 'N/A')}`")
            st.markdown(f"**Cantidad de Luminarias:** **{reg.get('Cantidad_Unidades', 0)} unidades**")
            st.markdown(f"**Potencia Requerida:** `{reg.get('Requerimiento_Potencia', 'N/A')}`")
            st.markdown(f"**Flujo Lumínico:** `{reg.get('Requerimiento_Flujo_Luminoso', 'N/A')}`")
            st.markdown(f"**Protección IP / IK:** `{reg.get('Requerimiento_IP', 'N/A')} / {reg.get('Requerimiento_IK', 'N/A')}`")
            st.markdown(f"**Control / Telegestión:** {reg.get('Sistemas_Control_Telegestion', 'N/A')}")
            st.markdown(f"**Normas / Certificaciones:** {reg.get('Certificaciones_Exigidas', 'N/A')}")

        st.markdown("#### 📈 Informe de Scoring y Análisis Técnico")
        st.info(reg.get('Analisis_Brecha_Tecnica', 'Sin análisis registrado'))

with tab2:
    st.subheader("🏆 Mapa de Competencia y Adjudicadas")
    cols_t2 = [c for c in ['CodigoExterno', 'Nombre', 'Proveedor_Adjudicado', 'Monto_Adjudicado_CLP', 'Score_Relevancia', 'Estado_Cumplimiento_Signify'] if c in df_licitaciones.columns]
    st.dataframe(df_licitaciones[cols_t2], use_container_width=True)

with tab3:
    st.subheader("💡 Portafolio Tecnológico Profesional Signify Chile")
    portafolio_df = pd.DataFrame({
        "Familia_Signify": ["RoadFlair + Interact City", "Arena X + Interact Sports", "Tango Pro + Dynalite", "Color Kinetics", "GreenVision Solar"],
        "Aplicacion": ["Vial Pública e Inteligente / Túneles", "Estadios, Canchas y Polideportivos", "Ornamental y Arquitectónica Avanzada", "Fachadas Monumentales", "Iluminación Solar Autónoma"],
        "Estrategia_Tecnologica": ["Smart cities, zócalos Zhaga/NEMA y telegestión centralizada IoT", "Alto rendimiento lumínico, control DMX y cumplimiento IND", "Control dinámico de escenas DALI/DMX y tonos", "Diseño lumínico de precisión con norma DS1 estricta", "Autonomía energética total sin conexión a red eléctrica"]
    })
    st.dataframe(portafolio_df, use_container_width=True)
