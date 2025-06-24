# app_dashboard.py – Dashboard NPS Avanzado + PDF
# ───────────────────────────────────────────────
import io, datetime, copy
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.graph_objects import Figure
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

st.set_page_config("Dashboard NPS Avanzado", layout="wide")

# ---------- utilidades PDF ----------
def fig_to_bytes(fig: Figure, w=800, h=500) -> bytes:
    try:
        f = copy.deepcopy(fig)
        f.update_layout(template="plotly_white",
                        paper_bgcolor="white", plot_bgcolor="white")
        return f.to_image(format="png", width=w, height=h, engine="kaleido")
    except Exception:  # kaleido no disponible
        return b""

def build_pdf(kpis, figs):
    buff = io.BytesIO()
    pdf  = canvas.Canvas(buff, pagesize=A4)
    W, H = A4
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(W/2, H-70, "Reporte NPS – Walmart Chile")
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(W/2, H-100, datetime.date.today().isoformat())
    pdf.showPage()
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, H-80, "Indicadores clave")
    pdf.setFont("Helvetica", 12)
    y = H-110
    for k, v in kpis.items():
        pdf.drawString(50, y, f"{k}: {v}")
        y -= 18
    pdf.showPage()
    for title, fig in figs:
        img = fig_to_bytes(fig)
        if img:
            pdf.drawImage(ImageReader(io.BytesIO(img)),
                          40, 180, width=W-80, preserveAspectRatio=True)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(40, 160, title)
        pdf.showPage()
    pdf.save(); buff.seek(0); return buff.read()

# ---------- Cargar datos ----------
df = pd.read_excel("outputs/resultado_nps.xlsx")
df["fecha_hora_de_apertura"] = pd.to_datetime(df["fecha_hora_de_apertura"],
                                              errors="coerce")
for col in ["Tipo", "causa_principal", "categoria",
            "id_ejecutivo_resolutor_de_caso", "es_recuperable"]:
    df[col] = df[col].astype(str)

def seg(n):  # clasifica NPS
    if n >= 9: return "Promotor"
    if n >= 7: return "Neutro"
    return "Detractor"
df["segmento"] = df["NPS"].apply(seg)

# ---------- Sidebar filtros ----------
with st.sidebar:
    st.title("Filtros")
    seg_sel = st.multiselect("Segmento NPS",
                             ["Promotor", "Neutro", "Detractor"],
                             default=["Promotor", "Neutro", "Detractor"])
    df = df[df["segmento"].isin(seg_sel)]
    fecha_min = df["fecha_hora_de_apertura"].min().date()
    fecha_max = df["fecha_hora_de_apertura"].max().date()
    rango = st.date_input("Rango Apertura", (fecha_min, fecha_max))
    if len(rango) == 2:
        df = df[
            (df["fecha_hora_de_apertura"].dt.date >= rango[0]) &
            (df["fecha_hora_de_apertura"].dt.date <= rango[1])
        ]
# ---------- KPI generales ----------
total_casos   = len(df)
pct_prom      = round((df["segmento"] == "Promotor").mean()  * 100, 1)
pct_neut      = round((df["segmento"] == "Neutro").mean()    * 100, 1)
pct_detr      = round((df["segmento"] == "Detractor").mean() * 100, 1)
nps_val       = round(pct_prom - pct_detr, 1)          # fórmula NPS real

# ---------- Tarjetas visuales ----------
st.header("Dashboard NPS Avanzado – Walmart Chile")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total encuestas", f"{total_casos:,}")
col2.metric("% Promotores",   f"{pct_prom} %",     delta=None)
col3.metric("% Neutros",      f"{pct_neut} %")
col4.metric("% Detractores",  f"{pct_detr} %")
col5.metric("NPS",            f"{nps_val} %")

# ---------- Evolución temporal (NPS clásico) ----------
# 1) Agregamos una columna con la semana (lunes) para agrupar
df["semana"] = df["fecha_hora_de_apertura"].dt.to_period("W").apply(lambda p: p.start_time)

# 2) Contamos casos por semana y segmento
semanal = (df.groupby(["semana", "segmento"])
             .size()
             .unstack(fill_value=0))           # columnas: Detractor, Neutro, Promotor

# 3) Nos aseguramos de que existan ambas columnas
for col in ["Promotor", "Detractor"]:
    if col not in semanal.columns:
        semanal[col] = 0

# 4) Calculamos el NPS semanal
semanal["Total"] = semanal.sum(axis=1)
semanal["NPS"] = ((semanal["Promotor"] - semanal["Detractor"])
                  / semanal["Total"] * 100).round(1)
semanal = semanal.reset_index()

# 5) Gráfico
fig_evo = px.line(
    semanal, x="semana", y="NPS",
    title="Evolución semanal de NPS (Promotores − Detractores)",
    template="plotly_white"
)
st.plotly_chart(fig_evo, use_container_width=True)


import pandas as pd   # ya está importado arriba, pero lo usamos en la lambda

# ---------- Tabla Agente × Mes con NPS (%) ----------

# 1) Filtro LOCAL por agente(s)
agentes = sorted(df["id_ejecutivo_resolutor_de_caso"].unique())
agentes_sel = st.multiselect(
    "Filtrar por agente",
    agentes,
    default=agentes           # todos seleccionados por defecto
)

df_nps = df[df["id_ejecutivo_resolutor_de_caso"].isin(agentes_sel)].copy()

# 2) Mes y conteos
df_nps["mes"] = df_nps["fecha_hora_de_apertura"].dt.to_period("M").astype(str)

conteos = (df_nps.groupby(
               ["id_ejecutivo_resolutor_de_caso", "mes", "segmento"])
             .size()
             .unstack(fill_value=0))

for col in ["Promotor", "Detractor"]:
    conteos[col] = conteos.get(col, 0)

conteos["Total"] = conteos.sum(axis=1)

conteos["NPS"] = ((conteos["Promotor"] - conteos["Detractor"])
                  / conteos["Total"] * 100).round()      # entero; NaN si Total=0

tabla_nps = (conteos["NPS"]
             .unstack(level="mes")
             .sort_index())

st.subheader("NPS (%) por agente y mes")
st.dataframe(
    tabla_nps.style
        .format(lambda v: "" if pd.isna(v) else f"{int(v)} %")
        .background_gradient(cmap="RdYlGn", axis=None),
    use_container_width=True
)

# =====================================================================
#            BLOQUE → “Análisis de resultados”
# =====================================================================
st.markdown("## Análisis de resultados")

# 1) Filtro por segmento
segmento_local = st.radio(
    "Selecciona segmento:",
    ["Promotor", "Neutro", "Detractor"],
    index=0,
    horizontal=True
)
df_local = df[df["segmento"] == segmento_local]

# 2) Top-5 categorías (para el segmento elegido)
top_cats = (df_local["categoria"]
              .value_counts()
              .head(5)
              .reset_index(name="conteo")
              .rename(columns={"index": "categoria"}))

fig_top = px.bar(
    top_cats,
    x="conteo",
    y="categoria",
    orientation="h",
    title=f"Top 5 categorías – {segmento_local}",
    template="plotly_white"
)

# 3) Selector con las mismas categorías del Top-5
categoria_sel = st.selectbox(
    "Filtra las causas por categoría:",
    options=top_cats["categoria"].tolist()
)

# 4) Causas de la categoría seleccionada
df_cat = df_local[df_local["categoria"] == categoria_sel]
causas = (df_cat["causa_principal"]
            .value_counts()
            .reset_index(name="casos")
            .rename(columns={"index": "causa_principal"}))

fig_causas = px.bar(
    causas,
    x="casos",
    y="causa_principal",
    orientation="h",
    title=f"Causas en la categoría «{categoria_sel}»",
    template="plotly_white"
)

# 5) Presentación lado a lado
c1, c2 = st.columns(2)
c1.plotly_chart(fig_top,     use_container_width=True)
c2.plotly_chart(fig_causas,  use_container_width=True)

# ---------- Recuperables ----------
r1, r2 = st.columns([1, 2])       # 1:2 para darle más ancho a la tabla

# 1) Pie Recuperables vs No
rec = (df["es_recuperable"]
         .replace({"True": "Recuperable",
                   "False": "No Recuperable",
                   "No": "No Recuperable"})
         .value_counts(normalize=True)
         .reset_index())
rec.columns = ["estado", "proporcion"]

fig_rec = px.pie(rec, names="estado", values="proporcion",
                 title="Recuperables vs No", template="plotly_white")
r1.plotly_chart(fig_rec, use_container_width=True)

# 2) Tabla con ID y comentario de los No Recuperables
nr = df[df["es_recuperable"].isin(["False", "No", "No Recuperable"])]

r2.subheader("Comentarios – No Recuperables")

if nr.empty:
    r2.info("No hay casos no recuperables con comentarios.")
else:
    tabla_nr = (nr[["numero_del_caso", "detalle_analisis"]]
                .rename(columns={
                    "numero_del_caso": "ID Caso",
                    "detalle_analisis": "Comentario"
                }))

    # Convertimos la tabla a HTML y la incrustamos con estilos propios
    table_html = tabla_nr.to_html(index=False, escape=False)

    r2.markdown(
        f"""
<style>
/* fondo negro, texto blanco */
.nr-table {{
    background:#000;
    color:#fff;
    border-collapse:collapse;
    width:100%;
}}
.nr-table th,
.nr-table td {{
    border:1px solid #444;
    padding:6px 8px;
    text-align:left;
}}
.nr-table th {{background:#222;}}
</style>

<div style="max-height:420px; overflow-y:auto; padding-right:8px;">
{table_html.replace('<table', '<table class="nr-table"')}
</div>
""",
        unsafe_allow_html=True
    )


# ---------- Tabla detalle ----------
st.subheader("Detalle de casos")
st.dataframe(
    df[[
        "numero_del_caso", "fecha_hora_de_apertura", "segmento", "Tipo",
        "categoria", "causa_principal", "es_recuperable",
        "id_ejecutivo_resolutor_de_caso", "recomendacion"
    ]],
    use_container_width=True
)

# ---------- PDF ----------
if st.button("📄 Descargar PDF"):
    kpi_dict = {"Total": total, "NPS": nps_val}
    figs = [
        ("Evolución NPS", fig_evo),
        ("NPS Agente x Mes (tabla)", px.imshow(tabla_nps)),  # captura rápida
        (f"Top 5 categorías – {segmento_local}", fig_top),
        ("Recuperables vs No", fig_rec)
    ]
    pdf_bytes = build_pdf(kpi_dict, figs)
    st.download_button("Descargar PDF", pdf_bytes,
                       "reporte_nps_avanzado.pdf", mime="application/pdf")