class ConsoleView:
    def mostrar_login(self, mensagem):
        print(mensagem)

    def mostrar_temporada_rodada(self, temporada, numero_rodada):
        print(f"\nTemporada escolhida: {temporada}")
        print(f"Rodada escolhida: {numero_rodada}")

    def mostrar_catalogo_jogadores(self, jogadores, limite=20):
        print(f"\nJogadores conhecidos no sistema: {len(jogadores)}")

        if not jogadores:
            print("Nenhum jogador carregado.")
            return

        for indice, jogador in enumerate(jogadores[:limite], start=1):
            nome_time = jogador.nome_time or "sem time"
            print(
                f"{indice}. [{jogador.api_id}] {jogador.nome} - "
                f"{nome_time} - {jogador.posicao}"
            )

        if len(jogadores) > limite:
            print(f"... e mais {len(jogadores) - limite} jogadores.")

    def mostrar_resumo_cache_rodada(self, dados_rodada):
        total_partidas = len(dados_rodada.get("partidas_api", {}).get("response", []))
        total_cacheadas = len(dados_rodada.get("partidas", []))
        print(
            f"\nPartidas com estatisticas em cache: "
            f"{total_cacheadas}/{total_partidas}"
        )

    def mostrar_jogadores_disponiveis_rodada(self, jogadores, limite=40):
        print("\nJogadores disponiveis na rodada:")

        if not jogadores:
            print("Nenhum jogador disponivel no cache da rodada.")
            return

        for indice, jogador in enumerate(jogadores[:limite], start=1):
            print(
                f"{indice}. {jogador['nome']} - {jogador['time']} - "
                f"{jogador['posicao']} - {jogador['minutos']} minutos - "
                f"{jogador['partida']}"
            )

        if len(jogadores) > limite:
            print(f"... e mais {len(jogadores) - limite} jogadores.")

    def mostrar_pontuacao(self, numero_rodada, pontuacao_total, jogadores_fantasy):
        print(f"\nPontuacao total da rodada {numero_rodada}: {pontuacao_total}")
        print("Pontuacao por jogador:")

        for jogador_fantasy in jogadores_fantasy:
            jogador = jogador_fantasy.jogador
            capitao = " (capitao)" if jogador_fantasy.capitao else ""
            print(
                f"- {jogador.nome}{capitao}: "
                f"{jogador_fantasy.pontuacao} pontos"
            )

    def mostrar_ranking(self, ranking_formatado):
        print("\nRanking de usuarios:")
        print(ranking_formatado)

    def mostrar_erro(self, mensagem):
        print(f"Erro: {mensagem}")
