import os
import tkinter as tk

from src.controllers import AppController
from src.controllers import AuthController
from src.controllers import LineupController
from src.controllers import MarketController
from src.controllers import PlayerCatalogController
from src.controllers import RankingController
from src.controllers import RoundController
from src.views import ConsoleView
from src.views import SofaFutGui


def main():
    app_controller = AppController()
    auth_controller = AuthController(app_controller)
    player_catalog_controller = PlayerCatalogController(app_controller)
    round_controller = RoundController(app_controller)
    lineup_controller = LineupController(app_controller)
    ranking_controller = RankingController(app_controller)
    market_controller = MarketController(app_controller)

    if os.getenv("SOFAFUT_VIEW") == "console":
        executar_console(
            auth_controller,
            player_catalog_controller,
            round_controller,
            lineup_controller,
            ranking_controller,
            market_controller,
        )
        return

    try:
        app = _criar_app_grafico(
            auth_controller=auth_controller,
            player_catalog_controller=player_catalog_controller,
            round_controller=round_controller,
            lineup_controller=lineup_controller,
            ranking_controller=ranking_controller,
            market_controller=market_controller,
        )
        app.run()
    except tk.TclError as erro:
        print(f"Nao foi possivel abrir interface grafica: {erro}")
        print("Rodando fluxo de console. Para forcar console: SOFAFUT_VIEW=console")
        executar_console(
            auth_controller,
            player_catalog_controller,
            round_controller,
            lineup_controller,
            ranking_controller,
            market_controller,
        )


def executar_console(
    auth_controller,
    player_catalog_controller,
    round_controller,
    lineup_controller,
    ranking_controller,
    market_controller=None,
):
    view = ConsoleView()

    if not os.getenv("API_FOOTBALL_KEY"):
        print("Aviso: API_FOOTBALL_KEY ausente. O console só funcionará com caches já existentes.")

    try:
        testar_fluxo_console(
            view=view,
            auth_controller=auth_controller,
            player_catalog_controller=player_catalog_controller,
            round_controller=round_controller,
            lineup_controller=lineup_controller,
            ranking_controller=ranking_controller,
        )
    except RuntimeError as erro:
        view.mostrar_erro(str(erro))


def testar_fluxo_console(
    view,
    auth_controller,
    player_catalog_controller,
    round_controller,
    lineup_controller,
    ranking_controller,
):
    liga_id = _env_int("API_FOOTBALL_LEAGUE_ID", padrao=71)
    temporada = _env_int("API_FOOTBALL_SEASON", padrao=2024)
    numero_rodada = _env_int("SOFAFUT_ROUND_NUMBER", padrao=2)
    max_partidas = _env_int("API_FOOTBALL_MAX_FIXTURES", padrao=2)

    username = "lucas"
    senha = "senha"

    auth_controller.cadastrar(
        username=username,
        senha=senha,
        cpf="000",
        email="lucas@email.com",
        nome_team_fantasy="SofaFut FC",
    )
    view.mostrar_login(auth_controller.login(username, senha))

    view.mostrar_temporada_rodada(temporada, numero_rodada)

    jogadores_temporada = player_catalog_controller.carregar_jogadores_temporada(
        liga_id=liga_id,
        temporada=temporada,
    )
    view.mostrar_catalogo_jogadores(jogadores_temporada)

    dados_rodada = round_controller.baixar_dados_rodada(
        liga_id=liga_id,
        temporada=temporada,
        numero_rodada=numero_rodada,
        status="FT",
        max_partidas=max_partidas,
    )
    view.mostrar_resumo_cache_rodada(dados_rodada)

    jogadores_disponiveis = round_controller.listar_jogadores_disponiveis(
        liga_id=liga_id,
        temporada=temporada,
        numero_rodada=numero_rodada,
    )
    view.mostrar_jogadores_disponiveis_rodada(jogadores_disponiveis)

    if len(jogadores_disponiveis) < 11:
        raise RuntimeError("Nao ha jogadores suficientes no cache para montar escalacao.")

    jogadores = lineup_controller.selecionar_players_do_catalogo(
        jogadores_disponiveis[:11]
    )

    if len(jogadores) < 11:
        raise RuntimeError(
            "Catalogo de jogadores ainda nao contem os 11 jogadores escolhidos. "
            "Atualize manualmente o arquivo data/api_football/players_available.json."
        )

    jogadores_fantasy = lineup_controller.criar_escalacao_fantasy(jogadores)

    rodada_model = round_controller.montar_rodada_por_cache(
        liga_id=liga_id,
        temporada=temporada,
        numero_rodada=numero_rodada,
        jogadores_escalados=jogadores,
    )
    round_controller.adicionar_rodada(rodada_model)

    pontuacao_total = lineup_controller.executar_rodada(
        username=username,
        numero_rodada=numero_rodada,
        jogadores_fantasy=jogadores_fantasy,
    )
    escalacao = lineup_controller.buscar_escalacao(numero_rodada)
    jogadores_calculados = escalacao.jogadores if escalacao is not None else jogadores_fantasy

    view.mostrar_pontuacao(
        numero_rodada,
        pontuacao_total,
        jogadores_calculados,
    )
    view.mostrar_ranking(ranking_controller.formatar_ranking_usuarios())


def _criar_app_grafico(
    auth_controller,
    player_catalog_controller,
    round_controller,
    lineup_controller,
    ranking_controller,
    market_controller,
):
    if os.getenv("SOFAFUT_GUI") == "tkinter":
        return SofaFutGui(
            auth_controller=auth_controller,
            player_catalog_controller=player_catalog_controller,
            round_controller=round_controller,
            lineup_controller=lineup_controller,
            ranking_controller=ranking_controller,
            market_controller=market_controller,
        )

    try:
        from src.views.pyside_view import SofaFutPySideGui
    except ImportError:
        return SofaFutGui(
            auth_controller=auth_controller,
            player_catalog_controller=player_catalog_controller,
            round_controller=round_controller,
            lineup_controller=lineup_controller,
            ranking_controller=ranking_controller,
            market_controller=market_controller,
        )

    return SofaFutPySideGui(
        auth_controller=auth_controller,
        player_catalog_controller=player_catalog_controller,
        round_controller=round_controller,
        lineup_controller=lineup_controller,
        ranking_controller=ranking_controller,
        market_controller=market_controller,
    )


def _env_int(nome, padrao=None):
    valor = os.getenv(nome)
    if not valor:
        return padrao
    return int(valor)


if __name__ == "__main__":
    main()
