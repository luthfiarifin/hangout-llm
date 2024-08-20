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