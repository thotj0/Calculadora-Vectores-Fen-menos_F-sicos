import math
import streamlit as st

# Intento seguro de importar matplotlib
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False
    st.warning("Aviso: matplotlib no está disponible. La gráfica se desactivará.")

g = 9.81  # gravedad m/s^2

# ---------------- CLASES ----------------
class FuerzaVectorial:
    def __init__(self, nombre=None, magnitud=None, angulo=None, Fx=None, Fy=None,
                 altura=0.0, masa=None, aceleracion=None, peso=None, distancia=None):
        self.nombre = nombre or "F"
        self.magnitud = magnitud      # N
        self.angulo = angulo          # grados
        self.Fx = Fx                  # N
        self.Fy = Fy                  # N
        self.altura = altura          # m
        self.masa = masa              # kg (opcional por fuerza)
        self.aceleracion = aceleracion  # m/s^2 (opcional por fuerza)
        self.peso = peso              # N
        self.distancia = distancia    # m (para trabajo)
        self.trabajo = None           # J
        self._mensajes = []

    def completar_datos(self):
        self._mensajes = []

        # Componentes <-> polar
        if (self.Fx is not None) and (self.Fy is not None):
            self.magnitud = math.sqrt(self.Fx**2 + self.Fy**2)
            self.angulo = math.degrees(math.atan2(self.Fy, self.Fx))
        elif (self.magnitud is not None) and (self.angulo is not None):
            rad = math.radians(self.angulo)
            self.Fx = self.magnitud * math.cos(rad)
            self.Fy = self.magnitud * math.sin(rad)
        else:
            self._mensajes.append("Para calcular componentes o dirección: ingresa Fx y Fy, o magnitud y ángulo.")

        # Peso <-> masa (local a la fuerza si se usa)
        if (self.masa is not None) and (self.peso is None):
            self.peso = self.masa * g
        elif (self.peso is not None) and (self.masa is None):
            self.masa = self.peso / g
        else:
            if (self.masa is None) and (self.peso is None):
                self._mensajes.append("Para calcular peso o masa: proporciona m o P.")

        # Segunda ley (F = m a) local
        if (self.masa is not None) and (self.magnitud is not None) and (self.aceleracion is None):
            if self.masa == 0:
                self._mensajes.append("Masa no puede ser cero para calcular aceleración.")
            else:
                self.aceleracion = self.magnitud / self.masa
        elif (self.masa is not None) and (self.aceleracion is not None) and (self.magnitud is None):
            self.magnitud = self.masa * self.aceleracion
            if (self.angulo is not None) and ((self.Fx is None) or (self.Fy is None)):
                rad = math.radians(self.angulo)
                self.Fx = self.magnitud * math.cos(rad)
                self.Fy = self.magnitud * math.sin(rad)
        else:
            if (self.magnitud is None) and (self.aceleracion is None) and (self.masa is not None):
                self._mensajes.append("Para calcular aceleración o fuerza: falta F (magnitud) o a.")
            if (self.masa is None) and ((self.magnitud is not None) or (self.aceleracion is not None)):
                self._mensajes.append("Para relacionar F y a: falta la masa.")

        # Trabajo (suponiendo fuerza colineal con el desplazamiento)
        if (self.distancia is not None) and (self.magnitud is not None):
            self.trabajo = self.magnitud * self.distancia
        elif (self.distancia is not None) and (self.magnitud is None):
            self._mensajes.append("Para calcular trabajo (W), falta magnitud de la fuerza.")

    def momento(self):
        if self.Fy is None:
            self.completar_datos()
        return (self.Fy if self.Fy is not None else 0.0) * (self.altura if self.altura is not None else 0.0)

    def mensajes_faltantes(self):
        return self._mensajes[:]


class CuerpoFisico:
    def __init__(self, masa=None, peso=None, aceleracion_deseada=None, tension=None, angulo_fuerza_faltante=None):
        self.masa = masa
        self.peso = peso if peso is not None else (masa * g if masa else None)
        self.aceleracion_deseada = aceleracion_deseada
        self.tension = tension
        self.angulo_fuerza_faltante = angulo_fuerza_faltante  # grados (opcional)
        self.fuerzas_aplicadas = []

    def agregar_fuerza(self, fuerza: FuerzaVectorial):
        self.fuerzas_aplicadas.append(fuerza)

    def calcular_dinamica(self):
        # Completar datos de fuerzas
        for f in self.fuerzas_aplicadas:
            f.completar_datos()

        # Suma vectorial
        suma_fx = sum(f.Fx for f in self.fuerzas_aplicadas if f.Fx is not None)
        suma_fy = sum(f.Fy for f in self.fuerzas_aplicadas if f.Fy is not None)
        F_aplicada_mag = math.sqrt(suma_fx**2 + suma_fy**2)
        F_aplicada_ang = math.degrees(math.atan2(suma_fy, suma_fx)) if F_aplicada_mag != 0 else 0.0

        momentos = sum(f.momento() for f in self.fuerzas_aplicadas)
        trabajo_total = sum((f.trabajo or 0.0) for f in self.fuerzas_aplicadas)

        tipo = "indeterminado"
        aceleracion = None
        Fx_resultante = suma_fx
        Fy_resultante = suma_fy
        fuerza_resultante = F_aplicada_mag
        angulo_resultante = F_aplicada_ang

        fuerza_faltante_mag = None
        fuerza_faltante_ang = None
        inconsistencia_angulo = False

        # Caso 1: Grúa con tensión vertical
        if (self.tension is not None) and (self.masa is not None):
            Fy_total = self.tension - (self.masa * g) + suma_fy
            Fx_total = suma_fx
            fuerza_resultante = math.sqrt(Fx_total**2 + Fy_total**2)
            angulo_resultante = math.degrees(math.atan2(Fy_total, Fx_total)) if fuerza_resultante != 0 else 0.0
            Fx_resultante, Fy_resultante = Fx_total, Fy_total
            if self.masa and self.masa > 0:
                aceleracion = fuerza_resultante / self.masa
            tipo = "grua"

        # Caso 2: Fuerzas aplicadas sobre cuerpo con masa/peso -> aceleración
        elif (self.masa is not None) and (self.masa > 0) and (F_aplicada_mag is not None):
            aceleracion = F_aplicada_mag / self.masa
            tipo = "fuerzas_aplicadas"

        # Caso 3: Calcular fuerza faltante para lograr aceleración deseada
        if (self.aceleracion_deseada is not None) and (self.masa is not None) and (self.masa > 0):
            Fx_deseado = self.masa * self.aceleracion_deseada
            Fy_deseado = 0.0
            Fx_req = Fx_deseado - suma_fx
            Fy_req = Fy_deseado - suma_fy

            if self.angulo_fuerza_faltante is not None:
                rad = math.radians(self.angulo_fuerza_faltante)
                cos_a = math.cos(rad)
                sin_a = math.sin(rad)
                Mx = Fx_req / cos_a if cos_a != 0 else None
                My = Fy_req / sin_a if sin_a != 0 else None
                if (Mx is not None) and (My is not None):
                    if abs(Mx - My) <= 1e-6:
                        fuerza_faltante_mag = Mx
                    else:
                        inconsistencia_angulo = True
                        fuerza_faltante_mag = Fx_req * cos_a + Fy_req * sin_a
                elif Mx is not None:
                    fuerza_faltante_mag = Mx
                elif My is not None:
                    fuerza_faltante_mag = My
                else:
                    fuerza_faltante_mag = 0.0
                fuerza_faltante_ang = self.angulo_fuerza_faltante
            else:
                fuerza_faltante_mag = math.sqrt(Fx_req**2 + Fy_req**2)
                fuerza_faltante_ang = math.degrees(math.atan2(Fy_req, Fx_req)) if fuerza_faltante_mag != 0 else 0.0

            tipo = "fuerza_faltante"

        return {
            "tipo": tipo,
            "magnitud": fuerza_resultante,
            "angulo": angulo_resultante,
            "Fx": Fx_resultante,
            "Fy": Fy_resultante,
            "momento": momentos,
            "trabajo": trabajo_total,
            "aceleracion": aceleracion,
            "fuerza_faltante_mag": fuerza_faltante_mag,
            "fuerza_faltante_ang": fuerza_faltante_ang,
            "inconsistencia_angulo": inconsistencia_angulo
        }

# ---------------- FUNCIONES DE CÁLCULO ----------------
def calcular_resultante(fuerzas):
    # Completa datos de todas las fuerzas
    for f in fuerzas:
        f.completar_datos()

    hay_fx = any(f.Fx is not None for f in fuerzas)
    hay_fy = any(f.Fy is not None for f in fuerzas)
    if not hay_fx and not hay_fy:
        return None, None, (None, None), None, 0.0, 0.0, 0.0, None

    suma_fx = sum(f.Fx for f in fuerzas if f.Fx is not None)
    suma_fy = sum(f.Fy for f in fuerzas if f.Fy is not None)
    magnitud = math.sqrt(suma_fx**2 + suma_fy**2)
    angulo = math.degrees(math.atan2(suma_fy, suma_fx)) if magnitud != 0 else 0.0
    momentos = sum(f.momento() for f in fuerzas)

    masa_total = sum((f.masa or 0.0) for f in fuerzas)
    peso_total = sum((f.peso or 0.0) for f in fuerzas)
    trabajo_total = sum((f.trabajo or 0.0) for f in fuerzas)

    aceleracion_res = None
    if (masa_total is not None) and (masa_total > 0):
        aceleracion_res = magnitud / masa_total

    return magnitud, angulo, (suma_fx, suma_fy), momentos, masa_total, peso_total, trabajo_total, aceleracion_res


def graficar_vectores_fig(fuerzas, Fx_R, Fy_R, magnitud_R, angulo_R, aceleracion_R, masa_R, peso_R, trabajo_R):
    if not MATPLOTLIB_OK:
        return None

    # Chequeo: si no hay nada que graficar, salir
    hay_vectores = any((f.Fx is not None and f.Fy is not None) for f in fuerzas)
    if not hay_vectores and (Fx_R is None or Fy_R is None):
        return None

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_title("Sistema de fuerzas y datos resultantes")
    ax.set_xlabel("Fx (N)")
    ax.set_ylabel("Fy (N)")
    ax.axhline(0, color='gray', linewidth=0.8)
    ax.axvline(0, color='gray', linewidth=0.8)
    ax.set_aspect('equal', 'box')

    # Vectores individuales
    for f in fuerzas:
        if (f.Fx is not None) and (f.Fy is not None):
            ax.quiver(0, 0, f.Fx, f.Fy, angles='xy', scale_units='xy', scale=1, color='blue', alpha=0.85)
            etiqueta = f"{f.nombre}\n|F|={f.magnitud:.2f} N\nθ={f.angulo:.1f}°"
            if f.masa is not None: etiqueta += f"\nm={f.masa:.2f} kg"
            if f.peso is not None: etiqueta += f"\nP={f.peso:.2f} N"
            if f.aceleracion is not None: etiqueta += f"\na={f.aceleracion:.2f} m/s²"
            if f.trabajo is not None: etiqueta += f"\nW={f.trabajo:.2f} J"
            ax.text(f.Fx, f.Fy, etiqueta, color='blue', fontsize=8, ha='left', va='bottom')

    # Resultante
    if (Fx_R is not None) and (Fy_R is not None):
        ax.quiver(0, 0, Fx_R, Fy_R, angles='xy', scale_units='xy', scale=1, color='red', width=0.006)
        etiqueta_R = f"Resultante\n|F|={magnitud_R:.2f} N\nθ={angulo_R:.1f}°"
        if masa_R: etiqueta_R += f"\nm={masa_R:.2f} kg"
        if peso_R: etiqueta_R += f"\nP={peso_R:.2f} N"
        if aceleracion_R is not None: etiqueta_R += f"\na={aceleracion_R:.2f} m/s²"
        if trabajo_R: etiqueta_R += f"\nW={trabajo_R:.2f} J"
        ax.text(Fx_R, Fy_R, etiqueta_R, color='red', fontsize=9, ha='left', va='bottom')

    # Límites
    all_fx = [f.Fx for f in fuerzas if f.Fx is not None] + ([Fx_R] if Fx_R is not None else [])
    all_fy = [f.Fy for f in fuerzas if f.Fy is not None] + ([Fy_R] if Fy_R is not None else [])
    max_extent = max([1.0] + [abs(x) for x in all_fx + all_fy])
    ax.set_xlim(-1.2 * max_extent, 1.2 * max_extent)
    ax.set_ylim(-1.2 * max_extent, 1.2 * max_extent)

    ax.grid(True, linestyle='--', alpha=0.3)
    fig.tight_layout()
    return fig


def _to_float_or_none(s):
    s = (s or "").strip()
    try:
        return float(s) if s != "" else None
    except ValueError:
        return None

# ---------------- INTERFAZ STREAMLIT ----------------
st.set_page_config(page_title="Calculadora de fuerzas", layout="wide")
st.title("Calculadora vectorial de fuerzas, momentos, trabajo y dinámica")

# Estado de la app
if "fuerzas" not in st.session_state:
    st.session_state.fuerzas = []

# ---- Formulario para agregar fuerzas ----
with st.sidebar:
    st.header("Agregar fuerza")
    nombre = st.text_input("Nombre", value="F{}".format(len(st.session_state.fuerzas) + 1))
    magnitud = _to_float_or_none(st.text_input("Magnitud (N)"))
    angulo = _to_float_or_none(st.text_input("Ángulo (°)"))
    Fx = _to_float_or_none(st.text_input("Componente Fx (N)"))
    Fy = _to_float_or_none(st.text_input("Componente Fy (N)"))
    altura = _to_float_or_none(st.text_input("Altura para momento (m)"))
    masa_f = _to_float_or_none(st.text_input("Masa (kg) [opcional por fuerza]"))
    peso_f = _to_float_or_none(st.text_input("Peso (N) [opcional por fuerza]"))
    aceleracion_f = _to_float_or_none(st.text_input("Aceleración (m/s²) [opcional por fuerza]"))
    distancia = _to_float_or_none(st.text_input("Distancia (m, para trabajo W)"))

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Agregar fuerza"):
            f = FuerzaVectorial(
                nombre=nombre.strip() or "F",
                magnitud=magnitud,
                angulo=angulo,
                Fx=Fx,
                Fy=Fy,
                altura=altura if altura is not None else 0.0,
                masa=masa_f,
                peso=peso_f,
                aceleracion=aceleracion_f,
                distancia=distancia
            )
            f.completar_datos()
            st.session_state.fuerzas.append(f)
            st.success(f"Fuerza '{f.nombre}' agregada.")
    with col_btn2:
        if st.button("Limpiar fuerzas"):
            st.session_state.fuerzas = []
            st.info("Lista de fuerzas reiniciada.")

# ---- Lista y detalle de fuerzas ----
st.subheader("Fuerzas ingresadas")
if not st.session_state.fuerzas:
    st.info("No hay fuerzas agregadas. Usa el panel lateral para añadir.")
else:
    for idx, f in enumerate(st.session_state.fuerzas, start=1):
        with st.expander(f"Fuerza {idx}: {f.nombre}", expanded=False):
            st.write(f"- **|F|:** {f.magnitud:.3f} N" if f.magnitud is not None else "- **|F|:** (no definido)")
            st.write(f"- **θ:** {f.angulo:.3f}°" if f.angulo is not None else "- **θ:** (no definido)")
            if (f.Fx is not None) and (f.Fy is not None):
                st.write(f"- **Componentes:** Fx = {f.Fx:.3f} N, Fy = {f.Fy:.3f} N")
            if f.masa is not None: st.write(f"- **m:** {f.masa:.3f} kg")
            if f.peso is not None: st.write(f"- **P:** {f.peso:.3f} N")
            if f.aceleracion is not None: st.write(f"- **a:** {f.aceleracion:.3f} m/s²")
            if f.trabajo is not None: st.write(f"- **W:** {f.trabajo:.3f} J")
            faltantes = f.mensajes_faltantes()
            if faltantes:
                st.warning("Necesitas:")
                for m in faltantes:
                    st.write(f"- {m}")
            # Botón para eliminar fuerza
            if st.button(f"Eliminar {f.nombre}", key=f"del_{idx}"):
                st.session_state.fuerzas.pop(idx - 1)
                st.experimental_rerun()

# ---- Resultantes del sistema de fuerzas ----
st.subheader("Resultados del sistema de fuerzas")
if st.session_state.fuerzas:
    magnitud, angulo, (Fx_R, Fy_R), momentos, masa_total, peso_total, trabajo_total, aceleracion_res = calcular_resultante(st.session_state.fuerzas)

    if magnitud is None:
        st.error("No se pudo calcular la resultante. Ingresa al menos (Fx y Fy) o (magnitud y ángulo) en alguna fuerza.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Fuerza resultante |F|", f"{magnitud:.3f} N")
            st.metric("Dirección resultante θ", f"{angulo:.3f}°")
            st.write(f"**Componentes:** Fx = {Fx_R:.3f} N, Fy = {Fy_R:.3f} N")
        with col2:
            st.metric("Momento total (simplificado)", f"{momentos:.3f} N·m")
            if masa_total:
                st.metric("Masa total", f"{masa_total:.3f} kg")
            if peso_total:
                st.metric("Peso total", f"{peso_total:.3f} N")
        with col3:
            if trabajo_total:
                st.metric("Trabajo total", f"{trabajo_total:.3f} J")
            if aceleracion_res is not None:
                st.metric("Aceleración resultante", f"{aceleracion_res:.3f} m/s²")

        # Gráfica del sistema
        if MATPLOTLIB_OK:
            if st.checkbox("Mostrar gráfica del sistema de fuerzas", value=True):
                fig = graficar_vectores_fig(
                    st.session_state.fuerzas, Fx_R, Fy_R, magnitud, angulo,
                    aceleracion_res, masa_total, peso_total, trabajo_total
                )
                if fig is not None:
                    st.pyplot(fig)
                else:
                    st.info("No hay suficientes componentes para graficar.")
else:
    st.info("Agrega fuerzas para calcular la resultante.")

# ---- Dinámica del cuerpo (opcional) ----
st.subheader("Análisis del cuerpo (opcional)")
with st.form("cuerpo_fisico_form"):
    c1, c2, c3 = st.columns(3)
    with c1:
        masa_cuerpo = _to_float_or_none(st.text_input("Masa del cuerpo (kg)"))
        peso_cuerpo = _to_float_or_none(st.text_input("Peso del cuerpo (N)"))
    with c2:
        acel_deseada = _to_float_or_none(st.text_input("Aceleración deseada (m/s²)"))
        tension = _to_float_or_none(st.text_input("Tensión del cable (N)"))
    with c3:
        ang_faltante = _to_float_or_none(st.text_input("Ángulo de la fuerza faltante (°)"))
    submitted = st.form_submit_button("Calcular dinámica del cuerpo")

if submitted:
    if any([masa_cuerpo, peso_cuerpo, acel_deseada, tension, ang_faltante]):
        cuerpo = CuerpoFisico(
            masa=masa_cuerpo,
            peso=peso_cuerpo,
            aceleracion_deseada=acel_deseada,
            tension=tension,
            angulo_fuerza_faltante=ang_faltante
        )
        for f in st.session_state.fuerzas:
            cuerpo.agregar_fuerza(f)

        resultado = cuerpo.calcular_dinamica()

        st.success(f"Tipo de problema detectado: {resultado['tipo']}")
        colA, colB, colC = st.columns(3)
        with colA:
            st.metric("Fuerza resultante |F|", f"{resultado['magnitud']:.3f} N")
            st.metric("Dirección θ", f"{resultado['angulo']:.3f}°")
        with colB:
            st.write(f"**Componentes:** Fx = {resultado['Fx']:.3f} N, Fy = {resultado['Fy']:.3f} N")
            st.metric("Momento total", f"{resultado['momento']:.3f} N·m")
        with colC:
            st.metric("Trabajo total", f"{resultado['trabajo']:.3f} J")
            if resultado["aceleracion"] is not None:
                st.metric("Aceleración resultante", f"{resultado['aceleracion']:.3f} m/s²")

        if resultado["fuerza_faltante_mag"] is not None:
            if resultado["fuerza_faltante_ang"] is not None:
                st.info(f"Fuerza faltante: {resultado['fuerza_faltante_mag']:.3f} N a {resultado['fuerza_faltante_ang']:.1f}°")
            else:
                st.info(f"Fuerza faltante: {resultado['fuerza_faltante_mag']:.3f} N")
            if resultado["inconsistencia_angulo"]:
                st.warning("Con ese ángulo, la fuerza faltante no coincide exactamente con el vector requerido; se usó la proyección más cercana.")

        # Gráfica del cuerpo
        if MATPLOTLIB_OK and st.checkbox("Mostrar gráfica del cuerpo", value=True):
            fig_cuerpo = graficar_vectores_fig(
                st.session_state.fuerzas,
                resultado["Fx"], resultado["Fy"], resultado["magnitud"], resultado["angulo"],
                resultado["aceleracion"], masa_cuerpo, peso_cuerpo, resultado["trabajo"]
            )
            if fig_cuerpo is not None:
                st.pyplot(fig_cuerpo)
            else:
                st.info("No hay suficientes componentes para graficar.")
    else:
        st.info("No se ingresaron datos del cuerpo físico. Se omite ese análisis.")



st.markdown("""
<h3 style="text-align: center;">Objetivos principales</h3>
<ul>
  <li><b>Ingresar fuerzas individuales</b> con datos como magnitud, ángulo, componentes (Fx, Fy), masa, peso, aceleración, altura (para momentos) y distancia (para trabajo).</li>
  <li><b>Completar automáticamente valores faltantes</b>: por ejemplo, si das magnitud y ángulo, calcula Fx y Fy; si das masa, calcula peso; si das fuerza y masa, calcula aceleración.</li>
  <li><b>Calcular la resultante del sistema</b>: suma vectorial de todas las fuerzas, con magnitud, dirección, componentes, momento total, trabajo total y aceleración resultante.</li>
  <li><b>Analizar un cuerpo físico</b>: permite introducir datos como masa, tensión en un cable, aceleración deseada o ángulo de una fuerza faltante, y determina:
    <ul>
      <li>Tipo de problema (grúa, fuerzas aplicadas, fuerza faltante).</li>
      <li>Fuerza faltante necesaria para lograr la aceleración deseada.</li>
      <li>Inconsistencias si el ángulo no coincide con el vector requerido.</li>
    </ul>
  </li>
  <li><b>Visualizar gráficamente</b>: dibuja los vectores individuales y la fuerza resultante en un plano, con etiquetas que muestran magnitud, ángulo y datos asociados.</li>
</ul>

<h3 style="text-align: center;">Usos prácticos</h3>
<ul>
  <li>Resolver problemas de <b>estática y dinámica</b> en cursos de física o ingeniería.</li>
  <li>Aplicar conceptos a situaciones reales: tensión en cables, trabajo realizado por fuerzas, momentos en estructuras.</li>
  <li>Verificar cálculos manuales con una herramienta interactiva que muestra resultados y gráficas.</li>
</ul>
            
<h3 style="text-align: center;">Ejemplos de ejercicios</h3>
<h6>Calcula la fuerza resultante de dos fuerzas: fuerza uno de 100 N en una dirección de 120 grados y fuerza dos de 80 N en una dirección de 30 grados.
    <br><br>Calcula la fuerza resultante de tres fuerzas: fuerza uno de 200 N en una dirección de 165 grados, fuerza dos de 180 N en una dirección de 60 grados y una fuerza tres de 250 N en una dirección de 270 grados.
    <br><br>Calcula la fuerza que se requiere para mover una caja, cuya masa es de 60 kg y su aceleración es de 0.5 metros sobre segundo al cuadrado. 
    <br><br>Calcular la aceleración que se obtiene cuando a un objeto de 250 kg se le aplica una fuerza de 75 N.
    <br><br>Calcular la fuerza necesaria para jalar una caja de 60 kg a una aceleración deseada de 1.5 metros sobre segundo al cuadrado, si voy a jalar en una dirección de 30 grados.
    <br><br>Calcular la tensión que se le ejerce a un cable si está bajando una masa de 57 kg a una aceleración de 0.75 metros sobre segundo al cuadrado.
    <br><br>Calcular el trabajo que se realiza al aplicar una fuerza de 35 N a un objeto y este se desplace 3 metros.</h6>
""", unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center;'>Colegio de Bachilleres del Estado de Oaxaca<br>COBAO Plantel 42 Huitzo</h3>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center;'>UAQ: Fenômenos fisicos<br>Arq. Arturo Mendosa Martinez<br>DACO 507</h5>", unsafe_allow_html=True)
st.markdown("<p>Baltazar Díaz melissa <br> Garcia Santiago Citlali Maribel <br> Mendoza Cruz Naomi Mariana <br> Ramírez Cruz José Manuel <br>Vera Morales Iveth Sarahi</p>", unsafe_allow_html=True)


st.markdown(
    """
    <style>
    .corner-img {
        position: absolute;
        top: 10px;
        right: 10px;
    }
    </style>
    <img src="https://pbs.twimg.com/profile_images/1529003743/cobao_logo_400x400.png" class="corner-img" width="100">
    """,
    unsafe_allow_html=True
)


