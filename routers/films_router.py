import time
from typing import Any, Literal

import requests
from fastapi import APIRouter, HTTPException, Query

films_router = APIRouter(prefix="/films", tags=["Films"])
SWAPI_BASE_URL = "https://swapi.dev/api"

_CACHE: dict[str, tuple[float, Any]] = {}
CACHE_TTL_SECONDS = 60


def _get_json_cached(url: str, ttl: int = CACHE_TTL_SECONDS) -> Any:
    now = time.time()

    cached = _CACHE.get(url)
    if cached:
        expires_at, value = cached
        if now < expires_at:
            return value
        _CACHE.pop(url, None)

    try:
        resp = requests.get(url, timeout=10)
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Upstream request failed")

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Resource not found")
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail="Upstream returned error")

    data = resp.json()
    _CACHE[url] = (now + ttl, data)
    return data


def _split_csv(value: str | None) -> set[str]:
    if not value:
        return set()
    return {v.strip() for v in value.split(",") if v.strip()}


def _normalize_str(v: Any) -> str:
    return str(v or "").strip().lower()

def _apply_local_filter(items: list[dict], q: str | None, field: str = "name") -> list[dict]:
    if not q:
        return items

    q_norm = q.strip().lower()
    if not q_norm:
        return items

    out: list[dict] = []
    for it in items:
        value = it.get(field)
        if isinstance(value, str) and q_norm in value.lower():
            out.append(it)
    return out
def _apply_sort(
    items: list[dict[str, Any]],
    sort: str | None,
    order: Literal["asc", "desc"],
    allowed_fields: set[str],
) -> list[dict[str, Any]]:
    if not sort:
        return items

    if sort not in allowed_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort field '{sort}'. Allowed: {sorted(allowed_fields)}",
        )

    reverse = order == "desc"

    def key_fn(x: dict[str, Any]):
        value = x.get(sort)
        return (value is None, str(value).lower() if value is not None else "")

    return sorted(items, key=key_fn, reverse=reverse)


def _paginate(items: list[dict[str, Any]], page: int, limit: int) -> list[dict[str, Any]]:
    start = (page - 1) * limit
    end = start + limit
    return items[start:end]


def _fetch_many(urls: list[str]) -> list[dict[str, Any]]:
    return [_get_json_cached(u) for u in urls if isinstance(u, str)]


def _pick_species(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specie = []

    for item in items:
        if not isinstance(item, dict):
            continue

        homeworld_name = None
        homeworld_url = item.get("homeworld")

        if homeworld_url:
            homeworld_data = _get_json_cached(homeworld_url)
            homeworld_name = homeworld_data.get("name")

        specie.append({
            "name": item.get("name"),
            "classification": item.get("classification"),
            "designation": item.get("designation"),
            "homeworld": homeworld_name
        })

    return  specie



def _pick_vehicles(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    vehicle = []

    for item in items:
        if not isinstance(item, dict):
            continue
        vehicle.append({
            "name": item.get("name"),
            "model": item.get("model")
        })

    return vehicle

def _pick_starships(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    starship = []

    for item in items:
        if not isinstance(item, dict):
            continue

        starship.append({
            "name": item.get("name"),
            "model": item.get("model"),
        })

    return starship

def _pick_planet(items: list[dict[str, Any]]) -> list[dict[str,Any]]:
    planet = []

    for item in items:
        if not isinstance(item, dict):
            continue

        planet.append({
            "name": item.get("name"),
            "year_duration":"{} days".format(item.get("orbital_period")),
            "climate": item.get("climate"),
            "population": item.get("population")
        })

    return planet

def _pick_people(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    people = []

    for item in items:
        if not isinstance(item, dict):
            continue

        homeworld_name = None
        homeworld_url = item.get("homeworld")

        if homeworld_url:
            homeworld_data = _get_json_cached(homeworld_url)
            homeworld_name = homeworld_data.get("name")

        people.append({
            "name": item.get("name"),
            "gender": item.get("gender"),
            "homeworld": homeworld_name
        })

    return people

def _expand_film(film: dict[str, Any], expand: set[str]) -> dict[str, Any]:
    expanded = dict(film)

    if "characters" in expand:
        characters = _fetch_many(film.get("characters") or [])
        expanded["characters"] = _pick_people(characters)

    if "planets" in expand:
        planets = _fetch_many(film.get("planets") or [])
        expanded["planets"] = _pick_planet(planets)

    if "starships" in expand:
        starships = _fetch_many(film.get("starships") or [])
        expanded["starships"] = _pick_starships(starships)

    if "vehicles" in expand:
        vehicles = _fetch_many(film.get("vehicles") or [])
        expanded["vehicles"] = _pick_vehicles(vehicles)

    if "species" in expand:
        species = _fetch_many(film.get("species") or [])
        expanded["species"] = _pick_species(species)

    return expanded


@films_router.get("/")
def all_films(
    q: str | None = Query(None, description="Search by title (contains, case-insensitive)"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    sort: str | None = Query(None),
    order: Literal["asc", "desc"] = Query("asc"),
    expand: str | None = Query(None),
):
    started_at = time.time()
    expand_set = _split_csv(expand)

    allowed_sort_fields = {"title", "release_date", "episode_id", "director"}

    base_url = f"{SWAPI_BASE_URL}/films/"
    if q:
        base_url += "?search=" + requests.utils.quote(q)

    data = _get_json_cached(base_url)
    collected = data.get("results", [])

    filtered = _apply_local_filter(collected, q, "title")
    sorted_items = _apply_sort(filtered, sort, order, allowed_sort_fields)
    paged = _paginate(sorted_items, page, limit)

    if expand_set:
        paged = [_expand_film(f, expand_set) for f in paged]

    return {
        "resource": "films",
        "count": len(sorted_items),
        "page": page,
        "limit": limit,
        "q": q,
        "sort": sort,
        "order": order,
        "expand": sorted(expand_set),
        "time": round(time.time() - started_at, 3),
        "results": paged,
    }


@films_router.get("/{id}")
async def film_by_id(
    id: int,
    expand: str | None = Query(None),
):
    expand_set = _split_csv(expand)
    film = _get_json_cached(f"{SWAPI_BASE_URL}/films/{id}/")

    if expand_set:
        film = _expand_film(film, expand_set)

    return {"resource": "films", "id": id, "expand": sorted(expand_set), "result": film}
