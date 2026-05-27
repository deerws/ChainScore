from src.models.player import Player
from src.models.player_fantasy import PlayerFantasy
class Lineup():

    def __init__(self, rodada, jogadores : list[PlayerFantasy]):

        self.__rodada = rodada
        self.__jogadores = jogadores
        self.__pontuacao = 0

    @property
    def rodada(self):
        return self.__rodada

    @rodada.setter
    def rodada(self, rodada):
        self.__rodada = rodada

    @property
    def jogadores(self):
        return self.__jogadores

    @jogadores.setter
    def jogadores(self, jogadores):
        self.__jogadores = jogadores

    @property
    def pontuacao(self):
        return self.__pontuacao

    @pontuacao.setter
    def pontuacao(self, pontuacao):
        self.__pontuacao = pontuacao