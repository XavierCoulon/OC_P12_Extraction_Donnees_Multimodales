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
| [HEMT-Fake](https://zenodo.org/records/11408513) | texte + image | EN/HI/GU/MR/TE | vrai/faux |
| [MediaEval VMU](https://multimediaeval.github.io/) | tweet + image | EN | real/fake/non-verifiable |
| RSS fiables (Le Monde, Reuters, BBC, Snopes) | texte + image | FR/EN | real (implicite) |

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
    fakeddit.py       ← CSV + téléchargement images
    mmfakebench.py    ← HuggingFace datasets (token requis)
    hemt_fake.py      ← Zenodo (téléchargement auto)
    mediaeval.py      ← Archives GitHub MediaEval
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
make install              # uv sync
make rss LIMIT=100        # Extraire les flux RSS
make fakeddit LIMIT=5000  # Extraire Fakeddit (CSV requis dans data/raw/fakeddit/)
make mmfakebench          # Extraire MMFakeBench (HF_TOKEN dans .env)
make hemt_fake            # Extraire HEMT-Fake (téléchargement auto Zenodo)
make mediaeval            # Extraire MediaEval VMU
make all LIMIT=1000       # Toutes les sources
```

Sortie : `data/processed/<source>.jsonl`

### Configuration

Copier `.env.example` → `.env` et renseigner `HF_TOKEN` (requis uniquement pour MMFakeBench).

Les flux RSS sont configurables dans `config.py` → `RSS_FEEDS`.

---

## Stack

- Python 3.12
- `requests`, `feedparser`, `pandas`, `datasets`, `Pillow`, `tqdm`, `python-dotenv`
- `uv` pour la gestion des dépendances
