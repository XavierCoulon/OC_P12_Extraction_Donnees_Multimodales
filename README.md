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

## Stack

- Python 3.12
