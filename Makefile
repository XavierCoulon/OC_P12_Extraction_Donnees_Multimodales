PYTHON  = python
OUTPUT  = data/processed
LIMIT   ?= 100

help:
	@echo "Commandes disponibles :"
	@echo ""
	@echo "  Extraction (étape 2)"
	@echo "  make install                  Installer les dépendances (uv)"
	@echo "  make extract [LIMIT=N]        Extraire toutes les sources"
	@echo "  make extract-rss [LIMIT=N]    Extraire les flux RSS"
	@echo "  make extract-fakeddit [LIMIT=N]    Extraire Fakeddit (CSV requis dans data/raw/fakeddit/)"
	@echo "  make extract-mmfakebench [LIMIT=N] Extraire MMFakeBench (HF_TOKEN requis dans .env)"
	@echo "  make extract-miragenews [LIMIT=N]  Extraire MiRAGeNews (téléchargement auto HuggingFace)"
	@echo "  make extract-mediaeval [LIMIT=N]   Extraire MediaEval VMU (téléchargement auto)"
	@echo ""
	@echo "  Transformation (étape 3)"
	@echo "  make transform                Transformer toutes les sources → Parquet"
	@echo "  make transform-SOURCE         Transformer une source (ex: make transform-rss)"
	@echo "  make verify                   Vérifier le Parquet produit"
	@echo ""
	@echo "  Qualité"
	@echo "  make test                     Lancer les tests pytest"
	@echo ""
	@echo "  LIMIT : nombre max d'entrées valides par source (défaut: 100)"
	@echo "  Exemple : make extract-rss LIMIT=500"

# Extraction (étape 2)
extract:
	uv run python main.py --source all --limit $(LIMIT) --output $(OUTPUT)

extract-%:
	uv run python main.py --source $* --limit $(LIMIT) --output $(OUTPUT)

# Transformation (étape 3)
transform:
	uv run python transform.py --source all

transform-%:
	uv run python transform.py --source $*

verify:
	uv run python verify.py

# Installation des dépendances
install:
	uv sync

# Tests
test:
	uv run pytest tests/ -v

.PHONY: help extract transform verify install test
.DEFAULT_GOAL := help
