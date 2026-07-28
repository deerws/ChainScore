import json
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

from src.external.api_client import SofaScoreApiClient
from src.external.api_football_client import ApiFootballClient
from src.external.api_football_client import ApiFootballRateLimitError
from src.models.club import Club
from src.models.match import Match
from src.models.player import Player
from src.models.player_match import MatchPlayerStats
from src.models.rounds import Round

'''
Classe que vai chamar a API
'''


class MatchService():

    CACHE_DIR = Path("data/api_football")

    def __init__(
        self,
        sofa_api: SofaScoreApiClient | None = None,
        api_football: ApiFootballClient | None = None,
    ):
        self.sofa_api = sofa_api
        self.api_football = api_football

    def get_match_info(self, event_id):
        if self.sofa_api is None:
            raise ValueError("SofaScoreApiClient nao configurado")

        evento = self.sofa_api.get_event(event_id)
        estatisticas = self.sofa_api.get_event_statistics(event_id)

        return {
            "evento": evento,
            "estatisticas": estatisticas,
        }

    def buscar_partidas_por_data(
        self,
        data,
        liga_id=None,
        temporada=None,
        time_id=None,
        status=None,
    ):
        return self._api_football().buscar_partidas_por_data(
            data=data,
            liga_id=liga_id,
            temporada=temporada,
            time_id=time_id,
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
        return self._api_football().buscar_partidas_por_periodo(
            data_inicio=data_inicio,
            data_fim=data_fim,
            liga_id=liga_id,
            temporada=temporada,
            time_id=time_id,
            status=status,
        )

    def buscar_partida_por_id(self, fixture_id):
        return self._api_football().buscar_partida_por_id(fixture_id)

    def buscar_estatisticas_jogadores_partida(self, fixture_id, time_id=None):
        return self._api_football().buscar_estatisticas_jogadores_partida(
            fixture_id=fixture_id,
            time_id=time_id,
        )

    def buscar_partidas_por_rodada_api_football(
        self,
        liga_id,
        temporada,
        rodada,
        status=None,
    ):
        return self._api_football().buscar_partidas_por_rodada(
            liga_id=liga_id,
            temporada=temporada,
            rodada=rodada,
            status=status,
        )

    def buscar_partidas_por_ids_api_football(self, fixture_ids):
        return self._api_football().buscar_partidas_por_ids(fixture_ids)

    def montar_rodada_por_fixture_api_football(
        self,
        fixture_id,
        numero_rodada,
        jogadores_escalados: list[Player],
    ):
        dados_partida = self.baixar_dados_partida_api_football(fixture_id)

        return self.montar_rodada_por_cache_api_football(
            fixture_id=fixture_id,
            numero_rodada=numero_rodada,
            jogadores_escalados=jogadores_escalados,
            dados_partida=dados_partida,
        )

    def baixar_dados_partida_api_football(self, fixture_id, usar_cache=True):
        caminho_cache = self._caminho_cache_partida(fixture_id)

        if usar_cache and caminho_cache.exists():
            return self.carregar_dados_partida_api_football(fixture_id)

        partida_api = self.buscar_partida_por_id(fixture_id)
        estatisticas_api = self.buscar_estatisticas_jogadores_partida(fixture_id)

        dados_partida = {
            "fixture_id": fixture_id,
            "partida": partida_api,
            "estatisticas_jogadores": estatisticas_api,
        }

        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        caminho_temporario = caminho_cache.with_suffix(caminho_cache.suffix + ".tmp")

        with caminho_temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(dados_partida, arquivo, ensure_ascii=False, indent=2)

        caminho_temporario.replace(caminho_cache)

        return dados_partida

    def carregar_dados_partida_api_football(self, fixture_id):
        caminho_cache = self._caminho_cache_partida(fixture_id)

        with caminho_cache.open("r", encoding="utf-8") as arquivo:
            return json.load(arquivo)

    def listar_jogadores_disponiveis_cache_api_football(self, fixture_id):
        dados_partida = self.carregar_dados_partida_api_football(fixture_id)
        jogadores = []

        for time in dados_partida["estatisticas_jogadores"].get("response", []):
            nome_time = time.get("team", {}).get("name")

            for jogador_api in time.get("players", []):
                stats = jogador_api.get("statistics", [])
                if not stats:
                    continue

                minutos = stats[0].get("games", {}).get("minutes") or 0

                if minutos > 0:
                    jogadores.append(
                        {
                            "nome": jogador_api.get("player", {}).get("name"),
                            "time": nome_time,
                            "posicao": stats[0].get("games", {}).get("position"),
                            "idade": 0,
                            "minutos": minutos,
                        }
                    )

        return jogadores

    def baixar_dados_rodada_api_football(
        self,
        liga_id,
        temporada,
        rodada,
        status=None,
        usar_cache=True,
        max_partidas=None,
    ):
        caminho_cache = self._caminho_cache_rodada(liga_id, temporada, rodada)

        if usar_cache and caminho_cache.exists():
            dados_rodada = self._carregar_cache_rodada_ou_none(caminho_cache)
        else:
            dados_rodada = None

        if dados_rodada is not None:
            partidas_api = dados_rodada.get("partidas_api", {})
        else:
            partidas_api = self.buscar_partidas_por_rodada_api_football(
                liga_id=liga_id,
                temporada=temporada,
                rodada=rodada,
                status=status,
            )
            dados_rodada = {
                "liga_id": liga_id,
                "temporada": temporada,
                "rodada": rodada,
                "partidas_api": partidas_api,
                "partidas": [],
            }

        self._normalizar_cache_rodada(dados_rodada)
        self._remover_partidas_duplicadas_cache(dados_rodada)
        baixadas = self._fixture_ids_cacheados(dados_rodada)
        partidas_para_baixar = []

        for partida in partidas_api.get("response", []):
            fixture_id = partida["fixture"]["id"]

            if fixture_id in baixadas:
                continue

            if max_partidas is not None and len(partidas_para_baixar) >= max_partidas:
                break

            partidas_para_baixar.append(partida)

        self._baixar_estatisticas_partidas_rodada(
            caminho_cache,
            dados_rodada,
            partidas_para_baixar,
        )

        self._salvar_cache_rodada(caminho_cache, dados_rodada)
        return dados_rodada

    def _baixar_estatisticas_partidas_rodada(
        self,
        caminho_cache,
        dados_rodada,
        partidas_para_baixar,
    ):
        for partida in partidas_para_baixar:
            fixture_id = partida["fixture"]["id"]

            try:
                estatisticas_api = self.buscar_estatisticas_jogadores_partida(
                    fixture_id
                )
            except ApiFootballRateLimitError:
                self._salvar_cache_rodada(caminho_cache, dados_rodada)
                raise

            dados_rodada["partidas"].append(
                {
                    "fixture_id": fixture_id,
                    "estatisticas_jogadores": estatisticas_api,
                }
            )
            self._remover_partidas_duplicadas_cache(dados_rodada)
            self._salvar_cache_rodada(caminho_cache, dados_rodada)

    def _salvar_cache_rodada(self, caminho_cache, dados_rodada):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        caminho_temporario = caminho_cache.with_suffix(caminho_cache.suffix + ".tmp")

        with caminho_temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(dados_rodada, arquivo, ensure_ascii=False, indent=2)

        caminho_temporario.replace(caminho_cache)

    def _fixture_ids_cacheados(self, dados_rodada):
        return {
            int(partida_cache["fixture_id"])
            for partida_cache in dados_rodada.get("partidas", [])
        }

    def _remover_partidas_duplicadas_cache(self, dados_rodada):
        partidas_unicas = {}

        for partida_cache in dados_rodada.get("partidas", []):
            partidas_unicas[int(partida_cache["fixture_id"])] = partida_cache

        dados_rodada["partidas"] = list(partidas_unicas.values())

    def _normalizar_cache_rodada(self, dados_rodada):
        fixture_ids_partidas_api = {
            int(partida.get("fixture", {}).get("id", 0))
            for partida in dados_rodada.get("partidas_api", {}).get("response", [])
        }

        for partida_cache in dados_rodada.get("partidas", []):
            fixture_id = int(partida_cache.get("fixture_id", 0))

            if fixture_id in fixture_ids_partidas_api:
                partida_cache.pop("partida", None)

    def carregar_dados_rodada_api_football(self, liga_id, temporada, rodada):
        caminho_cache = self._caminho_cache_rodada(liga_id, temporada, rodada)
        dados_rodada = self._carregar_cache_rodada_ou_none(caminho_cache)

        if dados_rodada is None:
            raise RuntimeError(
                f"Cache da rodada esta vazio ou invalido: {caminho_cache}"
            )

        return dados_rodada

    def _carregar_cache_rodada_ou_none(self, caminho_cache):
        try:
            with caminho_cache.open("r", encoding="utf-8") as arquivo:
                return json.load(arquivo)
        except (OSError, json.JSONDecodeError):
            return None

    def listar_jogadores_disponiveis_cache_rodada_api_football(
        self,
        liga_id,
        temporada,
        rodada,
    ):
        dados_rodada = self.carregar_dados_rodada_api_football(
            liga_id,
            temporada,
            rodada,
        )
        jogadores = []

        for dados_partida in dados_rodada.get("partidas", []):
            fixture_id = dados_partida["fixture_id"]
            partida_api = self._buscar_partida_cache_rodada(dados_rodada, fixture_id)
            fixture = partida_api["response"][0]
            nome_partida = fixture.get("teams", {}).get("home", {}).get("name")
            nome_partida += " x "
            nome_partida += fixture.get("teams", {}).get("away", {}).get("name")

            for time in dados_partida["estatisticas_jogadores"].get("response", []):
                nome_time = time.get("team", {}).get("name")

                for jogador_api in time.get("players", []):
                    stats = jogador_api.get("statistics", [])
                    if not stats:
                        continue

                    minutos = stats[0].get("games", {}).get("minutes") or 0

                    if minutos > 0:
                        jogadores.append(
                            {
                                "api_id": jogador_api.get("player", {}).get("id"),
                                "nome": jogador_api.get("player", {}).get("name"),
                                "time": nome_time,
                                "posicao": stats[0].get("games", {}).get("position"),
                                "idade": 0,
                                "minutos": minutos,
                                "fixture_id": fixture_id,
                                "partida": nome_partida,
                            }
                        )

        return jogadores

    def montar_rodada_por_cache_rodada_api_football(
        self,
        liga_id,
        temporada,
        rodada,
        numero_rodada,
        jogadores_escalados: list[Player],
    ):
        dados_rodada = self.carregar_dados_rodada_api_football(
            liga_id,
            temporada,
            rodada,
        )
        rodada_model = Round(numero_rodada)

        for dados_partida in dados_rodada.get("partidas", []):
            partida_api = self._buscar_partida_cache_rodada(
                dados_rodada,
                dados_partida["fixture_id"],
            )
            partida = self._converter_fixture_para_match(
                partida_api=partida_api,
                estatisticas_api=dados_partida["estatisticas_jogadores"],
                jogadores_escalados=jogadores_escalados,
            )
            rodada_model.adicionar_partidas_rodada(partida)

        return rodada_model

    def montar_rodada_por_cache_api_football(
        self,
        fixture_id,
        numero_rodada,
        jogadores_escalados: list[Player],
        dados_partida=None,
    ):
        dados_partida = dados_partida or self.carregar_dados_partida_api_football(
            fixture_id
        )

        partida = self._converter_fixture_para_match(
            partida_api=dados_partida["partida"],
            estatisticas_api=dados_partida["estatisticas_jogadores"],
            jogadores_escalados=jogadores_escalados,
        )

        rodada = Round(numero_rodada)
        rodada.adicionar_partidas_rodada(partida)
        return rodada

    def _caminho_cache_partida(self, fixture_id):
        return self.CACHE_DIR / f"fixture_{fixture_id}.json"

    def _caminho_cache_rodada(self, liga_id, temporada, rodada):
        numero_rodada = self._numero_rodada(rodada)
        return self.CACHE_DIR / f"brasileirao_round_{numero_rodada}.json"

    def _numero_rodada(self, rodada):
        if isinstance(rodada, int):
            return rodada

        try:
            return int(str(rodada).rsplit("-", 1)[1].strip())
        except (IndexError, ValueError):
            raise ValueError(f"Nome de rodada invalido: {rodada}")

    def _buscar_partida_cache_rodada(self, dados_rodada, fixture_id):
        fixture_id = int(fixture_id)

        for partida in dados_rodada.get("partidas_api", {}).get("response", []):
            if int(partida.get("fixture", {}).get("id", 0)) == fixture_id:
                return {"response": [partida]}

        for partida_cache in dados_rodada.get("partidas", []):
            if int(partida_cache.get("fixture_id", 0)) != fixture_id:
                continue

            partida_api = partida_cache.get("partida")
            if partida_api and partida_api.get("response"):
                return partida_api

        raise ValueError(f"Partida {fixture_id} nao encontrada no cache da rodada")

    def _converter_fixture_para_match(
        self,
        partida_api,
        estatisticas_api,
        jogadores_escalados: list[Player],
    ):
        fixtures = partida_api.get("response", [])
        if not fixtures:
            raise ValueError("Partida nao encontrada na API-Football")

        fixture = fixtures[0]
        home_team = fixture["teams"]["home"]
        away_team = fixture["teams"]["away"]

        mandante = Club(home_team["name"], [], 0, 0, 0, 0)
        visitante = Club(away_team["name"], [], 0, 0, 0, 0)
        atuacoes_api = self._indexar_atuacoes_api_football(estatisticas_api)
        jogadores_partida = []

        for jogador in jogadores_escalados:
            jogador_api = atuacoes_api["por_api_id"].get(jogador.api_id)

            if jogador_api is None:
                nome_normalizado = self._normalizar_nome(jogador.nome)
                jogador_api = atuacoes_api["por_nome"].get(nome_normalizado)

            if jogador_api is None:
                nome_normalizado = self._normalizar_nome(jogador.nome)
                jogador_api = self._buscar_atuacao_por_nome_aproximado(
                    nome_normalizado,
                    atuacoes_api["por_nome"],
                )

            if jogador_api is None:
                continue

            jogadores_partida.append(
                self._converter_atuacao_api_football(jogador, jogador_api)
            )

        return Match(
            mandante=mandante,
            visitante=visitante,
            data=fixture["fixture"]["date"],
            jogadores_partida=jogadores_partida,
        )

    def _indexar_atuacoes_api_football(self, estatisticas_api):
        atuacoes = {
            "por_api_id": {},
            "por_nome": {},
        }

        for time in estatisticas_api.get("response", []):
            for jogador_api in time.get("players", []):
                api_id = jogador_api.get("player", {}).get("id")
                nome = jogador_api.get("player", {}).get("name")

                if api_id is not None:
                    atuacoes["por_api_id"][api_id] = jogador_api

                if nome:
                    atuacoes["por_nome"][self._normalizar_nome(nome)] = jogador_api

        return atuacoes

    def _converter_atuacao_api_football(self, jogador, jogador_api):
        if jogador_api is None:
            return MatchPlayerStats(
                jogador=jogador,
                atuou=False,
                titular=False,
                gols=0,
                assistencias=0,
                cartoes_amarelos=0,
                cartoes_vermelhos=0,
                faltas=0,
                gols_sofridos=0,
            )

        stats = jogador_api.get("statistics", [{}])[0]
        games = stats.get("games", {})
        goals = stats.get("goals", {})
        cards = stats.get("cards", {})
        fouls = stats.get("fouls", {})

        minutos = games.get("minutes") or 0

        return MatchPlayerStats(
            jogador=jogador,
            atuou=minutos > 0,
            titular=not games.get("substitute", True),
            gols=goals.get("total") or 0,
            assistencias=goals.get("assists") or 0,
            cartoes_amarelos=cards.get("yellow") or 0,
            cartoes_vermelhos=cards.get("red") or 0,
            faltas=fouls.get("committed") or 0,
            gols_sofridos=goals.get("conceded") or 0,
        )

    def _normalizar_nome(self, nome):
        sem_acento = unicodedata.normalize("NFKD", nome)
        sem_acento = "".join(
            caractere
            for caractere in sem_acento
            if not unicodedata.combining(caractere)
        )
        return sem_acento.casefold().strip()

    def _buscar_atuacao_por_nome_aproximado(self, nome_normalizado, atuacoes):
        melhor_nome = None
        melhor_score = 0

        for nome_api in atuacoes:
            score = SequenceMatcher(None, nome_normalizado, nome_api).ratio()

            if score > melhor_score:
                melhor_nome = nome_api
                melhor_score = score

        if melhor_score >= 0.86:
            return atuacoes[melhor_nome]

        return None

    def _api_football(self):
        if self.api_football is None:
            self.api_football = ApiFootballClient()

        return self.api_football
