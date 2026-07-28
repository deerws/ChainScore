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

    def listar_usuarios(self):
        return list(self.__usuarios_cadastrados.values())

    def update_username(self, username, novo_username):
        if novo_username in self.__usuarios_cadastrados:
            return "Usuario com esse username ja cadastrado"

        user = self.__usuarios_cadastrados.pop(username, None)
        if user is None:
            return "Usuario nao encontrado"

        user.alterar_nome(novo_username)
        self.__usuarios_cadastrados[novo_username] = user
        return "Username atualizado"
