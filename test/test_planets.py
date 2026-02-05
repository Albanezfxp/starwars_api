def test_planets_list_q_filter(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            def __init__(self, data):
                self.status_code = 200
                self._data = data
            def json(self):
                return self._data

        if url.endswith("/planets/"):
            return Resp({"results": [{"name": "Tatooine"}, {"name": "Alderaan"}], "next": None})
        return Resp({})

    import routers.planets_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/planets/?q=tat")
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["results"][0]["name"] == "Tatooine"


def test_planets_sort_order(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            status_code = 200
            def json(self):
                return {"results": [{"name": "B"}, {"name": "A"}], "next": None}
        return Resp()

    import routers.planets_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/planets/?sort=name&order=asc")
    assert res.status_code == 200
    assert [x["name"] for x in res.json()["results"]] == ["A", "B"]


def test_planets_expand_residents_films(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            def __init__(self, data):
                self.status_code = 200
                self._data = data
            def json(self):
                return self._data

        if url.endswith("/planets/1/"):
            return Resp({
                "name": "Tatooine",
                "orbital_period": "304",
                "climate": "arid",
                "population": "200000",
                "terrain": "desert",
                "gravity": "1 standard",
                "residents": ["https://swapi.dev/api/people/1/"],
                "films": ["https://swapi.dev/api/films/1/"]
            })

        if url.endswith("/people/1/"):
            return Resp({"name": "Luke Skywalker", "gender": "male", "homeworld": "https://swapi.dev/api/planets/1/"})

        if url.endswith("/films/1/"):
            return Resp({"title": "A New Hope", "episode_id": 4, "release_date": "1977-05-25"})

        if url.endswith("/planets/"):
            return Resp({"results": [{"name": "Tatooine"}], "next": None})

        return Resp({})

    import routers.planets_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/planets/1?expand=residents,films")
    assert res.status_code == 200
    result = res.json()["result"]
    assert result["residents"][0]["name"] == "Luke Skywalker"
    assert result["films"][0]["title"] == "A New Hope"


def test_planets_upstream_timeout_502(client, auth_off, monkeypatch):
    import routers.planets_router as mod

    class FakeReqExc(mod.requests.RequestException):
        pass

    def fake_get(url, timeout=10):
        raise FakeReqExc("timeout")

    monkeypatch.setattr(mod.requests, "get", fake_get)
    res = client.get("/planets/")
    assert res.status_code == 502
