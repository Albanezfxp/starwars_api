import time
from typing import Any
import requests
from fastapi import APIRouter, HTTPException

starships_router = APIRouter(prefix="/starships", tags=["Starships"])

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


@starships_router.get("/")
async def get_all_starships():
    data = _get_json_cached("https://swapi.dev/api/starships/")

    starships_list_response = []

    for starship in data.get("results", []):
        pilots_list = []
        films_list = []

        for pilot in starship["pilots"]:
            pilot_data = _get_json_cached(pilot)

            pilots_list.append({
                "name": pilot_data["name"],
                "gender": pilot_data["gender"],
                "birth_year": pilot_data["birth_year"]
            })

        for film in starship["films"]:
            film_data = _get_json_cached(film)

            films_list.append({
                "film_title": film_data["title"],
                "episode": film_data["episode_id"],
                "date": film_data["release_date"]
            })

        starships_list_response.append({
            "name": starship["name"],
            "model": starship["model"],
            "manufacturer": starship["manufacturer"],
            "cost_in_credits": starship["cost_in_credits"],
            "length": starship["length"],
            "crew": starship["crew"],
            "passengers": starship["passengers"],
            "starship_class": starship["starship_class"],
            "pilots": pilots_list,
            "films": films_list,
        })

    return starships_list_response


@starships_router.get("/{id}")
async def get_by_id(id: int):
    data = _get_json_cached(f"https://swapi.dev/api/starships/{id}")

    pilots_list = []
    films_list = []

    for pilot in data["pilots"]:
        pilot_data = _get_json_cached(pilot)

        pilots_list.append({
            "name": pilot_data["name"],
            "gender": pilot_data["gender"],
            "birth_year": pilot_data["birth_year"]
        })

    for film in data["films"]:
        film_data = _get_json_cached(film)

        films_list.append({
            "film_title": film_data["title"],
            "episode": film_data["episode_id"],
            "date": film_data["release_date"]
        })

    return {
        "name": data["name"],
        "model": data["model"],
        "manufacturer": data["manufacturer"],
        "cost_in_credits": data["cost_in_credits"],
        "length": data["length"],
        "crew": data["crew"],
        "passengers": data["passengers"],
        "starship_class": data["starship_class"],
        "pilots": pilots_list,
        "films": films_list,
    }
