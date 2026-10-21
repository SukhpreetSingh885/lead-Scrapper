import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, engine
from app.models import Base
import sqlalchemy as sa


def run_migration():
    print("=" * 60)
    print("MIGRATION: Create discovery_job_leads & update discovery_job_items")
    print("=" * 60)

    inspector = sa.inspect(engine)
    existing_tables = inspector.get_table_names()

    with engine.connect() as conn:
        # 1. Create discovery_job_leads table if not exists
        if "discovery_job_leads" not in existing_tables:
            print("Creating discovery_job_leads table...")
            conn.execute(sa.text("""
                CREATE TABLE discovery_job_leads (
                    job_id VARCHAR(36) NOT NULL,
                    branch_id VARCHAR(36) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (job_id, branch_id),
                    FOREIGN KEY(job_id) REFERENCES discovery_jobs(id) ON DELETE CASCADE,
                    FOREIGN KEY(branch_id) REFERENCES branches(id) ON DELETE CASCADE
                )
            """))
            conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_discovery_job_leads_job_id ON discovery_job_leads (job_id)"))
            conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_discovery_job_leads_branch_id ON discovery_job_leads (branch_id)"))
            conn.commit()
            print("Successfully created discovery_job_leads table.")
        else:
            print("Table discovery_job_leads already exists.")

        # 2. Add branch_id to discovery_job_items if not exists
        job_item_cols = [c["name"] for c in inspector.get_columns("discovery_job_items")]
        if "branch_id" not in job_item_cols:
            print("Adding branch_id column to discovery_job_items...")
            conn.execute(sa.text("ALTER TABLE discovery_job_items ADD COLUMN branch_id VARCHAR(36)"))
            conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_discovery_job_items_branch_id ON discovery_job_items (branch_id)"))
            conn.commit()
            print("Successfully added branch_id column to discovery_job_items.")
        else:
            print("Column branch_id already exists on discovery_job_items.")

    # 3. Backfill association for any existing jobs if matching branches exist by source_reference
    db = SessionLocal()
    try:
        from app.models import DiscoveryJob, DiscoveryJobItem, Branch
        jobs = db.query(DiscoveryJob).all()
        linked_count = 0
        for j in jobs:
            items = db.query(DiscoveryJobItem).filter(DiscoveryJobItem.job_id == j.id).all()
            for it in items:
                if it.external_id:
                    branch = db.query(Branch).filter(Branch.source_reference == it.external_id).first()
                    if branch:
                        it.branch_id = branch.id
                        # Check if association exists
                        exists = db.execute(
                            sa.text("SELECT 1 FROM discovery_job_leads WHERE job_id = :jid AND branch_id = :bid"),
                            {"jid": j.id, "bid": branch.id}
                        ).first()
                        if not exists:
                            db.execute(
                                sa.text("INSERT INTO discovery_job_leads (job_id, branch_id) VALUES (:jid, :bid)"),
                                {"jid": j.id, "bid": branch.id}
                            )
                            linked_count += 1
        db.commit()
        print(f"Backfilled {linked_count} historical job-to-lead associations.")
    finally:
        db.close()

    print("Migration finished successfully!")


if __name__ == "__main__":
    run_migration()

