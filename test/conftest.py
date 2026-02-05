import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_on(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    yield
    monkeypatch.delenv("API_KEY", raising=False)

@pytest.fixture
def auth_off(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    yield


@pytest.fixture(autouse=True)
def clear_router_caches():
    """
    Zera o cache em memória entre testes.
    Sem isso, monkeypatch do requests.get não funciona porque o cache devolve 200 antigo.
    """
    from routers import (
        films_router,
        people_router,
        planets_router,
        species_router,
        starships_router,
        vehicles_router,
    )

    films_router._CACHE.clear()
    people_router._CACHE.clear()
    planets_router._CACHE.clear()
    species_router._CACHE.clear()
    starships_router._CACHE.clear()
    vehicles_router._CACHE.clear()
    yield
