# main.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from routers.films_router import films_router
from routers.people_router import people_router
from routers.planets_router import planets_router
from routers.species_router import species_router
from routers.starships_router import starships_router
from routers.vehicles_router import vehicles_router

app = FastAPI()

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    api_key = os.getenv("API_KEY")  # se não existir, auth fica desligada
    if api_key:
        sent = request.headers.get("x-api-key")
        if sent != api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"},
            )
    return await call_next(request)

app.include_router(people_router)
app.include_router(films_router)
app.include_router(planets_router)
app.include_router(species_router)
app.include_router(vehicles_router)
app.include_router(starships_router)
