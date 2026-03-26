"""Fonctions de visualisation Altair pour le dashboard KPI."""
from __future__ import annotations

import altair as alt
import pandas as pd

_COLORS = {
    "real": "#2ecc71",
    "fake": "#e74c3c",
    "unknown": "#95a5a6",
    "auto": "#f39c12",
}

_SOURCE_PALETTE = alt.Color(
    "source:N",
    scale=alt.Scale(scheme="tableau10"),
    legend=alt.Legend(title="Source"),
)


# ---------------------------------------------------------------------------
# Qualité des données
# ---------------------------------------------------------------------------

def bar_image_valid(df: pd.DataFrame) -> alt.Chart:
    """Barres horizontales : % image_valid par source."""
    return (
        alt.Chart(df, title="% images valides par source")
        .mark_bar()
        .encode(
            y=alt.Y("source:N", sort="-x", title=None),
            x=alt.X("image_valid_pct:Q", scale=alt.Scale(domain=[0, 100]), title="% image_valid"),
            color=_SOURCE_PALETTE,
            tooltip=["source", "image_valid_pct", "total"],
        )
        .properties(height=200)
    )


def bar_text_image_ok(df: pd.DataFrame) -> alt.Chart:
    """Barres horizontales : % text_image_ok par source."""
    return (
        alt.Chart(df, title="% associations texte+image valides par source")
        .mark_bar()
        .encode(
            y=alt.Y("source:N", sort="-x", title=None),
            x=alt.X("text_image_ok_pct:Q", scale=alt.Scale(domain=[0, 100]), title="% text_image_ok"),
            color=_SOURCE_PALETTE,
            tooltip=["source", "text_image_ok_pct", "total"],
        )
        .properties(height=200)
    )


def bar_label_distribution(df_labels: pd.DataFrame) -> alt.Chart:
    """Barres empilées : distribution labels par source."""
    color_map = {k: v for k, v in _COLORS.items() if k in df_labels["label"].unique()}
    return (
        alt.Chart(df_labels, title="Distribution des labels par source")
        .mark_bar()
        .encode(
            x=alt.X("source:N", title=None),
            y=alt.Y("count:Q", title="Nombre d'articles"),
            color=alt.Color(
                "label:N",
                scale=alt.Scale(domain=list(color_map), range=list(color_map.values())),
                legend=alt.Legend(title="Label"),
            ),
            tooltip=["source", "label", "count"],
        )
        .properties(height=250)
    )


# ---------------------------------------------------------------------------
# Performance d'extraction
# ---------------------------------------------------------------------------

def bar_duration(df_run: pd.DataFrame) -> alt.Chart:
    """Barres : durée par tâche pour le dernier run."""
    return (
        alt.Chart(df_run, title="Durée par tâche (dernier run)")
        .mark_bar()
        .encode(
            y=alt.Y("task:N", sort="-x", title=None),
            x=alt.X("duration_s:Q", title="Durée (s)"),
            color=_SOURCE_PALETTE,
            tooltip=["task", "source", "duration_s", "total", "errors"],
        )
        .properties(height=220)
    )


def bar_error_rate(df_run: pd.DataFrame) -> alt.Chart:
    """Barres : taux d'erreur par source pour le dernier run."""
    df_extract = df_run[df_run["task"].str.startswith("extract_")].copy()
    return (
        alt.Chart(df_extract, title="Taux d'erreur par source (dernier run)")
        .mark_bar()
        .encode(
            y=alt.Y("source:N", sort="-x", title=None),
            x=alt.X("error_rate:Q", scale=alt.Scale(domain=[0, 100]), title="% erreurs"),
            color=alt.condition(
                alt.datum.error_rate > 5,
                alt.value("#e74c3c"),
                alt.value("#2ecc71"),
            ),
            tooltip=["source", "total", "errors", "error_rate"],
        )
        .properties(height=200)
    )


# ---------------------------------------------------------------------------
# Historique multi-runs
# ---------------------------------------------------------------------------

def line_duration_history(df_history: pd.DataFrame) -> alt.Chart:
    """Courbe : évolution de la durée totale par run."""
    df_total = (
        df_history.groupby(["run_id", "run_date"])["duration_s"]
        .sum()
        .reset_index()
    )
    return (
        alt.Chart(df_total, title="Durée totale du pipeline par run")
        .mark_line(point=True)
        .encode(
            x=alt.X("run_date:T", title="Date"),
            y=alt.Y("duration_s:Q", title="Durée totale (s)"),
            tooltip=["run_id", alt.Tooltip("run_date:T", format="%Y-%m-%d %H:%M"), "duration_s"],
        )
        .properties(height=220)
    )


def line_errors_history(df_history: pd.DataFrame) -> alt.Chart:
    """Courbe : évolution du nb d'erreurs par source par run."""
    df_ext = df_history[df_history["task"].str.startswith("extract_")].copy()
    return (
        alt.Chart(df_ext, title="Erreurs par source — historique")
        .mark_line(point=True)
        .encode(
            x=alt.X("run_date:T", title="Date"),
            y=alt.Y("errors:Q", title="Erreurs"),
            color=_SOURCE_PALETTE,
            tooltip=["source", alt.Tooltip("run_date:T", format="%Y-%m-%d %H:%M"), "errors", "total"],
        )
        .properties(height=220)
    )
