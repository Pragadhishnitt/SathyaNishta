"""
Graph Database Population - Store corporate network data in Neo4j
Reads CSV files, creates nodes and relationships for graph analysis
Uses proper schema: Company, Person, ShellEntity, BankAccount
"""

import sys
import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add repo to path
repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "backend"))

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from dotenv import load_dotenv

# Load environment variables
load_dotenv(repo_root / ".env")

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

class GraphDatabasePopulator:
    def __init__(self):
        # For Neo4j Aura, use neo4j+ssc:// to skip certificate verification in development
        uri = NEO4J_URI.replace("neo4j+s://", "neo4j+ssc://") if NEO4J_URI.startswith("neo4j+s://") else NEO4J_URI

        self.driver = GraphDatabase.driver(
            uri,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        self.legal_docs_path = Path(__file__).parent / "legal_docs"

    def test_connection(self):
        """Test Neo4j connection before proceeding."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 'Neo4j connection successful' as message")
                record = result.single()
                print(f"Connected to Neo4j: {record['message']}")
                return True
        except ServiceUnavailable as e:
            print(f"Failed to connect to Neo4j: {e}")
            print("Please check your NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in .env")
            return False
        except Exception as e:
            print(f"Unexpected error connecting to Neo4j: {e}")
            return False

    def close(self):
        """Close the Neo4j driver connection."""
        self.driver.close()

    def read_csv(self, filename: str) -> List[Dict[str, Any]]:
        """Read CSV file and return list of dictionaries."""
        filepath = self.legal_docs_path / filename
        if not filepath.exists():
            print(f"Warning: {filename} not found")
            return []

        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean up whitespace
                cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
                data.append(cleaned_row)
        return data

    def create_constraints(self):
        """Create Neo4j constraints and indexes."""
        with self.driver.session() as session:
            # Get all indexes and drop them
            try:
                result = session.run("SHOW INDEXES")
                for record in result:
                    index_name = record.get('name')
                    if index_name:
                        try:
                            session.run(f"DROP INDEX {index_name}")
                        except:
                            pass
            except:
                pass
            
            # Company constraints and indexes
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE")
            
            # Person constraints and indexes (din = Director Identification Number)
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.din IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE")
            
            # ShellEntity constraints and indexes
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:ShellEntity) REQUIRE s.id IS UNIQUE")
            
            # BankAccount constraints
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (b:BankAccount) REQUIRE b.account_number IS UNIQUE")
            
            # Create performance indexes
            session.run("CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.name)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.sector)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.name)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (s:ShellEntity) ON (s.name)")

            print("Created constraints and indexes")

    def create_companies(self, companies_data: List[Dict[str, Any]]):
        """Create Company nodes."""
        with self.driver.session() as session:
            for company in companies_data:
                session.run("""
                    MERGE (c:Company {
                        id: $company_id,
                        name: $company_name,
                        cin: $registration_number,
                        sector: $sector,
                        listing_status: $listing_status,
                        country: $country
                    })
                """, **company)
            print(f"Created {len(companies_data)} Company nodes")

    def create_directors_and_individuals(self, directors_data: List[Dict[str, Any]]):
        """Create Person nodes and DIRECTOR_OF relationships."""
        with self.driver.session() as session:
            for director in directors_data:
                # Create Person node with DIN
                session.run("""
                    MERGE (p:Person {
                        id: $director_id,
                        din: $director_id,
                        name: $director_name,
                        pan: $pan,
                        appointment_date: date($appointment_date),
                        designation: $designation
                    })
                """, director)

                # Link Person to Company with DIRECTOR_OF relationship
                session.run("""
                    MATCH (p:Person {id: $director_id})
                    MATCH (c:Company {id: $company_id})
                    MERGE (p)-[:DIRECTOR_OF {
                        designation: $designation,
                        appointment_date: date($appointment_date),
                        sector_category: $sector_category
                    }]->(c)
                """, director)

            print(f"Created {len(directors_data)} Person nodes and DIRECTOR_OF relationships")

    def create_trusts_and_entities(self, trusts_data: List[Dict[str, Any]]):
        """Create ShellEntity nodes for offshore and shell entities."""
        with self.driver.session() as session:
            for trust in trusts_data:
                entity_type = trust.get('entity_type', 'Shell Company').strip()
                
                # Create ShellEntity node - use SET for optional properties
                session.run("""
                    MERGE (s:ShellEntity {
                        id: $entity_id,
                        name: $entity_name,
                        type: $entity_type
                    })
                    SET s.beneficial_owner = $beneficial_owner,
                        s.country = $country,
                        s.jurisdiction = $jurisdiction
                """, {
                    'entity_id': trust.get('entity_id'),
                    'entity_name': trust.get('entity_name'),
                    'entity_type': entity_type,
                    'beneficial_owner': trust.get('beneficial_owner'),
                    'country': trust.get('country'),
                    'jurisdiction': trust.get('country')
                })

            print(f"Created {len(trusts_data)} ShellEntity nodes")

    def create_ownership_relationships(self, shareholding_data: List[Dict[str, Any]]):
        """Create OWNS relationships from shareholders to companies."""
        with self.driver.session() as session:
            for holding in shareholding_data:
                shareholder_type = holding.get('shareholder_type', 'Company').strip()
                
                # Map shareholder type to node label
                if shareholder_type.lower() == 'company':
                    from_type = 'Company'
                elif shareholder_type.lower() == 'individual':
                    from_type = 'Person'
                elif shareholder_type.lower() in ['shell', 'offshore', 'offshore company']:
                    from_type = 'ShellEntity'
                else:
                    from_type = 'Company'
                
                session.run(f"""
                    MATCH (from:{from_type} {{id: $shareholder_id}})
                    MATCH (to:Company {{id: $company_id}})
                    MERGE (from)-[:OWNS {{
                        percentage_stake: toFloat($percentage_stake),
                        holding_type: $holding_type,
                        as_of_date: date($as_of_date)
                    }}]->(to)
                """, holding)

            print(f"Created {len(shareholding_data)} OWNS relationships")

    def create_company_relationships(self, relationships_data: List[Dict[str, Any]]):
        """Create PARENT_OF relationships between companies."""
        with self.driver.session() as session:
            for rel in relationships_data:
                # Convert relationship type to valid Cypher identifier
                rel_type = rel.get('relationship_type', 'SUBSIDIARY').upper().replace(' ', '_')
                
                session.run(f"""
                    MATCH (parent:Company {{id: $parent_company_id}})
                    MATCH (child:Company {{id: $child_company_id}})
                    MERGE (parent)-[:{rel_type} {{
                        percentage_ownership: toFloat($percentage_ownership),
                        relationship_date: date($relationship_date)
                    }}]->(child)
                """, rel)

            print(f"Created {len(relationships_data)} company relationships")

    def create_transactions(self, transactions_data: List[Dict[str, Any]]):
        """Create transaction relationships between companies."""
        with self.driver.session() as session:
            for txn in transactions_data:
                # Convert amount to integer (INR paise)
                txn['amount_paise'] = int(float(txn['amount_paise']))

                session.run("""
                    MATCH (from:Company {id: $from_company_id})
                    MATCH (to:Company {id: $to_company_id})
                    MERGE (from)-[:TRANSACTS_WITH {
                        id: $transaction_id,
                        amount: $amount_paise,
                        date: date($transaction_date),
                        description: $description,
                        type: $transaction_type
                    }]->(to)
                """, txn)

            print(f"Created {len(transactions_data)} transaction relationships")

    def _get_entity_type(self, entity_id: str) -> str:
        """Determine entity type from ID prefix."""
        if entity_id.startswith('SHELL_') or entity_id.startswith('OFFSHORE_'):
            return 'ShellEntity'
        else:
            return 'Company'

    def validate_circular_loops(self):
        """Find and report circular transaction loops."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = (c:Company)-[:TRANSACTS_WITH*3..5]-(c)
                WHERE ALL(r IN relationships(path) WHERE r.amount > 10000000000)
                RETURN path, length(path) as path_length,
                       reduce(total = 0, r IN relationships(path) | total + r.amount) as loop_total
                LIMIT 10
            """)

            loops = []
            for record in result:
                path = record['path']
                total_amount = record['loop_total']
                companies = [node['name'] for node in path.nodes]

                loops.append({
                    'path': companies,
                    'total_amount': total_amount
                })

            if loops:
                print(f"Found {len(loops)} potential circular loops:")
                for loop in loops:
                    amount_cr = loop['total_amount'] / 100_00_00_000
                    print(f"  {loop['path']} - ₹{amount_cr:.1f} Cr")

    def populate_all(self):
        """Main population function."""
        print("Starting Neo4j graph population...")

        # Test connection first
        if not self.test_connection():
            print("Aborting population due to connection failure.")
            return

        # Read all CSV data
        companies = self.read_csv('companies.csv')
        directors = self.read_csv('directors.csv')
        trusts = self.read_csv('trusts_and_entities.csv')
        shareholding = self.read_csv('shareholding_pattern.csv')
        relationships = self.read_csv('company_relationships.csv')
        transactions = self.read_csv('related_party_transactions.csv')

        print(f"Data loaded: {len(companies)} companies, {len(directors)} directors, "
              f"{len(trusts)} trusts, {len(shareholding)} holdings, "
              f"{len(relationships)} relationships, {len(transactions)} transactions")

        # Create constraints
        self.create_constraints()

        # Create nodes
        self.create_companies(companies)
        self.create_directors_and_individuals(directors)
        self.create_trusts_and_entities(trusts)

        # Create relationships
        self.create_ownership_relationships(shareholding)
        self.create_company_relationships(relationships)
        self.create_transactions(transactions)

        # Validate
        self.validate_circular_loops()

        print("Graph population complete!")


def main():
    populator = GraphDatabasePopulator()
    try:
        populator.populate_all()
    except Exception as e:
        print(f"Error during population: {e}")
        import traceback
        traceback.print_exc()
    finally:
        populator.close()


if __name__ == "__main__":
    main()