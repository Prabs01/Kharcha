from contextlib import asynccontextmanager
from fastapi import FastAPI
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

app.include_router(users.router)
app.include_router(groups.router)
app.include_router(expenses.router)
app.include_router(analytics.router)
app.include_router(analytics.router)

@app.get('/')
async def home():
    return{"message": "welcome"}




