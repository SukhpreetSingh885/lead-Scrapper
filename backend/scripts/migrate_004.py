import sqlite3
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH = ROOT_DIR / "india_leads.db"

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

# Check alembic_version
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version';")
has_alembic = cur.fetchone()
if not has_alembic:
    print("Creating alembic_version table...")
    cur.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num));")
    cur.execute("INSERT INTO alembic_version (version_num) VALUES ('003_job_leads_association');")
    conn.commit()
else:
    cur.execute("SELECT version_num FROM alembic_version;")
    row = cur.fetchone()
    print("Current alembic_version:", row)
    if not row:
        cur.execute("INSERT INTO alembic_version (version_num) VALUES ('003_job_leads_association');")
        conn.commit()

# Inspect columns of discovery_job_items
cur.execute("PRAGMA table_info(discovery_job_items);")
cols = [r[1] for r in cur.fetchall()]
print("Current discovery_job_items columns:", cols)

add_job_items_cols = [
    ("category", "VARCHAR(100)"),
    ("mobile", "VARCHAR(100)"),
    ("whatsapp", "VARCHAR(100)"),
    ("email", "VARCHAR(255)"),
    ("city", "VARCHAR(100)"),
    ("state", "VARCHAR(100)"),
    ("source_code", "VARCHAR(50)"),
    ("is_saved", "BOOLEAN DEFAULT 0 NOT NULL"),
    ("is_already_saved", "BOOLEAN DEFAULT 0 NOT NULL"),
    ("expires_at", "DATETIME")
]

for col_name, col_type in add_job_items_cols:
    if col_name not in cols:
        print(f"Adding column '{col_name}' to discovery_job_items...")
        cur.execute(f"ALTER TABLE discovery_job_items ADD COLUMN {col_name} {col_type};")

# Inspect discovery_jobs columns
cur.execute("PRAGMA table_info(discovery_jobs);")
job_cols = [r[1] for r in cur.fetchall()]
if "expires_at" not in job_cols:
    print("Adding column 'expires_at' to discovery_jobs...")
    cur.execute("ALTER TABLE discovery_jobs ADD COLUMN expires_at DATETIME;")

# Inspect exports columns
cur.execute("PRAGMA table_info(exports);")
export_cols = [r[1] for r in cur.fetchall()]
if "filename" not in export_cols:
    print("Adding column 'filename' to exports...")
    cur.execute("ALTER TABLE exports ADD COLUMN filename VARCHAR(255);")

# Update alembic version to 004
cur.execute("UPDATE alembic_version SET version_num = '004_search_preview_and_export_filename';")
conn.commit()
print("Successfully upgraded to 004_search_preview_and_export_filename!")

conn.close()

