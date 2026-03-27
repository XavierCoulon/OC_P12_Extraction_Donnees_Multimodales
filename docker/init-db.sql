-- Initialisation du data warehouse (exécuté une seule fois au démarrage du container)
-- Crée l'utilisateur ETL avec permissions minimales (principe du moindre privilège)

CREATE USER etl_user WITH PASSWORD :'ETL_PASSWORD';

CREATE TABLE IF NOT EXISTS articles (
    id                TEXT PRIMARY KEY,
    source            TEXT,
    title             TEXT,
    text              TEXT,
    image_url         TEXT,
    image_path        TEXT,
    label             TEXT,
    label_int         INTEGER,
    label_confidence  TEXT,
    language          TEXT,
    date              TEXT,
    url               TEXT,
    domain            TEXT,
    extraction_method TEXT,
    image_valid       BOOLEAN,
    has_image         BOOLEAN,
    text_image_ok     BOOLEAN,
    text_length       INTEGER,
    word_count        INTEGER
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id       TEXT,
    run_date     TIMESTAMP,
    task         TEXT,
    source       TEXT,
    total        INTEGER,
    success      INTEGER,
    skipped      INTEGER,
    errors       INTEGER,
    duration_s   FLOAT,
    parquet_rows INTEGER,
    parquet_mb   FLOAT,
    PRIMARY KEY (run_id, task)
);

-- Permissions minimales : lecture + écriture sur articles uniquement
GRANT CONNECT ON DATABASE multimodal TO etl_user;
GRANT INSERT, SELECT, UPDATE ON articles TO etl_user;
GRANT INSERT, SELECT ON pipeline_runs TO etl_user;
