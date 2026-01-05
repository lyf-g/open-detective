from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Open-Detective API",
    description="Backend for Open-Detective: An AI-powered OSS governance tool.",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"message": "Open-Detective Backend is running!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
