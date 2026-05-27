from src.repositories.users_database import UserDataBase
from SofaFut.src.models.user import User
from src.services.session import Session

"""
Essa classe faz o protocolo de autenticacao do usuario
login e cadastro basicamente
"""

class AuthService: 

    def __init__(self, user_database : UserDataBase, session : Session):

        self.user_database = user_database
        self.session = session

    def cadastrar(self, username, cpf, email, senha):

        if self.user_database.search_user(username) is None:
            
            self.user_database.add_user(User(username, cpf, email, senha))

        else:
            print("Usuario com esse username ja cadastrado")

        return "Usuario cadastrado"
    
    def login(self, username, senha):


        user = self.user_database.search_user(username)

        if user is not None:

            if user.verificar_senha(senha) and not self.session.is_logged(username):
                self.session.login(user)

                return "Usuario Loggado" 
            
            else:
                print("Senha invalida ou usuario ja logado")
        
        else:
            print("Usuario nao encontrado")

