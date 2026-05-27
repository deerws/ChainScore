from src.models.player import Player

class PlayerFantasy:

    def __init__(self, jogador : Player, capitao : bool, pontuacao):
    
        self.jogador = jogador
        self.capitao = capitao
        self.pontuacao = pontuacao

    