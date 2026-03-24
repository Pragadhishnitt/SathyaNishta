import os
import sys
from pathlib import Path
from supabase import create_client, Client

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.core.config import settings

url: str = settings.SUPABASE_URL
key: str = settings.SUPABASE_SERVICE_KEY

if not url or not key:
    print("Missing Supabase URL or Service Key")
    sys.exit(1)

supabase: Client = create_client(supabase_url=url, supabase_key=key)

repo_root = Path("/app")
financial_dir = repo_root / "app" / "agents" / "financial" / "annual_reports"
regulatory_dir = repo_root / "app" / "agents" / "compliance" / "legal_docs"

# 1. Ensure Buckets exist
buckets = [b.name for b in supabase.storage.list_buckets()]
for b_name in ["financial_docs", "regulatory_docs"]:
    if b_name not in buckets:
        print(f"Creating bucket: {b_name}")
        supabase.storage.create_bucket(b_name)
    else:
        print(f"Bucket {b_name} already exists.")

# 2. Upload Financial Docs
if financial_dir.exists():
    for pdf in financial_dir.glob("*.pdf"):
        # Format: {COMPANY}/{doc_type}.pdf
        parts = pdf.stem.split("_")
        company = parts[0]
        doc_type = parts[1] if len(parts) > 1 else "Unknown"
        storage_path = f"{company}/FY2024/Annual/{doc_type}.pdf"
        
        print(f"Uploading {pdf.name} to financial_docs/{storage_path}...")
        with open(pdf, "rb") as f:
            try:
                supabase.storage.from_("financial_docs").upload(file=f, path=storage_path, file_options={"content-type": "application/pdf"})
            except Exception as e:
                print(f"  Failed: {e}")
                
# 3. Upload Regulatory Docs
if regulatory_dir.exists():
    for pdf in regulatory_dir.rglob("*.pdf"):
        # Format: {source}/{filename}.pdf
        source = pdf.parent.name
        storage_path = f"{source}/{pdf.name}"
        
        print(f"Uploading {pdf.name} to regulatory_docs/{storage_path}...")
        with open(pdf, "rb") as f:
            try:
                supabase.storage.from_("regulatory_docs").upload(file=f, path=storage_path, file_options={"content-type": "application/pdf"})
            except Exception as e:
                print(f"  Failed: {e}")

print("Upload complete!")
