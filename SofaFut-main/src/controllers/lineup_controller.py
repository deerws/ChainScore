from src.controllers.app_controller import AppController
from src.models.player_fantasy import PlayerFantasy


class LineupController:
    def __init__(self, app_controller: AppController):
        self.app_controller = app_controller

    def selecionar_players_do_catalogo(self, jogadores_disponiveis):
        catalogo = self.app_controller.listar_jogadores()
        catalogo_por_api_id = {
            jogador.api_id: jogador
            for jogador in catalogo
            if jogador.api_id is not None
        }
        catalogo_por_nome_time = {
            (self._normalizar(jogador.nome), self._normalizar(jogador.nome_time)): jogador
            for jogador in catalogo
        }
        jogadores = []

        for jogador_disponivel in jogadores_disponiveis:
            jogador = catalogo_por_api_id.get(jogador_disponivel.get("api_id"))

            if jogador is None:
                chave = (
                    self._normalizar(jogador_disponivel.get("nome")),
                    self._normalizar(jogador_disponivel.get("time")),
                )
                jogador = catalogo_por_nome_time.get(chave)

            if jogador is not None:
                jogadores.append(jogador)

        return jogadores

    def criar_escalacao_fantasy(self, jogadores, capitao=None):
        capitao = capitao or (jogadores[0] if jogadores else None)

        return [
            PlayerFantasy(jogador, jogador is capitao, 0)
            for jogador in jogadores
        ]

    def montar_escalacao(self, username, numero_rodada, jogadores_fantasy):
        return self.app_controller.montar_escalacao(
            username=username,
            rodada=numero_rodada,
            jogadores=jogadores_fantasy,
        )

    def executar_rodada(self, username, numero_rodada, jogadores_fantasy):
        return self.app_controller.executar_rodada(
            username=username,
            rodada=numero_rodada,
            jogadores=jogadores_fantasy,
        )

    def buscar_escalacao(self, numero_rodada):
        usuario = self.app_controller.usuario_logado()

        if usuario is None:
            return None

        return usuario.team_fantasy.escalacoes.get(numero_rodada)

    def _normalizar(self, valor):
        return (valor or "").casefold().strip()
