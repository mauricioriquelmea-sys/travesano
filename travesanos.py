# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import os

# =================================================================
# 1. MOTOR DE CÁLCULO ACTUALIZADO (MÉTRICO)
# =================================================================
def calcular_todo_metrico():
    # Propiedades del Material (Aluminio/Acero)
    E = 21000000000 if "Acero" in material else 7101002754
    Fcy = 27532337.75 if "Acero" in material else (17576739.5 if "T6" in material else 11249113.3)

    L_m, U_m, e_m = L / 1000, U / 1000, e_vidrio / 1000
    
    # --- Criterios de Deformación ---
    df_h_adm = (L / 175) if L < 4115 else ((L / 240) + 6.35)
    df_v_adm = min(L / 360, 3.18)

    # --- Inercias y Módulos ---
    # Eje X-X (Viento)
    ratio_h = U_m / (2 * L_m)
    factor_h = (1 - (4/3) * (ratio_h**2)) if ratio_h < 1 else 1.0
    ix_val = ((5 / 384) * q_viento * U_m * L_m**4 / (E * (df_h_adm/1000))) * factor_h
    
    # Eje Y-Y (Peso Vidrio)
    peso_lineal = 2500 * e_m * U_m 
    iy_val = (5 / 384) * peso_lineal * L_m**4 / (E * (df_v_adm/1000))

    Fb = 0.6 * Fcy
    sx_val = ((1/8 * q_viento * U_m * L_m**2) / Fb) * 100**3
    sy_val = ((1/8 * peso_lineal * L_m**2) / Fb) * 100**3

    # --- CÁLCULO DE CALZOS (UNIDADES MÉTRICAS) ---
    area_m2 = L_m * U_m
    
    # Aplicación de fórmulas: Neopreno (27 mm/m2) / PVC (14 mm/m2)
    if mat_block == "Neopreno/EPDM/Silicona":
        longitud_calc = 27 * area_m2
        minimo_norma = 100.0 if L > 1219.2 else 50.0 # Mínimos de seguridad en mm
    elif mat_block == "PVC":
        longitud_calc = 14 * area_m2
        minimo_norma = 100.0 if L > 1219.2 else 50.0
    else: # Plomo u otros (Referencia anterior)
        longitud_calc = 25.4 * (0.05 * (area_m2 * 10.764))
        minimo_norma = 100.0
    
    final_sb_mm = max(longitud_calc, minimo_norma)
    dist_sb_mm = L * (0.25 if "L/4" in pos_block else 0.125)

    return (ix_val * 100**4, iy_val * 100**4, sx_val, sy_val, 
            final_sb_mm, dist_sb_mm, area_m2, df_h_adm, df_v_adm)

# =================================================================
# 2. INTERFAZ DE USUARIO (SIDEBAR Y BOTONES)
# =================================================================
st.sidebar.header("⚙️ Parámetros de Diseño")

with st.sidebar.expander("📐 Geometría y Cargas", expanded=True):
    L = st.number_input("Longitud Travesaño (L) [mm]", value=1500.0)
    U = st.number_input("Altura Vidrio Superior (U) [mm]", value=2500.0)
    q_viento = st.number_input("Carga Viento (q) [kgf/m²]", value=100.0)
    e_vidrio = st.number_input("Espesor Vidrio (e) [mm]", value=12.0)

with st.sidebar.expander("🛠️ Configuración de Calzos", expanded=True):
    mat_block = st.selectbox("Material del Calzo", ["Neopreno/EPDM/Silicona", "PVC"])
    pos_block = st.radio("Posición de Apoyo", ["L/4 (Preferida)", "L/8 (Alternativa)"])
    
    # Botón dinámico para la guía
    if st.button("Ver Guía de Calzos"):
        if os.path.exists("setting.jpg"):
            st.image("setting.jpg", caption="Ubicación de tacos de asentamiento")

# Ejecución de cálculos
ix, iy, sx, sy, sb_len, sb_pos, area, d_h, d_v = calcular_todo_metrico()

# =================================================================
# 3. DESPLIEGUE DE RESULTADOS
# =================================================================
st.subheader("📊 Requerimientos de Sección y Calzos")

# Filas de Inercia y Módulo
c1, c2 = st.columns(2)
with c1: st.metric("Inercia Ix (Viento)", f"{ix:.2f} cm⁴")
with c2: st.metric("Inercia Iy (Peso)", f"{iy:.2f} cm⁴")

c3, c4 = st.columns(2)
with c3: st.metric("Módulo Sx", f"{sx:.2f} cm³")
with c4: st.metric("Módulo Sy", f"{sy:.2f} cm³")

st.divider()

# Resultados de Calzos con la nueva fórmula métrica
st.markdown(f"""
<div style="background-color: #fffaf0; padding: 20px; border: 1px solid #ff9900; border-radius: 8px;">
    <h4 style="color: #ff9900; margin-top:0;">Especificación de Calzos (Métrico):</h4>
    <ul>
        <li><strong>Área del Vidrio:</strong> {area:.2f} m²</li>
        <li><strong>Fórmula aplicada:</strong> {"27 mm/m²" if mat_block == "Neopreno/EPDM/Silicona" else "14 mm/m²"}</li>
        <li><strong>Largo calculado por bloque:</strong> {sb_len:.2f} mm</li>
        <li><strong>Distancia desde extremos:</strong> {sb_pos:.1f} mm</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Imagen del travesaño siempre visible
if os.path.exists("trav.jpg"):
    st.image("trav.jpg", caption="Detalle de Travesaño", width=500)

# =================================================================
# 4. DESPLIEGUE DE RESULTADOS
# =================================================================
st.subheader("📊 Resumen de Requerimientos Mínimos de Sección")

# Fila 1: Inercias
c1, c2 = st.columns(2)
with c1: st.metric("Inercia Ix (Viento)", f"{ix:.2f} cm⁴", help=f"Límite: {d_h:.2f} mm")
with c2: st.metric("Inercia Iy (Peso Vidrio)", f"{iy:.2f} cm⁴", help=f"Límite: {d_v:.2f} mm")

# Fila 2: Módulos
c3, c4 = st.columns(2)
with c3: st.metric("Módulo Sx (Resistencia Viento)", f"{sx:.2f} cm³")
with c4: st.metric("Módulo Sy (Resistencia Peso)", f"{sy:.2f} cm³")

st.divider()

# Sección de Calzos
st.subheader("🛠️ Especificación de Setting Blocks (Calzos)")
col_sb1, col_sb2 = st.columns(2)

with col_sb1:
    st.markdown(f"""
    <div class="guide-box">
        <h4 style="margin-top:0; color: #ff9900;">Resultados del Cálculo:</h4>
        <ul>
            <li><strong>Área del Vidrio:</strong> {area_ft2:.2f} ft²</li>
            <li><strong>Longitud mínima del calzo:</strong> {sb_len:.2f} mm</li>
            <li><strong>Ubicación ({pos_block.split()[0]}):</strong> {sb_pos:.2f} mm desde extremos</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col_sb2:
    if os.path.exists("trav.jpg"):
        st.image("trav.jpg", caption="Diagrama de Travesaño", use_column_width=True)
    else:
        st.info("Imagen 'trav.jpg' no disponible.")


# =================================================================
# 5. GRÁFICOS DE SENSIBILIDAD (Ix e Iy vs LONGITUD)
# =================================================================
st.subheader("📈 Análisis de Sensibilidad de Inercia Requerida")
st.markdown("Visualización de cómo aumentan Ix e Iy al incrementar la longitud del travesaño (L), manteniendo fijos U y q.")

# Rango de longitudes para el eje X (2000mm a 6000mm)
L_axis = np.linspace(2000, 6000, 50)
Ix_axis = []
Iy_axis = []

# Módulo de elasticidad según material seleccionado
Ex = 21000000000 if material == "Acero A42-27ES" else 7101002754

# Parámetros fijos para el gráfico
U_m_plot = U / 1000
e_m_plot = e_vidrio / 1000

# Bucle para calcular inercias en cada punto de longitud
for lx in L_axis:
    lx_m = lx / 1000
    
    # --- Cálculo Ix (Viento) ---
    # Criterio de deflexión horizontal variable según longitud
    dfx_h = (lx / 175) if lx < 4115 else ((lx / 240) + 6.35)
    
    # Factor trapezoidal variable
    r_h = U_m_plot / (2 * lx_m)
    f_h = (1 - (4/3)*r_h**2) if r_h < 1 else 1.0
    
    # Ix requerida en cm4
    ix_plot = ((5 / 384) * q_viento * U_m_plot * lx_m**4 / (Ex * (dfx_h/1000))) * f_h
    Ix_axis.append(ix_plot * 100**4)
    
    # --- Cálculo Iy (Peso) ---
    # Criterio de deflexión vertical estándar variable min(L/360, 3.18)
    dfx_v = min(lx / 360, 3.18)
    
    # Iy requerida en cm4 (uniform load assumed for DL)
    peso_v = 2500 * e_m_plot * U_m_plot
    iy_plot = (5 / 384) * peso_v * lx_m**4 / (Ex * (dfx_v/1000))
    Iy_axis.append(iy_plot * 100**4)

# Creación de los gráficos
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Gráfico 1: Inercia Ix (Viento, Horizontal)
ax1.plot(L_axis, Ix_axis, color='#003366', linewidth=2, label=f'Ix Req. (Viento, U={U}mm)')
ax1.axvline(4115, color='red', ls='--', alpha=0.5, label='Umbral Cambio Criterio (4115mm)')
ax1.scatter([L], [ix], color='red', zorder=5, label='Punto de Diseño Actual')
ax1.set_xlabel("Longitud Travesaño L (mm)")
ax1.set_ylabel("Inercia Ix Req. (cm4)")
ax1.set_title("Ix Requerida ante Carga de Viento")
ax1.legend()
ax1.grid(True, alpha=0.3)

# Gráfico 2: Inercia Iy (Peso, Vertical)
ax2.plot(L_axis, Iy_axis, color='#ff9900', linewidth=2, label=f'Iy Req. (Peso Vidrio, e={e_vidrio}mm)')
ax2.scatter([L], [iy], color='red', zorder=5, label='Punto de Diseño Actual')
ax2.set_xlabel("Longitud Travesaño L (mm)")
ax2.set_ylabel("Inercia Iy Req. (cm4)")
ax2.set_title("Iy Requerida ante Peso Propio del Vidrio")
ax2.legend()
ax2.grid(True, alpha=0.3)

# Desplegar los gráficos
st.pyplot(fig)

# Pie de página
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>AccuraWall Port | Mauricio Riquelme | Prediseño de Travesaños</div>", unsafe_allow_html=True)