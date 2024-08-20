from fastapi import FastAPI
from db.connector import *
from enums.country import Country

app = FastAPI()

@app.get("/")
async def root(
    day: str,
    country: Country,
    startTime: str,
    endTime: str,
    address: str,
):
    response = query(day, country, startTime, endTime, address)
    return response

@app.post("/chat")
async def chat_handler(
    histories: ChatMessages,
    query: str,
    country: Country,
):
    response = chat_query(histories, query, country)
    return response