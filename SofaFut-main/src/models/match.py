from src.models.player_match import MatchPlayerStats
from src.models.club import Club

class Match:

    def __init__(self, mandante : Club, visitante : Club, data, jogadores_partida : list[MatchPlayerStats]):
        self.__mandante = mandante
        self.__visitante = visitante
        self.__data = data
        self.__jogadores_partida = jogadores_partida

    @property
    def mandante(self):
        return self.__mandante

    @mandante.setter
    def mandante(self, mandante):
        self.__mandante = mandante

    @property
    def visitante(self):
        return self.__visitante

    @visitante.setter
    def visitante(self, visitante):
        self.__visitante = visitante

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, data):
        self.__data = data

    @property
    def jogadores_partida(self):
        return self.__jogadores_partida

    @jogadores_partida.setter
    def jogadores_partida(self, jogadores_partida):
        self.__jogadores_partida = jogadores_partida

    def adicionar_jogador_partida(self, jogador : MatchPlayerStats):
        self.jogadores_partida.append(jogador)