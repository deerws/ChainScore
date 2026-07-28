import tkinter as tk
from tkinter import messagebox
from tkinter import ttk


class SofaFutGui:
    def __init__(
        self,
        auth_controller,
        player_catalog_controller,
        round_controller,
        lineup_controller,
        ranking_controller,
        market_controller=None,
    ):
        self.auth_controller = auth_controller
        self.player_catalog_controller = player_catalog_controller
        self.round_controller = round_controller
        self.lineup_controller = lineup_controller
        self.ranking_controller = ranking_controller
        self.market_controller = market_controller
        self.username = None
        self.jogadores_catalogo = []
        self.jogadores_disponiveis = []
        self.jogadores_mercado = []
        self.jogadores_escalados = []
        self.jogadores_fantasy = []
        self.capitao = None
        self.sort_directions = {}

        self.root = tk.Tk()
        self.root.title("SofaFut")
        self.root.geometry("1180x760")
        self.root.minsize(980, 640)
        self._configurar_estilo()
        self._montar_layout()

    def run(self):
        self.root.mainloop()

    def _configurar_estilo(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#f7f4ef")
        style.configure("TLabel", background="#f7f4ef", foreground="#260d33")
        style.configure("Title.TLabel", foreground="#003f69", font=("Arial", 22, "bold"))
        style.configure("Subtitle.TLabel", foreground="#106b87", font=("Arial", 10))
        style.configure("TButton", padding=(10, 6), font=("Arial", 10, "bold"))
        style.configure("Accent.TButton", background="#003f69", foreground="#ffffff")
        style.configure("Treeview", rowheight=28)
        style.configure("Treeview.Heading", background="#003f69", foreground="#ffffff", font=("Arial", 10, "bold"))

    def _montar_layout(self):
        self.root.configure(background="#f7f4ef")
        self.container = ttk.Frame(self.root, padding=18)
        self.container.pack(fill=tk.BOTH, expand=True)
        self._montar_tela_login()

    def _limpar_container(self):
        for child in self.container.winfo_children():
            child.destroy()

    def _montar_tela_login(self):
        self._limpar_container()
        wrapper = ttk.Frame(self.container)
        wrapper.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        ttk.Label(wrapper, text="SofaFut", style="Title.TLabel").grid(row=0, column=0, columnspan=2, pady=(0, 8))
        ttk.Label(
            wrapper,
            text="Entre ou cadastre-se para montar sua escalação.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, columnspan=2, pady=(0, 24))

        ttk.Label(wrapper, text="Usuário").grid(row=2, column=0, sticky=tk.W, padx=6, pady=6)
        self.username_entry = ttk.Entry(wrapper, width=34)
        self.username_entry.grid(row=2, column=1, padx=6, pady=6)

        ttk.Label(wrapper, text="Senha").grid(row=3, column=0, sticky=tk.W, padx=6, pady=6)
        self.password_entry = ttk.Entry(wrapper, width=34, show="*")
        self.password_entry.grid(row=3, column=1, padx=6, pady=6)

        buttons = ttk.Frame(wrapper)
        buttons.grid(row=4, column=0, columnspan=2, pady=(18, 0))
        ttk.Button(buttons, text="Entrar", command=self._login).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text="Cadastrar", command=self._cadastrar).pack(side=tk.LEFT, padx=6)

        self.status_label = ttk.Label(wrapper, text="", style="Subtitle.TLabel")
        self.status_label.grid(row=5, column=0, columnspan=2, pady=(16, 0))

    def _login(self):
        username = self.username_entry.get().strip()
        senha = self.password_entry.get().strip()
        if not username or not senha:
            self._mostrar_erro("Preencha usuário e senha.")
            return

        mensagem = self.auth_controller.login(username, senha)
        if mensagem != "Usuario logado":
            self.status_label.configure(text=mensagem)
            return

        self.username = username
        self._montar_tela_principal()

    def _cadastrar(self):
        username = self.username_entry.get().strip()
        senha = self.password_entry.get().strip()
        if not username or not senha:
            self._mostrar_erro("Preencha usuário e senha.")
            return

        mensagem = self.auth_controller.cadastrar(username=username, senha=senha)
        self.status_label.configure(text=mensagem)

    def _montar_tela_principal(self):
        self._limpar_container()
        header = ttk.Frame(self.container)
        header.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(header, text="SofaFut", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Button(header, text="Logout", command=self._logout).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Label(header, text=f"Usuário: {self.username}", style="Subtitle.TLabel").pack(side=tk.RIGHT)

        self.tabs = ttk.Notebook(self.container)
        self.tabs.pack(fill=tk.BOTH, expand=True)
        self._montar_aba_rodada()
        self._montar_aba_mercado()
        self._montar_aba_escalacao()
        self._montar_aba_ranking()

        self._carregar_catalogo()
        self._atualizar_ranking()
        self._atualizar_mercado()

    def _logout(self):
        self.auth_controller.logout()
        self.username = None
        self.jogadores_catalogo = []
        self.jogadores_disponiveis = []
        self.jogadores_mercado = []
        self.jogadores_escalados = []
        self.jogadores_fantasy = []
        self.capitao = None
        self._montar_tela_login()

    def _montar_aba_rodada(self):
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="Rodada")

        filters = ttk.Frame(tab)
        filters.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filters, text="Temporada").pack(side=tk.LEFT, padx=(0, 6))
        self.temporada_var = tk.StringVar(value="2024")
        temporada_combo = ttk.Combobox(
            filters,
            textvariable=self.temporada_var,
            values=[str(item) for item in self.round_controller.listar_temporadas_disponiveis()],
            width=8,
            state="readonly",
        )
        temporada_combo.pack(side=tk.LEFT, padx=(0, 14))

        ttk.Label(filters, text="Rodada").pack(side=tk.LEFT, padx=(0, 6))
        self.rodada_var = tk.StringVar(value="1")
        rodada_combo = ttk.Combobox(
            filters,
            textvariable=self.rodada_var,
            values=[str(item) for item in self.round_controller.listar_rodadas_disponiveis()],
            width=8,
            state="readonly",
        )
        rodada_combo.pack(side=tk.LEFT, padx=(0, 14))

        ttk.Label(filters, text="Máx. partidas").pack(side=tk.LEFT, padx=(0, 6))
        self.max_partidas_var = tk.StringVar(value="10")
        ttk.Entry(filters, textvariable=self.max_partidas_var, width=6).pack(side=tk.LEFT, padx=(0, 14))

        ttk.Button(filters, text="Carregar Rodada", command=self._carregar_rodada).pack(side=tk.LEFT)

        columns = ("api_id", "nome", "time", "posicao", "minutos", "partida")
        self.available_tree = ttk.Treeview(tab, columns=columns, show="headings", selectmode="browse")
        for column, label, width in (
            ("api_id", "ID", 72),
            ("nome", "Jogador", 190),
            ("time", "Time", 150),
            ("posicao", "Pos", 60),
            ("minutos", "Min", 60),
            ("partida", "Partida", 250),
        ):
            self.available_tree.heading(
                column,
                text=label,
                command=lambda coluna=column: self._ordenar_jogadores_disponiveis(coluna),
            )
            self.available_tree.column(column, width=width, anchor=tk.W)
        self.available_tree.pack(fill=tk.BOTH, expand=True)

        footer = ttk.Frame(tab)
        footer.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(footer, text="Ir para Mercado", command=lambda: self.tabs.select(1)).pack(side=tk.LEFT)
        self.round_status_label = ttk.Label(footer, text="", style="Subtitle.TLabel")
        self.round_status_label.pack(side=tk.LEFT, padx=12)

    def _montar_aba_escalacao(self):
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="Escalação")

        columns = ("api_id", "nome", "time", "posicao", "capitao")
        self.lineup_tree = ttk.Treeview(tab, columns=columns, show="headings", selectmode="browse")
        for column, label, width in (
            ("api_id", "ID", 72),
            ("nome", "Jogador", 220),
            ("time", "Time", 170),
            ("posicao", "Pos", 70),
            ("capitao", "Capitão", 90),
        ):
            self.lineup_tree.heading(column, text=label)
            self.lineup_tree.column(column, width=width, anchor=tk.W)
        self.lineup_tree.pack(fill=tk.BOTH, expand=True)

        footer = ttk.Frame(tab)
        footer.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(footer, text="Definir Capitão", command=self._definir_capitao).pack(side=tk.LEFT)
        ttk.Button(footer, text="Remover", command=self._remover_escalado).pack(side=tk.LEFT, padx=8)
        ttk.Button(footer, text="Calcular Pontuação", command=self._calcular_pontuacao).pack(side=tk.LEFT, padx=8)
        self.lineup_status_label = ttk.Label(footer, text="0/11 jogadores", style="Subtitle.TLabel")
        self.lineup_status_label.pack(side=tk.LEFT, padx=12)

        self.score_text = tk.Text(tab, height=8, wrap=tk.WORD)
        self.score_text.pack(fill=tk.X, pady=(10, 0))

    def _montar_aba_mercado(self):
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="Mercado")

        header = ttk.Frame(tab)
        header.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(header, text="Atualizar Mercado", command=self._atualizar_mercado).pack(side=tk.LEFT)
        self.market_status_label = ttk.Label(header, text="", style="Subtitle.TLabel")
        self.market_status_label.pack(side=tk.LEFT, padx=12)

        panes = ttk.PanedWindow(tab, orient=tk.HORIZONTAL)
        panes.pack(fill=tk.BOTH, expand=True)

        catalog_frame = ttk.Frame(panes, padding=(0, 0, 8, 0))
        elenco_frame = ttk.Frame(panes, padding=(8, 0, 0, 0))
        panes.add(catalog_frame, weight=3)
        panes.add(elenco_frame, weight=2)

        ttk.Label(catalog_frame, text="Jogadores disponíveis na rodada", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 6))
        market_columns = ("api_id", "nome", "time", "posicao", "valor")
        self.market_catalog_tree = ttk.Treeview(
            catalog_frame,
            columns=market_columns,
            show="headings",
            selectmode="browse",
        )
        for column, label, width in (
            ("api_id", "ID", 72),
            ("nome", "Jogador", 220),
            ("time", "Time", 150),
            ("posicao", "Pos", 60),
            ("valor", "Valor", 80),
        ):
            self.market_catalog_tree.heading(
                column,
                text=label,
                command=lambda coluna=column: self._ordenar_jogadores_mercado(coluna),
            )
            self.market_catalog_tree.column(column, width=width, anchor=tk.W)
        self.market_catalog_tree.pack(fill=tk.BOTH, expand=True)
        ttk.Button(catalog_frame, text="Comprar Selecionado", command=self._comprar_selecionado).pack(
            anchor=tk.W,
            pady=(10, 0),
        )

        ttk.Label(elenco_frame, text="Elenco", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 6))
        self.market_roster_tree = ttk.Treeview(
            elenco_frame,
            columns=market_columns,
            show="headings",
            selectmode="browse",
        )
        for column, label, width in (
            ("api_id", "ID", 72),
            ("nome", "Jogador", 180),
            ("time", "Time", 130),
            ("posicao", "Pos", 60),
            ("valor", "Valor", 80),
        ):
            self.market_roster_tree.heading(column, text=label)
            self.market_roster_tree.column(column, width=width, anchor=tk.W)
        self.market_roster_tree.pack(fill=tk.BOTH, expand=True)
        ttk.Button(elenco_frame, text="Vender Selecionado", command=self._vender_selecionado).pack(
            anchor=tk.W,
            pady=(10, 0),
        )
        ttk.Button(elenco_frame, text="Confirmar Elenco", command=self._confirmar_elenco).pack(
            anchor=tk.W,
            pady=(8, 0),
        )

        self.transactions_text = tk.Text(elenco_frame, height=6, wrap=tk.WORD)
        self.transactions_text.pack(fill=tk.X, pady=(10, 0))

    def _montar_aba_ranking(self):
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="Ranking")
        ttk.Button(tab, text="Atualizar Ranking", command=self._atualizar_ranking).pack(anchor=tk.W, pady=(0, 8))
        self.ranking_text = tk.Text(tab, wrap=tk.WORD)
        self.ranking_text.pack(fill=tk.BOTH, expand=True)

    def _carregar_catalogo(self):
        temporada = int(self.temporada_var.get())
        jogadores = self.player_catalog_controller.carregar_jogadores_temporada(temporada=temporada)
        self.jogadores_catalogo = jogadores
        self.round_status_label.configure(text=f"Catálogo carregado: {len(jogadores)} jogadores")

    def _carregar_rodada(self):
        try:
            temporada = int(self.temporada_var.get())
            rodada = int(self.rodada_var.get())
            max_partidas = self._max_partidas()
            dados = self.round_controller.baixar_dados_rodada(
                temporada=temporada,
                numero_rodada=rodada,
                max_partidas=max_partidas,
            )
            total = len(dados.get("partidas_api", {}).get("response", []))
            cacheadas = len(dados.get("partidas", []))
            self._listar_jogadores_rodada()
            self._reiniciar_elenco_rodada()
            self.round_status_label.configure(text=f"Rodada {rodada}: {cacheadas}/{total} partidas com estatísticas")
        except Exception as exc:
            self._mostrar_erro(str(exc))

    def _listar_jogadores_rodada(self):
        try:
            temporada = int(self.temporada_var.get())
            rodada = int(self.rodada_var.get())
            self.jogadores_disponiveis = self.round_controller.listar_jogadores_disponiveis(
                temporada=temporada,
                numero_rodada=rodada,
            )
            self._preencher_disponiveis()
            self._preencher_catalogo_mercado()
            self.round_status_label.configure(text=f"{len(self.jogadores_disponiveis)} atuações disponíveis")
        except Exception as exc:
            self._mostrar_erro(str(exc))

    def _preencher_disponiveis(self):
        self.available_tree.delete(*self.available_tree.get_children())
        for index, jogador in enumerate(self.jogadores_disponiveis):
            self.available_tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=(
                    jogador.get("api_id") or "",
                    jogador.get("nome") or "",
                    jogador.get("time") or "",
                    jogador.get("posicao") or "",
                    jogador.get("minutos") or 0,
                    jogador.get("partida") or "",
                ),
            )

    def _preencher_escalacao(self):
        self.lineup_tree.delete(*self.lineup_tree.get_children())

        for index, jogador in enumerate(self.jogadores_escalados):
            self.lineup_tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=(
                    jogador.api_id or "",
                    jogador.nome or "",
                    jogador.nome_time or "",
                    jogador.posicao or "",
                    "Sim" if jogador is self.capitao else "",
                ),
            )

        self.lineup_status_label.configure(text=f"{len(self.jogadores_escalados)}/11 jogadores")

    def _definir_capitao(self):
        selection = self.lineup_tree.selection()
        if not selection:
            return
        index = int(selection[0])
        self.capitao = self.jogadores_escalados[index]
        self._preencher_escalacao()

    def _remover_escalado(self):
        selection = self.lineup_tree.selection()
        if not selection:
            return
        jogador = self.jogadores_escalados[int(selection[0])]

        if self.market_controller is not None:
            self.market_controller.vender(self.username, jogador)
            self._atualizar_mercado()
            return

        self.jogadores_escalados.remove(jogador)
        if jogador is self.capitao:
            self.capitao = None
        self._preencher_escalacao()

    def _calcular_pontuacao(self):
        try:
            if len(self.jogadores_escalados) != 11:
                raise RuntimeError("Voce precisa comprar exatamente 11 jogadores para a rodada.")

            if self.capitao is None:
                raise RuntimeError("Escolha um capitao antes de calcular a pontuacao.")

            temporada = int(self.temporada_var.get())
            rodada = int(self.rodada_var.get())
            jogadores_fantasy = self.lineup_controller.criar_escalacao_fantasy(
                self.jogadores_escalados,
                capitao=self.capitao,
            )
            rodada_model = self.round_controller.montar_rodada_por_cache(
                temporada=temporada,
                numero_rodada=rodada,
                jogadores_escalados=self.jogadores_escalados,
            )
            self.round_controller.adicionar_rodada(rodada_model)
            pontuacao_total = self.lineup_controller.executar_rodada(
                username=self.username,
                numero_rodada=rodada,
                jogadores_fantasy=jogadores_fantasy,
            )
            escalacao = self.lineup_controller.buscar_escalacao(rodada)
            jogadores_calculados = escalacao.jogadores if escalacao is not None else jogadores_fantasy
            self.jogadores_fantasy = jogadores_calculados
            self._mostrar_pontuacao(rodada, pontuacao_total, jogadores_calculados)
            self._atualizar_ranking()
        except Exception as exc:
            self._mostrar_erro(str(exc))

    def _mostrar_pontuacao(self, rodada, pontuacao_total, jogadores_fantasy):
        self.score_text.delete("1.0", tk.END)
        self.score_text.insert(tk.END, f"Rodada {rodada}: {pontuacao_total} pontos\n\n")
        for jogador_fantasy in jogadores_fantasy:
            capitao = " (capitão)" if jogador_fantasy.capitao else ""
            self.score_text.insert(
                tk.END,
                f"{jogador_fantasy.jogador.nome}{capitao}: {jogador_fantasy.pontuacao} pontos\n",
            )

    def _atualizar_ranking(self):
        if not hasattr(self, "ranking_text"):
            return
        self.ranking_text.delete("1.0", tk.END)
        self.ranking_text.insert(tk.END, self.ranking_controller.formatar_ranking_usuarios())

    def _atualizar_mercado(self):
        if self.market_controller is None or not hasattr(self, "market_catalog_tree"):
            return

        self._preencher_catalogo_mercado()
        self._preencher_elenco_mercado()

    def _preencher_catalogo_mercado(self, ordenar=True):
        if not hasattr(self, "market_catalog_tree"):
            return

        self.market_catalog_tree.delete(*self.market_catalog_tree.get_children())
        if ordenar:
            jogadores_rodada = self.lineup_controller.selecionar_players_do_catalogo(
                self.jogadores_disponiveis
            )
            api_ids_elenco = {
                jogador.api_id
                for jogador in self.market_controller.listar_elenco(self.username)
            }
            self.jogadores_mercado = [
                jogador for jogador in jogadores_rodada if jogador.api_id not in api_ids_elenco
            ]
        for index, jogador in enumerate(self.jogadores_mercado):
            self.market_catalog_tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=self._valores_jogador_mercado(jogador),
            )

    def _ordenar_jogadores_disponiveis(self, coluna):
        reverse = self._proxima_direcao_ordenacao(f"disponiveis:{coluna}")
        self.jogadores_disponiveis.sort(
            key=lambda jogador: self._valor_ordenacao_dict(jogador, coluna),
            reverse=reverse,
        )
        self._preencher_disponiveis()
        self._preencher_catalogo_mercado()

    def _ordenar_jogadores_mercado(self, coluna):
        reverse = self._proxima_direcao_ordenacao(f"mercado:{coluna}")
        criterio = {
            "api_id": "api_id",
            "nome": "nome",
            "time": "nome_time",
            "posicao": "posicao",
            "valor": "valor_mercado",
        }.get(coluna, coluna)
        self.jogadores_mercado.sort(
            key=lambda jogador: self._valor_ordenacao_obj(jogador, criterio),
            reverse=reverse,
        )
        self._preencher_catalogo_mercado(ordenar=False)

    def _proxima_direcao_ordenacao(self, chave):
        reverse = not self.sort_directions.get(chave, False)
        self.sort_directions[chave] = reverse
        return reverse

    def _valor_ordenacao_dict(self, item, coluna):
        valor = item.get(coluna)
        return self._valor_ordenacao(valor)

    def _valor_ordenacao_obj(self, item, atributo):
        return self._valor_ordenacao(getattr(item, atributo, None))

    def _valor_ordenacao(self, valor):
        if valor is None:
            return (1, "")

        if isinstance(valor, (int, float)):
            return (0, valor)

        try:
            return (0, float(valor))
        except (TypeError, ValueError):
            return (0, str(valor).casefold())

    def _preencher_elenco_mercado(self):
        if self.market_controller is None or not hasattr(self, "market_roster_tree"):
            return

        self.market_roster_tree.delete(*self.market_roster_tree.get_children())
        elenco = self.market_controller.listar_elenco(self.username)
        self.jogadores_escalados = list(elenco)
        if self.capitao not in self.jogadores_escalados:
            self.capitao = None

        for index, jogador in enumerate(elenco):
            self.market_roster_tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=self._valores_jogador_mercado(jogador),
            )

        patrimonio = self.market_controller.patrimonio(self.username)
        self.market_status_label.configure(
            text=f"Patrimônio: {patrimonio:.2f} | Elenco: {len(elenco)} jogadores"
        )
        self._preencher_transacoes()
        self._preencher_escalacao()

    def _preencher_transacoes(self):
        self.transactions_text.delete("1.0", tk.END)
        for transacao in self.market_controller.listar_transacoes(self.username)[-8:]:
            self.transactions_text.insert(
                tk.END,
                (
                    f"{transacao.data_hora:%d/%m %H:%M} - "
                    f"{transacao.tipo.value}: {transacao.jogador.nome} "
                    f"({transacao.valor:.2f})\n"
                ),
            )

    def _comprar_selecionado(self):
        if self.market_controller is None:
            return

        selection = self.market_catalog_tree.selection()
        if not selection:
            return

        try:
            jogador = self.jogadores_mercado[int(selection[0])]
            self.market_controller.comprar(self.username, jogador)
            self._atualizar_mercado()
        except Exception as exc:
            self._mostrar_erro(str(exc))

    def _vender_selecionado(self):
        if self.market_controller is None:
            return

        selection = self.market_roster_tree.selection()
        if not selection:
            return

        try:
            elenco = self.market_controller.listar_elenco(self.username)
            jogador = elenco[int(selection[0])]
            self.market_controller.vender(self.username, jogador)
            self._atualizar_mercado()
        except Exception as exc:
            self._mostrar_erro(str(exc))

    def _confirmar_elenco(self):
        if len(self.jogadores_escalados) != 11:
            self._mostrar_erro("Compre exatamente 11 jogadores antes de confirmar.")
            return

        self.tabs.select(2)
        self.lineup_status_label.configure(
            text="11/11 jogadores. Escolha o capitão e calcule a pontuação."
        )

    def _reiniciar_elenco_rodada(self):
        self.jogadores_escalados = []
        self.capitao = None

        if self.market_controller is not None and self.username is not None:
            self.market_controller.limpar_elenco_rodada(self.username)

        self._atualizar_mercado()
        self._preencher_escalacao()

    def _valores_jogador_mercado(self, jogador):
        return (
            jogador.api_id or "",
            jogador.nome or "",
            jogador.nome_time or "",
            jogador.posicao or "",
            f"{float(jogador.valor_mercado or 0):.2f}",
        )

    def _max_partidas(self):
        valor = self.max_partidas_var.get().strip()
        if not valor:
            return None
        return int(valor)

    def _mostrar_erro(self, mensagem):
        messagebox.showerror("SofaFut", mensagem)
