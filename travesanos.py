import tkinter as tk
from tkinter import ttk, messagebox
import math

class CalculadorTravesaños:
    def __init__(self, root):
        self.root = root
        self.root.title("Cálculo Estructural de Travesaños (Muro Cortina)")
        self.root.geometry("900x750")

        # --- Variables de Entrada ---
        self.proyecto = tk.StringVar(value="Proyecto Muro Cortina N°1")
        self.item = tk.StringVar(value="Travesaño, Silicona y Vidrios")
        
        # Dimensiones (mm)
        self.B = tk.DoubleVar(value=1500.0) # Ancho del Vidrio / Largo Horizontal
        self.U = tk.DoubleVar(value=2500.0) # Altura Superior
        self.L = tk.DoubleVar(value=1000.0) # Altura Inferior
        self.q = tk.DoubleVar(value=100.0)  # Carga de viento kgf/m2
        
        # Setting Blocks
        self.tipo_material_block = tk.StringVar(value="Neopreno/EPDM")
        self.posicion_block_tipo = tk.StringVar(value="L/4") # L/4 o L/8
        self.espesor_vidrio = tk.DoubleVar(value=12.0)

        self.crear_interfaz()

    def crear_interfaz(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # --- SECCIÓN: Deformaciones Admisibles ---
        lbl_frame_def = ttk.LabelFrame(main_frame, text="Criterios de Deformación Admisible", padding="10")
        lbl_frame_def.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)

        ttk.Label(lbl_frame_def, text="Horizontal (Transversal):").grid(row=0, column=0, sticky="w")
        self.chk_h1 = ttk.Checkbutton(lbl_frame_def, text="L / 175")
        self.chk_h1.grid(row=0, column=1, sticky="w")
        self.chk_h1.state(['selected'])
        
        self.chk_h2 = ttk.Checkbutton(lbl_frame_def, text="L / 240 + 6.35 mm")
        self.chk_h2.grid(row=0, column=2, sticky="w")

        ttk.Label(lbl_frame_def, text="Vertical (Peso Propio):").grid(row=1, column=0, sticky="w")
        self.chk_v1 = ttk.Checkbutton(lbl_frame_def, text="L / 360 (Máx 3.18 mm)")
        self.chk_v1.grid(row=1, column=1, sticky="w")
        self.chk_v1.state(['selected'])

        # --- SECCIÓN: Parámetros de Diseño ---
        lbl_frame_params = ttk.LabelFrame(main_frame, text="Parámetros del Vidrio y Carga", padding="10")
        lbl_frame_params.grid(row=1, column=0, sticky="nsew", pady=5)

        ttk.Label(lbl_frame_params, text="Ancho del Vidrio (B) [mm]:").grid(row=0, column=0, sticky="w")
        ttk.Entry(lbl_frame_params, textvariable=self.B).grid(row=0, column=1)

        ttk.Label(lbl_frame_params, text="Altura Superior (U) [mm]:").grid(row=1, column=0, sticky="w")
        ttk.Entry(lbl_frame_params, textvariable=self.U).grid(row=1, column=1)

        ttk.Label(lbl_frame_params, text="Carga de Viento (q) [kgf/m²]:").grid(row=2, column=0, sticky="w")
        ttk.Entry(lbl_frame_params, textvariable=self.q).grid(row=2, column=1)

        # --- SECCIÓN: Setting Blocks (Calzos) ---
        lbl_frame_blocks = ttk.LabelFrame(main_frame, text="Configuración de Setting Blocks (Calzos)", padding="10")
        lbl_frame_blocks.grid(row=1, column=1, sticky="nsew", pady=5)

        ttk.Label(lbl_frame_blocks, text="Material:").grid(row=0, column=0, sticky="w")
        combo_mat = ttk.Combobox(lbl_frame_blocks, textvariable=self.tipo_material_block, 
                                 values=["Neopreno/EPDM", "Plomo (Lead)", "Lock-strip Gasket"])
        combo_mat.grid(row=0, column=1)

        ttk.Label(lbl_frame_blocks, text="Posición Sugerida:").grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(lbl_frame_blocks, text="L/4 (Preferido)", variable=self.posicion_block_tipo, value="L/4").grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(lbl_frame_blocks, text="L/8 (Alternativo)", variable=self.posicion_block_tipo, value="L/8").grid(row=2, column=1, sticky="w")

        # --- BOTÓN CALCULAR ---
        btn_calc = ttk.Button(main_frame, text="Calcular Requerimientos", command=self.ejecutar_calculos)
        btn_calc.grid(row=2, column=0, columnspan=2, pady=10)

        # --- SECCIÓN RESULTADOS ---
        self.txt_resultados = tk.Text(main_frame, height=12, width=80)
        self.txt_resultados.grid(row=3, column=0, columnspan=2)

    def ejecutar_calculos(self):
        try:
            b = self.B.get()
            u = self.U.get()
            
            # 1. Cálculo de Deformaciones Admisibles
            adm_h1 = b / 175
            adm_h2 = (b / 240) + 6.35
            adm_v = min(b / 360, 3.18)

            # 2. Cálculo de Longitud de Setting Blocks
            # Area en pies cuadrados (1 sq ft = 92903.04 mm2)
            area_vidrio_mm2 = b * u
            area_sqft = area_vidrio_mm2 / 92903.04
            
            material = self.tipo_material_block.get()
            min_length_inch = 0.0
            
            if material == "Neopreno/EPDM":
                len_inch = 0.1 * area_sqft
                if b > 1219.2: # 48 pulgadas
                    min_length_inch = 4.0
            elif material == "Plomo (Lead)":
                len_inch = 0.05 * area_sqft
                if b > 1219.2:
                    min_length_inch = 4.0
            else: # Lock-strip Gasket
                len_inch = 0.5 * area_sqft
                min_length_inch = 6.0
            
            final_len_inch = max(len_inch, min_length_inch)
            final_len_mm = final_len_inch * 25.4

            # 3. Ubicación de los bloques
            factor_pos = 0.25 if self.posicion_block_tipo.get() == "L/4" else 0.125
            distancia_pos = b * factor_pos

            # Mostrar Resultados
            res = f"--- RESULTADOS DE DISEÑO ---\n"
            res += f"Deformación Horizontal Admisible (L/175): {adm_h1:.2f} mm\n"
            res += f"Deformación Horizontal Admisible (L/240 + 6.35): {adm_h2:.2f} mm\n"
            res += f"Deformación Vertical Admisible (L/360): {adm_v:.2f} mm\n"
            res += f"--------------------------------------------\n"
            res += f"CÁLCULO DE SETTING BLOCKS (CALZOS DE APOYO):\n"
            res += f"Área del Vidrio: {area_sqft:.2f} ft²\n"
            res += f"Longitud Calculada por bloque: {final_len_mm:.2f} mm ({final_len_inch:.2f} in)\n"
            res += f"Ubicación desde el borde ({self.posicion_block_tipo.get()}): {distancia_pos:.2f} mm\n"
            
            self.txt_resultados.delete(1.0, tk.END)
            self.txt_resultados.insert(tk.END, res)

        except Exception as e:
            messagebox.showerror("Error", f"Error en los datos de entrada: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculadorTravesaños(root)
    root.mainloop()