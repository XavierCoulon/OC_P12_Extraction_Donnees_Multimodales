# Rapport d'exploration des sources de données multimodales

**Projet** : Détection de fake news multimodales
**Date** : 2026-03-17
**Auteur** : Xavier Coulon

---

## 1. Tableau comparatif des sources retenues

| # | Source | Modalités | Volume | Langue | Labels | Qualité labels | Faisabilité |
|---|--------|-----------|--------|--------|--------|----------------|-------------|
| 1 | **Fakeddit** | texte + image + metadata | ~1M | EN | 2 et 6 classes | Haute | ✅ |
| 2 | **MMFakeBench** | texte + image | ~10k | EN | vrai/faux (12 sous-catégories) | Très haute | ✅ |
| 3 | **HEMT-Fake** | texte + image | 74k | EN/HI/GU/MR/TE | vrai/faux | Haute | ✅ |
| 4 | **MediaEval VMU** | tweet + image | ~15k | EN | real/fake/non-verifiable | Haute | ✅ |
| 5 | **RSS flux fiables** | texte + image | continu | FR/EN | real (implicite) | Moyenne | ✅ |

### Sources écartées

| Source | Raison d'exclusion |
|--------|-------------------|
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
  "source": "fakeddit|mmfakebench|hemt_fake|mediaeval|rss",
  "title": "Titre de l'article ou du post",
  "text": "Corps textuel ou résumé",
  "image_url": "https://example.com/image.jpg",
  "image_path": "data/images/<id>.jpg",
  "label": "real|fake|unknown",
  "label_confidence": "high|medium|low",
  "language": "en|fr|hi|...",
  "date": "2024-01-15T12:00:00Z",
  "url": "https://example.com/article",
  "domain": "example.com",
  "extraction_method": "dataset|rss"
}
```

**Champs obligatoires** : `id`, `source`, `text`, `image_url`, `label`, `extraction_method`
**Stockage** : JSON Lines (`.jsonl`), un enregistrement par ligne, compatible `pandas` et HuggingFace `datasets`

---

## 3. Description détaillée des sources

### 3.1 Fakeddit

| Propriété | Valeur |
|-----------|--------|
| **Type** | Dataset statique |
| **Format** | CSV (Google Drive) + URLs images |
| **Langue** | Anglais |
| **Labels** | 2 classes (real/fake) + 6 classes détaillées |
| **Volume** | ~1 million d'échantillons |
| **Licence** | Usage académique non commercial |
| **Accès** | [fakeddit.netlify.app](https://fakeddit.netlify.app/) · [GitHub](https://github.com/entitize/Fakeddit) |

**Description**
Dataset construit à partir de posts Reddit couvrant 22 subreddits. Chaque entrée comprend le titre du post, l'image associée et des métadonnées sociales (votes, subreddit, domaine). Les labels 6 classes distinguent : *true*, *satire*, *misleading*, *manipulated*, *false content*, *non-verifiable*.

**Qualité des labels**
Haute — labels dérivés des règles communautaires de chaque subreddit (r/TheOnion = satire, r/worldnews = réel). Biais potentiel : surreprésentation de la politique américaine et du divertissement.

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
- Certaines URLs d'images sont mortes depuis les restrictions API Reddit 2023 — utiliser les fichiers pré-téléchargés disponibles sur le site officiel
- Le label *non-verifiable* ne correspond pas à de la désinformation → à exclure ou mapper sur `unknown`

---

### 3.2 MMFakeBench

| Propriété | Valeur |
|-----------|--------|
| **Type** | Dataset statique — benchmark |
| **Format** | Parquet via HuggingFace `datasets` |
| **Langue** | Anglais |
| **Labels** | Binaire (real/fake) + 3 catégories × 4 sous-catégories |
| **Licence** | CC-BY 4.0 (Data Usage Protocol à accepter sur HuggingFace) |
| **Accès** | [HuggingFace](https://huggingface.co/datasets/liuxuannan/MMFakeBench) · [GitHub](https://github.com/liuxuannan/MMFakeBench) — ICLR 2025 |

**Description**
Benchmark de référence (2025) couvrant 3 types de fake news multimodales : *text-only manipulation*, *image-only manipulation*, *cross-modal inconsistency*. Conçu spécifiquement pour l'évaluation de modèles multimodaux.

**Qualité des labels**
Très haute — annotations humaines expertes avec double validation, conçu pour être benchmark de référence ICLR 2025.

**Mapping vers le format unifié**

| Champ MMFakeBench | Champ unifié |
|-------------------|--------------|
| `id` | `id` |
| `text` | `text` |
| `title` | `title` |
| `image` / `image_url` | `image_path` / `image_url` |
| `label` | `label` (0 = fake, 1 = real) |
| `category` | `label_confidence` (proxy) |
| `source` | `domain` |
| `date` | `date` |

**Points de vigilance**
- Signature du Data Usage Protocol obligatoire avant accès sur HuggingFace
- Dataset orienté évaluation : distributions réel/faux équilibrées artificiellement, éloignées de la réalité terrain
- Droits d'image potentiellement complexes pour redistribution (images issues de Twitter et sites d'actualité)

---

### 3.3 HEMT-Fake

| Propriété | Valeur |
|-----------|--------|
| **Type** | Dataset statique |
| **Format** | Téléchargement direct (Zenodo) |
| **Langue** | Anglais, Hindi, Gujarati, Marathi, Telugu |
| **Labels** | Binaire (real/fake) |
| **Volume** | 74 032 articles |
| **Licence** | Open access |
| **Accès** | [Zenodo DOI 10.5281/zenodo.11408513](https://zenodo.org/records/11408513) |

**Description**
Dataset multilingue rare couvrant 5 langues du sous-continent indien et l'anglais. Chaque entrée associe un article textuel et son image. Publié en 2024-2025, conçu pour la recherche en détection de désinformation multimodale et multilingue.

**Qualité des labels**
Haute — annotations manuelles, sources vérifiées via fact-checkers reconnus dans chaque langue.

**Mapping vers le format unifié**

| Champ HEMT-Fake | Champ unifié |
|-----------------|--------------|
| `id` | `id` |
| `title` | `title` |
| `text` / `content` | `text` |
| `image_url` / `image_path` | `image_url` / `image_path` |
| `label` | `label` |
| `language` | `language` |
| `source_url` | `url` + `domain` |
| `date` | `date` |

**Points de vigilance**
- Couverture géographique centrée sur le sous-continent indien — biais thématique si le cas d'usage cible l'Europe ou les États-Unis
- Langues indiennes : nécessite un tokenizer multilingue (mBERT, XLM-R) pour l'entraînement
- Vérifier la structure exacte du fichier JSON après téléchargement (peut varier selon la version Zenodo)

---

### 3.4 MediaEval Verifying Multimedia Use (VMU)

| Propriété | Valeur |
|-----------|--------|
| **Type** | Dataset statique — benchmark de challenge |
| **Format** | JSON + images |
| **Langue** | Anglais |
| **Labels** | `real` / `fake` / `non-verifiable` |
| **Volume** | ~15 000 entrées (variable selon édition) |
| **Éditions** | 2015–2022 (archivées) |
| **Licence** | Usage académique |
| **Accès** | [multimediaeval.github.io](https://multimediaeval.github.io/) |

**Description**
Challenge annuel (2015-2022) centré sur la vérification de contenu multimédia partagé sur les réseaux sociaux. Les données consistent en tweets avec images potentiellement *out-of-context* : l'image est réelle, mais associée à un faux contexte textuel.

**Qualité des labels**
Haute — annotations par des équipes de journalistes et fact-checkers. Le label `non-verifiable` signale les cas ambigus (à distinguer des opinions).

**Mapping vers le format unifié**

| Champ MediaEval | Champ unifié |
|-----------------|--------------|
| `tweetId` | `id` |
| `tweetText` | `text` |
| `imageUrl` | `image_url` |
| `label` | `label` |
| `date` | `date` |
| `tweetId` (construit) | `url` (url Twitter) |

**Points de vigilance**
- Contenu centré sur la manipulation visuelle hors-contexte : utile pour détecter les images réutilisées, moins représentatif des fake news purement textuelles
- URLs Twitter dans les données peuvent être inaccessibles (comptes suspendus, contenus supprimés)
- Le label `non-verifiable` doit être mappé sur `unknown` et traité séparément en entraînement

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

**Flux retenus**

| Source | URL RSS | Langue | Label |
|--------|---------|--------|-------|
| Le Monde | `https://www.lemonde.fr/rss/une.xml` | FR | real (implicite) |
| Reuters | `https://feeds.reuters.com/reuters/topNews` | EN | real (implicite) |
| BBC News | `http://feeds.bbci.co.uk/news/rss.xml` | EN | real (implicite) |
| Snopes | `https://www.snopes.com/feed/` | EN | real/false/mixture (titre) |

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
- Tous les flux n'incluent pas d'image : vérifier la présence des balises `<enclosure>` ou `<media:content>` avant intégration
- Snopes : le label explicite est parseable depuis le titre (préfixe "True:", "False:", "Mixture:") — traitement supplémentaire nécessaire

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

Les datasets retenus (Fakeddit, MMFakeBench, HEMT-Fake) distinguent explicitement ces cas dans leurs protocoles d'annotation. Vérifier néanmoins les labels borderline lors du nettoyage.

### Champs secondaires à conserver

Ne pas négliger : `domain`, `url`, `date`, `label_confidence`. Ils permettent :
- Des analyses de biais (sources surreprésentées, dérives temporelles)
- La traçabilité et reproductibilité
- Des features supplémentaires pour le modèle (fiabilité du domaine)

### Association texte–image

Vérifier systématiquement que chaque entrée contient **à la fois** un `text` non vide et un `image_url` valide. Les entrées incomplètes sont à filtrer ou à isoler dans un split séparé.

---

## 5. Conclusion

Les 5 sources retenues couvrent des cas d'usage complémentaires :

- **Fakeddit** et **HEMT-Fake** apportent du volume et de la diversité linguistique
- **MMFakeBench** apporte la précision de label et couvre les 3 types principaux de manipulation multimodale
- **MediaEval VMU** apporte des cas réels de manipulation d'images hors-contexte
- **RSS fiables** apportent un flux dynamique récent avec couverture française

**Format retenu** : JSON Lines (`.jsonl`) — lisible ligne par ligne, compatible `pandas`, HuggingFace `datasets` et Apache Arrow, sans chargement mémoire complet.

**Prochaine étape** : implémentation des scripts d'extraction pour chaque source.
