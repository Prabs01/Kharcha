from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import app.models as models

from app.routers import users, groups, expenses, analytics

from alembic.config import Config
from alembic import command

import os


#lifecycle manager
#before yield - At startup
#after yield - At shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    models.create_db_and_table()
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
    ROOT_DIR = os.path.dirname(BASE_DIR)               
    
    alembic_cfg = Config(os.path.join(ROOT_DIR, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(ROOT_DIR, "migrations"))

    command.upgrade(alembic_cfg, "head")
    yield

app = FastAPI(lifespan= lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ORIGIN", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(groups.router)
app.include_router(expenses.router)
app.include_router(analytics.router)

@app.get("/")
def health():
    return {"status": "ok"}