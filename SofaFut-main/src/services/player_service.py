
from src.repositories.players_repository import PlayerRepository
from src.models.estatistics import Estatisticas
from src.models.player import Player

class PlayerService:

    def __init__(self, player_repository : PlayerRepository):
        self.player_repository = player_repository

    def listar_jogadores_ordenados(self, criterio : Estatisticas) -> list[Player]:
        
        jogadores = self.player_repository.listar_jogadores()

        jogadores.sort(key=lambda jogador : getattr(jogador, criterio.value), reverse=True)

        return jogadores