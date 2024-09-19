from fastapi import FastAPI
from app.api import router as api_router
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# from app.db.redis import connect_redis

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# @app.on_event("startup")
# async def startup_event():
#     # Connect to Redis on startup
#     await connect_redis()


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Contact List API!"}
