from fastapi import FastAPI
from db.connector import *
from enums.country import Country

app = FastAPI()

@app.get("/")
async def root(
    date: str,
    country: Country,
    startTime: str,
    endTime: str,
    address: str,
    lat: float,
    lon: float,
):
    response = query(date, country, startTime, endTime, address, lat, lon)
    return response

@app.post("/chat")
async def chat_handler(
    histories: ChatMessages,
    query: str,
    date: str,
    country: Country,
    startTime: str,
    endTime: str,
    address: str,
):
    response = chat_query(histories, query, date, country, startTime, endTime, address)
    return response