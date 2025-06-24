import time, json, pandas as pd
from tqdm import tqdm
from openai import OpenAI
from config import OPENAI_API_KEY, MODEL
# ⬇️  importa la nueva función  (ajusta si tu archivo se llama distinto)
from prompts import construir_prompt_mejorado as construir_prompt

# ─────────────────────── Configuración ────────────────────────
client       = OpenAI(api_key=OPENAI_API_KEY)
EXCEL_IN     = "data/encuestas_nps.xlsx"
EXCEL_OUT    = "outputs/resultado_nps.xlsx"
MAX_RETRIES  = 4
BACKOFF_SEC  = 5

# columnas obligatorias (incluye Plazo resolución…)
COLUMNAS_REQ = [
    'NPS',
    '¿Tu requerimiento fue resuelto en base a lo acordado?',
    'Satisfacción con resolución',
    'Plazo resolución de requerimiento',              # ← nueva
    'Nivel de esfuerzo cliente',
    'Número de interacciones para resolver requerimiento',
    'Tipo',
    'Subfamilia',
    'Causa',
    'Walmart LTR - Comentario'
]

# ───────────────────── Leer y limpiar Excel ───────────────────
try:
    df = pd.read_excel(EXCEL_IN).copy()
except FileNotFoundError:
    raise SystemExit(f"❌ No se encontró: {EXCEL_IN}")

faltan = [c for c in COLUMNAS_REQ if c not in df.columns]
if faltan:
    raise SystemExit(f"❌ Faltan columnas: {faltan}")

string_cols = df.select_dtypes(include="object").columns
num_cols    = df.select_dtypes(exclude="object").columns
df[string_cols] = df[string_cols].fillna("")
df[num_cols]    = df[num_cols].fillna(0)

df_proc = df[df['Walmart LTR - Comentario'].str.strip() != ""].reset_index(drop=True)

print(f"🔎 Total encuestas: {len(df)}")
print(f"✅ Con comentario : {len(df_proc)}")
print(f"⏭️ Sin comentario : {len(df) - len(df_proc)}")

# ───────────────────── Procesamiento OpenAI ───────────────────
resultados = []

for i, fila in tqdm(df_proc.iterrows(), total=len(df_proc), desc="Analizando"):
    prompt = construir_prompt(fila)

    for intento in range(1, MAX_RETRIES + 1):
        try:
            rsp = client.chat.completions.create(
                model=MODEL,
                response_format={"type": "json_object"},
                temperature=0.0,
                messages=[
                    {"role": "system",
                     "content": "Eres un analista de experiencia que solo responde con JSON EXACTO."},
                    {"role": "user", "content": prompt}
                ]
            )
            resultado_json = json.loads(rsp.choices[0].message.content)
            break
        except Exception as e:
            if intento == MAX_RETRIES:
                print(f"⚠️  Fila {i}: {e}")
                resultado_json = {
                    "tipo_experiencia": "Error",
                    "causa_principal": str(e),
                    "categoria": "",
                    "detalle_analisis": "",
                    "emocion_detectada": "",
                    "es_recuperable": "",
                    "recomendacion": ""
                }
            else:
                time.sleep(BACKOFF_SEC * intento)
                continue

    resultados.append(resultado_json)

# ───────────────────── Guardar salida ─────────────────────────
pd.concat([df_proc, pd.DataFrame(resultados)], axis=1)\
  .to_excel(EXCEL_OUT, index=False)

print(f"✅ Análisis completado. Revisa «{EXCEL_OUT}».")
