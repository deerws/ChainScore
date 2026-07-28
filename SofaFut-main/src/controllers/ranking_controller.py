from src.controllers.app_controller import AppController


class RankingController:
    def __init__(self, app_controller: AppController):
        self.app_controller = app_controller

    def gerar_ranking_usuarios(self):
        return self.app_controller.gerar_ranking_usuarios()

    def formatar_ranking_usuarios(self):
        return self.app_controller.exibir_ranking_usuarios()

    def historico_pontuacao_usuario(self, username):
        return self.app_controller.gerar_historico_pontuacao_usuario(username)

    def formatar_historico_pontuacao_usuario(self, username):
        return self.app_controller.exibir_historico_pontuacao_usuario(username)
