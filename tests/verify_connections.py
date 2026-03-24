import sys
import os
import time
from sqlalchemy import text
from neo4j import GraphDatabase

# Add parent directory to sys.path so we can import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.db import engine
from app.shared.llm_portkey import chat_complete

def verify_llm():
    print("Checking Portkey LLM connectivity...")
    started = time.monotonic()
    try:
        result = chat_complete(
            user_prompt="Reply with a single word: PASSED",
            system_prompt="You are a connection verification script.",
            temperature=0,
            metadata={"source": "verify_script"}
        )
        elapsed = int((time.monotonic() - started) * 1000)
        content = (result.get("content") or "").strip()
        print(f"[PASSED] Portkey responded in {elapsed}ms: {content}")
        return True
    except Exception as e:
        print(f"[FAILED] Portkey error: {str(e)}")
        return False

def verify_postgres():
    print("Checking Supabase PostgreSQL connectivity...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            val = result.scalar()
            if val == 1:
                print("[PASSED] Supabase PostgreSQL connected.")
                return True
            else:
                print(f"[FAILED] Supabase PostgreSQL returned unexpected value: {val}")
                return False
    except Exception as e:
        print(f"[FAILED] Supabase PostgreSQL error: {str(e)}")
        return False

def verify_neo4j():
    print("Checking Neo4j connectivity...")
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        with driver.session() as session:
            result = session.run("RETURN 1 AS val")
            val = result.single()["val"]
            if val == 1:
                print("[PASSED] Neo4j Aura connected.")
                driver.close()
                return True
            else:
                print(f"[FAILED] Neo4j returned unexpected value: {val}")
                driver.close()
                return False
    except Exception as e:
        print(f"[FAILED] Neo4j error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== SATHYA NISHTA CONNECTION VERIFICATION ===")
    results = [
        verify_llm(),
        verify_postgres(),
        verify_neo4j()
    ]
    print("============================================")
    if all(results):
        print("ALL CONNECTIONS VERIFIED SUCCESSFULLY.")
        sys.exit(0)
    else:
        print("SOME CONNECTIONS FAILED.")
        sys.exit(1)
