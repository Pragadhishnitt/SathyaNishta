import yfinance as yf
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio

router = APIRouter(prefix="/api/market", tags=["market"])


class MarketDataResponse(BaseModel):
    nifty: dict
    sensex: dict


def fetch_ticker_data(symbol):
    """Fetch ticker data with timeout"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "price": info.get("currentPrice") or info.get("regularMarketPrice", 0),
            "change": info.get("regularMarketChange", 0),
            "changePercent": info.get("regularMarketChangePercent", 0)
        }
    except Exception as e:
        print(f"Error fetching {symbol}: {str(e)}")
        return {"price": 0, "change": 0, "changePercent": 0}


@router.get("/indices", response_model=MarketDataResponse)
async def get_market_indices():
    """Fetch NIFTY 50 and SENSEX data using yfinance"""
    try:
        print("Starting market data fetch...")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        nifty_task = loop.run_in_executor(None, fetch_ticker_data, "^NSEI")
        sensex_task = loop.run_in_executor(None, fetch_ticker_data, "^BSESN")
        
        nifty_quote = await asyncio.wait_for(nifty_task, timeout=15.0)
        sensex_quote = await asyncio.wait_for(sensex_task, timeout=15.0)
        
        print(f"NIFTY: {nifty_quote}")
        print(f"SENSEX: {sensex_quote}")
        
        return MarketDataResponse(
            nifty=nifty_quote,
            sensex=sensex_quote
        )
    
    except asyncio.TimeoutError:
        print("Timeout fetching market data")
        raise HTTPException(status_code=504, detail="Market data fetch timeout")
    except Exception as e:
        print(f"Error fetching market data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching market data: {str(e)}")
