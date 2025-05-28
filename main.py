from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import router 
from typing import List

app = FastAPI(title="Asset Market API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
