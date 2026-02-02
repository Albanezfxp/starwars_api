import time
from typing import Any

from fastapi import APIRouter, HTTPException
import requests


films_router = APIRouter(prefix="/films", tags=["Films"])


_CACHE: dict[str, tuple[float, Any]] = {}
CACHE_TTL_SECONDS = 60
def _get_json_cached(url: str, ttl: int = CACHE_TTL_SECONDS) -> Any:
    now = time.time()

    cached = _CACHE.get(url)
    if cached:
        expires_at, value = cached
        if now < expires_at:
            return value
        else:
            _CACHE.pop(url, None)
    try:
        resp = requests.get(url, timeout=10)
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Upstream request failed")

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Resource not found")
    if resp.status_code >= 400:
        raise HTTPException(status_code=502)

    data = resp.json()
    _CACHE[url] = (now + ttl, data)
    return data

@films_router.get("/")
async def all_films():
    data = _get_json_cached("https://swapi.dev/api/films/")

    films_response = []

    for films in data.get("results", []):
        persons_list = []
        planet_list = []
        starships_list = []
        vehicles_list = []
        species_list = []
        for persons in films["characters"]:
            data_persons = _get_json_cached(persons)
            persons_list.append({"name": data_persons["name"]})

        for planet in films["planets"]:
            data_planets = _get_json_cached(planet)
            planet_list.append({'name': data_planets["name"]})

        for starships in films["starships"]:
            data_starships = _get_json_cached(starships)
            starships_list.append({"name": data_starships["name"]})

        for vehicles in films["vehicles"]:
            data_vehicles = _get_json_cached(vehicles)
            vehicles_list.append({'name': data_vehicles["name"]})

        for species in films["species"]:
            data_species = _get_json_cached(species)
            species_list.append({"name": data_species["name"]})

        films_response.append(
            {
            "title": films["title"],
            'episode': films["episode_id"],
            "description": films["opening_crawl"],
            "director": films["director"],
            "producer": films["producer"],
            "persons": persons_list,
            "planets": planet_list,
            "vehicles": vehicles_list,
            "species": species_list,
            "url": films["url"]
            }
        )
    return {"response": films_response}

@films_router.get("/{id}")
async def get_by_id(id: int):
    data = _get_json_cached(f"https://swapi.dev/api/films/{id}/")

    persons_list = []
    planet_list = []
    starships_list = []
    vehicles_list = []
    species_list = []
    for persons in data["characters"]:
            data_persons = _get_json_cached(persons)
            persons_list.append({"name": data_persons["name"]})

    for planet in data["planets"]:
        data_planets = _get_json_cached(planet)
        planet_list.append({'name': data_planets["name"]})

    for starships in data["starships"]:
        data_starships = _get_json_cached(starships)
        starships_list.append({"name": data_starships["name"]})

    for vehicles in data["vehicles"]:
        data_vehicles = _get_json_cached(vehicles)
        vehicles_list.append({'name': data_vehicles["name"]})

    for species in data["species"]:
        data_species = _get_json_cached(species)
        species_list.append({"name": data_species["name"]})

    return {"response": {
        "title": data["title"],
        'episode': data["episode_id"],
        "description": data["opening_crawl"],
        "director": data["director"],
        "producer": data["producer"],
        "persons": persons_list,
        "planets": planet_list,
        "vehicles": vehicles_list,
        "species": species_list,
        "url": data["url"]}}
