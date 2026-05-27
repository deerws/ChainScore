import hashlib
import errno
import os, pathlib
#from external import sofascore_api
from src.models.team_fantasy import TeamFantasy

"""
Classe do cliente. Os metodos de alterar dados (email, nome e senha) nao devem
ser chamados sozinhos. Quem faz as verificacoes antes de chamar é a classe UserService
"""

class User:
    def __init__(self, nome, cpf, email, senha, pontuacao, saldo, nome_team_fantasy):

        self.__nome = nome
        self.__cpf = cpf
        self.__email = email
        self.__senha = self._generate_hash(senha)
        self.__pontuacao = pontuacao
        self.__saldo = saldo
        self.__team_fantasy = TeamFantasy(nome_team_fantasy)

    def _generate_hash(self, senha):
        return hashlib.sha256(senha.encode()).hexdigest()
    
    def verificar_senha(self, tentativa_senha):
        return self._generate_hash(tentativa_senha) == self.__senha
    
    def alterar_email(self, novo_email):
        self.email = novo_email
    
    def alterar_nome(self, novo_nome):
        self.nome = novo_nome

    def alterar_senha(self, nova_senha):
        self.__senha = self._generate_hash(nova_senha)

    @property
    def nome(self):
        return self.__nome
    
    @property
    def cpf(self):
        return self.__cpf
    
    @property
    def email(self):
        return self.__email
    
    @property
    def pontuacao(self):
        return self.__pontuacao
    
    @property
    def saldo(self):
        return self.__saldo
    
    @nome.setter
    def nome(self, valor):
        self.__nome = valor

    @cpf.setter
    def cpf(self, valor):
        self.__cpf = valor

    @email.setter
    def email(self, valor):
        self.__email = valor
    
    @pontuacao.setter
    def pontuacao(self, valor):
        self.__pontuacao = valor

    @saldo.setter
    def saldo(self, valor):
        self.__saldo = valor
    
    @property
    def team_fantasy(self):
        return self.__team_fantasy
    
    @team_fantasy.setter
    def team_fantasy(self, nome):
        self.__team_fantasy = nome
    


    
