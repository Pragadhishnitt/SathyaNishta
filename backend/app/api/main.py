from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.email_routes import router as email_router
from app.api.routes.investigate import router as investigate_router
from app.api.routes.chat import router as chat_router
from app.api.routes.report import router as report_router
from app.api.routes.market_data import router as market_data_router
from app.api.routes.generate_brief import router as generate_brief_router
from app.api.routes.extract_entities import router as extract_entities_router
from app.api.routes.compare import router as compare_router
from app.api.routes.chat_persistence import router as chat_persistence_router

app = FastAPI(
    title="MarketChatGPT API",
    description="Next-gen AI Financial Intelligence",
    version="0.2.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health_router)
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(email_router, prefix="/api/email", tags=["email"])
app.include_router(chat_router, prefix="/api")
app.include_router(investigate_router, prefix="/api")
app.include_router(report_router, prefix="/api")
app.include_router(generate_brief_router, prefix="/api")
app.include_router(extract_entities_router, prefix="/api")
app.include_router(market_data_router)
app.include_router(compare_router)
app.include_router(chat_persistence_router, prefix="/api/persistence", tags=["chat-persistence"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
