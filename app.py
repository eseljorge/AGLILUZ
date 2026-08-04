import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="AgliLuz | Enterprise Intelligence & Tender Analytics",
    page_icon="💡",
    layout="wide"
)

# Estilo visual ejecutivo, corporativo y de alta tecnología (Tech/Enterprise)
st.markdown("""
    <style>
    /* Fondo general y tipografía */
    .main {
        background-color: #f8fafc;
        color: #1e293b;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Encabezado Principal Ejecutivo */
    .executive-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 2.5rem 2rem;
        border-radius: 12px;
        color: #ffffff;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .executive-header h1 {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .executive-header p {
        color: #93c5fd;
        font-size: 1.1rem;
        margin-bottom: 0;
    }

    /* Tarjetas de Métricas Ejecutivas */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 1.25rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        border-left: 4px solid #2563eb;
    }
    
    /* Contenedores de Ficha Detallada */
    .tech-card {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Banner Ejecutivo
st.markdown("""
    <div class="executive-header">
        <h1>💡 AgliLuz Enterprise Intelligence</h1>
        <p>Plataforma Autónoma de Análisis Técnico, Bases Comerciales y Mapeo de Competencia | Signify Chile</p>
    </div>
""", unsafe_allow_html=True)

HISTORIAL_PATH = 'agliluz/historial_licitaciones.xlsx'

@st.cache_data
def cargar_datos():
    if os.path.exists(HISTORIAL_PATH):
        try:
            df = pd.read_excel(HISTORIAL_PATH)
            if not df.empty and 'CodigoExterno' in df.columns:
                if not df['CodigoExterno'].astype(str).str.contains('Ejemplo', case=False).all():
                    return df, False
        except Exception:
            pass
    
    # Datos de demostración estructurados con formato ejecutivo
    data_demo = pd.DataFrame({
        'CodigoExterno': ['TÚNEL-LO-RUIZ-2026', '858-190-LR25', '4483-17-LR26'],
        'Nombre': ['[Ejemplo] Túnel Lo Ruiz - Alumbrado y Control Telensa', '[Ejemplo] Mejoramiento Iluminación Estadio Municipal', '[Ejemplo] Suministro de Proyectores Deportivos IND'],
        'Categoria_Proyecto': ['Iluminación Vial / Túneles', 'Iluminación Deportiva / IND', 'Iluminación Deportiva / IND'],
        'Signify_Equivalente': ['RoadFlair / Xceed Pro + Interact City', 'Arena X + Interact Sports', 'Arena X + Interact Sports'],
        'Requerimiento_Potencia': ['100W - 150W', '1000W - 1200W', '800W - 1000W'],
        'Requerimiento_Flujo_Luminoso': ['12,000 lm - 18,000 lm', '120,000 lm - 150,000 lm', '95,000 lm - 120,000 lm'],
        'Requerimiento_IP': ['IP66', 'IP66', 'IP66'],
        'Requerimiento_IK': ['IK08', 'IK08', 'IK08'],
        'Certificaciones_Exigidas': ['Certificación SEC | Decreto Supremo N°1 (DS1)', 'Certificación SEC', 'Certificación SEC | DS1'],
        'Sistemas_Control_Telegestion': ['Exige Telegestión / Zócalo Zhaga', 'Sin requerimientos', 'Sistema DMX / Interact Sports'],
        'Moneda_Oferta': ['Unidad de Fomento (UF)', 'Pesos Chilenos (CLP)', 'Pesos Chilenos (CLP)'],
        'Visita_Terreno': ['No hay por parte del cliente, ir solos si se requiere', 'Obligatoria', 'Facultativa'],
        'Garantias_Requeridas': ['Boleta Fiel Cumplimiento 10%', 'Boleta Fiel Cumplimiento 5%', 'Boleta Seriedad Oferta 5%'],
        'Plazo_Entrega_Bodega': ['Primer día hábil de mayo de 2028', '30 días corridos', '45 días corridos'],
        'Garantia_Producto_Anios': ['5 Años + mediciones anuales', '5 Años', '5 Años'],
        'Multas_Y_Sanciones': ['Multa 0.5 UF por día de atraso', '1% por día de retraso en entrega', 'Estándar MOP'],
        'Estado_Cumplimiento_Signify': ['Cumple Totalmente (Conectividad IoT)', 'Cumple Totalmente', 'Cumple Totalmente'],
        'Analisis_Brecha_Tecnica': ['Túnel y vial: RoadFlair con zócalo Zhaga/NEMA sobre plataforma Interact City cumple 100% y norma DS1.', 'Estadio municipal: Arena X cumple rendimiento lumínico y protección IP66.', 'Proyecto IND: Arena X cumple rendimiento y DS1.'],
        'Proveedor_Adjudicado': ['En proceso / Licitación Privada', 'Proveedor Externo A', 'Proveedor Externo B'],
        'Monto_Adjudicado_CLP': [250000000, 45000000, 120000000],
        'Cantidad_Unidades': [50, 120, 240],
        'Fecha_Creacion': ['2026-03-01', '2026-02-10', '2026-03-15'],
        'Fecha_Cierre': ['2026-05-07', '2026-03-15', '2026-04-10']
    })
    return data_demo, True

df_licitaciones, es_demo = cargar_datos()

if es_demo:
    st.info("ℹ️ **Modo Demostración Activo:** Estás viendo datos estructurados corporativos. Ejecuta tu flujo en GitHub Actions para sincronizar procesos reales del portal.")

# Panel de Métricas Ejecutivas
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Procesos Totales", len(df_licitaciones))
with c2:
    st.metric("Procesos Filtrados", len(df_licitaciones))
with c3:
    volumen = df_licitaciones['Monto_Adjudicado_CLP'].sum() if 'Monto_Adjudicado_CLP' in df_licitaciones.columns else 0
    st.metric("Volumen Mercado", f"${volumen:,.0f} CLP")
with c4:
    st.metric("Fit Signify High-Tech", f"{len(df_licitaciones)} Activos")

st.markdown("<br>", unsafe_allow_html=True)

# Navegación por pestañas ejecutivas
tab1, tab2, tab3 = st.tabs(["📊 Dashboard Ejecutivo de Licitaciones", "🏆 Mapa de Competencia y Adjudicadas", "💡 Portafolio Tecnológico Signify"])

with tab1:
    st.subheader("Listado Estratégico y Parámetros Técnicos Clave")
    st.markdown("Filtro y visión general de proyectos de iluminación profesional, vial, deportiva y telegestión detectados:")
    
    cols_t1 = [c for c in ['CodigoExterno', 'Nombre', 'Categoria_Proyecto', 'Signify_Equivalente', 'Requerimiento_Potencia', 'Requerimiento_Flujo_Luminoso', 'Sistemas_Control_Telegestion', 'Estado_Cumplimiento_Signify'] if c in df_licitaciones.columns]
    st.dataframe(df_licitaciones[cols_t1], use_container_width=True)
    
    st.markdown("---")
    st.subheader("🔍 Ficha de Auditoría Técnica y Comercial por Proyecto")
    st.markdown("Seleccione un código externo para desplegar la ficha de análisis profundo con plazos, condiciones comerciales y normativas:")
    
    if not df_licitaciones.empty:
        codigos = df_licitaciones['CodigoExterno'].tolist()
        sel_codigo = st.selectbox("Seleccione Código de Licitación:", codigos, key="sel_codigo_exec")
        
        reg = df_licitaciones[df_licitaciones['CodigoExterno'] == sel_codigo].iloc[0]
        
        st.markdown(f"### 🏢 Ficha de Proyecto: {reg.get('Nombre', 'Sin Nombre')}")
        
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("#### 📋 Condiciones Comerciales y Contractuales")
            st.markdown(f"**Código Externo:** `{reg.get('CodigoExterno', 'N/A')}`")
            st.markdown(f"**Categoría:** {reg.get('Categoria_Proyecto', 'N/A')}")
            st.markdown(f"**Proveedor Adjudicado:** {reg.get('Proveedor_Adjudicado', 'N/A')}")
            st.markdown(f"**Monto Estimado / Adjudicado:** ${reg.get('Monto_Adjudicado_CLP', 0):,.0f} CLP")
            st.markdown(f"**Moneda de Oferta:** {reg.get('Moneda_Oferta', 'N/A')}")
            st.markdown(f"**Fechas (Creación / Cierre):** {reg.get('Fecha_Creacion', 'N/A')} al {reg.get('Fecha_Cierre', 'N/A')}")
            st.markdown(f"**Visita a Terreno:** {reg.get('Visita_Terreno', 'N/A')}")
            st.markdown(f"**Plazo Entrega Bodega:** {reg.get('Plazo_Entrega_Bodega', 'N/A')}")
            st.markdown(f"**Garantías Requeridas:** {reg.get('Garantias_Requeridas', 'N/A')}")
            st.markdown(f"**Multas / Sanciones:** {reg.get('Multas_Y_Sanciones', 'N/A')}")
            st.markdown(f"**Garantía de Producto:** {reg.get('Garantia_Producto_Anios', 'N/A')}")
            
        with col_right:
            st.markdown("#### ⚡ Especificaciones Técnicas y IoT")
            st.markdown(f"**Solución Signify Equivalente:** `{reg.get('Signify_Equivalente', 'N/A')}`")
            st.markdown(f"**Estado de Cumplimiento:** **{reg.get('Estado_Cumplimiento_Signify', 'N/A')}**")
            st.markdown(f"**Potencia Requerida:** `{reg.get('Requerimiento_Potencia', 'N/A')}`")
            st.markdown(f"**Flujo Lumínico:** `{reg.get('Requerimiento_Flujo_Luminoso', 'N/A')}`")
            st.markdown(f"**Protección IP:** `{reg.get('Requerimiento_IP', 'N/A')}`")
            st.markdown(f"**Resistencia IK:** `{reg.get('Requerimiento_IK', 'N/A')}`")
            st.markdown(f"**Normas / Certificaciones:** {reg.get('Certificaciones_Exigidas', 'N/A')}")
            st.markdown(f"**Control / Telegestión:** {reg.get('Sistemas_Control_Telegestion', 'N/A')}")

        st.markdown("#### 📈 Informe de Brecha Tecnológica y Oportunidad Comercial")
        st.info(reg.get('Analisis_Brecha_Tecnica', 'Sin análisis registrado'))

with tab2:
    st.subheader("🏆 Mapa de Competencia y Adjudicadas")
    st.markdown("Análisis estratégico de posicionamiento frente a competidores en licitaciones del sector público:")
    cols_t2 = [c for c in ['CodigoExterno', 'Nombre', 'Proveedor_Adjudicado', 'Monto_Adjudicado_CLP', 'Estado_Cumplimiento_Signify', 'Signify_Equivalente', 'Marcas_Competencia_Detectadas'] if c in df_licitaciones.columns]
    st.dataframe(df_licitaciones[cols_t2], use_container_width=True)

with tab3:
    st.subheader("💡 Portafolio Tecnológico Profesional Signify Chile")
    st.markdown("Líneas de infraestructura inteligente de referencia corporativa en `signify.com/es-cl/prof`:")
    portafolio_df = pd.DataFrame({
        "Familia_Signify": ["RoadFlair + Interact City", "Arena X + Interact Sports", "Tango Pro + Dynalite", "Color Kinetics", "GreenVision Solar"],
        "Aplicacion": ["Vial Pública e Inteligente / Túneles", "Estadios, Canchas y Polideportivos", "Ornamental y Arquitectónica Avanzada", "Fachadas Monumentales", "Iluminación Solar Autónoma"],
        "Estrategia_Tecnologica": ["Smart cities, zócalos Zhaga/NEMA y telegestión centralizada IoT", "Alto rendimiento lumínico, control DMX y cumplimiento IND", "Control dinámico de escenas DALI/DMX y tonos", "Diseño lumínico de precisión con norma DS1 estricta", "Autonomía energética total sin conexión a red eléctrica"]
    })
    st.dataframe(portafolio_df, use_container_width=True)
    
