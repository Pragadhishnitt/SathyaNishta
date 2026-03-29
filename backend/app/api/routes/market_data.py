import asyncio

import yfinance as yf
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

router = APIRouter(prefix="/api/market", tags=["market"])


class MarketDataResponse(BaseModel):
    nifty: dict
    sensex: dict


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
def fetch_ticker_data(symbol):
    """Fetch ticker data with timeout"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "price": info.get("currentPrice") or info.get("regularMarketPrice", 0),
            "change": info.get("regularMarketChange", 0),
            "changePercent": info.get("regularMarketChangePercent", 0),
        }
    except Exception as e:
        print(f"Error fetching {symbol}: {str(e)}")
        return {"price": 0, "change": 0, "changePercent": 0}


# Simple in-memory cache
_cache = {"data": None, "timestamp": 0}
_cache_lock = asyncio.Lock()
CACHE_TTL = 5  # seconds


@router.get("/indices", response_model=MarketDataResponse)
async def get_market_indices():
    """Fetch NIFTY 50 and SENSEX data using yfinance with caching"""
    # FIX: removed `global _cache` — it was flagged by F824 because _cache is never
    # reassigned here, only mutated (dict key updates). `global` is only needed
    # when you do `_cache = something_new`, not when you do `_cache["key"] = value`.
    async with _cache_lock:
        now = asyncio.get_event_loop().time()
        if _cache["data"] and (now - _cache["timestamp"]) < CACHE_TTL:
            return _cache["data"]

    try:
        print("Starting market data fetch...")
        loop = asyncio.get_event_loop()
        nifty_task = loop.run_in_executor(None, fetch_ticker_data, "^NSEI")
        sensex_task = loop.run_in_executor(None, fetch_ticker_data, "^BSESN")

        nifty_quote = await asyncio.wait_for(nifty_task, timeout=15.0)
        sensex_quote = await asyncio.wait_for(sensex_task, timeout=15.0)

        print(f"NIFTY: {nifty_quote}")
        print(f"SENSEX: {sensex_quote}")

        res = MarketDataResponse(nifty=nifty_quote, sensex=sensex_quote)

        async with _cache_lock:
            _cache["data"] = res
            _cache["timestamp"] = asyncio.get_event_loop().time()

        return res

    except asyncio.TimeoutError:
        print("Timeout fetching market data")
        raise HTTPException(status_code=504, detail="Market data fetch timeout")
    except Exception as e:
        print(f"Error fetching market data: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching market data: {str(e)}"
        )
