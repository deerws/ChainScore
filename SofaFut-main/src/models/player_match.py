from src.models.player import Player

class MatchPlayerStats:

    def __init__(
        self,
        jogador: Player,
        atuou : bool,
        titular : bool,
        gols,
        assistencias,
        cartoes_amarelos,
        cartoes_vermelhos,
        faltas,
        gols_sofridos,
    ):
    
        self.jogador = jogador
        self.atuou = atuou
        self.titular = titular
        self.gols = gols
        self.assistencias = assistencias
        self.cartoes_amarelos = cartoes_amarelos
        self.cartoes_vermelhos = cartoes_vermelhos
        self.faltas = faltas
        self.gols_sofridos = gols_sofridos