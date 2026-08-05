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
    
    # Datos de demostración adaptados a la nueva estructura modular
    data_demo = pd.DataFrame({
        'CodigoExterno': ['TÚNEL-LO-RUIZ-2026', '858-190-LR25', '4483-17-LR26'],
        'Nombre': ['[Ejemplo] Túnel Lo Ruiz - Alumbrado y Control Telensa', '[Ejemplo] Mejoramiento Iluminación Estadio Municipal', '[Ejemplo] Suministro de Proyectores Deportivos IND'],
        'Categoria_Proyecto': ['Iluminación Vial / Pública', 'Iluminación Deportiva', 'Iluminación Deportiva'],
        'Proveedor_Adjudicado': ['En curso / Vigente', 'Proveedor Externo A', 'Proveedor Externo B'],
        'Monto_Propuesta_CLP': [250000000, 50000000, 130000000],
        'Monto_Adjudicado_CLP': [0, 45000000, 120000000],
        'Score_Relevancia': [85, 75, 80],
        'Estado_Cumplimiento_Signify': ['Cumple Totalmente (Alta Prioridad)', 'Cumple Totalmente', 'Cumple Totalmente'],
        'Analisis_Brecha_Tecnica': ['Score: 85 | +25 (túnel) +25 (alumbrado) +20 (telegestion)', 'Score: 75 | +25 (luminaria) +25 (estadio) +15 (vial)', 'Score: 80 | +25 (proyector) +25 (cancha) +20 (deportivo)'],
        'Fecha_Creacion': ['2026-08-01', '2026-02-10', '2026-03-15'],
        'Fecha_Cierre': ['2026-08-15', '2026-03-15', '2026-04-10']
    })
    return data_demo, True

df_licitaciones, es_demo = cargar_datos()

if es_demo:
    st.info("ℹ️ **Modo Demostración Activo:** Visualizando datos estructurados de prueba. Ejecuta el workflow para cargar los datos reales procesados por SQLite.")

# Métricas Ejecutivas
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Procesos Totales", len(df_licitaciones))
with c2:
    volumen_total = df_licitaciones['Monto_Propuesta_CLP'].sum() if 'Monto_Propuesta_CLP' in df_licitaciones.columns else 0
    st.metric("Volumen Mercado Total", f"${volumen_total:,.0f} CLP")
with c3:
    score_promedio = df_licitaciones['Score_Relevancia'].mean() if 'Score_Relevancia' in df_licitaciones.columns else 0
    st.metric("Score Promedio Relevancia", f"{score_promedio:.1f} pts")
with c4:
    st.metric("Fit Signify High-Tech", f"{len(df_licitaciones)} Activos")

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Dashboard Ejecutivo de Licitaciones", "🏆 Mapa de Competencia y Adjudicadas", "💡 Portafolio Tecnológico Signify"])

with tab1:
    st.subheader("Listado Estratégico con Motor de Scoring Ponderado")
    st.markdown("Proyectos filtrados y puntuados mediante análisis de relevancia comercial y exclusión de ruido:")
    
    cols_t1 = [c for c in ['CodigoExterno', 'Nombre', 'Categoria_Proyecto', 'Score_Relevancia', 'Monto_Propuesta_CLP', 'Estado_Cumplimiento_Signify'] if c in df_licitaciones.columns]
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
            st.markdown(f"**Monto de Propuesta / Presupuesto:** **${reg.get('Monto_Propuesta_CLP', 0):,.0f} CLP**")
            st.markdown(f"**Monto Real Adjudicado:** **${reg.get('Monto_Adjudicado_CLP', 0):,.0f} CLP**")
            st.markdown(f"**Fechas (Creación / Cierre):** {reg.get('Fecha_Creacion', 'N/A')} al {reg.get('Fecha_Cierre', 'N/A')}")
            
        with col_right:
            st.markdown("#### ⚡ Evaluación de Relevancia y Oportunidad")
            st.markdown(f"**Score de Relevancia (AI):** **{reg.get('Score_Relevancia', 0)} / 100 pts**")
            st.markdown(f"**Estado de Cumplimiento:** **{reg.get('Estado_Cumplimiento_Signify', 'N/A')}**")

        st.markdown("#### 📈 Informe de Scoring y Análisis de Brecha")
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
