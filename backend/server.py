import logging
import os
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from core.db import client
from routers import auth, jobs, units, vendors, movements, purchase_orders, board, issues, digest

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ShopTrack API")

api = APIRouter(prefix="/api")
api.include_router(auth.router)
api.include_router(jobs.router)
api.include_router(units.router)
api.include_router(vendors.router)
api.include_router(movements.router)
api.include_router(purchase_orders.router)
api.include_router(board.router)
api.include_router(issues.router)
api.include_router(digest.router)


@api.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client() -> None:
    client.close()
