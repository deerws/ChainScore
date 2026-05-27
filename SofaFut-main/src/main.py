from src.repositories.players_repository import PlayerRepository
from src.services.player_service import PlayerService
from src.models.estatistics import Estatisticas
#from src.external.api_client import SofaScoreApiClient
from src.services.team_fantasy_service import TeamFantasyService
from src.models.match import Match
from src.models.rounds import Round
from src.models.lineup import Lineup
from src.models.player_match import MatchPlayerStats
from src.models.player_fantasy import PlayerFantasy
from src.models.player import Player
from src.repositories.rounds_repository import RoundRepository
from src.models.club import Club


def main():

    # api = SofaScoreApiClient(timeout=10)
    
    # try:
    #     data = api.search("internacional")
    # except Exception as e:
    #     print(f"Erro: {e}")

    # =========================
    # Players
    # =========================
    alan = Player("Alan Patrick", None, "meia", 33)
    borre = Player("Borré", None, "atacante", 28)
    rochet = Player("Rochet", None, "goleiro", 31)

    arrascaeta = Player("Arrascaeta", None, "meia", 30)
    pedro = Player("Pedro", None, "atacante", 27)
    leo_pereira = Player("Leo Pereira", None, "zagueiro", 29)

    # =========================
    # Clubs
    # =========================
    internacional = Club("Internacional", [alan, borre, rochet], 0, 0, 0, 1)
    flamengo = Club("Flamengo", [arrascaeta, pedro, leo_pereira], 0, 0, 0, 2)

    # liga os players aos clubes
    alan.clube = internacional
    borre.clube = internacional
    rochet.clube = internacional

    arrascaeta.clube = flamengo
    pedro.clube = flamengo
    leo_pereira.clube = flamengo

    # =========================
    # MatchPlayerStats
    # =========================
    stats_alan = MatchPlayerStats(
        jogador=alan,
        atuou=True,
        titular=True,
        gols=1,
        assistencias=1,
        cartoes_amarelos=1,
        cartoes_vermelhos=0,
        faltas=2,
        gols_sofridos=0
    )

    stats_borre = MatchPlayerStats(
        jogador=borre,
        atuou=True,
        titular=True,
        gols=1,
        assistencias=0,
        cartoes_amarelos=0,
        cartoes_vermelhos=0,
        faltas=1,
        gols_sofridos=0
    )

    stats_rochet = MatchPlayerStats(
        jogador=rochet,
        atuou=True,
        titular=True,
        gols=0,
        assistencias=0,
        cartoes_amarelos=0,
        cartoes_vermelhos=0,
        faltas=0,
        gols_sofridos=1
    )

    stats_arrascaeta = MatchPlayerStats(
        jogador=arrascaeta,
        atuou=True,
        titular=True,
        gols=0,
        assistencias=1,
        cartoes_amarelos=0,
        cartoes_vermelhos=0,
        faltas=3,
        gols_sofridos=0
    )

    stats_pedro = MatchPlayerStats(
        jogador=pedro,
        atuou=True,
        titular=True,
        gols=1,
        assistencias=0,
        cartoes_amarelos=1,
        cartoes_vermelhos=0,
        faltas=1,
        gols_sofridos=0
    )

    stats_leo = MatchPlayerStats(
        jogador=leo_pereira,
        atuou=True,
        titular=True,
        gols=0,
        assistencias=0,
        cartoes_amarelos=0,
        cartoes_vermelhos=0,
        faltas=2,
        gols_sofridos=2
    )

    # =========================
    # Match
    # =========================
    partida = Match(
        mandante=internacional,
        visitante=flamengo,
        data="2026-05-17",
        jogadores_partida=[
            stats_alan,
            stats_borre,
            stats_rochet,
            stats_arrascaeta,
            stats_pedro,
            stats_leo
        ]
    )

    # =========================
    # Round 0
    # =========================
    rodada0 = Round(0)
    rodada0.adicionar_partidas_rodada(partida)

    # =========================
    # Repository de rodadas
    # =========================
    rodadas_repo = RoundRepository()
    rodadas_repo.adicionar_rodada(rodada0)

    # =========================
    # Escalacao fantasy
    # =========================
    fantasy_alan = PlayerFantasy(alan, True, 0)
    fantasy_borre = PlayerFantasy(borre, False, 0)
    fantasy_pedro = PlayerFantasy(pedro, False, 0)

    escalacao = Lineup(
        rodada=0,
        jogadores=[fantasy_alan, fantasy_borre, fantasy_pedro]
    )

    # =========================
    # Calcula pontuacao
    # =========================
    service = TeamFantasyService()
    pontuacao = service.calcular_pontuacao_lineup(escalacao, rodadas_repo)

    print("Pontuação total da escalação:", pontuacao)

    for jogador in escalacao.jogadores:
        print(f"{jogador.jogador.nome} = {jogador.pontuacao}")


if __name__ == "__main__":
    main()