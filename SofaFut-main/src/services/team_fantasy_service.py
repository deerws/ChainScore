from src.models.match import Match
from src.models.rounds import Round
from src.models.lineup import Lineup
from src.models.player_match import MatchPlayerStats
from src.models.player_fantasy import PlayerFantasy
from src.models.player import Player
from src.repositories.rounds_repository import RoundRepository
from src.models.user import User
from src.models.team_fantasy import TeamFantasy

class TeamFantasyService:

    def calcular_pontuacao_lineup(self, escalacao : Lineup, rodadas_repo : RoundRepository):

        round = rodadas_repo.buscar_por_numero(escalacao.rodada)

        for partida in round.partidas:
            for jogador in partida.jogadores_partida: # acessa os players_match
                for jogador_fantasy in escalacao.jogadores: # acesssa os player_fantasy
                    
                    if jogador_fantasy.jogador == jogador.jogador: # verifica se ambos player_ referenciam o mesmo jogador
                        jogador_fantasy.pontuacao = self.calculo_pontuacao_logica(jogador, jogador_fantasy.capitao)
                        escalacao.pontuacao += jogador_fantasy.pontuacao

        return escalacao.pontuacao

    def calculo_pontuacao_logica(self, jogador : MatchPlayerStats, capitao : bool):
        pontuacao = 0
        if jogador.atuou:

            pontuacao += jogador.gols * 40 
            pontuacao += jogador.assistencias * 20
            pontuacao -= jogador.cartoes_amarelos * 10
            pontuacao -= jogador.cartoes_vermelhos * 50
            pontuacao += jogador.faltas * 3
            pontuacao -= jogador.gols_sofridos * 10

        if capitao:
            pontuacao *= 2

        return pontuacao
    
    def montar_escalacao(self, user : User, rodada : int, jogadores : list[PlayerFantasy]):
        team = user.team_fantasy

        if len(jogadores) != 11:
            raise Exception("QUANTIDADE INCORRETA DE JOGADORES")        

        capitao = 0
        for jogador in jogadores:
            if jogador.capitao:
                capitao += 1

        if capitao != 1: 
            raise Exception("QUANTIDADE DE CAPITAO INCORRETA")
        
        team.escalacoes[rodada] = Lineup(rodada=rodada, jogadores=jogadores)

        return team.escalacoes[rodada]


    def executar_rodada(self, user : User, rodada : int, jogadores : list[PlayerFantasy], rodadas_repo : RoundRepository):
        
        # primeiro tem que fazer uma verificacao se a rodada ja existe, se ja existir vai estar em cache em algum arquivo json
        # e dai é so acessar o arquivo. Se nao estiver dai tem que ver se faz uma chamada de API pra verificar se esta disponivel

        lineup = self.montar_escalacao(user, rodada, jogadores)

        user.pontuacao += self.calcular_pontuacao_lineup(lineup, rodadas_repo)
        
