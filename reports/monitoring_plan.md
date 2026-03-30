# Plan de monitoring — Pipeline ETL Multimodal

## 1. Vue d'ensemble

Ce document décrit la stratégie de surveillance du pipeline ETL multimodal en production. Il couvre les indicateurs à surveiller, les seuils d'alerte, la gestion des erreurs et la fréquence des vérifications.

Le pipeline extrait des données depuis 5 sources (RSS, Fakeddit, MMFakeBench, MiRAGeNews, MediaEval), les transforme et les charge dans PostgreSQL. Il est orchestré par Apache Airflow et ses métriques sont stockées dans la table `pipeline_runs`.

---

## 2. Indicateurs clés (KPIs) — ✅ Implémenté

Les KPIs sont calculés à chaque run et stockés dans `pipeline_runs` (table PostgreSQL). Ils sont visualisés dans le dashboard Streamlit (`dashboard/app.py`).

### 2.1 Précision des données

| Indicateur | Calcul | Source |
|------------|--------|--------|
| % images valides | `image_valid_count / total × 100` | `articles` |
| % associations texte+image | `text_image_ok_count / total × 100` | `articles` |
| % erreurs extraction | `errors / total × 100` | `pipeline_runs` |
| % doublons supprimés | `(total_read - total_after_dedup) / total_read × 100` | `pipeline_runs` |

### 2.2 Rapidité

| Indicateur | Calcul | Source |
|------------|--------|--------|
| Durée totale pipeline | `SUM(duration_s)` toutes tâches | `pipeline_runs` |
| Durée par tâche | `duration_s` par `task` | `pipeline_runs` |
| Durée extraction par source | `duration_s` pour `extract_{source}` | `pipeline_runs` |

### 2.3 Coût / Volume

| Indicateur | Valeur | Source |
|------------|--------|--------|
| Volume articles traités | `total` par source | `pipeline_runs` |
| Taille Parquet final | `parquet_mb` | `pipeline_runs` |
| Nb images téléchargées | Compteur `miragenews.success` | `pipeline_runs` |

---

## 3. Seuils d'alerte — ⚠️ Définis, non automatisés

Les seuils ci-dessous sont documentés et visibles dans le dashboard, mais ne déclenchent pas encore d'alerte automatique. En production, ils seraient connectés à un outil comme Grafana Alerts ou Great Expectations.

| Indicateur | Seuil WARNING | Seuil CRITICAL | Action |
|------------|--------------|----------------|--------|
| % erreurs extraction | > 5% | > 15% | Vérifier logs + source |
| % images valides | < 70% | < 50% | Vérifier URLs / images locales |
| % texte+image OK | < 60% | < 40% | Vérifier pipeline transform |
| Durée totale pipeline | > 15 min | > 30 min | Vérifier limites sources + réseau |
| Durée extraction RSS | > 2 min | > 5 min | Vérifier flux RSS (timeout) |
| Articles extraits (RSS) | < 50 | < 10 | Vérifier disponibilité des flux |
| Articles extraits (fakeddit) | < 500 | < 100 | Vérifier fichiers CSV bruts |
| Taille Parquet | > 100 MB | > 500 MB | Vérifier limites d'extraction |

---

## 4. Fréquence de vérification — ✅ Implémenté (partiel)

| Vérification | Fréquence | Méthode | Statut |
|-------------|-----------|---------|--------|
| Run complet pipeline | Manuel (démo) / Quotidien en prod | Airflow schedule | ⚠️ `schedule=None` — à activer |
| Dashboard KPI | À la demande | Streamlit (`make dashboard`) | ✅ |
| Logs d'extraction | Après chaque run | `logs/extraction.log` | ✅ |
| Santé PostgreSQL | Toutes les 10s | Docker healthcheck (`pg_isready`) | ✅ |
| Disponibilité flux RSS | À chaque run | RSSExtractor (timeout 30s) | ✅ |

Pour planifier le DAG quotidiennement, modifier `schedule=None` en :
```python
schedule="0 2 * * *"  # 02:00 UTC chaque jour
```

---

## 5. Alertes Airflow — ✅ Implémenté

### 5.1 Email via Mailjet

Le système d'alerte email est **entièrement configuré et testé**. Airflow envoie automatiquement un email sur échec de tâche, après épuisement des retries, via le fournisseur SMTP Mailjet.

- Transport SMTP configuré dans `docker-compose.yaml`
- Destinataire configuré via variable d'environnement dans `.env`
- DAG : `email_on_failure=True`, `retries=1`, `retry_delay=30s`

> En production, `retry_delay` serait porté à 5 minutes.

### 5.2 SLA (Service Level Agreement) — ⚠️ Must have en production

```python
with DAG(
    ...,
    dagrun_timeout=timedelta(minutes=30),  # alerte si dépassé
) as dag:
    ...
```

---

## 6. Gestion des erreurs — ✅ Implémenté

### 6.1 Stratégie de retry

- Chaque tâche Airflow : `retries=1` avec `retry_delay=30s` (démo) / `5 min` (prod)
- Extraction images MiRAGeNews : `IMAGE_DOWNLOAD_RETRIES=3` (backoff exponentiel)
- Chargement PostgreSQL : idempotent (`ON CONFLICT DO NOTHING`) — safe à rejouer

### 6.2 Procédure en cas d'anomalie

| Symptôme | Diagnostic | Action |
|---------|-----------|--------|
| Tâche `extract_rss` échoue | Flux RSS indisponible | Vérifier URL dans `config.py` > `RSS_FEEDS` |
| Tâche `extract_fakeddit` échoue | Fichiers CSV absents | Vérifier `data/raw/fakeddit/` |
| Tâche `load_to_postgres` échoue | PostgreSQL down | `docker compose up data-postgres` |
| % erreurs > 15% | Source dégradée | Inspecter `logs/extraction.log` |
| Parquet vide | Transformation échouée | Vérifier `transform_data` logs |
| `export_metrics` échoue | DB non joignable | Non bloquant — relancer manuellement |

### 6.3 Re-run d'urgence

Via l'UI Airflow ou CLI :
```bash
airflow dags trigger etl_multimodal
# ou avec une date spécifique
airflow dags backfill etl_multimodal --start-date 2026-03-25
```

---

## 7. Rotation des logs — ⚠️ Must have en production

Actuellement les logs sont écrits dans `logs/extraction.log` sans rotation. En production, ajouter un `RotatingFileHandler` :

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    log_file, maxBytes=100 * 1024 * 1024, backupCount=5
)
```

- **Taille max recommandée** : 100 MB par fichier
- **Rétention** : 30 jours
- **Archivage** : compresser les logs > 7 jours (`gzip logs/extraction.log.1`)

---

## 8. Accord sur les niveaux de service (SLA) — ⚠️ Référentiel cible

Objectifs définis pour un contexte de production. Non enforced automatiquement dans l'implémentation actuelle.

| Métrique | Objectif |
|---------|---------|
| Disponibilité pipeline | 95% (max 18 jours d'indisponibilité/an) |
| Fraîcheur données RSS | < 24h |
| Durée run complet | < 15 min (WARNING), < 30 min (CRITICAL) |
| % données valides | > 70% (WARNING en dessous) |
| Réponse en cas d'alerte | < 1h (heures ouvrées) |
