from src.models.user import User
from src.repositories.users_database import UserDataBase
from src.services.session import Session

"""
Essa classe faz o protocolo de autenticacao do usuario:
login e cadastro basicamente.
"""


class AuthService:

    def __init__(self, user_database: UserDataBase, session: Session):
        self.user_database = user_database
        self.session = session

    def cadastrar(self, username, cpf, email, senha, nome_team_fantasy=None):
        if self.user_database.search_user(username) is not None:
            return "Usuario com esse username ja cadastrado"

        user = User(
            username,
            cpf,
            email,
            senha,
            0,
            0,
            nome_team_fantasy or f"Time de {username}",
        )
        self.user_database.add_user(user)
        return "Usuario cadastrado"

    def login(self, username, senha):
        user = self.user_database.search_user(username)

        if user is None:
            return "Usuario nao encontrado"

        if user.verificar_senha(senha) and not self.session.is_logged(username):
            self.session.login(user)
            return "Usuario logado"

        return "Senha invalida ou usuario ja logado"
