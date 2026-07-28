from src.external.api_client import SofaScoreApiClient
from src.external.api_football_client import ApiFootballClient
from src.models.estatistics import Estatisticas
from src.models.player_fantasy import PlayerFantasy
from src.repositories.players_repository import PlayerRepository
from src.repositories.rounds_repository import RoundRepository
from src.repositories.users_database import UserDataBase
from src.services.auth_service import AuthService
from src.services.market_service import MarketService
from src.services.match_service import MatchService
from src.services.player_service import PlayerService
from src.services.session import Session
from src.services.team_fantasy_service import TeamFantasyService
from src.services.user_service import UserService


class AppController:
    """Ponto de entrada para comandos vindos da interface visual."""

    def __init__(
        self,
        user_database: UserDataBase | None = None,
        player_repository: PlayerRepository | None = None,
        round_repository: RoundRepository | None = None,
        sofa_api: SofaScoreApiClient | None = None,
        api_football: ApiFootballClient | None = None,
        session: Session | None = None,
    ):
        self.session = session or Session()
        self.user_database = user_database or UserDataBase()
        self.player_repository = player_repository or PlayerRepository(api_client=sofa_api)
        self.round_repository = round_repository or RoundRepository()
        self.api_football = api_football

        self.auth_service = AuthService(self.user_database, self.session)
        self.user_service = UserService(self.user_database, self.session)
        self.team_fantasy_service = TeamFantasyService()
        self.market_service = MarketService()
        self.player_service = PlayerService(self.player_repository)
        self.match_service = MatchService(
            sofa_api=sofa_api or SofaScoreApiClient(),
            api_football=self.api_football,
        )

    def cadastrar_usuario(
        self,
        username: str,
        cpf: str,
        email: str,
        senha: str,
        nome_team_fantasy: str | None = None,
    ):
        return self.auth_service.cadastrar(
            username=username,
            cpf=cpf,
            email=email,
            senha=senha,
            nome_team_fantasy=nome_team_fantasy,
        )

    def login(self, username: str, senha: str):
        return self.auth_service.login(username, senha)

    def logout(self):
        self.session.logout()
        return "Usuario deslogado"

    def usuario_logado(self):
        return self.session.current_user

    def alterar_email(self, username: str, novo_email: str):
        return self.user_service.alterar_email(username, novo_email)

    def alterar_nome(self, username: str, novo_username: str):
        return self.user_service.alterar_nome(username, novo_username)

    def alterar_senha(self, username: str, senha_atual: str, nova_senha: str):
        return self.user_service.alterar_senha(username, senha_atual, nova_senha)

    def listar_jogadores(
        self,
        criterio: Estatisticas | str | None = None,
        reverse=True,
    ):
        if criterio is None:
            return self.player_repository.listar_jogadores()

        if isinstance(criterio, str):
            nome_enum = criterio.upper()
            criterio = Estatisticas[nome_enum] if nome_enum in Estatisticas.__members__ else criterio

        return self.player_service.listar_jogadores_ordenados(criterio, reverse=reverse)

    def carregar_jogadores_brasileirao_temporada(
        self,
        temporada,
        liga_id=71,
        usar_cache=True,
        max_paginas=None,
        paginas_por_execucao=1,
    ):
        return self.player_service.carregar_jogadores_brasileirao_temporada(
            temporada=temporada,
            liga_id=liga_id,
            usar_cache=usar_cache,
            max_paginas=max_paginas,
            paginas_por_execucao=paginas_por_execucao,
        )

    def carregar_jogadores_temporada_cache(self, liga_id, temporada):
        return self.player_service.carregar_jogadores_temporada_cache(
            liga_id=liga_id,
            temporada=temporada,
        )

    def montar_escalacao(
        self,
        username: str,
        rodada: int,
        jogadores: list[PlayerFantasy],
    ):
        user = self._buscar_usuario_autorizado(username)
        return self.team_fantasy_service.montar_escalacao(user, rodada, jogadores)

    def executar_rodada(
        self,
        username: str,
        rodada: int,
        jogadores: list[PlayerFantasy],
    ):
        user = self._buscar_usuario_autorizado(username)
        self.team_fantasy_service.executar_rodada(
            user=user,
            rodada=rodada,
            jogadores=jogadores,
            rodadas_repo=self.round_repository,
        )
        return user.pontuacao

    def adicionar_rodada(self, rodada):
        self.round_repository.adicionar_rodada(rodada)
        return rodada

    def listar_rodadas(self):
        return self.round_repository.listar_rodadas()

    def buscar_partida(self, event_id: int):
        return self.match_service.get_match_info(event_id)

    def buscar_partidas_por_data(
        self,
        data,
        liga_id=None,
        temporada=None,
        time_id=None,
        status=None,
    ):
        return self.match_service.buscar_partidas_por_data(
            data=data,
            liga_id=liga_id,
            temporada=temporada,
            time_id=time_id,
            status=status,
        )

    def buscar_partidas_por_periodo(
        self,
        data_inicio,
        data_fim,
        liga_id=None,
        temporada=None,
        time_id=None,
        status=None,
    ):
        return self.match_service.buscar_partidas_por_periodo(
            data_inicio=data_inicio,
            data_fim=data_fim,
            liga_id=liga_id,
            temporada=temporada,
            time_id=time_id,
            status=status,
        )

    def buscar_partida_api_football(self, fixture_id):
        return self.match_service.buscar_partida_por_id(fixture_id)

    def buscar_estatisticas_jogadores_partida(self, fixture_id, time_id=None):
        return self.match_service.buscar_estatisticas_jogadores_partida(
            fixture_id=fixture_id,
            time_id=time_id,
        )

    def buscar_partidas_por_rodada_api_football(
        self,
        liga_id,
        temporada,
        rodada,
        status=None,
    ):
        return self.match_service.buscar_partidas_por_rodada_api_football(
            liga_id=liga_id,
            temporada=temporada,
            rodada=rodada,
            status=status,
        )

    def buscar_partidas_por_ids_api_football(self, fixture_ids):
        return self.match_service.buscar_partidas_por_ids_api_football(fixture_ids)

    def montar_rodada_por_fixture_api_football(
        self,
        fixture_id,
        numero_rodada,
        jogadores_escalados,
    ):
        return self.match_service.montar_rodada_por_fixture_api_football(
            fixture_id=fixture_id,
            numero_rodada=numero_rodada,
            jogadores_escalados=jogadores_escalados,
        )

    def baixar_dados_partida_api_football(self, fixture_id, usar_cache=True):
        return self.match_service.baixar_dados_partida_api_football(
            fixture_id=fixture_id,
            usar_cache=usar_cache,
        )

    def carregar_dados_partida_api_football(self, fixture_id):
        return self.match_service.carregar_dados_partida_api_football(fixture_id)

    def listar_jogadores_disponiveis_cache_api_football(self, fixture_id):
        return self.match_service.listar_jogadores_disponiveis_cache_api_football(
            fixture_id
        )

    def montar_rodada_por_cache_api_football(
        self,
        fixture_id,
        numero_rodada,
        jogadores_escalados,
    ):
        return self.match_service.montar_rodada_por_cache_api_football(
            fixture_id=fixture_id,
            numero_rodada=numero_rodada,
            jogadores_escalados=jogadores_escalados,
        )

    def baixar_dados_rodada_api_football(
        self,
        liga_id,
        temporada,
        rodada,
        status=None,
        usar_cache=True,
        max_partidas=None,
    ):
        return self.match_service.baixar_dados_rodada_api_football(
            liga_id=liga_id,
            temporada=temporada,
            rodada=rodada,
            status=status,
            usar_cache=usar_cache,
            max_partidas=max_partidas,
        )

    def carregar_dados_rodada_api_football(self, liga_id, temporada, rodada):
        return self.match_service.carregar_dados_rodada_api_football(
            liga_id,
            temporada,
            rodada,
        )

    def listar_jogadores_disponiveis_cache_rodada_api_football(
        self,
        liga_id,
        temporada,
        rodada,
    ):
        return self.match_service.listar_jogadores_disponiveis_cache_rodada_api_football(
            liga_id,
            temporada,
            rodada,
        )

    def montar_rodada_por_cache_rodada_api_football(
        self,
        liga_id,
        temporada,
        rodada,
        numero_rodada,
        jogadores_escalados,
    ):
        return self.match_service.montar_rodada_por_cache_rodada_api_football(
            liga_id=liga_id,
            temporada=temporada,
            rodada=rodada,
            numero_rodada=numero_rodada,
            jogadores_escalados=jogadores_escalados,
        )

    def gerar_ranking_usuarios(self):
        return self.user_service.gerar_ranking_usuarios()

    def exibir_ranking_usuarios(self):
        ranking = self.gerar_ranking_usuarios()
        return self.user_service.formatar_ranking_usuarios(ranking)

    def gerar_historico_pontuacao_usuario(self, username: str):
        return self.user_service.gerar_historico_pontuacao_usuario(username)

    def exibir_historico_pontuacao_usuario(self, username: str):
        historico = self.gerar_historico_pontuacao_usuario(username)
        return self.user_service.formatar_historico_pontuacao_usuario(historico)

    def comprar_jogador(self, username: str, jogador):
        user = self._buscar_usuario_autorizado(username)
        return self.market_service.comprar(user, jogador)

    def vender_jogador(self, username: str, jogador):
        user = self._buscar_usuario_autorizado(username)
        return self.market_service.vender(user, jogador)

    def limpar_elenco_rodada(self, username: str):
        user = self._buscar_usuario_autorizado(username)
        return self.market_service.limpar_elenco_rodada(user)

    def listar_elenco(self, username: str):
        user = self._buscar_usuario_autorizado(username)
        return user.team_fantasy.elenco

    def listar_transacoes_mercado(self, username: str):
        user = self._buscar_usuario_autorizado(username)
        return user.team_fantasy.transacoes

    def patrimonio_time_fantasy(self, username: str):
        user = self._buscar_usuario_autorizado(username)
        return user.team_fantasy.patrimonio

    def abrir_mercado(self):
        self.market_service.abrir_mercado()

    def fechar_mercado(self):
        self.market_service.fechar_mercado()

    def _buscar_usuario_autorizado(self, username: str):
        if not self.session.is_logged(username):
            raise PermissionError("Sem permissao")

        user = self.user_database.search_user(username)
        if user is None:
            raise ValueError("Usuario nao encontrado")

        return user
