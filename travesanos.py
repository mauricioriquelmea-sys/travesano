import streamlit as st

# Configuración de la interfaz
st.set_page_config(page_title="Cálculo de Travesaños - Mauricio", layout="wide")
st.title("Cálculo Estructural de Travesaños y Apoyos")

# --- ENTRADA DE DATOS ---
with st.sidebar:
    st.header("Parámetros de Diseño")
    b = st.number_input("Ancho del Vidrio (B) [mm]", value=1500.0)
    u = st.number_input("Altura Superior (U) [mm]", value=2500.0)
    
    st.subheader("Criterios de Deflexión")
    # Criterios solicitados: L/175, L/240 + 6.35 y L/360
    usa_h1 = st.checkbox("L / 175", value=True)
    usa_h2 = st.checkbox("L / 240 + 6.35 mm", value=True)
    usa_v1 = st.checkbox("L / 360 (Máx 3.18 mm)", value=True)

    st.subheader("Setting Blocks")
    material = st.selectbox("Material", ["Neopreno/EPDM", "Plomo (Lead)", "Lock-strip Gasket"])
    posicion = st.radio("Posición", ["L/4", "L/8"])

# --- LÓGICA DE CÁLCULO ---
# 1. Deflexiones Admisibles
deflexion_h1 = b / 175
deflexion_h2 = (b / 240) + 6.35
deflexion_v = min(b / 360, 3.18)

# 2. Cálculo de Setting Blocks (Basado en imagen: 0.1", 0.05" o 0.5" por sqft)
area_sqft = (b * u) / 92903.04  # Conversión mm2 a ft2
if material == "Neopreno/EPDM":
    l_inch = 0.1 * area_sqft
    min_l = 4.0 if b > 1219.2 else 0
elif material == "Plomo (Lead)":
    l_inch = 0.05 * area_sqft
    min_l = 4.0 if b > 1219.2 else 0
else: # Lock-strip Gasket
    l_inch = 0.5 * area_sqft
    min_l = 6.0

final_l_mm = max(l_inch, min_l) * 25.4
distancia_apoyo = b * (0.25 if posicion == "L/4" else 0.125)

# --- VISUALIZACIÓN DE RESULTADOS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Límites de Deformación")
    if usa_h1: st.info(f"**Horizontal (L/175):** {deflexion_h1:.2f} mm")
    if usa_h2: st.info(f"**Horizontal (L/240 + 6.35):** {deflexion_h2:.2f} mm")
    if usa_v1: st.warning(f"**Vertical (L/360):** {deflexion_v:.2f} mm")

with col2:
    st.subheader("Especificación de Calzos (Vidrio)")
    st.success(f"**Longitud mínima del calzo:** {final_l_mm:.2f} mm")
    st.success(f"**Ubicar a:** {distancia_apoyo:.2f} mm desde los extremos")
    st.write(f"Área calculada: {area_sqft:.2f} ft²")

# Imagen de referencia para los apoyos