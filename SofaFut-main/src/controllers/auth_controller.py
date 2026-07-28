from src.controllers.app_controller import AppController


class AuthController:
    def __init__(self, app_controller: AppController):
        self.app_controller = app_controller

    def cadastrar(
        self,
        username,
        senha,
        cpf="000",
        email=None,
        nome_team_fantasy=None,
    ):
        return self.app_controller.cadastrar_usuario(
            username=username,
            cpf=cpf,
            email=email or f"{username}@email.com",
            senha=senha,
            nome_team_fantasy=nome_team_fantasy or f"{username} FC",
        )

    def login(self, username, senha):
        return self.app_controller.login(username, senha)

    def logout(self):
        return self.app_controller.logout()

    def usuario_logado(self):
        return self.app_controller.usuario_logado()
