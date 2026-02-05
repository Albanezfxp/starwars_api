def test_people_list_q_filter(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            def __init__(self, data):
                self.status_code = 200
                self._data = data
            def json(self):
                return self._data

        if "people/" in url and "search=" in url:
            return Resp({"results": [{"name": "Luke Skywalker"}], "next": None})
        if url.endswith("/people/"):
            return Resp({"results": [{"name": "Luke Skywalker"}, {"name": "Leia Organa"}], "next": None})
        return Resp({})

    import routers.people_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/peoples/?q=luke")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 1
    assert body["results"][0]["name"] == "Luke Skywalker"


def test_people_sort_order(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            status_code = 200
            def json(self):
                return {"results": [{"name": "B"}, {"name": "A"}], "next": None}
        return Resp()

    import routers.people_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/peoples/?sort=name&order=asc")
    assert res.status_code == 200
    names = [x["name"] for x in res.json()["results"]]
    assert names == ["A", "B"]


def test_people_expand_homeworld_films(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            def __init__(self, data):
                self.status_code = 200
                self._data = data
            def json(self):
                return self._data

        if url.endswith("/people/1/"):
            return Resp({
                "name": "Luke Skywalker",
                "homeworld": "https://swapi.dev/api/planets/1/",
                "films": ["https://swapi.dev/api/films/1/"],
                "vehicles": [],
                "starships": [],
                "species": []
            })

        if url.endswith("/planets/1/"):
            return Resp({"name": "Tatooine", "climate": "arid", "population": "200000"})

        if url.endswith("/films/1/"):
            return Resp({"title": "A New Hope", "episode_id": 4, "release_date": "1977-05-25"})

        if url.endswith("/people/"):
            return Resp({"results": [{"name": "Luke Skywalker"}], "next": None})

        return Resp({})

    import routers.people_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/peoples/1?expand=homeworld,films")
    assert res.status_code == 200
    result = res.json()["result"]
    assert result["homeworld"]["name"] == "Tatooine"
    assert result["films"][0]["title"] == "A New Hope"


def test_people_detail_by_id(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            status_code = 200
            def json(self):
                return {"name": "Luke Skywalker", "species": []}
        return Resp()

    import routers.people_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/peoples/1")
    assert res.status_code == 200
    assert res.json()["result"]["name"] == "Luke Skywalker"


def test_people_upstream_timeout_502(client, auth_off, monkeypatch):
    import routers.people_router as mod

    class FakeReqExc(mod.requests.RequestException):
        pass

    def fake_get(url, timeout=10):
        raise FakeReqExc("timeout")

    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/peoples/")
    assert res.status_code == 502
