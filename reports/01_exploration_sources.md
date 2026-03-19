# Rapport d'exploration des sources de données multimodales

**Projet** : Détection de fake news multimodales
**Date** : 2026-03-19
**Auteur** : Xavier Coulon

---

## 1. Tableau comparatif des sources retenues

| # | Source | Modalités | Volume | Langue | Labels | Qualité labels | Faisabilité |
|---|--------|-----------|--------|--------|--------|----------------|-------------|
| 1 | **Fakeddit** | texte + image + metadata | ~1M | EN | 2 et 6 classes | Haute | ✅ |
| 2 | **MMFakeBench** | texte + image | ~11k | EN | vrai/faux (12 sous-catégories) | Très haute | ✅ |
| 3 | **MiRAGeNews** | texte + image | ~15k | EN | real / fake (image AI-générée) | Haute | ✅ |
| 4 | **MediaEval VMU** | tweet + image (référence locale) | ~2 177 | EN | real/fake/non-verifiable | Haute | ✅ |
| 5 | **RSS flux fiables** | texte + image | continu | FR/EN | real (implicite) | Moyenne | ✅ |

### Sources écartées

| Source | Raison d'exclusion |
|--------|-------------------|
| **HEMT-Fake** | Dataset text-only constaté à l'usage : les ZIPs Zenodo ne contiennent que des fichiers `.txt`, sans image — incompatible avec un pipeline multimodal |
| **FakeNewsNet** | Requiert credentials Twitter/X API — accès très restrictif depuis 2023 |
| **Reddit / PRAW** | API Reddit 2023+ trop restrictive ; historique largement inaccessible |
| **NewsData.io API** | Free tier insuffisant : délai 12h, pas de texte intégral, 200 crédits/jour |
| **AFP Factuel RSS** | AFP a désactivé ses flux RSS publics |

---

## 2. Format de sortie unifié

Toutes les sources sont normalisées vers le schéma **JSON Lines** (`.jsonl`) suivant :

```json
{
  "id": "uuid-v4",
  "source": "fakeddit|mmfakebench|miragenews|mediaeval|rss",
  "title": "Titre de l'article ou du post",
  "text": "Corps textuel ou résumé",
  "image_url": "https://example.com/image.jpg",
  "image_path": "data/images/<id>.jpg",
  "label": "real|fake|unknown",
  "label_confidence": "high|medium|low",
  "language": "en|fr",
  "date": "2024-01-15T12:00:00Z",
  "url": "https://example.com/article",
  "domain": "example.com",
  "extraction_method": "dataset|rss"
}
```

**Champs obligatoires** : `id`, `source`, `text`, `label`, `extraction_method`
**Stockage** : JSON Lines (`.jsonl`), un enregistrement par ligne, compatible `pandas` et HuggingFace `datasets`

---

## 3. Description détaillée des sources

### 3.1 Fakeddit

| Propriété | Valeur |
|-----------|--------|
| **Type** | Dataset statique |
| **Format** | CSV (téléchargement manuel) + URLs images |
| **Langue** | Anglais |
| **Labels** | 2 classes (real/fake) + 6 classes détaillées |
| **Volume** | ~1 million d'échantillons |
| **Licence** | Usage académique non commercial |
| **Accès** | [fakeddit.netlify.app](https://fakeddit.netlify.app/) · [GitHub](https://github.com/entitize/Fakeddit) |

**Description**
Dataset construit à partir de posts Reddit couvrant 22 subreddits. Chaque entrée comprend le titre du post, l'image associée et des métadonnées sociales (votes, subreddit, domaine). Les labels 6 classes distinguent : *true*, *satire*, *misleading*, *manipulated*, *false content*, *non-verifiable*.

**Qualité des labels**
Haute — labels dérivés des règles communautaires de chaque subreddit (r/TheOnion = satire, r/worldnews = réel). Biais potentiel : surreprésentation de la politique américaine et du divertissement.

**Méthode d'extraction**
Téléchargement manuel des CSV depuis le site officiel, placement dans `data/raw/fakeddit/`. L'extracteur lit les CSV et utilise les URLs d'images.

**Mapping vers le format unifié**

| Champ Fakeddit | Champ unifié |
|----------------|--------------|
| `id` | `id` |
| `title` | `title` + `text` (seul texte disponible) |
| `image_url` | `image_url` |
| `2_way_label` | `label` (0 = fake, 1 = real) |
| `created_utc` | `date` |
| `domain` | `domain` |
| `permalink` | `url` (préfixe `reddit.com`) |

**Points de vigilance**
- Le texte est limité au titre du post (pas de corps d'article)
- URLs d'images potentiellement mortes — utiliser les fichiers pré-téléchargés du site officiel
- Le label *non-verifiable* ne correspond pas à de la désinformation → exclu ou mappé `unknown`

---

### 3.2 MMFakeBench

| Propriété | Valeur |
|-----------|--------|
| **Type** | Dataset statique — benchmark |
| **Format** | Parquet via HuggingFace `datasets` (HF_TOKEN requis) |
| **Langue** | Anglais |
| **Labels** | Binaire (real/fake) + 3 catégories × 4 sous-catégories |
| **Licence** | CC-BY 4.0 (Data Usage Protocol à accepter sur HuggingFace) |
| **Accès** | [HuggingFace](https://huggingface.co/datasets/liuxuannan/MMFakeBench) · [GitHub](https://github.com/liuxuannan/MMFakeBench) — ICLR 2025 |

**Description**
Benchmark de référence (ICLR 2025) couvrant 3 types de fake news multimodales : *text-only manipulation*, *image-only manipulation*, *cross-modal inconsistency*. Conçu spécifiquement pour l'évaluation de modèles multimodaux.

**Qualité des labels**
Très haute — annotations humaines expertes avec double validation.

**Méthode d'extraction**
API HuggingFace `datasets` avec token d'authentification. Splits val (1k) + test (10k).

**Mapping vers le format unifié**

| Champ MMFakeBench | Champ unifié |
|-------------------|--------------|
| `text` | `text` |
| `image_path` | `image_path` (référence interne HF) |
| `gt_answers` ("True"/"Fake") | `label` |
| `text_source` | `domain` |

**Points de vigilance**
- Signature du Data Usage Protocol obligatoire (variable d'environnement `HF_TOKEN`)
- Champ `gt_answers` : valeurs réelles = `"True"` et `"Fake"` (pas `"False"`)
- Dataset orienté évaluation : distributions équilibrées artificiellement

---

### 3.3 MiRAGeNews

| Propriété | Valeur |
|-----------|--------|
| **Type** | Dataset statique |
| **Format** | Parquet HuggingFace (images embarquées, aucun token requis) |
| **Langue** | Anglais |
| **Labels** | Binaire : real (0) / fake — image générée par IA (1) |
| **Volume** | ~15 000 paires (10k train + 2.5k val + 5×500 test) |
| **Licence** | Non spécifiée (usage recherche) |
| **Accès** | [HuggingFace](https://huggingface.co/datasets/anson-huang/mirage-news) · [GitHub](https://github.com/nosna/miragenews) |

**Description**
Dataset centré sur la détection d'images générées par IA (Midjourney, DALL-E 3, SDXL) associées à de vraies dépêches (NYT, BBC, CNN). Chaque entrée contient une image PIL directement embarquée dans les fichiers Parquet et la dépêche textuelle correspondante. Le "fake" représente une image AI-générée associée à un texte réel — cas typique de manipulation visuelle moderne.

**Qualité des labels**
Haute — dataset construit de façon contrôlée : les images réelles viennent de sources journalistiques vérifiées, les images fausses sont générées par IA avec différents modèles (5 combinaisons source×modèle dans les splits de test).

**Méthode d'extraction**
API HuggingFace `datasets` sans authentification. Images PIL sauvegardées localement dans `data/images/miragenews/`.

**Mapping vers le format unifié**

| Champ MiRAGeNews | Champ unifié |
|------------------|--------------|
| `text` | `text` |
| `image` (PIL.Image) | `image_path` (sauvegardé en JPEG local) |
| `label` (0/1) | `label` (0 = real, 1 = fake) |
| `_split` | `domain` (ex: `train`, `test2_bbc_dalle`) |

**Points de vigilance**
- Le "fake" = image AI-générée + texte réel — couverture d'un type spécifique de désinformation visuelle (deepfakes, illustrations trompeuses)
- Pas de fake news "textuellement fausses" — complémentaire à MMFakeBench et Fakeddit
- Espace disque : ~2 Go pour le dataset complet (images embarquées dans Parquet)

---

### 3.4 MediaEval Verifying Multimedia Use (VMU) 2016

| Propriété | Valeur |
|-----------|--------|
| **Type** | Dataset statique — benchmark de challenge |
| **Format** | TSV (tab-separated), images dans ZIP séparé |
| **Langue** | Anglais |
| **Labels** | `real` / `fake` / `humor` (→ fake) / `non-verifiable` (→ unknown) |
| **Volume** | 2 177 tweets (testset annoté) |
| **Éditions** | 2015–2022 (archivées) |
| **Licence** | Usage académique |
| **Accès** | [MKLab-ITI/image-verification-corpus](https://github.com/MKLab-ITI/image-verification-corpus) |

**Description**
Challenge annuel (2015-2022) centré sur la vérification de contenu multimédia partagé sur les réseaux sociaux. Les données consistent en tweets avec images potentiellement *out-of-context* : l'image est réelle, mais associée à un faux contexte textuel. Source réelle archivée : `MKLab-ITI/image-verification-corpus` (le repo `multimediaeval/2016-Fake-News-Detection` est une référence caduque).

**Qualité des labels**
Haute — annotations par des équipes de journalistes et fact-checkers. Le label `non-verifiable` signale les cas ambigus.

**Méthode d'extraction**
Téléchargement direct du fichier TSV `posts_groundtruth.txt` depuis GitHub. Mise en cache locale dans `data/raw/mediaeval/`.

**Mapping vers le format unifié**

| Champ TSV MediaEval | Champ unifié |
|---------------------|--------------|
| `post_id` | `id` + `url` (twitter.com) |
| `post_text` | `text` |
| `image_id` | `image_path` (identifiant local, ex: `airstrikes_1`) |
| `timestamp` | `date` |
| `label` | `label` |

**Points de vigilance**
- Les images référencées par `image_id` sont dans `Mediaeval2016_TestSet_Images.zip` (non téléchargé) — `image_path` contient l'identifiant, pas un chemin absolu
- Contenu centré sur la manipulation visuelle hors-contexte (images réutilisées dans un faux contexte)
- Le label `non-verifiable` → mappé `unknown`, à traiter séparément en entraînement

---

### 3.5 Flux RSS de sources fiables

| Propriété | Valeur |
|-----------|--------|
| **Type** | Source dynamique (live) |
| **Format** | RSS/Atom XML |
| **Langue** | Français et anglais |
| **Labels** | Aucun explicite (`real` implicite par réputation source) |
| **Outil** | `feedparser` v6.0.12 (maintenu, 99k+ dépendants) |
| **Licence** | Usage personnel/académique (CGU à vérifier par source) |

**Description**
Les flux RSS de médias de référence fournissent un flux continu d'articles récents avec titre, résumé et image. Ils constituent une source de données `real` pour équilibrer le corpus. Snopes ajoute une dimension fact-checking avec label explicite dans le titre.

**Méthode d'extraction**
`feedparser.parse(url)` — parsing XML natif, pas de scraping. Téléchargement des images via `requests`.

**Flux retenus**

| Source | URL RSS | Langue | Label |
|--------|---------|--------|-------|
| Le Monde | `https://www.lemonde.fr/rss/une.xml` | FR | real (implicite) |
| BBC News | `http://feeds.bbci.co.uk/news/rss.xml` | EN | real (implicite) |
| The Guardian | `https://www.theguardian.com/world/rss` | EN | real (implicite) |
| Snopes | `https://www.snopes.com/feed/` | EN | real/false/mixture (titre) |

> Note : Reuters a désactivé ses flux RSS publics en 2020. Remplacé par The Guardian.

**Mapping vers le format unifié**

| Champ RSS (`feedparser`) | Champ unifié |
|--------------------------|--------------|
| `entry.title` | `title` |
| `entry.summary` | `text` |
| `entry.enclosures` / `entry.media_content` | `image_url` |
| `entry.published` | `date` |
| `entry.link` | `url` |
| domaine extrait du `link` | `domain` |

**Points de vigilance**
- Les flux RSS ne donnent qu'un résumé (50-200 mots), pas le texte intégral
- `label_confidence: medium` — label `real` implicite, non vérifié article par article
- Tous les flux n'incluent pas d'image : vérifier la présence des balises `<enclosure>` ou `<media:content>`
- Snopes : le label explicite est parseable depuis le titre (préfixe "True:", "False:", "Mixture:")

---

## 4. Points de vigilance transversaux

### Distinction opinion controversée / désinformation

> Cette distinction est fondamentale pour la qualité des labels.

| | Opinion controversée | Désinformation |
|---|---|---|
| **Nature** | Subjective | Objectivement fausse |
| **Intention** | Expression d'un point de vue | Tromperie délibérée |
| **Vérifiabilité** | Non vérifiable | Vérifiable et réfutable |
| **Exemple** | "Cette politique économique est mauvaise" | "Le vaccin X contient une puce électronique" |
| **Traitement dans le dataset** | Exclure ou mapper `unknown` | Label `fake` |

Les datasets retenus (Fakeddit, MMFakeBench, MiRAGeNews) distinguent explicitement ces cas dans leurs protocoles d'annotation. Vérifier néanmoins les labels borderline lors du nettoyage.

### Champs secondaires à conserver

Ne pas négliger : `domain`, `url`, `date`, `label_confidence`. Ils permettent :
- Des analyses de biais (sources surreprésentées, dérives temporelles)
- La traçabilité et reproductibilité
- Des features supplémentaires pour le modèle (fiabilité du domaine)

### Association texte–image

Vérifier systématiquement que chaque entrée contient **à la fois** un `text` non vide et un `image_url` ou `image_path` valide. Les entrées incomplètes sont à filtrer ou à isoler dans un split séparé. La colonne `text_image_ok` du pipeline de transformation formalise ce contrôle.

---

## 5. Conclusion

Les 5 sources retenues couvrent des cas d'usage complémentaires :

- **Fakeddit** apporte du volume (>1M) et une classification fine (6 classes) sur des posts Reddit
- **MMFakeBench** apporte la précision de label et couvre les 3 types principaux de manipulation multimodale (ICLR 2025)
- **MiRAGeNews** couvre les images générées par IA (Midjourney, DALL-E 3, SDXL) — cas de désinformation visuelle moderne
- **MediaEval VMU** apporte des cas réels d'images hors-contexte (vraie image, faux contexte)
- **RSS fiables** apportent un flux dynamique récent avec couverture française

**Format retenu** : JSON Lines (`.jsonl`) — lisible ligne par ligne, compatible `pandas`, HuggingFace `datasets` et Apache Arrow, sans chargement mémoire complet.

**Prochaine étape** : pipeline de transformation (nettoyage, normalisation, export Parquet).
