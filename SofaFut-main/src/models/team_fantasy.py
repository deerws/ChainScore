from src.models.lineup import Lineup

class TeamFantasy():

    def __init__(self, nome, patrimonio=110.0):

        self.__nome = nome
        self.__escalacoes : dict[int, Lineup] = {}
        self.__patrimonio = patrimonio
        self.__elenco = []
        self.__transacoes = []

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

    @property
    def patrimonio(self):
        return self.__patrimonio

    @patrimonio.setter
    def patrimonio(self, patrimonio):
        self.__patrimonio = patrimonio

    @property
    def elenco(self):
        return self.__elenco

    @elenco.setter
    def elenco(self, elenco):
        self.__elenco = elenco

    @property
    def transacoes(self):
        return self.__transacoes

    @transacoes.setter
    def transacoes(self, transacoes):
        self.__transacoes = transacoes
