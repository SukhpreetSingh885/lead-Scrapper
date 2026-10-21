import os
import sys
import sqlite3
from pathlib import Path

# Base paths
ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"

DB_PATH = ROOT_DIR / "india_leads.db"
BACKEND_DB_PATH = BACKEND_DIR / "india_leads.db"

EXPORT_DIRS = [
    ROOT_DIR / "exports_data",
    BACKEND_DIR / "exports_data"
]

BACKUP_FILES = [
    ROOT_DIR / "india_leads_backup.db",
    BACKEND_DIR / "india_leads_backup.db"
]

TABLES_TO_CLEAR_IN_ORDER = [
    "discovery_job_leads",
    "discovery_job_items",
    "discovery_jobs",
    "enrichment_jobs",
    "duplicate_candidates",
    "business_contacts",
    "social_profiles",
    "branches",
    "companies",
    "exports",
    "source_permissions",
    "lead_sources",
]


def clean_database(db_file: Path):
    if not db_file.exists():
        print(f"[SKIP] Database file does not exist: {db_file}")
        return {}

    print(f"\n========================================================")
    print(f"CLEANING DATABASE: {db_file}")
    print(f"========================================================")

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()

    # Enable foreign keys
    cur.execute("PRAGMA foreign_keys = ON;")
    fk_status = cur.execute("PRAGMA foreign_keys;").fetchone()[0]
    print(f"Foreign keys enabled: {bool(fk_status)}")

    # Check existing table list
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = set(r[0] for r in cur.fetchall())

    deleted_counts = {}

    try:
        # Start transaction
        cur.execute("BEGIN IMMEDIATE TRANSACTION;")

        # Delete lead-related tables in topological order
        for table in TABLES_TO_CLEAR_IN_ORDER:
            if table in existing_tables:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                before_cnt = cur.fetchone()[0]
                cur.execute(f"DELETE FROM {table};")
                deleted_counts[table] = before_cnt
                print(f"  [-] Deleted {before_cnt} records from '{table}'")

        # Lead-related audit logs
        if "audit_logs" in existing_tables:
            cur.execute("""
                SELECT COUNT(*) FROM audit_logs 
                WHERE entity_type IN ('company', 'branch', 'lead', 'discovery_job', 'enrichment_job', 'export', 'duplicate')
                   OR action LIKE '%lead%' 
                   OR action LIKE '%job%' 
                   OR action LIKE '%export%';
            """)
            audit_cnt = cur.fetchone()[0]
            cur.execute("""
                DELETE FROM audit_logs 
                WHERE entity_type IN ('company', 'branch', 'lead', 'discovery_job', 'enrichment_job', 'export', 'duplicate')
                   OR action LIKE '%lead%' 
                   OR action LIKE '%job%' 
                   OR action LIKE '%export%';
            """)
            deleted_counts["audit_logs"] = audit_cnt
            print(f"  [-] Deleted {audit_cnt} lead-related audit logs")

        # Commit transaction
        cur.execute("COMMIT;")
        print("Transaction successfully committed.")

        # Foreign key integrity check
        cur.execute("PRAGMA foreign_key_check;")
        fk_violations = cur.fetchall()
        if fk_violations:
            print(f"WARNING: Foreign key violations detected: {fk_violations}")
        else:
            print("Foreign key integrity check passed: 0 violations.")

    except Exception as e:
        cur.execute("ROLLBACK;")
        print(f"ERROR: Transaction rolled back due to: {e}")
        conn.close()
        raise e

    # Verification of preserved and cleared tables
    print("\n--- Final Table Counts ---")
    verification = {}
    check_tables = [
        "users", "organizations", "india_locations",
        "companies", "branches", "business_contacts", "social_profiles",
        "discovery_jobs", "discovery_job_items", "discovery_job_leads",
        "enrichment_jobs", "duplicate_candidates", "exports",
        "lead_sources", "source_permissions", "audit_logs"
    ]
    for t in check_tables:
        if t in existing_tables:
            cur.execute(f"SELECT COUNT(*) FROM {t};")
            verification[t] = cur.fetchone()[0]
            print(f"  {t}: {verification[t]}")

    conn.close()
    return deleted_counts, verification


def delete_backup_files():
    print(f"\n========================================================")
    print("DELETING PREVIOUS SQLITE BACKUP FILES")
    print(f"========================================================")
    deleted_backups = []
    for bf in BACKUP_FILES:
        if bf.exists():
            size = bf.stat().st_size
            bf.unlink()
            deleted_backups.append(f"{bf.name} ({size} bytes)")
            print(f"  [X] Deleted backup file: {bf} ({size} bytes)")
        else:
            print(f"  [.] Backup file not present: {bf}")
    return deleted_backups


def delete_export_files():
    print(f"\n========================================================")
    print("DELETING GENERATED EXPORT FILES (CSV/XLSX)")
    print(f"========================================================")
    deleted_exports = []
    for exp_dir in EXPORT_DIRS:
        if exp_dir.exists():
            for f in exp_dir.glob("leads_export_*"):
                if f.is_file() and f.suffix in [".csv", ".xlsx"]:
                    size = f.stat().st_size
                    f.unlink()
                    deleted_exports.append(f"{f.name} ({size} bytes)")
                    print(f"  [X] Deleted export: {f.name} ({size} bytes)")
    if not deleted_exports:
        print("  [.] No generated export files found.")
    return deleted_exports


if __name__ == "__main__":
    print("=" * 60)
    print("INDIA LEADS PLATFORM: COMPLETE CLEAN RESET")
    print("=" * 60)

    # 1. Clean primary active database
    del_counts, final_counts = clean_database(DB_PATH)

    # 2. Clean secondary database if present
    if BACKEND_DB_PATH.exists() and BACKEND_DB_PATH.resolve() != DB_PATH.resolve():
        clean_database(BACKEND_DB_PATH)

    # 3. Delete previous SQLite backup files
    deleted_backups = delete_backup_files()

    # 4. Delete generated export files
    deleted_exports = delete_export_files()

    print("\n" + "=" * 60)
    print("CLEAN RESET EXECUTION COMPLETED")
    print("=" * 60)

