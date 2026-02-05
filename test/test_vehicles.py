def test_vehicles_list_q_filter(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            def __init__(self, data):
                self.status_code = 200
                self._data = data
            def json(self):
                return self._data

        if url.endswith("/vehicles/"):
            return Resp({"results": [{"name": "Sand Crawler"}, {"name": "Speeder Bike"}], "next": None})
        return Resp({})

    import routers.vehicles_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/vehicles/?q=sand")
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["results"][0]["name"] == "Sand Crawler"


def test_vehicles_expand_pilots_films(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            def __init__(self, data):
                self.status_code = 200
                self._data = data
            def json(self):
                return self._data

        if url.endswith("/vehicles/4/"):
            return Resp({
                "name": "Sand Crawler",
                "model": "Digger",
                "manufacturer": "Corellia",
                "vehicle_class": "wheeled",
                "crew": "46",
                "passengers": "30",
                "pilots": ["https://swapi.dev/api/people/1/"],
                "films": ["https://swapi.dev/api/films/1/"]
            })

        if url.endswith("/people/1/"):
            return Resp({"name": "Luke Skywalker", "gender": "male", "homeworld": "https://swapi.dev/api/planets/1/"})

        if url.endswith("/planets/1/"):
            return Resp({"name": "Tatooine"})

        if url.endswith("/films/1/"):
            return Resp({"title": "A New Hope", "episode_id": 4, "release_date": "1977-05-25"})

        if url.endswith("/vehicles/"):
            return Resp({"results": [{"name": "Sand Crawler"}], "next": None})

        return Resp({})

    import routers.vehicles_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/vehicles/4?expand=pilots,films")
    assert res.status_code == 200
    result = res.json()["result"]
    assert result["pilots"][0]["name"] == "Luke Skywalker"
    assert result["films"][0]["title"] == "A New Hope"


def test_vehicles_upstream_timeout_502(client, auth_off, monkeypatch):
    import routers.vehicles_router as mod

    class FakeReqExc(mod.requests.RequestException):
        pass

    def fake_get(url, timeout=10):
        raise FakeReqExc("timeout")

    monkeypatch.setattr(mod.requests, "get", fake_get)
    res = client.get("/vehicles/")
    assert res.status_code == 502
