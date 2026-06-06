from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import app.models as models

from app.routers import users, groups, expenses, analytics

#lifecycle manager
#before yield - At startup
#after yield - At shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    models.create_db_and_table()
    yield

app = FastAPI(lifespan= lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(groups.router)
app.include_router(expenses.router)
app.include_router(analytics.router)

@app.get('/')
async def home():
    return{"message": "welcome"}