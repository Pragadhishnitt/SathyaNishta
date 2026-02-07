# Storage Contracts
## Sathya Nishta — Storage Contracts

**TEAM A & B SHARED RESPONSIBILITY**

This document defines the Object Storage (Supabase Storage) structure. Both the Frontend (upload) and Backend (processing) must adhere to these path conventions.

**Version:** 1.0.0  
**Last Updated:** Sprint 1

---

## 1. Buckets Overview

| Bucket Name | Privacy | Max File Size | Allowed MIME Types | Purpose |
|---|---|---|---|---|
| `financial_docs` | Private | 50 MB | `application/pdf` | Balance sheets, annual reports |
| `audio_recordings`| Private | 200 MB | `audio/mpeg`, `audio/wav`, `audio/m4a` | Earnings calls, meetings |
| `temp_uploads` | Private | 100 MB | Any | Temporary holding area before processing |

---

## 2. Bucket Definitions

### 📂 `financial_docs`

**Purpose:** Stores raw PDF filings for the Financial Agent.

**Path Convention:**
```
{company_ticker}/{fiscal_year}/{period}/{doc_type}.pdf
```

**Variables:**
- `company_ticker`: Uppercase (e.g., `ADANI`, `RELIANCE`)
- `fiscal_year`: Format `FY{YYYY}` (e.g., `FY2024`)
- `period`: `Q1`, `Q2`, `Q3`, `Q4`, or `Annual`
- `doc_type`: `balance_sheet`, `cash_flow`, `income_statement`

**Example:**
- `ADANI/FY2024/Q3/balance_sheet.pdf`
- `RELIANCE/FY2023/Annual/annual_report.pdf`

**RLS Policy:**
- **INSERT**: Authenticated users with `investigator` role.
- **SELECT**: Authenticated users with `investigator` role.
- **UPDATE/DELETE**: Admin only.

---

### 📂 `audio_recordings`

**Purpose:** Stores raw audio files for the Audio Agent.

**Path Convention:**
```
{company_ticker}/{fiscal_year}/{period}/{call_type}_{date}.{ext}
```

**Variables:**
- `call_type`: `earnings`, `analyst`, `agm`
- `date`: `YYYY-MM-DD`
- `ext`: `mp3`, `wav`, `m4a`

**Example:**
- `ADANI/FY2024/Q3/earnings_2024-10-15.mp3`

**RLS Policy:**
- **INSERT**: Authenticated users.
- **SELECT**: Backend service role ONLY (agents download via signed URL or service key).

---

## 3. Storage <-> Database Linkage

The `file_key` column in the database MUST match the full path in storage.

### `financial_filings` Table
- Column: `source_file_key`
- Value: `ADANI/FY2024/Q3/balance_sheet.pdf`

### `audio_files` Table
- Column: `file_key`
- Value: `ADANI/FY2024/Q3/earnings_2024-10-15.mp3`

---

## 4. Ingestion Workflow

1.  **Frontend**:
    - Uploads file to `temp_uploads/{uuid}/{filename}`.
    - Sends `investigation_request` with `context: { "temp_file_key": "..." }`.

2.  **Backend (Ingestion Worker)**:
    - Validates file type and size.
    - Moves file from `temp_uploads` to `financial_docs` or `audio_recordings` using the standard path convention.
    - Creates entry in `financial_filings` or `audio_files` table with the new `file_key`.
    - Triggers RAG processing (chunking + embedding).
