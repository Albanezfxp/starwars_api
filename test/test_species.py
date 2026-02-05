def test_species_list_q_filter(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            def __init__(self, data):
                self.status_code = 200
                self._data = data
            def json(self):
                return self._data

        if url.endswith("/species/"):
            return Resp({"results": [{"name": "Human"}, {"name": "Droid"}], "next": None})
        return Resp({})

    import routers.species_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/species/?q=dro")
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["results"][0]["name"] == "Droid"


def test_species_expand_people_films(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            def __init__(self, data):
                self.status_code = 200
                self._data = data
            def json(self):
                return self._data

        if url.endswith("/species/1/"):
            return Resp({
                "name": "Human",
                "classification": "mammal",
                "designation": "sentient",
                "language": "Galactic Basic",
                "homeworld": "https://swapi.dev/api/planets/1/",
                "people": ["https://swapi.dev/api/people/1/"],
                "films": ["https://swapi.dev/api/films/1/"]
            })

        if url.endswith("/planets/1/"):
            return Resp({"name": "Coruscant"})

        if url.endswith("/people/1/"):
            return Resp({"name": "Luke Skywalker", "gender": "male", "homeworld": "https://swapi.dev/api/planets/1/"})

        if url.endswith("/films/1/"):
            return Resp({"title": "A New Hope", "episode_id": 4, "release_date": "1977-05-25"})

        if url.endswith("/species/"):
            return Resp({"results": [{"name": "Human"}], "next": None})

        return Resp({})

    import routers.species_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/species/1?expand=people,films")
    assert res.status_code == 200
    result = res.json()["result"]
    assert result["people"][0]["name"] == "Luke Skywalker"
    assert result["films"][0]["title"] == "A New Hope"


def test_species_upstream_timeout_502(client, auth_off, monkeypatch):
    import routers.species_router as mod

    class FakeReqExc(mod.requests.RequestException):
        pass

    def fake_get(url, timeout=10):
        raise FakeReqExc("timeout")

    monkeypatch.setattr(mod.requests, "get", fake_get)
    res = client.get("/species/")
    assert res.status_code == 502
