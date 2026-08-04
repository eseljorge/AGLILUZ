import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="AgliLuz: Inteligencia y Análisis de Licitaciones",
    page_icon="💡",
    layout="wide"
)

st.markdown("# 💡 AgliLuz: Plataforma Online de Inteligencia y Análisis de Licitaciones")
st.markdown("Sistema autónomo de análisis técnico profundo, bases comerciales y mapeo de competencia para **Signify Chile**.")

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
    
    # Datos de demostración completos con estructura técnica y comercial detallada
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
    st.info("ℹ️ **Modo Demostración Activo:** Estás viendo datos estructurados completos. Ejecuta tu flujo en GitHub Actions para sincronizar procesos reales.")

# Métricas Principales
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Procesos Analizados", len(df_licitaciones))
with col2:
    st.metric("Procesos Filtrados Activos", len(df_licitaciones))
with col3:
    volumen_total = df_licitaciones['Monto_Adjudicado_CLP'].sum() if 'Monto_Adjudicado_CLP' in df_licitaciones.columns else 0
    st.metric("Volumen Mercado (CLP)", f"${volumen_total:,.0f}")
with col4:
    st.metric("Alta Compatibilidad Signify", len(df_licitaciones))

st.markdown("---")

# 3 Pestañas de Dashboards
tab1, tab2, tab3 = st.tabs(["📊 Dashboard de Licitaciones", "🏆 Mapa de Competencia y Adjudicadas", "💡 Portafolio Signify Chile"])

with tab1:
    st.subheader("Listado Detallado y Requerimientos Técnicos Extraídos")
    st.markdown("Extracción exhaustiva de elementos técnicos (potencia, flujo, IP, IK, telegestión) y estado de cumplimiento por proyecto:")
    
    # Tabla resumen con todos los requerimientos técnicos clave visibles
    cols_t1 = [c for c in ['CodigoExterno', 'Nombre', 'Categoria_Proyecto', 'Signify_Equivalente', 'Requerimiento_Potencia', 'Requerimiento_Flujo_Luminoso', 'Sistemas_Control_Telegestion', 'Estado_Cumplimiento_Signify'] if c in df_licitaciones.columns]
    st.dataframe(df_licitaciones[cols_t1], use_container_width=True)
    
    st.markdown("---")
    st.subheader("🔍 Ficha de Detalle Técnico y Comercial por Licitación")
    st.markdown("Selecciona un Código Externo para desplegar la ficha completa con plazos, monedas, garantías, multas y análisis de brecha:")
    
    if not df_licitaciones.empty:
        codigos = df_licitaciones['CodigoExterno'].tolist()
        sel_codigo = st.selectbox("Seleccione un Código Externo:", codigos, key="sel_codigo_detalle")
        
        reg = df_licitaciones[df_licitaciones['CodigoExterno'] == sel_codigo].iloc[0]
        
        st.markdown(f"### 📄 {reg.get('Nombre', 'Sin Nombre')}")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 📋 Información Comercial y Plazos")
            st.markdown(f"**ID / Código Externo:** `{reg.get('CodigoExterno', 'N/A')}`")
            st.markdown(f"**Categoría:** {reg.get('Categoria_Proyecto', 'N/A')}")
            st.markdown(f"**Proveedor Adjudicado:** {reg.get('Proveedor_Adjudicado', 'N/A')}")
            st.markdown(f"**Monto Adjudicado:** ${reg.get('Monto_Adjudicado_CLP', 0):,.0f} CLP")
            st.markdown(f"**Moneda de Oferta:** {reg.get('Moneda_Oferta', 'N/A')}")
            st.markdown(f"**Fechas (Creación / Cierre):** {reg.get('Fecha_Creacion', 'N/A')} al {reg.get('Fecha_Cierre', 'N/A')}")
            st.markdown(f"**Visita a Terreno:** {reg.get('Visita_Terreno', 'N/A')}")
            st.markdown(f"**Plazo de Entrega en Bodega:** {reg.get('Plazo_Entrega_Bodega', 'N/A')}")
            st.markdown(f"**Garantías Requeridas:** {reg.get('Garantias_Requeridas', 'N/A')}")
            st.markdown(f"**Multas y Sanciones:** {reg.get('Multas_Y_Sanciones', 'N/A')}")
            st.markdown(f"**Garantía de Producto:** {reg.get('Garantia_Producto_Anios', 'N/A')}")
            
        with col_b:
            st.markdown("#### ⚙️ Requerimientos Técnicos y Control")
            st.markdown(f"**Equivalente Signify:** `{reg.get('Signify_Equivalente', 'N/A')}`")
            st.markdown(f"**Estado de Cumplimiento:** **{reg.get('Estado_Cumplimiento_Signify', 'N/A')}**")
            st.markdown(f"**Potencia Requerida:** `{reg.get('Requerimiento_Potencia', 'N/A')}`")
            st.markdown(f"**Flujo Lumínico:** `{reg.get('Requerimiento_Flujo_Luminoso', 'N/A')}`")
            st.markdown(f"**Protección IP:** `{reg.get('Requerimiento_IP', 'N/A')}`")
            st.markdown(f"**Resistencia IK:** `{reg.get('Requerimiento_IK', 'N/A')}`")
            st.markdown(f"**Certificaciones / Normas:** {reg.get('Certificaciones_Exigidas', 'N/A')}")
            st.markdown(f"**Sistemas de Control / Telegestión:** {reg.get('Sistemas_Control_Telegestion', 'N/A')}")

        st.markdown("#### 📊 Análisis Técnico de Brecha y Cumplimiento Signify")
        st.success(reg.get('Analisis_Brecha_Tecnica', 'Sin análisis registrado'))

with tab2:
    st.subheader("🏆 Mapa de Competencia y Adjudicadas")
    st.markdown("Cruzando proveedores adjudicados, montos de mercado y estados de cumplimiento técnico:")
    cols_t2 = [c for c in ['CodigoExterno', 'Nombre', 'Proveedor_Adjudicado', 'Monto_Adjudicado_CLP', 'Estado_Cumplimiento_Signify', 'Signify_Equivalente', 'Marcas_Competencia_Detectadas'] if c in df_licitaciones.columns]
    st.dataframe(df_licitaciones[cols_t2], use_container_width=True)

with tab3:
    st.subheader("💡 Portafolio Profesional Signify Chile")
    st.markdown("Líneas de productos y soluciones integrales de referencia en `signify.com/es-cl/prof`:")
    portafolio_df = pd.DataFrame({
        "Familia_Signify": ["RoadFlair + Interact City", "Arena X + Interact Sports", "Tango Pro + Dynalite", "Color Kinetics", "GreenVision Solar"],
        "Aplicacion": ["Vial Inteligente y Túneles", "Estadios y Polideportivos IND", "Arquitectónica y Control Dinámico", "Fachadas Monumentales", "Fotovoltaica Autónoma"],
        "Estrategia_Chile": ["Smart cities, zócalos Zhaga/NEMA y telegestión centralizada", "Máximo rendimiento, alta potencia y cumplimiento DS1", "Control avanzado de escenas y gestión DALI/DMX", "Diseño y cumplimiento estricto norma lumínica", "Autonomía completa fuera de red"]
    })
    st.dataframe(portafolio_df, use_container_width=True)
