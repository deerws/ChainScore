from src.controllers.app_controller import AppController


class PlayerCatalogController:
    def __init__(self, app_controller: AppController):
        self.app_controller = app_controller

    def carregar_jogadores_temporada(
        self,
        temporada,
        liga_id=71,
        usar_cache=True,
        max_paginas=None,
        paginas_por_execucao=1,
    ):
        return self.app_controller.carregar_jogadores_brasileirao_temporada(
            temporada=temporada,
            liga_id=liga_id,
            usar_cache=usar_cache,
            max_paginas=max_paginas,
            paginas_por_execucao=paginas_por_execucao,
        )

    def listar_jogadores(self):
        return self.app_controller.listar_jogadores()

    def listar_jogadores_ordenados(self, criterio, reverse=True):
        return self.app_controller.listar_jogadores(criterio=criterio, reverse=reverse)

    def buscar_por_nome(self, nome):
        nome_normalizado = self._normalizar_nome(nome)

        for jogador in self.listar_jogadores():
            if self._normalizar_nome(jogador.nome) == nome_normalizado:
                return jogador

        return None

    def buscar_por_api_id(self, api_id):
        for jogador in self.listar_jogadores():
            if jogador.api_id == api_id:
                return jogador

        return None

    def _normalizar_nome(self, nome):
        return (nome or "").casefold().strip()
