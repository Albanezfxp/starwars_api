import time
from typing import Any

import requests
from fastapi import APIRouter, HTTPException

planets_router = APIRouter(prefix="/planets", tags= ["Planets"])
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

@planets_router.get("/")
async def find_all_planets():
    data = _get_json_cached('https://swapi.dev/api/planets')

    planet_list_response = []

    for planet in data.get("results", []):
        residents_list = []
        films_list = []

        for films in planet["films"]:
            data_film = _get_json_cached(films)
            films_list.append({
                'film_title': data_film["title"],
                'episode': data_film["episode_id"],
                'date': data_film["release_date"]
            })

        for residents in planet["residents"]:
            data_residents = _get_json_cached(residents)
            residents_list.append({
            "name": data_residents["name"],
            "gender": data_residents["gender"]
            })

        planet_list_response.append({
            "name": planet["name"],
            "rotation_period": planet["rotation_period"],
            "climate": planet["climate"],
            "gravity": planet["gravity"],
            "terrain": planet["terrain"],
            "population": planet["population"],
            "residents": residents_list,
            "films": films_list
        })

    return planet_list_response

@planets_router.get("/{id}")
async def get_one_planet(id: int):
    data = _get_json_cached(f'https://swapi.dev/api/planets/{id}')

    residents_list = []
    films_list = []

    for films in data["films",[]]:
        data_film = _get_json_cached(films)
        films_list.append({
            'film_title': data_film["title"],
            'episode': data_film["episode_id"],
            'date': data_film["release_date"]
        })

    for residents in data["residents", []]:
        data_residents = _get_json_cached(residents)
        residents_list.append({
            "name": data_residents["name"],
            "gender": data_residents["gender"]
        })

    return {
        "name": data["name"],
        "rotation_period": data["rotation_period"],
        "climate": data["climate"],
        "gravity": data["gravity"],
        "terrain": data["terrain"],
        "population": data["population"],
        "residents": residents_list,
        "films": films_list
    }