import time
from typing import Any
import requests
from fastapi import APIRouter, HTTPException

vehicles_router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

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


@vehicles_router.get("/")
async def get_all_vehicles():
    data = _get_json_cached("https://swapi.dev/api/vehicles/")

    vehicles_list_response = []

    for vehicle in data.get("results", []):
        pilots_list = []
        films_list = []

        for pilot in vehicle["pilots"]:
            pilot_data = _get_json_cached(pilot)

            pilots_list.append({
                "name": pilot_data["name"],
                "gender": pilot_data["gender"],
                "birth_year": pilot_data["birth_year"]
            })

        for film in vehicle["films"]:
            film_data = _get_json_cached(film)

            films_list.append({
                "film_title": film_data["title"],
                "episode": film_data["episode_id"],
                "date": film_data["release_date"]
            })

        vehicles_list_response.append({
            "name": vehicle["name"],
            "model": vehicle["model"],
            "manufacturer": vehicle["manufacturer"],
            "cost_in_credits": vehicle["cost_in_credits"],
            "length": vehicle["length"],
            "crew": vehicle["crew"],
            "passengers": vehicle["passengers"],
            "vehicle_class": vehicle["vehicle_class"],
            "pilots": pilots_list,
            "films": films_list,
        })

    return vehicles_list_response


@vehicles_router.get("/{id}")
async def get_by_id(id: int):
    data = _get_json_cached(f"https://swapi.dev/api/vehicles/{id}")

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
        "vehicle_class": data["vehicle_class"],
        "pilots": pilots_list,
        "films": films_list,
    }
