from src.models.user import User
from src.models.lineup import Lineup
from src.repositories.users_database import UserDataBase
from src.services.session import Session
from src.services.team_fantasy_service import TeamFantasyService

"""Essa classe é a responsavel por executar a edicao dos dados.
Apesar de chamar os metodos de edicao de dados da classe Cliente
ele é responsavel por validar senhas e se o usuario esta presente na base de dados
antes de chamar os metodos de edicao de dados
"""
class UserService:

    def __init__(self, user_database : UserDataBase, session : Session):
        self.user_database = user_database
        self.session = session

    def _verificar_permissao(self, username):
        if not self.session.is_logged(username):
            raise PermissionError("Sem permissao")
        

    def alterar_email(self, username, novo_email):

        self._verificar_permissao(username)

        user = self.user_database.search_user(username)

        if user is None:
            return "Usuario nao encontrado"
        
        user.alterar_email(novo_email)
        return "Email atualizado"
    
    def alterar_nome(self, username, novo_username):

        self._verificar_permissao(username)

        user = self.user_database.search_user(username)

        if user is None:
            return "Usuario nao encontrado"
        
        return self.user_database.update_username(username, novo_username)
    
    def alterar_senha(self, username, senha_atual, nova_senha):

        self._verificar_permissao(username)

        user = self.user_database.search_user(username)

        if user is None: 
            return "Usuario nao encontrado"
        
        if user.verificar_senha(senha_atual):
            user.alterar_senha(nova_senha)
            return "Senha atualizada"
        else: 
            return "Senha incorreta"
        
    def atribuir_pontuacao(self, username, pontuacao):

        user = self.user_database.search_user(username)

        if user is not None:
            user.pontuacao += pontuacao
            return "Pontuacao atualizada"

        else: 
            return "Usuario nao encontrado"

    def gerar_ranking_usuarios(self) -> list[User]:
        ranking = self.user_database.listar_usuarios()
        ranking.sort(
            key=lambda user: (
                -user.pontuacao,
                -user.saldo,
                user.nome,
            )
        )
        return ranking

    def formatar_ranking_usuarios(self, ranking: list[User]):
        if not ranking:
            return "Ranking de usuarios vazio"

        linhas = []
        for posicao, user in enumerate(ranking, start=1):
            linhas.append(
                f"{posicao}. {user.nome} - "
                f"{user.pontuacao} pontos - saldo {user.saldo:.2f}"
            )

        return "\n".join(linhas)

    def gerar_historico_pontuacao_usuario(self, username) -> list[Lineup]:
        user = self.user_database.search_user(username)

        if user is None:
            return []

        historico = list(user.team_fantasy.escalacoes.values())
        historico.sort(key=lambda escalacao: escalacao.rodada)
        return historico

    def formatar_historico_pontuacao_usuario(
        self,
        historico: list[Lineup],
    ):
        if not historico:
            return "Historico de pontuacao vazio"

        linhas = []
        for escalacao in historico:
            linhas.append(
                f"Rodada {escalacao.rodada}: {escalacao.pontuacao} pontos"
            )

        return "\n".join(linhas)
