PYTHON  = python
OUTPUT  = data/processed
LIMIT   ?= 100

help:
	@echo "Commandes disponibles :"
	@echo "  make install              Installer les dépendances (uv)"
	@echo "  make rss [LIMIT=N]        Extraire les flux RSS"
	@echo "  make fakeddit [LIMIT=N]   Extraire Fakeddit (CSV requis dans data/raw/fakeddit/)"
	@echo "  make mmfakebench [LIMIT=N] Extraire MMFakeBench (HF_TOKEN requis dans .env)"
	@echo "  make hemt_fake [LIMIT=N]  Extraire HEMT-Fake (téléchargement auto Zenodo)"
	@echo "  make mediaeval [LIMIT=N]  Extraire MediaEval VMU (téléchargement auto)"
	@echo "  make all [LIMIT=N]        Extraire toutes les sources"
	@echo ""
	@echo "  LIMIT : nombre max d'entrées valides par source (défaut: 100)"
	@echo "  Exemple : make rss LIMIT=500"

# Extraction par source
rss:
	$(PYTHON) main.py --source rss --limit $(LIMIT) --output $(OUTPUT)

fakeddit:
	$(PYTHON) main.py --source fakeddit --limit $(LIMIT) --output $(OUTPUT)

mmfakebench:
	$(PYTHON) main.py --source mmfakebench --limit $(LIMIT) --output $(OUTPUT)

hemt_fake:
	$(PYTHON) main.py --source hemt_fake --limit $(LIMIT) --output $(OUTPUT)

mediaeval:
	$(PYTHON) main.py --source mediaeval --limit $(LIMIT) --output $(OUTPUT)

all:
	$(PYTHON) main.py --source all --limit $(LIMIT) --output $(OUTPUT)

# Installation des dépendances
install:
	uv sync

.PHONY: help rss fakeddit mmfakebench hemt_fake mediaeval all install
.DEFAULT_GOAL := help
