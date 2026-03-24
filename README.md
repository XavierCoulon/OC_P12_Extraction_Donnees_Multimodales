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
| Validation image | `image_valid: bool` — format et schéma URL vérifiés |
| Association texte-image | `text_image_ok: bool` — texte ET image présents ensemble |
| Mapping labels | `label_int: int` — real=1, fake=0, unknown=-1 |
| Enrichissement | `text_length`, `word_count`, `has_image` |
| Déduplication | Hash MD5 sur (source + texte[:200]), première occurrence conservée |

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
# 1. Copier .env.example → .env et renseigner les variables (voir ci-dessous)
cp .env.example .env

# 2. Initialiser Airflow (première fois uniquement)
make airflow-init

# 3. Démarrer les services
make airflow-up
# → Interface : http://localhost:8080 (admin / admin)

# 4. Activer et déclencher le DAG "etl_multimodal" depuis l'UI

# 5. Arrêter
make airflow-down
```

### Variables d'environnement (`.env`)

| Variable | Description |
|----------|-------------|
| `AIRFLOW__CORE__FERNET_KEY` | Clé Fernet (chiffrement connexions Airflow) — `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `AIRFLOW_SECRET_KEY` | Clé secrète webserver — `python -c "import secrets; print(secrets.token_hex(32))"` |
| `AIRFLOW_POSTGRES_PASSWORD` | Mot de passe PostgreSQL interne Airflow |
| `DATA_POSTGRES_URL` | URL connexion data warehouse (`postgresql+psycopg2://etl_user:...@data-postgres/multimodal`) |

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

## Stack

- Python 3.12
- `requests`, `feedparser`, `pandas`, `datasets`, `Pillow`, `pyarrow`, `tqdm`, `python-dotenv`
- `sqlalchemy`, `psycopg2-binary`
- `uv` pour la gestion des dépendances
- Docker + Apache Airflow 2.9, PostgreSQL 16
