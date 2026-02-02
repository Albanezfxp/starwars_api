import time
from typing import Any
import requests
from fastapi import APIRouter, HTTPException

species_router = APIRouter(prefix="/species", tags=["Species"])

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

@species_router.get('/')
async def get_all_species():
    data = _get_json_cached('https://swapi.dev/api/species/')

    species_list_response = []

    for specie in data["results", []]:
        people_list = []
        films_list = []
        homeworld_data  = _get_json_cached(specie["homeworld"])

        for people in specie['people']:
            people_data = _get_json_cached(people)

            people_list.append({
                'name': people_data["name"],
                "gender": people_data["gender"],
                "skin_color": people_data['skin_color']
            })
        for films in specie["films"]:
            films_data = _get_json_cached(films)

            films_list.append({
                'film_title': films_data["title"],
                'episode': films_data["episode_id"],
                'date': films_data["release_date"]
            })

        species_list_response.append({
            "name": specie["name"],
            "classification": specie["classification"],
            "average_lifespan": specie["average_lifespan"],
            "designation": specie["designation"],
            "skin_colors": specie["skin_colors"],
            "home_world": homeworld_data.get("name"),
            "language": specie["language"],
            "peoples": people_list,
            "films": films_list,
        })
    return species_list_response

@species_router.get("/{id}")
async def get_by_id(id: int):
    data = _get_json_cached(f"https://swapi.dev/api/species/{id}")

    people_list = []
    films_list = []

    homeworld_data = _get_json_cached(data["homeworld"])

    for people in data["people"]:
        people_data = _get_json_cached(people)

        people_list.append({
            "name": people_data["name"],
            "gender": people_data["gender"],
            "skin_color": people_data["skin_color"]
        })

    for films in data["films"]:
        films_data = _get_json_cached(films)

        films_list.append({
            "film_title": films_data["title"],
            "episode": films_data["episode_id"],
            "date": films_data["release_date"]
        })

    return {
        "name": data["name"],
        "classification": data["classification"],
        "average_lifespan": data["average_lifespan"],
        "designation": data["designation"],
        "skin_colors": data["skin_colors"],
        "home_world": homeworld_data.get("name"),
        "language": data["language"],
        "peoples": people_list,
        "films": films_list,
    }
