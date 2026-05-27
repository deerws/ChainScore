import json, csv
from pathlib import Path
from src.models.player import Player


class PlayerRepository:

    def __init__(self, api_client):
        self._api_client = api_client
        self._jogadores = []
    
    def listar_jogadores(self):
        return self._jogadores

    def atualizar_jogadores(self):
        pass
        #dados = self._api_client.buscar_jogadores()
        #self._jogadores = self._converter_para_players(dados)

    def _converter_para_players(self, dados):
        jogadores = []

        for jogador in dados:
            jogadores.append(
                Player(
                    nome=jogador["nome"],
                    time=jogador["time"],
                    posicao=jogador["posicao"],
                    idade=jogador["idade"],
                    gols=jogador["gols"],
                    assistencias=jogador["assistencias"],
                    cartoes_amarelos=jogador["cartoes_amarelos"],
                    cartoes_vermelhos=jogador["cartoes_vermelhos"],
                    faltas=jogador["faltas"],
                    gols_sofridos=jogador["gols_sofridos"]
                )
            )

        return jogadores