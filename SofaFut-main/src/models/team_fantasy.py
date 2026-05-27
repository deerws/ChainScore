from src.models.lineup import Lineup

class TeamFantasy():

    def __init__(self, nome):

        self.__nome = nome
        self.__escalacoes : dict[int, Lineup] = {}

    @property
    def nome(self):
        return self.__nome

    @nome.setter
    def nome(self, nome):
        self.__nome = nome

    @property
    def escalacoes(self):
        return self.__escalacoes

    @escalacoes.setter
    def escalacoes(self, escalacoes):
        self.__escalacoes = escalacoes