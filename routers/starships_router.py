import time
from typing import Any, Literal

import requests
from fastapi import APIRouter, HTTPException, Query

starships_router = APIRouter(prefix="/starships", tags=["Starships"])
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
        else:
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


def _apply_local_filter(items: list[dict], q: str | None, field: str) -> list[dict]:
    if not q:
        return items
    q_norm = q.strip().lower()
    if not q_norm:
        return items
    out: list[dict] = []
    for it in items:
        v = it.get(field)
        if isinstance(v, str) and q_norm in v.lower():
            out.append(it)
    return out


def _try_float(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _apply_sort(
    items: list[dict],
    sort: str | None,
    order: Literal["asc", "desc"],
    allowed: set[str],
) -> list[dict]:
    if not sort:
        return items
    if sort not in allowed:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    reverse = order == "desc"

    def key_fn(it: dict):
        val = it.get(sort)
        num = _try_float(val)
        if num is not None:
            return (0, num)
        return (1, str(val or "").strip().lower())

    return sorted(items, key=key_fn, reverse=reverse)


def _paginate(items: list[dict], page: int, limit: int) -> list[dict]:
    start = (page - 1) * limit
    end = start + limit
    return items[start:end]


def _pick_people(data: dict) -> dict:
    return {
        "name": data.get("name"),
        "height": data.get("height"),
        "mass": data.get("mass"),
        "gender": data.get("gender"),
        "url": data.get("url"),
    }


def _pick_films(data: dict) -> dict:
    return {
        "title": data.get("title"),
        "episode_id": data.get("episode_id"),
        "release_date": data.get("release_date"),
        "url": data.get("url"),
    }


def _pick_starship(data: dict) -> dict:
    return {
        "name": data.get("name"),
        "model": data.get("model"),
        "manufacturer": data.get("manufacturer"),
        "starship_class": data.get("starship_class"),
        "url": data.get("url"),
    }


def _expand_starship(data: dict, expand_set: set[str]) -> dict:
    expanded = dict(data)

    if "pilots" in expand_set and isinstance(expanded.get("pilots"), list):
        expanded["pilots"] = [_pick_people(_get_json_cached(u)) for u in expanded["pilots"]]

    if "films" in expand_set and isinstance(expanded.get("films"), list):
        expanded["films"] = [_pick_films(_get_json_cached(u)) for u in expanded["films"]]

    return expanded


@starships_router.get("/")
def all_starships(
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    sort: str | None = Query(None),
    order: Literal["asc", "desc"] = Query("asc"),
    expand: str | None = Query(None),
):
    started_at = time.time()
    expand_set = _split_csv(expand)

    allowed_sort_fields = {"name", "model", "manufacturer", "starship_class"}

    target = page * limit
    base_url_no_search = f"{SWAPI_BASE_URL}/starships/"
    base_url = base_url_no_search
    if q:
        base_url += "?search=" + requests.utils.quote(q)

    collected: list[dict[str, Any]] = []
    next_url: str | None = base_url
    pages = 0

    while next_url and len(collected) < target and pages < 10:
        data = _get_json_cached(next_url)
        collected.extend(data.get("results", []))
        next_url = data.get("next")
        pages += 1

    if q and not collected:
        collected = []
        next_url = base_url_no_search
        pages = 0
        while next_url and len(collected) < target and pages < 10:
            data = _get_json_cached(next_url)
            collected.extend(data.get("results", []))
            next_url = data.get("next")
            pages += 1

    filtered = _apply_local_filter(collected, q, "name")
    sorted_items = _apply_sort(filtered, sort, order, allowed_sort_fields)
    paged = _paginate(sorted_items, page, limit)

    if expand_set:
        paged = [_expand_starship(p, expand_set) for p in paged]
    else:
        paged = [_pick_starship(p) for p in paged]

    return {
        "resource": "starships",
        "count": len(filtered),
        "page": page,
        "limit": limit,
        "q": q,
        "sort": sort,
        "order": order,
        "expand": sorted(expand_set) if expand_set else [],
        "results": paged,
        "elapsed_ms": int((time.time() - started_at) * 1000),
    }


@starships_router.get("/{starship_id}")
def starship_by_id(
    starship_id: int,
    expand: str | None = Query(None),
):
    started_at = time.time()
    expand_set = _split_csv(expand)

    data = _get_json_cached(f"{SWAPI_BASE_URL}/starships/{starship_id}/")

    if expand_set:
        result = _expand_starship(data, expand_set)
    else:
        result = _pick_starship(data)

    return {
        "resource": "starships",
        "id": starship_id,
        "expand": sorted(expand_set) if expand_set else [],
        "result": result,
        "elapsed_ms": int((time.time() - started_at) * 1000),
    }
