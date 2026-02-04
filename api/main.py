from fastapi import FastAPI
from api.routes import health, investigate

app = FastAPI(title="Sathya Nishta API")

app.include_router(health.router)
app.include_router(investigate.router)
