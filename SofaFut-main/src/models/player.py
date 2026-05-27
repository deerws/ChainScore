from src.models.club import Club

class Player:

    def __init__(self, nome, time : Club, posicao, idade):
        
        self.__nome = nome
        self.__time = time
        self.__posicao = posicao
        self.__idade = idade
        

    @property
    def nome(self):
        return self.__nome

    @nome.setter
    def nome(self, nome):
        self.__nome = nome

    @property
    def time(self):
        return self.__time

    @time.setter
    def time(self, time):
        self.__time = time

    @property
    def posicao(self):
        return self.__posicao

    @posicao.setter
    def posicao(self, posicao):
        self.__posicao = posicao

    @property
    def idade(self):
        return self.__idade

    @idade.setter
    def idade(self, idade):
        self.__idade = idade
