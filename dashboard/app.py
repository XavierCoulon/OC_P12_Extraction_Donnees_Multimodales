"""Dashboard KPI — Pipeline ETL Multimodal.

Lancement :
    uv run streamlit run dashboard/app.py

Prérequis :
    - DATA_POSTGRES_URL définie (ou .env chargé)
    - PostgreSQL data-postgres actif (docker compose up data-postgres)
    - Avoir lancé au moins 1 run du DAG etl_multimodal
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from dashboard.kpi import (
    load_quality_kpis,
    load_quality_kpis_parquet,
    load_run_history,
    load_latest_run,
)
from dashboard import charts

# ---------------------------------------------------------------------------
# Config page
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="KPI Dashboard — ETL Multimodal",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Dashboard KPI — Pipeline ETL Multimodal")
st.caption("Évaluation des performances du pipeline : précision, rapidité, coût.")

# ---------------------------------------------------------------------------
# Chargement des données
# ---------------------------------------------------------------------------

_PARQUET_PATH = Path(__file__).parent.parent / "data" / "processed" / "transformed.parquet"


@st.cache_data(ttl=60)
def _load_quality():
    try:
        return load_quality_kpis()
    except Exception:
        if _PARQUET_PATH.exists():
            st.warning("PostgreSQL indisponible — lecture du Parquet en fallback.")
            return load_quality_kpis_parquet(_PARQUET_PATH)
        raise


@st.cache_data(ttl=60)
def _load_history():
    try:
        return load_run_history()
    except Exception:
        return None


df_quality, df_labels = _load_quality()
df_history = _load_history()
df_latest = load_latest_run(df_history) if df_history is not None and not df_history.empty else None

# ---------------------------------------------------------------------------
# Section 1 — Vue globale
# ---------------------------------------------------------------------------

st.header("Vue globale")

total_articles = int(df_quality["total"].sum())
avg_image_valid = round((df_quality["image_valid_count"].sum() / total_articles * 100), 1)
avg_text_ok = round((df_quality["text_image_ok_count"].sum() / total_articles * 100), 1)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Articles totaux", f"{total_articles:,}")
col2.metric("% images valides", f"{avg_image_valid}%")
col3.metric("% texte+image OK", f"{avg_text_ok}%")

if df_latest is not None and not df_latest.empty:
    total_duration = round(df_latest["duration_s"].sum(), 1)
    col4.metric("Durée dernier run", f"{total_duration}s")
    parquet_mb = df_latest["parquet_mb"].iloc[0]
    if parquet_mb:
        st.caption(f"Parquet final : {df_latest['parquet_rows'].iloc[0]:,} lignes — {parquet_mb} MB")
else:
    col4.metric("Durée dernier run", "N/A")

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Qualité des données
# ---------------------------------------------------------------------------

st.header("Qualité des données")

col_a, col_b = st.columns(2)
with col_a:
    st.altair_chart(charts.bar_image_valid(df_quality), use_container_width=True)
with col_b:
    st.altair_chart(charts.bar_text_image_ok(df_quality), use_container_width=True)

st.altair_chart(charts.bar_label_distribution(df_labels), use_container_width=True)

with st.expander("Détail par source"):
    display_cols = ["source", "total", "image_valid_pct", "text_image_ok_pct", "has_image_pct", "avg_text_length", "avg_word_count"]
    st.dataframe(
        df_quality[display_cols].rename(columns={
            "image_valid_pct": "image_valid %",
            "text_image_ok_pct": "text_image_ok %",
            "has_image_pct": "has_image %",
            "avg_text_length": "longueur moy.",
            "avg_word_count": "mots moy.",
        }),
        hide_index=True,
        use_container_width=True,
    )

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Performance d'extraction
# ---------------------------------------------------------------------------

st.header("Performance d'extraction")

if df_latest is not None and not df_latest.empty:
    col_c, col_d = st.columns(2)
    with col_c:
        st.altair_chart(charts.bar_duration(df_latest), use_container_width=True)
    with col_d:
        st.altair_chart(charts.bar_error_rate(df_latest), use_container_width=True)

    with st.expander("Données brutes — dernier run"):
        st.dataframe(
            df_latest[["task", "source", "total", "success", "skipped", "errors", "duration_s"]],
            hide_index=True,
            use_container_width=True,
        )
else:
    st.info("Aucun run enregistré dans pipeline_runs. Lancez le DAG Airflow pour voir ces métriques.")

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — Historique multi-runs
# ---------------------------------------------------------------------------

st.header("Historique multi-runs")

if df_history is not None and not df_history.empty and df_history["run_id"].nunique() > 1:
    col_e, col_f = st.columns(2)
    with col_e:
        st.altair_chart(charts.line_duration_history(df_history), use_container_width=True)
    with col_f:
        st.altair_chart(charts.line_errors_history(df_history), use_container_width=True)

    nb_runs = df_history["run_id"].nunique()
    st.caption(f"{nb_runs} runs enregistrés.")
else:
    st.info("L'historique sera disponible après 2+ runs du DAG etl_multimodal.")
