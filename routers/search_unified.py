import time
from typing import Any, Literal

import requests
from fastapi import APIRouter, HTTPException, Query

search_unified = APIRouter(tags=["Search"])

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


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _normalize_str(v: Any) -> str:
    return str(v or "").strip().lower()


def _apply_local_filter(results: list[dict[str, Any]], q: str | None) -> list[dict[str, Any]]:
    """Filtra localmente por 'name' ou 'title' contendo q (case-insensitive)."""
    if not q:
        return results

    needle = _normalize_str(q)
    filtered: list[dict[str, Any]] = []
    for item in results:
        hay = _normalize_str(item.get("name") or item.get("title"))
        if needle in hay:
            filtered.append(item)
    return filtered


def _apply_sort(results: list[dict[str, Any]], sort: str | None, order: Literal["asc", "desc"]) -> list[dict[str, Any]]:
    """Ordena localmente por campo (se existir)."""
    if not sort:
        return results

    reverse = order == "desc"

    def key_fn(x: dict[str, Any]):
        val = x.get(sort)
        if val is None:
            return (1, "")
        return (0, str(val).lower())

    return sorted(results, key=key_fn, reverse=reverse)


def _paginate(results: list[dict[str, Any]], page: int, limit: int) -> list[dict[str, Any]]:
    start = (page - 1) * limit
    end = start + limit
    return results[start:end]


def _fetch_many(urls: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for u in urls:
        if isinstance(u, str) and u.startswith("http"):
            out.append(_get_json_cached(u))
    return out


def _expand_item(resource: str, item: dict[str, Any], expand: set[str]) -> dict[str, Any]:
    """
    Expand simples e útil (correlacionados) para SWAPI.
    - people: homeworld, films, starships, vehicles, species
    - films: characters, planets, starships, vehicles, species
    - planets: residents, films
    - starships/vehicles: pilots, films
    """
    expanded = dict(item)

    expand_map: dict[str, dict[str, str]] = {
        "people": {
            "homeworld": "homeworld",
            "films": "films",
            "starships": "starships",
            "vehicles": "vehicles",
            "species": "species",
        },
        "films": {
            "characters": "characters",
            "planets": "planets",
            "starships": "starships",
            "vehicles": "vehicles",
            "species": "species",
        },
        "planets": {
            "residents": "residents",
            "films": "films",
        },
        "starships": {
            "pilots": "pilots",
            "films": "films",
        },
        "vehicles": {
            "pilots": "pilots",
            "films": "films",
        },
    }

    allowed = expand_map.get(resource, {})
    for key in expand:
        field = allowed.get(key)
        if not field:
            continue

        value = item.get(field)

        if isinstance(value, str) and value.startswith("http"):
            expanded[key] = _get_json_cached(value)
        elif isinstance(value, list):
            expanded[key] = _fetch_many(value)

    return expanded


@search_unified.get("/search")
async def search(
    resource: Literal["people", "planets", "films", "starships", "vehicles"] = Query(...),
    q: str | None = Query(None, description="Busca por name/title (contains, case-insensitive)"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    sort: str | None = Query(None, description="Campo para ordenar (ex: name, title, release_date)"),
    order: Literal["asc", "desc"] = Query("asc"),
    expand: str | None = Query(None, description="CSV de correlacionados (ex: homeworld,films)"),
):
    """
    Endpoint unificado:
    - Consulta SWAPI usando endpoint do recurso
    - Aplica filtro local adicional (q)
    - Ordena localmente (sort/order)
    - Pagina localmente (page/limit)
    - Expande correlacionados (expand=...)
    """
    expand_set = set(_split_csv(expand))

    target_count = page * limit
    swapi_url = f"{SWAPI_BASE_URL}/{resource}/"

    params = {}
    if q:
        params["search"] = q

    if params:
        swapi_url = swapi_url + "?" + "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())

    collected: list[dict[str, Any]] = []
    next_url: str | None = swapi_url

    max_pages = 10
    pages = 0

    while next_url and len(collected) < target_count and pages < max_pages:
        data = _get_json_cached(next_url)
        results = data.get("results", [])
        if not isinstance(results, list):
            break

        collected.extend(results)
        next_url = data.get("next")
        pages += 1

    filtered = _apply_local_filter(collected, q)

    sorted_results = _apply_sort(filtered, sort, order)

    paged = _paginate(sorted_results, page, limit)

    if expand_set:
        paged = [_expand_item(resource, item, expand_set) for item in paged]

    return {
        "resource": resource,
        "count": len(sorted_results),
        "page": page,
        "limit": limit,
        "q": q,
        "sort": sort,
        "order": order,
        "expand": sorted(expand_set),
        "results": paged,
    }
