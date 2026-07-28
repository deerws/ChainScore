from src.controllers.app_controller import AppController


class RoundController:
    TEMPORADAS_DISPONIVEIS = [2024, 2023, 2022]
    LIGA_BRASILEIRAO = 71

    def __init__(self, app_controller: AppController):
        self.app_controller = app_controller

    def listar_temporadas_disponiveis(self):
        return self.TEMPORADAS_DISPONIVEIS.copy()

    def listar_rodadas_disponiveis(self):
        return list(range(1, 39))

    def nome_rodada_api(self, numero_rodada):
        if numero_rodada < 1 or numero_rodada > 38:
            raise RuntimeError("A rodada precisa estar entre 1 e 38")

        return f"Regular Season - {numero_rodada}"

    def baixar_dados_rodada(
        self,
        temporada,
        numero_rodada,
        liga_id=LIGA_BRASILEIRAO,
        status="FT",
        max_partidas=None,
    ):
        return self.app_controller.baixar_dados_rodada_api_football(
            liga_id=liga_id,
            temporada=temporada,
            rodada=self.nome_rodada_api(numero_rodada),
            status=status,
            max_partidas=max_partidas,
        )

    def listar_jogadores_disponiveis(
        self,
        temporada,
        numero_rodada,
        liga_id=LIGA_BRASILEIRAO,
    ):
        return self.app_controller.listar_jogadores_disponiveis_cache_rodada_api_football(
            liga_id,
            temporada,
            self.nome_rodada_api(numero_rodada),
        )

    def montar_rodada_por_cache(
        self,
        temporada,
        numero_rodada,
        jogadores_escalados,
        liga_id=LIGA_BRASILEIRAO,
    ):
        return self.app_controller.montar_rodada_por_cache_rodada_api_football(
            liga_id=liga_id,
            temporada=temporada,
            rodada=self.nome_rodada_api(numero_rodada),
            numero_rodada=numero_rodada,
            jogadores_escalados=jogadores_escalados,
        )

    def adicionar_rodada(self, rodada):
        return self.app_controller.adicionar_rodada(rodada)
