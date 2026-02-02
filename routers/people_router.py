import time
from typing import Any

from fastapi import APIRouter, HTTPException
import requests

people_router = (
    APIRouter(prefix="/peoples", tags=["Peoples"]))

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
@people_router.get("/")
def all_people():
    how_time = time.time()
    data = _get_json_cached("https://swapi.dev/api/people")

    peoples_response = []
    for person in data.get("results", []):
        peoples_films = []
        homeworld_data = _get_json_cached(person["homeworld"])
        if person["species"]:
            specie_data = _get_json_cached(person["species"][0])
        else:
            specie_data = {'name': "Human"}

        for films in person["films"]:
            data_films = _get_json_cached(films)
            peoples_films.append({
                "title": data_films.get("title"),
                "date": data_films.get("release_date")
            })

        peoples_response.append(
            {
                "name": person["name"],
                "home_world": homeworld_data.get("name"),
                "specie": specie_data.get("name"),
                "films": peoples_films,
                "url": person["url"]
            }

        )

    return {"response": peoples_response, 'time': round(time.time() - how_time, 3) }

@people_router.get("/{id}")
async def people_by_id(id: int):
    data = _get_json_cached(f"https://swapi.dev/api/people/{id}")
    homeworld_data = _get_json_cached(data["homeworld"])

    people_films = []
    starships_list = []
    vehicles_list = []

    if data["species"]:
        specie_data = _get_json_cached(data["species"][0])
    else:
        specie_data = {"name": "Human"}

    if data["starships"]:
        for starships in data["starships"]:
            data_starships = _get_json_cached(starships)
            starships_list.append({
                'name': data_starships["name"],
                'model': data_starships['model']
            })
    else:
        starships_list.append({"message": "Not have starships..."})

    if data["vehicles"]:
        for vehicles in data["vehicles"]:
            data_vehicles = _get_json_cached(vehicles)
            vehicles_list.append({
                'name': data_vehicles["name"],
                'model': data_vehicles['model']
            })
    else:
        vehicles_list.append({"message":"Not have vehicles..."})

    for films in data["films"]:
        data_films = _get_json_cached(films)
        people_films.append({
            "title": data_films.get("title"),
            "date": data_films.get("release_date")
        })

    return {
        "name": data["name"],
        "home_world": homeworld_data.get("name"),
        "specie": specie_data.get("name"),
        "films": people_films,
        "starships": starships_list,
        "vehicles": vehicles_list,
        "url": data["url"]
    }
