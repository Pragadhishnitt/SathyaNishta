#!/usr/bin/env python3
"""
Seed Structured Financial Data for new companies
Inserts balance sheet and cash flow data into financial_filings table
"""

import sys
import json
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add repo to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from sqlalchemy import create_engine, text
from sqlmodel import Session
from app.core.config import settings
from app.shared.logger import setup_logger

logger = setup_logger("SeedFinancialData")

engine = create_engine(settings.DATABASE_URL)

# Financial data for 5 new companies
COMPANIES_DATA = [
    {
        "name": "AlphaTech Solutions",
        "code": "ATS",
        "ticker": "ATS",
        "balance_sheet": {
            "total_assets": 120000,
            "total_liabilities": 70000,
            "equity": 50000,
            "debt": 40000,
            "cash": 5000,
            "ebitda": 18000,
            "current_assets": 45000,
            "current_liabilities": 30000,
        },
        "cash_flow": {
            "operating_cash_flow": 15000,
            "investing_cash_flow": -8000,
            "financing_cash_flow": 2000,
            "net_cash_change": 9000,
        },
        "ratios": {
            "debt_to_equity": 0.8,
            "current_ratio": 1.5,
            "ebitda_margin": 0.15,
            "roe": 0.36,
        }
    },
    {
        "name": "GreenField Retail",
        "code": "GFR",
        "ticker": "GFR",
        "balance_sheet": {
            "total_assets": 90000,
            "total_liabilities": 65000,
            "equity": 25000,
            "debt": 42000,
            "cash": 3000,
            "ebitda": 8000,
            "current_assets": 35000,
            "current_liabilities": 28000,
        },
        "cash_flow": {
            "operating_cash_flow": 7000,
            "investing_cash_flow": -5000,
            "financing_cash_flow": 1000,
            "net_cash_change": 3000,
        },
        "ratios": {
            "debt_to_equity": 1.68,
            "current_ratio": 1.25,
            "ebitda_margin": 0.089,
            "roe": 0.32,
        }
    },
    {
        "name": "Urban Infra Ltd",
        "code": "UIL",
        "ticker": "UIL",
        "balance_sheet": {
            "total_assets": 150000,
            "total_liabilities": 130000,
            "equity": 20000,
            "debt": 100000,
            "cash": 2000,
            "ebitda": 9000,
            "current_assets": 25000,
            "current_liabilities": 35000,
        },
        "cash_flow": {
            "operating_cash_flow": 8000,
            "investing_cash_flow": -12000,
            "financing_cash_flow": 5000,
            "net_cash_change": 1000,
        },
        "ratios": {
            "debt_to_equity": 5.0,
            "current_ratio": 0.71,
            "ebitda_margin": 0.06,
            "roe": 0.45,
        }
    },
    {
        "name": "NextGen Pharma",
        "code": "NGP",
        "ticker": "NGP",
        "balance_sheet": {
            "total_assets": 80000,
            "total_liabilities": 50000,
            "equity": 30000,
            "debt": 20000,
            "cash": 4000,
            "ebitda": 11000,
            "current_assets": 30000,
            "current_liabilities": 18000,
        },
        "cash_flow": {
            "operating_cash_flow": 10000,
            "investing_cash_flow": -4000,
            "financing_cash_flow": 0,
            "net_cash_change": 6000,
        },
        "ratios": {
            "debt_to_equity": 0.67,
            "current_ratio": 1.67,
            "ebitda_margin": 0.1375,
            "roe": 0.37,
        }
    },
    {
        "name": "SkyHigh Aviation",
        "code": "SHA",
        "ticker": "SHA",
        "balance_sheet": {
            "total_assets": 110000,
            "total_liabilities": 100000,
            "equity": 10000,
            "debt": 85000,
            "cash": 1500,
            "ebitda": 5000,
            "current_assets": 15000,
            "current_liabilities": 25000,
        },
        "cash_flow": {
            "operating_cash_flow": 4000,
            "investing_cash_flow": -6000,
            "financing_cash_flow": 2000,
            "net_cash_change": 0,
        },
        "ratios": {
            "debt_to_equity": 8.5,
            "current_ratio": 0.6,
            "ebitda_margin": 0.045,
            "roe": 0.5,
        }
    },
]

def seed_financial_data():
    """Insert balance sheet, cash flow, and ratio data for new companies"""
    
    print("\n" + "="*80)
    print("SEEDING STRUCTURED FINANCIAL DATA FOR NEW COMPANIES")
    print("="*80)
    
    with Session(engine) as session:
        # Clear existing data
        print("\n🧹 Clearing existing financial_filings for new companies...")
        session.execute(text("DELETE FROM financial_filings WHERE company_name IN ('AlphaTech Solutions', 'GreenField Retail', 'Urban Infra Ltd', 'NextGen Pharma', 'SkyHigh Aviation')"))
        session.commit()
        print("   ✓ Cleared")
        
        total_inserted = 0
        
        for company in COMPANIES_DATA:
            company_name = company["name"]
            company_code = company["code"]
            company_ticker = company["ticker"]
            
            print(f"\n🏢 Processing: {company_name} ({company_code})")
            print("-" * 80)
            
            # 1. Balance Sheet
            bs_content = f"""
Balance Sheet - {company_name} (FY2024)

ASSETS:
- Total Assets: ₹{company['balance_sheet']['total_assets']:,}
- Current Assets: ₹{company['balance_sheet']['current_assets']:,}
- Cash and equivalents: ₹{company['balance_sheet']['cash']:,}

LIABILITIES:
- Total Liabilities: ₹{company['balance_sheet']['total_liabilities']:,}
- Current Liabilities: ₹{company['balance_sheet']['current_liabilities']:,}
- Debt: ₹{company['balance_sheet']['debt']:,}

EQUITY:
- Total Equity: ₹{company['balance_sheet']['equity']:,}

PROFITABILITY:
- EBITDA: ₹{company['balance_sheet']['ebitda']:,}
"""
            
            session.execute(
                text("""
                    INSERT INTO financial_filings (id, company_name, company_ticker, period, doc_type, content_chunk, metadata)
                    VALUES (:id, :name, :ticker, :period, :doc_type, :content, :meta)
                """),
                {
                    "id": str(uuid4()),
                    "name": company_name,
                    "ticker": company_ticker,
                    "period": "FY2024",
                    "doc_type": "balance_sheet",
                    "content": bs_content,
                    "meta": json.dumps({"source": "seed_script", "company_code": company_code})
                }
            )
            print("  ✓ Balance sheet inserted")
            total_inserted += 1
            
            # 2. Cash Flow Statement
            cf_content = f"""
Cash Flow Statement - {company_name} (FY2024)

OPERATING ACTIVITIES:
- Net cash from operations: ₹{company['cash_flow']['operating_cash_flow']:,}

INVESTING ACTIVITIES:
- Net cash from investing: ₹{company['cash_flow']['investing_cash_flow']:,}

FINANCING ACTIVITIES:
- Net cash from financing: ₹{company['cash_flow']['financing_cash_flow']:,}

NET CHANGE IN CASH:
- Net change: ₹{company['cash_flow']['net_cash_change']:,}
"""
            
            session.execute(
                text("""
                    INSERT INTO financial_filings (id, company_name, company_ticker, period, doc_type, content_chunk, metadata)
                    VALUES (:id, :name, :ticker, :period, :doc_type, :content, :meta)
                """),
                {
                    "id": str(uuid4()),
                    "name": company_name,
                    "ticker": company_ticker,
                    "period": "FY2024",
                    "doc_type": "cash_flow",
                    "content": cf_content,
                    "meta": json.dumps({"source": "seed_script", "company_code": company_code})
                }
            )
            print("  ✓ Cash flow statement inserted")
            total_inserted += 1
            
            # 3. Financial Ratios
            ratios_content = f"""
Financial Ratios Analysis - {company_name} (FY2024)

LEVERAGE RATIOS:
- Debt-to-Equity: {company['ratios']['debt_to_equity']:.2f}x
- Debt-to-Assets: {company['balance_sheet']['debt'] / company['balance_sheet']['total_assets']:.2%}

LIQUIDITY RATIOS:
- Current Ratio: {company['ratios']['current_ratio']:.2f}x
- Quick Ratio: {(company['balance_sheet']['current_assets'] - 10000) / company['balance_sheet']['current_liabilities']:.2f}x

PROFITABILITY RATIOS:
- EBITDA Margin: {company['ratios']['ebitda_margin']:.2%}
- Return on Equity (ROE): {company['ratios']['roe']:.2%}
- Asset Turnover: {company['cash_flow']['operating_cash_flow'] / company['balance_sheet']['total_assets']:.2f}x

EFFICIENCY METRICS:
- Cash Flow to Debt: {company['cash_flow']['operating_cash_flow'] / company['balance_sheet']['debt']:.2%}
"""
            
            session.execute(
                text("""
                    INSERT INTO financial_filings (id, company_name, company_ticker, period, doc_type, content_chunk, metadata)
                    VALUES (:id, :name, :ticker, :period, :doc_type, :content, :meta)
                """),
                {
                    "id": str(uuid4()),
                    "name": company_name,
                    "ticker": company_ticker,
                    "period": "FY2024",
                    "doc_type": "financial_ratios",
                    "content": ratios_content,
                    "meta": json.dumps({"source": "seed_script", "company_code": company_code})
                }
            )
            print("  ✓ Financial ratios inserted")
            total_inserted += 1
            
            # 4. Consolidated Financial Statements
            consolidated_content = f"""
Consolidated Financial Statements - {company_name} (FY2024)

BALANCE SHEET (Consolidated):
- Total Assets: ₹{company['balance_sheet']['total_assets']:,}
- Total Liabilities: ₹{company['balance_sheet']['total_liabilities']:,}
- Total Equity: ₹{company['balance_sheet']['equity']:,}
- Current Assets: ₹{company['balance_sheet']['current_assets']:,}
- Current Liabilities: ₹{company['balance_sheet']['current_liabilities']:,}

PROFITABILITY & OPERATIONS (Consolidated):
- EBITDA: ₹{company['balance_sheet']['ebitda']:,}
- Operating Cash Flow: ₹{company['cash_flow']['operating_cash_flow']:,}
- Cash & Equivalents: ₹{company['balance_sheet']['cash']:,}

FINANCIAL POSITION (Consolidated):
- Total Debt: ₹{company['balance_sheet']['debt']:,}
- Debt-to-Equity Ratio: {company['ratios']['debt_to_equity']:.2f}x
- Current Ratio: {company['ratios']['current_ratio']:.2f}x
- ROE: {company['ratios']['roe']:.2%}

CONSOLIDATED CASH POSITION:
- Net Change in Cash (FY2024): ₹{company['cash_flow']['net_cash_change']:,}
- Operating Activities: ₹{company['cash_flow']['operating_cash_flow']:,}
- Investing Activities: ₹{company['cash_flow']['investing_cash_flow']:,}
- Financing Activities: ₹{company['cash_flow']['financing_cash_flow']:,}
"""
            
            session.execute(
                text("""
                    INSERT INTO financial_filings (id, company_name, company_ticker, period, doc_type, content_chunk, metadata)
                    VALUES (:id, :name, :ticker, :period, :doc_type, :content, :meta)
                """),
                {
                    "id": str(uuid4()),
                    "name": company_name,
                    "ticker": company_ticker,
                    "period": "FY2024",
                    "doc_type": "consolidated",
                    "content": consolidated_content,
                    "meta": json.dumps({"source": "seed_script", "company_code": company_code})
                }
            )
            print("  ✓ Consolidated statements inserted")
            total_inserted += 1
        
        session.commit()
    
    print("\n" + "="*80)
    print(f"✅ SEEDING COMPLETE")
    print(f"   Total records inserted: {total_inserted}")
    print(f"   Companies: {len(COMPANIES_DATA)} (5 new companies)")
    print(f"   Doc types per company: 4 (balance_sheet, cash_flow, financial_ratios, consolidated)")
    print(f"   Expected total rows: {len(COMPANIES_DATA)} × 4 = 20 rows")
    print("="*80)

if __name__ == "__main__":
    seed_financial_data()
