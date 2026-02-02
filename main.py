from fastapi import FastAPI
from routers.films_router import films_router
from routers.people_router import people_router
from routers.species_router import species_router
from routers.starships_router import starships_router
from routers.vehicles_router import vehicles_router

app = FastAPI()
app.include_router(people_router)
app.include_router(films_router)
app.include_router(people_router)
app.include_router(species_router)
app.include_router(vehicles_router)
app.include_router(starships_router)