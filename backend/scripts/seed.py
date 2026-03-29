#!/usr/bin/env python3
"""
Database Seeding Script
========================
Usage: docker compose exec backend python scripts/seed.py

This script populates the database with initial data for development/testing.
It is idempotent where possible, or clears data before inserting.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, "/app")

from datetime import datetime, timezone
from uuid import uuid4

from neo4j import GraphDatabase
from sqlmodel import Session, create_engine, text

from app.core.config import settings


def main():
    print("🌱 Seeding database...")

    # 1. Connect to Supabase
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as session:
        # Example: Create a dummy investigation
        inv_id = uuid4()
        session.exec(
            text(
                """
            INSERT INTO investigations (id, query, status, created_at, updated_at, domains, cross_domain_insights, evidence_chain)
            VALUES (:id, :query, 'queued', :now, :now, '{}', '[]', '[]')
        """
            ),
            params={
                "id": str(inv_id),
                "query": "Seed Data Investigation",
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        session.commit()
        print(f"✅ Created investigation: {inv_id}")

    # 2. Connect to Neo4j
    driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD))
    with driver.session() as session:
        session.run("MERGE (c:Company {name: 'SeedCorp'}) SET c.created_at = datetime()")
        print("✅ Created/Merged 'SeedCorp' node in Neo4j")
    driver.close()

    print("✨ Seeding complete!")


if __name__ == "__main__":
    main()
