import json
from pathlib import Path

from src.models.estatistics import Estatisticas
from src.models.player import Player
from src.repositories.players_repository import PlayerRepository


class PlayerService:

    CATALOGO_PATH = Path("data/api_football/players_available.json")

    def __init__(self, player_repository: PlayerRepository):
        self.player_repository = player_repository

    def listar_jogadores_ordenados(
        self,
        criterio: Estatisticas | str,
        reverse=True,
    ) -> list[Player]:
        jogadores = self.player_repository.listar_jogadores().copy()
        atributo = self._normalizar_criterio_ordenacao(criterio)
        jogadores.sort(
            key=lambda jogador: self._valor_ordenacao(jogador, atributo),
            reverse=reverse,
        )
        return jogadores

    def carregar_jogadores_brasileirao_temporada(
        self,
        temporada=None,
        liga_id=None,
        usar_cache=True,
        max_paginas=None,
        paginas_por_execucao=None,
    ) -> list[Player]:
        return self.carregar_jogadores_temporada_cache(liga_id, temporada)

    def carregar_jogadores_temporada_cache(self, liga_id=None, temporada=None) -> list[Player]:
        dados = self._carregar_catalogo_fixo()
        jogadores = self._converter_catalogo_para_players(dados)
        self.player_repository.definir_jogadores(jogadores)
        return jogadores

    def _carregar_catalogo_fixo(self):
        if not self.CATALOGO_PATH.exists() or self.CATALOGO_PATH.stat().st_size == 0:
            raise RuntimeError(
                f"Catalogo fixo de jogadores vazio ou inexistente: {self.CATALOGO_PATH}"
            )

        with self.CATALOGO_PATH.open("r", encoding="utf-8") as arquivo:
            return json.load(arquivo)

    def _converter_catalogo_para_players(self, dados):
        jogadores_api = dados.get("response", dados if isinstance(dados, list) else [])
        jogadores = []

        for jogador_api in jogadores_api:
            dados_jogador = jogador_api.get("player", jogador_api)
            estatistica = self._primeira_estatistica(jogador_api)
            dados_time = estatistica.get("team", {})
            dados_jogo = estatistica.get("games", {})
            valor_mercado = (
                dados_jogador.get("valor_mercado")
                or dados_jogador.get("market_value")
                or jogador_api.get("valor_mercado")
                or 10.0
            )

            jogadores.append(
                Player(
                    nome=dados_jogador.get("name") or dados_jogador.get("nome"),
                    time=None,
                    posicao=(
                        dados_jogo.get("position")
                        or dados_jogador.get("posicao")
                        or "desconhecida"
                    ),
                    idade=dados_jogador.get("age") or dados_jogador.get("idade") or 0,
                    api_id=dados_jogador.get("id") or dados_jogador.get("api_id"),
                    nome_time=(
                        dados_time.get("name")
                        or dados_jogador.get("nome_time")
                        or dados_jogador.get("time")
                    ),
                    valor_mercado=valor_mercado,
                )
            )

        return jogadores

    def _primeira_estatistica(self, jogador_api):
        estatisticas = jogador_api.get("statistics", [])
        if not estatisticas:
            return {}
        return estatisticas[0]

    def _normalizar_criterio_ordenacao(self, criterio):
        if isinstance(criterio, Estatisticas):
            criterio = criterio.value

        criterio = str(criterio or "").casefold().strip().replace(" ", "_")
        aliases = {
            "id": "api_id",
            "time": "nome_time",
            "clube": "nome_time",
            "valor": "valor_mercado",
            "preco": "valor_mercado",
            "preço": "valor_mercado",
        }
        return aliases.get(criterio, criterio)

    def _valor_ordenacao(self, jogador, atributo):
        valor = getattr(jogador, atributo, None)

        if valor is None:
            return (1, "")

        if isinstance(valor, (int, float)):
            return (0, valor)

        try:
            return (0, float(valor))
        except (TypeError, ValueError):
            return (0, str(valor).casefold())
