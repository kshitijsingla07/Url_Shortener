from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from random import choice
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
import string
from dotenv import load_dotenv
import os

load_dotenv()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,  
    allow_methods=["*"],  
    allow_headers=["*"],  
)
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI) 
db = client.url_shortener
collection = db.urls

class URLRequest(BaseModel):
    original_url: str

class URLResponse(BaseModel):
    short_link: str
    original_url: str

def generate_short_link(length: int = 7):
    chars = string.ascii_letters + string.digits
    return ''.join(choice(chars) for _ in range(length))

@app.post("/shorten/", response_model=URLResponse)
def shorten_url(url_request: URLRequest):
    short_link = generate_short_link()

    while collection.find_one({"short_link": short_link}):
        short_link = generate_short_link()

    collection.insert_one({"short_link": short_link, "original_url": url_request.original_url})
    
    return {"short_link": short_link, "original_url": url_request.original_url}

@app.get("/{short_link}")
async def redirect_to_url(short_link: str):
    url_entry = collection.find_one({"short_link": short_link})
    
    if url_entry is None:
        raise HTTPException(status_code=404, detail="Short link not found")

    return RedirectResponse(url=url_entry["original_url"])
