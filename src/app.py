from fastapi import FastAPI

from src.config import get_settings

app = FastAPI()



@app.get("/")
def read_root():
    return {"hello": "world"}