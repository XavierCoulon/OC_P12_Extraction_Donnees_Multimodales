# OC P12 — Extraction de données multimodales

Système d'extraction automatisée de publications (texte + image) pour entraîner un détecteur de fake news.

---

## Étape 1 — Exploration et qualification des sources

**Livrable** : [`reports/01_exploration_sources.md`](reports/01_exploration_sources.md)

5 sources multimodales identifiées et qualifiées (accès vérifié en 2026) :

| Source | Modalités | Langue | Labels |
|--------|-----------|--------|--------|
| [Fakeddit](https://fakeddit.netlify.app/) | texte + image | EN | 2/6 classes |
| [MMFakeBench](https://github.com/liuxuannan/MMFakeBench) | texte + image | EN | vrai/faux |
| [MiRAGeNews](https://huggingface.co/datasets/anson-huang/mirage-news) | texte + image | EN | real/fake (image AI-générée) |
| [MediaEval VMU](https://github.com/MKLab-ITI/image-verification-corpus) | tweet + image (référence locale) | EN | real/fake/non-verifiable |
| RSS fiables (Le Monde, The Guardian, BBC, Snopes) | texte + image | FR/EN | real (implicite) |

Format de sortie unifié : **JSON Lines** (`.jsonl`)

---

## Étape 2 — Scripts d'extraction automatisée

**Issue** : [#1](https://github.com/XavierCoulon/OC_P12_Extraction_Donnees_Multimodales/issues/1)

Scripts Python modulaires pour extraire et normaliser les données de chaque source.

### Architecture

```
src/
  extractors/
    base.py           ← BaseExtractor (ABC : extract / normalize / run)
    fakeddit.py       ← CSV manuel + téléchargement images
    mmfakebench.py    ← HuggingFace datasets (HF_TOKEN requis)
    miragenews.py     ← HuggingFace datasets (public, sans token)
    mediaeval.py      ← TSV GitHub MKLab-ITI (téléchargement auto)
    rss.py            ← feedparser multi-sources
  utils/
    image.py          ← Téléchargement + validation images
    io.py             ← Lecture/écriture JSONL
    logger.py         ← Logging fichier + stdout
config.py             ← Paramètres centralisés + RSS_FEEDS
main.py               ← CLI (argparse)
```

### Utilisation

```bash
make install                        # uv sync
make extract LIMIT=1000             # Toutes les sources
make extract-rss LIMIT=100          # Flux RSS uniquement
make extract-fakeddit LIMIT=5000    # Fakeddit (CSV requis dans data/raw/fakeddit/)
make extract-mmfakebench            # MMFakeBench (HF_TOKEN dans .env)
make extract-miragenews             # MiRAGeNews (téléchargement auto HuggingFace)
make extract-mediaeval              # MediaEval VMU (téléchargement auto)
```

Sortie : `data/processed/<source>.jsonl`

### Prérequis par source

| Source | Prérequis |
|--------|-----------|
| **Fakeddit** | Téléchargement manuel requis (voir ci-dessous) |
| **MMFakeBench** | `HF_TOKEN` dans `.env` (Data Usage Protocol HuggingFace) |
| **MiRAGeNews** | Aucun — téléchargement automatique HuggingFace |
| **MediaEval VMU** | Aucun — téléchargement automatique GitHub |
| **RSS** | Aucun |

#### Fakeddit — téléchargement manuel

1. Aller sur [Google Drive Fakeddit v2.0](https://drive.google.com/drive/folders/1jU7qgDqU1je9Y0PMKJ_f31yXRo5uWGFm)
2. Télécharger les 3 fichiers du dossier `multimodal_only_samples/` :
   - `multimodal_train.tsv` (~148 Mo)
   - `multimodal_validate.tsv` (~16 Mo)
   - `multimodal_test_public.tsv` (~16 Mo)
3. Les placer dans `data/raw/fakeddit/`
4. Lancer : `make extract-fakeddit`

#### MMFakeBench — token HuggingFace

Copier `.env.example` → `.env` et renseigner `HF_TOKEN` :
1. Créer un token sur [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Accepter le Data Usage Protocol sur [la page du dataset](https://huggingface.co/datasets/liuxuannan/MMFakeBench)
3. Ajouter `HF_TOKEN=hf_...` dans `.env`

Les flux RSS sont configurables dans `config.py` → `RSS_FEEDS`.

---

## Étape 3 — Pipeline de transformation

**Issue** : [#8](https://github.com/XavierCoulon/OC_P12_Extraction_Donnees_Multimodales/issues/8)

Pipeline Python modulaire qui transforme les données brutes (JSONL) en un dataset consolidé (Parquet) prêt pour l'entraînement de modèles.

### Transformations appliquées

| Étape | Description |
|-------|-------------|
| Nettoyage texte | Suppression HTML, normalisation espaces, caractères de contrôle |
| Normalisation date | RFC 822 / ISO 8601 / UNIX → ISO 8601 unifié |
| Validation image | `image_valid: bool` — voir tableau ci-dessous |
| Association texte-image | `text_image_ok: bool` — texte ET image présents ensemble |
| Mapping labels | `label_int: int` — real=1, fake=0, unknown=-1 |
| Enrichissement | `text_length`, `word_count`, `has_image` |
| Déduplication | Hash MD5 sur (source + texte[:200]), première occurrence conservée |

### Validation des images par source

La stratégie de validation dépend du type de stockage de chaque source :

| Source | Champ image | Vérification format | Vérification accessibilité |
|--------|------------|--------------------|-----------------------------|
| **Fakeddit** | `image_url` | ✅ `is_valid_image_url()` — schéma HTTP(S) + extension | Optionnelle — HEAD request si `IMAGE_CHECK_ACCESSIBLE=true` |
| **RSS** | `image_url` | ✅ `is_valid_image_url()` — schéma HTTP(S) + extension | Optionnelle — HEAD request si `IMAGE_CHECK_ACCESSIBLE=true` |
| **MiRAGeNews** | `image_path` | ✅ Garanti par la sauvegarde PIL | ✅ `validate_image()` — vérification Pillow du fichier local |
| **MMFakeBench** | `image_path` | N/A — référence interne HuggingFace | N/A — pas de fichier local accessible |
| **MediaEval VMU** | `image_path` | N/A — identifiant local (ZIP non téléchargé) | N/A — images non téléchargées |

**Variable d'environnement** : `IMAGE_CHECK_ACCESSIBLE=true` active les HEAD requests pour les sources URL (Fakeddit, RSS). Désactivé par défaut — trop coûteux pour Fakeddit (~1M records).

### Architecture

```
src/transform/
  steps/
    clean_text.py        ← clean_text()
    normalize_date.py    ← normalize_date()
    validate_image.py    ← validate_image_fields()
    check_association.py ← check_text_image_association()
    map_labels.py        ← map_label()
    enrich.py            ← enrich()
    deduplicate.py       ← deduplicate()
  pipeline.py            ← run_pipeline()
transform.py             ← CLI
verify.py                ← Rapport de vérification
docs/schema_donnees.md   ← Schéma conceptuel Mermaid
```

### Utilisation

```bash
make transform            # Transformer toutes les sources
make transform-rss        # Transformer une source spécifique
make verify               # Vérifier le Parquet produit
```

Sortie : `data/processed/transformed.parquet`

### Schéma conceptuel

Voir [`docs/schema_donnees.md`](docs/schema_donnees.md) pour le modèle conceptuel des données (champs, types, rôles IA).

---

## Étape 4 — Orchestration ETL avec Apache Airflow

**Issue** : [#10](https://github.com/XavierCoulon/OC_P12_Extraction_Donnees_Multimodales/issues/10)

DAG Airflow qui orchestre le pipeline complet et charge les données dans PostgreSQL.

### Architecture

```
docker-compose.yaml       ← Infrastructure (Airflow + PostgreSQL)
docker/init-db.sql        ← Init data warehouse (table + rôles)
dags/
  etl_multimodal.py       ← DAG principal (7 tâches PythonOperator)
src/load/
  postgres_loader.py      ← Parquet → PostgreSQL (upsert idempotent)
```

### DAG

```
extract_rss ────────┐
extract_fakeddit ───┤
extract_mmfakebench ┼──► transform_data ──► load_to_postgres
extract_miragenews ─┤
extract_mediaeval ──┘
```

Toutes les tâches extract sont parallèles. Le DAG est déclenché manuellement depuis l'UI.

### Démarrage

**Prérequis** : Docker Desktop installé et démarré.

```bash
# 1. Renseigner les 3 variables du .env
cp .env.example .env
# Éditer HF_TOKEN, AIRFLOW_POSTGRES_PASSWORD, DATA_POSTGRES_PASSWORD

# 2. Générer les clés crypto (une seule fois)
make airflow-keygen

# 3. Initialiser Airflow (première fois uniquement)
make airflow-init

# 4. Démarrer les services
make airflow-up
# → Interface : http://localhost:8080 (admin / admin)

# 5. Activer et déclencher le DAG "etl_multimodal" depuis l'UI

# 6. Arrêter
make airflow-down
```

### Variables d'environnement (`.env`)

Seules 3 variables sont à renseigner manuellement :

| Variable | Description |
|----------|-------------|
| `HF_TOKEN` | Token HuggingFace (requis pour MMFakeBench) |
| `AIRFLOW_POSTGRES_PASSWORD` | Mot de passe PostgreSQL interne Airflow |
| `DATA_POSTGRES_PASSWORD` | Mot de passe du data warehouse ETL |

Les clés crypto (`AIRFLOW__CORE__FERNET_KEY`, `AIRFLOW_SECRET_KEY`) sont générées et ajoutées automatiquement dans `.env` par `make airflow-keygen`.

### Sécurité

- Utilisateur PostgreSQL dédié `etl_user` (permissions `INSERT, SELECT, UPDATE` uniquement, pas superuser)
- Credentials dans `.env` uniquement (jamais dans le code)
- Connexion PostgreSQL via `sslmode=require` en production
- `AIRFLOW__CORE__FERNET_KEY` pour le chiffrement des connexions stockées dans Airflow

### Idempotence

Les 3 extracteurs qui généraient des UUID4 aléatoires (RSS, MMFakeBench, MiRAGeNews) utilisent
désormais `uuid5(NAMESPACE_URL, source + url)` — IDs déterministes. Un re-run du DAG ajoute
les nouveaux articles et ignore les existants (`ON CONFLICT (id) DO NOTHING`).

---

---

## Étape 5 — Évaluation et visualisation des performances

**Livrable** : `dashboard/app.py` (Streamlit) + [`reports/monitoring_plan.md`](reports/monitoring_plan.md)

Dashboard KPI interactif et plan de monitoring du pipeline.

### Architecture

```
dashboard/
  app.py            ← Application Streamlit (4 sections)
  kpi.py            ← Requêtes SQL (articles + pipeline_runs)
  charts.py         ← Visualisations Altair
src/metrics/
  exporter.py       ← INSERT INTO pipeline_runs (appelé par export_metrics)
reports/
  monitoring_plan.md ← Plan de monitoring (seuils, alertes, fréquences)
```

### DAG mis à jour

```
extract_rss ────────┐
extract_fakeddit ───┤
extract_mmfakebench ┼──► transform_data ──► load_to_postgres ──► export_metrics
extract_miragenews ─┤
extract_mediaeval ──┘
```

La tâche `export_metrics` collecte les XCom (compteurs + timings) de toutes les tâches et les insère dans la table PostgreSQL `pipeline_runs`.

### Tables PostgreSQL

| Table | Contenu |
|-------|---------|
| `articles` | Données transformées (19 colonnes) — KPIs qualité |
| `pipeline_runs` | Métriques de run (durée, erreurs, volume) — KPIs performance |

### Lancement du dashboard

#### Prérequis

- Docker Desktop démarré
- `.env` contenant `DATA_POSTGRES_URL` (voir ci-dessous)
- Avoir lancé au moins 1 run du DAG `etl_multimodal` (pour les métriques de performance)

#### Étapes dans l'ordre

```bash
# 1. Ajouter DATA_POSTGRES_URL dans .env (une seule fois)
#    Remplacer DATA_POSTGRES_PASSWORD par la valeur de votre .env
echo "DATA_POSTGRES_URL=postgresql+psycopg2://etl_user:DATA_POSTGRES_PASSWORD@localhost/multimodal" >> .env

# 2. Démarrer PostgreSQL (suffit pour le dashboard, pas besoin d'Airflow complet)
docker compose up data-postgres -d

# 3a. Si le container PostgreSQL est NOUVEAU (volume vide) → le schéma est créé automatiquement via init-db.sql
# 3b. Si le container PostgreSQL EXISTAIT DÉJÀ avant l'étape 5 → créer pipeline_runs manuellement :
make dashboard-setup

# 4. Lancer le dashboard
make dashboard
# → http://localhost:8501
```

#### Pourquoi ces étapes ?

| Étape | Raison |
|-------|--------|
| `DATA_POSTGRES_URL` dans `.env` | Streamlit charge `.env` au démarrage — sans ça, il bascule en mode fallback Parquet |
| `docker compose up data-postgres` | Le dashboard lit `articles` et `pipeline_runs` via localhost:5432 |
| `make dashboard-setup` | PostgreSQL ne rejoue jamais `init-db.sql` si le volume de données existe déjà |
| `make dashboard` | Lance `streamlit run dashboard/app.py` avec l'environnement uv |

**Fallback automatique** : si PostgreSQL est indisponible, le dashboard lit `data/processed/transformed.parquet` (KPIs qualité uniquement, sans historique de runs).

### Exploration visuelle des articles (`notebooks/01_sample_articles.ipynb`)

Notebook Jupyter pour visualiser un exemple d'article (texte + image) par source.

```bash
uv run jupyter notebook notebooks/01_sample_articles.ipynb
```

| Source | Image disponible |
|--------|-----------------|
| **Fakeddit** | ✅ URL publique (Imgur) |
| **MirageNews** | ✅ Fichier local (`data/images/miragenews/`) |
| **RSS** | ✅ URL publique |
| **MMFakeBench** | ❌ Images dans un ZIP HuggingFace non extrait (~646 MB) |
| **MediaEval** | ❌ Tweets de 2016 — images non redistribuées par le dataset |

### KPIs disponibles

| Dimension | KPI | Source SQL |
|-----------|-----|-----------|
| **Précision** | % images valides par source | `articles` |
| **Précision** | % associations texte+image par source | `articles` |
| **Précision** | Distribution labels real/fake/unknown | `articles` |
| **Rapidité** | Durée par tâche Airflow (s) | `pipeline_runs` |
| **Rapidité** | Durée totale pipeline (s) | `pipeline_runs` |
| **Coût** | Volume articles par source | `pipeline_runs` |
| **Coût** | Taille Parquet final (MB) | `pipeline_runs` |

---

## Stack

- Python 3.12
- `requests`, `feedparser`, `pandas`, `datasets`, `Pillow`, `pyarrow`, `tqdm`, `python-dotenv`
- `sqlalchemy`, `psycopg2-binary`, `streamlit`, `altair`
- `uv` pour la gestion des dépendances
- Docker + Apache Airflow 2.9, PostgreSQL 16
