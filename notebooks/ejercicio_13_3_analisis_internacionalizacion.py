# -*- coding: utf-8 -*-
# Versión .py del notebook ejercicio_13_3 (generada). Las celdas están separadas por # %%
# %% [markdown]
# # Ejercicio 13.3 — Análisis de internacionalización de «Ernesto Investing AI» (IHC · Sesión 13)
# **Curso:** IHC 202W0606 · UNMSM · FISI · 2026-II · **Docente:** Prof. Ernesto D. Cancho-Rodríguez
# 
# **Qué hace este cuaderno:** (1) demuestra codificaciones en Python, (2) analiza la **auditoría real** de 14 sitios financieros (Fuente B), (3) mide la **expansión de texto** y los truncados medidos en el DOM del portal A frente a B (13.2) y (4) compara **formatos ambiguos (A) y explícitos (B)** en el experimento 13.3.
# 
# **Regla de datos:** los archivos `*_PRUEBA_TECNICA_BOT.csv` los generó un robot para probar el flujo: **no son datos de personas y no se interpretan**. Para conclusiones use los CSV de su grupo con consentimiento y código anónimo.
# %%
# Ejercicio 13.3 -- Configuración y carga de datos
# Entorno de ejecución: Google Colaboratory o Jupyter local (Python 3.10+).
import glob, os, unicodedata, math
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
os.makedirs("figuras", exist_ok=True)
PAL = ["#1F3864", "#800000", "#1B7E34", "#C5961A", "#5B2C6F", "#0A3D5C"]    # paleta del curso
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

def buscar(patron):
    # Busca el CSV en la carpeta actual, en datos_prueba y en el directorio padre; en Colab ofrece subirlo.
    for base in [".", "datos_prueba", "..", "../datos", "../datos/simulados"]:
        r = sorted(glob.glob(os.path.join(base, patron)))
        if r: return r
    try:
        from google.colab import files
        print("Suba el archivo que coincide con:", patron); return list(files.upload().keys())
    except Exception:
        return []

f_aud = buscar("auditoria_i18n_sitios_reales.csv")
f_132 = buscar("ejercicio_13_2_auditoria*.csv")
f_133 = buscar("ejercicio_13_3_experimento*.csv")
print("auditoría real:", f_aud, "| 13.2:", f_132, "| 13.3:", f_133)
aud = pd.read_csv(f_aud[0], encoding="utf-8-sig") if f_aud else pd.DataFrame()
t132 = pd.read_csv(f_132[0], encoding="utf-8-sig") if f_132 else pd.DataFrame()
t133 = pd.concat([pd.read_csv(f, encoding="utf-8-sig") for f in f_133], ignore_index=True) if f_133 else pd.DataFrame()
ES_BOT = any("BOT" in f for f in f_132 + f_133)
print("¿Datos rotulados PRUEBA_TECNICA_BOT? ->", ES_BOT, "(si es True, NO interprete los resultados como personas)")
# %% [markdown]
# ## 1. Codificaciones de caracteres en Python
# Un **carácter** (lo que ve la persona) se guarda como **punto de código Unicode** y luego como **bytes** según la codificación (UTF-8, UTF-16, Latin-1). Si se decodifica con la tabla equivocada aparece el **mojibake**.
# %%
# Ejercicio 13.3a -- Codificar, decodificar y detectar mojibake
textos = ["Señal COMPRAR", "Ñandú Minerals · S/ 1 234,56", "買い / 売り", "شراء / بيع", "📈 NVDA +3,2 %"]
filas = []
for s in textos:
    b8, b16, grafemas = s.encode("utf-8"), s.encode("utf-16-le"), len(s)   # len() cuenta puntos de código, no grafemas
    try: b1 = len(s.encode("latin-1"))
    except UnicodeEncodeError: b1 = None
    moji = b8.decode("windows-1252", errors="replace")                    # UTF-8 leído como Windows-1252
    filas.append(dict(texto=s, puntos_de_codigo=len(s), bytes_utf8=len(b8), bytes_utf16=len(b16), bytes_latin1=b1, mojibake=moji))
enc = pd.DataFrame(filas); display(enc) if "display" in globals() else print(enc.to_string())
# Normalización: «ñ» como 1 punto de código (NFC) o como n + tilde (NFD)
a, d = unicodedata.normalize("NFC", "ñ"), unicodedata.normalize("NFD", "ñ")
print("NFC:", [hex(ord(c)) for c in a], "| NFD:", [hex(ord(c)) for c in d], "| ¿iguales sin normalizar?", a == d)
# Prueba: UTF-8 usa 1 a 4 bytes por punto de código
assert len("ñ".encode("utf-8")) == 2 and len("買".encode("utf-8")) == 3 and len("📈".encode("utf-8")) == 4
print("OK: ñ=2 bytes, 買=3 bytes, 📈=4 bytes en UTF-8")
# %% [markdown]
# ## 2. Auditoría real de internacionalización (Fuente B)
# Datos de **la página de inicio** de 14 sitios, medidos con Chrome en una fecha y hora declaradas. Los sitios que bloquean el acceso se registran como **NO VÁLIDA** y **no se promedian**. El puntaje 0–10 es **heurístico** (lang 2, charset 1, hreflang 2, selector de idioma 2, respuesta a `Accept-Language` 2, sin banderas como idioma 1): no es un veredicto del sitio.
# %%
# Ejercicio 13.3b -- Puntaje i18n por sitio y comparación Perú frente a internacional
if aud.empty:
    print("No hay auditoría cargada.")
else:
    val = aud[aud["estado"] == "VÁLIDA"].copy()
    print("Sitios válidos:", len(val), "de", len(aud), "| no válidos:", list(aud.loc[aud["estado"] != "VÁLIDA", "sitio"]))
    resumen = val.groupby("pais")["puntaje_i18n"].agg(["count", "mean", "median", "min", "max"]).round(2)
    print(resumen.to_string())
    for col in ["hreflang", "lenguas_originarias", "selector_idioma", "responde_accept_language"]:
        print(col, "->", val[col].astype(str).value_counts().to_dict())
    fig, ax = plt.subplots(figsize=(9, 5)); v = val.sort_values("puntaje_i18n")
    ax.barh(v["sitio"].str.slice(0, 28), v["puntaje_i18n"], color=[PAL[0] if p == "PE" else PAL[1] for p in v["pais"]])
    ax.set_xlabel("Puntaje heurístico de internacionalización (0–10)"); ax.set_title("Auditoría real de 14 sitios financieros (azul = Perú, granate = internacional)")
    plt.tight_layout(); plt.savefig("figuras/S13_fig_puntaje_i18n.png", dpi=150); plt.close()
    print("Figura guardada: figuras/S13_fig_puntaje_i18n.png")
# %% [markdown]
# ## 3. Expansión de texto y truncados en el portal (13.2)
# La auditoría del DOM cuenta **truncados** (texto cortado por ancho fijo) y **desbordes** en la versión **A** (con errores) y la **B** (internacionalizada). La *expansión* compara los caracteres visibles con es-PE.
# %%
# Ejercicio 13.3c -- Versión A frente a B: truncados, desbordes, expansión
if t132.empty:
    print("No hay datos de 13.2.")
else:
    sin_pseudo = t132[t132["pseudo"] == "no"]
    pv = sin_pseudo.groupby(["version", "locale"])[["truncados", "desbordes", "fechas_fijas", "dinero_fijo", "expansion"]].mean().round(1)
    print(pv.to_string())
    tab = sin_pseudo.pivot_table(index="locale", columns="version", values="truncados", aggfunc="mean")
    fig, ax = plt.subplots(figsize=(7, 4)); tab.plot(kind="bar", ax=ax, color=[PAL[1], PAL[2]]); ax.set_ylabel("Elementos truncados (DOM)")
    ax.set_title("Truncados por idioma: A (con errores) frente a B (internacionalizada)"); plt.xticks(rotation=0); plt.tight_layout()
    plt.savefig("figuras/S13_fig_truncados_AB.png", dpi=150); plt.close()
    ps = t132[t132["pseudo"] == "sí"]
    print("Con pseudolocalización (+40 %):"); print(ps[["version", "locale", "truncados", "desbordes", "caracteres"]].to_string(index=False))
# %% [markdown]
# ## 4. Experimento 13.3: formato ambiguo (A) frente a explícito (B)
# Diseño **intra-sujetos** con contrabalanceo del orden. Métrica principal: **proporción de aciertos**. Intervalo de Wald ajustado (Agresti–Coull) al 95 %. **Con datos de robot no se concluye nada.**
# %%
# Ejercicio 13.3d -- Aciertos, tiempos e intervalos por formato
def wald_ajustado(x, n, z=1.96):
    # Agresti-Coull: p~ = (x + z^2/2) / (n + z^2); IC = p~ +/- z*sqrt(p~(1-p~)/(n+z^2))
    pt = (x + z * z / 2) / (n + z * z); h = z * math.sqrt(pt * (1 - pt) / (n + z * z))
    return max(0, pt - h), min(1, pt + h)
if t133.empty:
    print("No hay datos del experimento 13.3.")
else:
    g = t133.groupby("formato").agg(n=("correcta", "size"), aciertos=("correcta", "sum"), tiempo_ms=("tiempo_ms", "median"), confianza=("confianza", "mean"))
    g["tasa"] = (g["aciertos"] / g["n"]).round(3)
    g[["ic_inf", "ic_sup"]] = [wald_ajustado(r.aciertos, r.n) for r in g.itertuples()]; g = g.round(3)
    print(g.to_string()); print("Participantes:", t133["participante"].nunique())
    por_p = t133.pivot_table(index="participante", columns="formato", values="correcta", aggfunc="mean")
    por_p["diferencia_B_menos_A"] = por_p["B"] - por_p["A"]
    print("Diferencia media por participante (B−A):", round(por_p["diferencia_B_menos_A"].mean(), 3))
    fig, ax = plt.subplots(figsize=(5.5, 4)); ax.bar(g.index, g["tasa"], yerr=[g["tasa"] - g["ic_inf"], g["ic_sup"] - g["tasa"]], color=[PAL[1], PAL[2]], capsize=6)
    ax.set_ylim(0, 1.05); ax.set_ylabel("Proporción de aciertos"); ax.set_title("Aciertos por formato (IC 95 %, Agresti–Coull)" + (" · DATOS BOT" if ES_BOT else ""))
    plt.tight_layout(); plt.savefig("figuras/S13_fig_aciertos_AB.png", dpi=150); plt.close()
    it = t133.groupby(["item", "formato"])["correcta"].mean().unstack().round(2); print(it.to_string())
# %% [markdown]
# ## 5. Conclusiones (complete usted con SUS datos)
# 1. **Qué midió la auditoría real y qué no:** solo la página de inicio, un día, con una heurística.
# 2. **Versión A frente a B:** ¿cuántos truncados y desbordes produjo cada una en cada idioma?
# 3. **Formatos ambiguos:** ¿mejoró el formato explícito (B) los aciertos? ¿Con qué intervalo?
# 4. **Límites:** traducciones ar/ja/qu son borradores; el experimento requiere participantes reales con consentimiento.
# 5. **Siguiente paso para Investing AI:** externalizar cadenas, `Intl`, CSS lógico, pseudolocalización en la integración continua.
