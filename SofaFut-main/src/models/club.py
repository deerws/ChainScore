class Club():

    def __init__(self, nome, jogadores, vitorias, derrotas, empates, pos_tabela):

        self.__nome = nome
        self.__jogadores = jogadores
        self.__vitorias = vitorias
        self.__derrotas = derrotas
        self.__empates = empates
        self.__pos_tabela = pos_tabela

    @property
    def nome(self):
        return self.__nome

    @nome.setter
    def nome(self, nome):
        self.__nome = nome

    @property
    def jogadores(self):
        return self.__jogadores

    @jogadores.setter
    def jogadores(self, jogadores):
        self.__jogadores = jogadores

    @property
    def vitorias(self):
        return self.__vitorias

    @vitorias.setter
    def vitorias(self, vitorias):
        self.__vitorias = vitorias

    @property
    def derrotas(self):
        return self.__derrotas

    @derrotas.setter
    def derrotas(self, derrotas):
        self.__derrotas = derrotas

    @property
    def empates(self):
        return self.__empates

    @empates.setter
    def empates(self, empates):
        self.__empates = empates

    @property
    def pos_tabela(self):
        return self.__pos_tabela

    @pos_tabela.setter
    def pos_tabela(self, pos_tabela):
        self.__pos_tabela = pos_tabela