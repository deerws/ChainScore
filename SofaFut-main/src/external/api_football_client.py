import json
import os
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class ApiFootballRateLimitError(RuntimeError):
    pass


class ApiFootballClient:
    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self, api_key=None, timeout=15):
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY")
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "Configure a variavel de ambiente API_FOOTBALL_KEY com sua chave da API-Football"
            )

    def _get(self, path, **params):
        clean_params = {
            chave: valor
            for chave, valor in params.items()
            if valor is not None
        }
        query_string = urlencode(clean_params)
        url = f"{self.BASE_URL}{path}"

        if query_string:
            url = f"{url}?{query_string}"

        request = Request(
            url,
            headers={
                "x-apisports-key": self.api_key,
                "Accept": "application/json",
            },
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except HTTPError as erro:
            body = erro.read().decode("utf-8")

            if erro.code == 429:
                raise ApiFootballRateLimitError(
                    f"Limite de requisicoes da API-Football atingido: {body}"
                ) from erro

            raise RuntimeError(
                f"Erro HTTP {erro.code} da API-Football: {body}"
            ) from erro

        data = json.loads(body)

        errors = data.get("errors")
        if errors:
            raise RuntimeError(f"Erro da API-Football: {errors}")

        return data

    def buscar_partidas_por_data(
        self,
        data,
        liga_id=None,
        temporada=None,
        time_id=None,
        status=None,
    ):
        return self._get(
            "/fixtures",
            date=data,
            league=liga_id,
            season=temporada,
            team=time_id,
            status=status,
        )

    def buscar_partidas_por_periodo(
        self,
        data_inicio,
        data_fim,
        liga_id=None,
        temporada=None,
        time_id=None,
        status=None,
    ):
        return self._get(
            "/fixtures",
            **{
                "from": data_inicio,
                "to": data_fim,
                "league": liga_id,
                "season": temporada,
                "team": time_id,
                "status": status,
            },
        )

    def buscar_partidas_por_rodada(
        self,
        liga_id,
        temporada,
        rodada,
        status=None,
    ):
        return self._get(
            "/fixtures",
            league=liga_id,
            season=temporada,
            round=rodada,
            status=status,
        )

    def buscar_partidas_por_ids(self, fixture_ids):
        return self._get(
            "/fixtures",
            ids="-".join(str(fixture_id) for fixture_id in fixture_ids),
        )

    def buscar_partida_por_id(self, fixture_id):
        return self._get("/fixtures", id=fixture_id)

    def buscar_estatisticas_jogadores_partida(self, fixture_id, time_id=None):
        return self._get(
            "/fixtures/players",
            fixture=fixture_id,
            team=time_id,
        )

    def buscar_jogadores_liga_temporada(self, liga_id, temporada, pagina=1):
        return self._get(
            "/players",
            league=liga_id,
            season=temporada,
            page=pagina,
        )
