import logging
import os
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models as models

from app.routers import analytics, expenses, groups, users

import app.log_config as log_config


logger = logging.getLogger(__name__)

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

    log_config.setup_logging()

    logger.info("Database migrations applied successfully")
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