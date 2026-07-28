from src.models.user import User

"""
Classe que controla o usuario logado no sistema
"""


class Session:

    def __init__(self):
        self.current__user = None

    def login(self, user : User):
        self.current__user = user

    def logout(self):
        self.current__user = None

    def is_logged(self, username):
        return self.current__user is not None and self.current__user.nome == username

    @property
    def current_user(self):
        return self.current__user
