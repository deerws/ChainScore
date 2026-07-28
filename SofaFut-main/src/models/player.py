class Player:

    def __init__(
        self,
        nome,
        time=None,
        posicao=None,
        idade=0,
        api_id=None,
        nome_time=None,
        valor_mercado=10.0,
    ):
        
        self.__nome = nome
        self.__time = time
        self.__posicao = posicao
        self.__idade = idade
        self.__api_id = api_id
        self.__nome_time = nome_time
        self.__valor_mercado = valor_mercado
        

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

    @property
    def api_id(self):
        return self.__api_id

    @api_id.setter
    def api_id(self, api_id):
        self.__api_id = api_id

    @property
    def nome_time(self):
        return self.__nome_time

    @nome_time.setter
    def nome_time(self, nome_time):
        self.__nome_time = nome_time

    @property
    def valor_mercado(self):
        return self.__valor_mercado

    @valor_mercado.setter
    def valor_mercado(self, valor_mercado):
        self.__valor_mercado = valor_mercado
