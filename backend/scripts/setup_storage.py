#!/usr/bin/env python3
"""
Supabase Storage Setup Script
=============================
Creates required storage buckets if they don't exist.
Uses Supabase Storage API directly via requests.

Buckets:
1. financial_docs (Private, 50MB, PDF)
2. audio_recordings (Private, 200MB, Audio)
3. temp_uploads (Private, 100MB, Any)
"""
import sys
import os
import requests

# Add project root to path
sys.path.insert(0, "/app")

from app.core.config import settings


def create_bucket(name: str, public: bool = False, file_size_limit: int = None, allowed_mime_types: list = None):
    url = f"{settings.SUPABASE_URL}/storage/v1/bucket"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "id": name,
        "name": name,
        "public": public,
        "file_size_limit": file_size_limit,
        "allowed_mime_types": allowed_mime_types,
    }

    # 1. Check if exists
    try:
        check = requests.get(f"{url}/{name}", headers=headers)
        if check.status_code == 200:
            print(f"✅ Bucket '{name}' already exists.")
            return
    except Exception as e:
        print(f"⚠️ Error checking bucket {name}: {e}")

    # 2. Create
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"✅ Created bucket '{name}'")
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"✅ Bucket '{name}' already exists (400 check).")
        else:
            print(f"❌ Failed to create bucket '{name}': {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error creating bucket {name}: {e}")


def main():
    print("📦 Setting up Supabase Storage Buckets...")

    # 1. financial_docs
    create_bucket(
        "financial_docs", public=False, file_size_limit=52428800, allowed_mime_types=["application/pdf"]  # 50MB
    )

    # 2. audio_recordings (reduced to 50MB for free tier compatibility)
    create_bucket(
        "audio_recordings",
        public=False,
        file_size_limit=52428800,  # 50MB
        allowed_mime_types=["audio/mpeg", "audio/wav", "audio/x-m4a"],
    )

    # 3. temp_uploads
    create_bucket("temp_uploads", public=False, file_size_limit=52428800, allowed_mime_types=None)  # 50MB  # Any

    print("✨ Storage setup complete!")


if __name__ == "__main__":
    main()
