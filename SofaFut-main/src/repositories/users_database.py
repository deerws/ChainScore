from src.models.user import User

"""
Essa classe é basicamente o banco de dados. 
Por enquanto busca e adiciona usuarios na base de dados
"""
class UserDataBase:

    def __init__(self):

        self.__usuarios_cadastrados = {}

    def add_user(self, user : User):

        self.__usuarios_cadastrados[user.nome] = user

    def search_user(self, username):
        return self.__usuarios_cadastrados.get(username)