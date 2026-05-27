from SofaFut.src.models.user import User
from src.repositories.users_database import UserDataBase
from src.services.session import Session
from SofaFut.src.services.team_fantasy_service import TeamFantasyService

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
        
        user.alterar_nome(novo_username)

        return "Username atualizado"
    
    def alterar_senha(self, username, senha_atual, nova_senha):

        self._verificar_permissao(username)

        user = self.user_database.search_user(username)

        if user is None: 
            return "Usuario nao encontrado"
        
        if user.verificar_senha(senha_atual):
            user.alterar_senha(nova_senha)
        else: 
            return "Senha incorreta"
        
    def atribuir_pontuacao(self, username, pontuacao):

        user = self.user_database.search_user(username)

        if user is not None:
            user.pontuacao += pontuacao

        else: 
            return "Usuario nao encontrado"
