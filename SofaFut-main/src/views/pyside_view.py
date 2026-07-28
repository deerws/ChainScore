from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class SofaFutPySideGui:

    def __init__(
        self,
        auth_controller,
        player_catalog_controller,
        round_controller,
        lineup_controller,
        ranking_controller,
        market_controller,
    ):
        self.app = QApplication.instance() or QApplication([])
        self.window = _LoginWindow(
            auth_controller=auth_controller,
            player_catalog_controller=player_catalog_controller,
            round_controller=round_controller,
            lineup_controller=lineup_controller,
            ranking_controller=ranking_controller,
            market_controller=market_controller,
        )

    def run(self):
        self.window.showMaximized()
        return self.app.exec()


class _LoginWindow(QMainWindow):

    def __init__(
        self,
        auth_controller,
        player_catalog_controller,
        round_controller,
        lineup_controller,
        ranking_controller,
        market_controller,
    ):
        super().__init__()
        self.auth_controller = auth_controller
        self.player_catalog_controller = player_catalog_controller
        self.round_controller = round_controller
        self.lineup_controller = lineup_controller
        self.ranking_controller = ranking_controller
        self.market_controller = market_controller
        self.main_window = None

        self.setWindowTitle("SofaFut")
        self.setMinimumSize(900, 700)
        self._build_ui()

    def _build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(48, 42, 48, 42)
        layout.addStretch(1)

        panel = QWidget()
        panel.setMaximumWidth(520)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setSpacing(12)

        title = QLabel("SofaFut")
        title.setProperty("role", "title")
        panel_layout.addWidget(title)
        panel_layout.addWidget(QLabel("Entre ou cadastre-se para montar sua escalação."))

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("usuario")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("senha")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        panel_layout.addWidget(self.username_input)
        panel_layout.addWidget(self.password_input)

        buttons = QHBoxLayout()
        login_button = QPushButton("Entrar")
        login_button.clicked.connect(self._login)
        cadastro_button = QPushButton("Cadastrar")
        cadastro_button.clicked.connect(self._cadastrar)
        buttons.addWidget(login_button)
        buttons.addWidget(cadastro_button)
        panel_layout.addLayout(buttons)

        layout.addWidget(panel, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
        self.setCentralWidget(root)
        self.setStyleSheet(_STYLE)

    def _login(self):
        username = self.username_input.text().strip()
        senha = self.password_input.text().strip()

        if not username or not senha:
            self._erro("Preencha usuario e senha.")
            return

        mensagem = self.auth_controller.login(username, senha)
        if mensagem != "Usuario logado":
            self._erro(mensagem)
            return

        self.main_window = _MainWindow(
            username=username,
            auth_controller=self.auth_controller,
            player_catalog_controller=self.player_catalog_controller,
            round_controller=self.round_controller,
            lineup_controller=self.lineup_controller,
            ranking_controller=self.ranking_controller,
            market_controller=self.market_controller,
        )
        self.main_window.showMaximized()
        self.close()

    def _cadastrar(self):
        username = self.username_input.text().strip()
        senha = self.password_input.text().strip()

        if not username or not senha:
            self._erro("Preencha usuario e senha.")
            return

        mensagem = self.auth_controller.cadastrar(username=username, senha=senha)
        QMessageBox.information(self, "SofaFut", mensagem)

    def _erro(self, mensagem):
        QMessageBox.warning(self, "SofaFut", mensagem)


class _MainWindow(QMainWindow):

    def __init__(
        self,
        username,
        auth_controller,
        player_catalog_controller,
        round_controller,
        lineup_controller,
        ranking_controller,
        market_controller,
    ):
        super().__init__()
        self.username = username
        self.auth_controller = auth_controller
        self.player_catalog_controller = player_catalog_controller
        self.round_controller = round_controller
        self.lineup_controller = lineup_controller
        self.ranking_controller = ranking_controller
        self.market_controller = market_controller
        self.jogadores_catalogo = []
        self.jogadores_disponiveis = []
        self.jogadores_mercado = []
        self.jogadores_escalados = []
        self.capitao = None
        self.sort_directions = {}

        self.setWindowTitle("SofaFut")
        self.setMinimumSize(1100, 720)
        self._build_ui()
        self._carregar_catalogo()
        self._atualizar_ranking()
        self._atualizar_mercado()

    def _build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 18, 22, 18)

        header = QHBoxLayout()
        title = QLabel("SofaFut")
        title.setProperty("role", "title")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(QLabel(f"Usuario: {self.username}"))
        logout_button = QPushButton("Logout")
        logout_button.clicked.connect(self._logout)
        header.addWidget(logout_button)
        layout.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_round_tab(), "Rodada")
        self.tabs.addTab(self._build_market_tab(), "Mercado")
        self.tabs.addTab(self._build_lineup_tab(), "Escalacao")
        self.tabs.addTab(self._build_ranking_tab(), "Ranking")
        layout.addWidget(self.tabs, 1)

        self.setCentralWidget(root)
        self.setStyleSheet(_STYLE)

    def _logout(self):
        self.auth_controller.logout()
        self.login_window = _LoginWindow(
            auth_controller=self.auth_controller,
            player_catalog_controller=self.player_catalog_controller,
            round_controller=self.round_controller,
            lineup_controller=self.lineup_controller,
            ranking_controller=self.ranking_controller,
            market_controller=self.market_controller,
        )
        self.login_window.showMaximized()
        self.close()

    def _build_round_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        filters = QHBoxLayout()

        self.temporada_combo = QComboBox()
        self.temporada_combo.addItems(
            [str(item) for item in self.round_controller.listar_temporadas_disponiveis()]
        )
        self.rodada_combo = QComboBox()
        self.rodada_combo.addItems(
            [str(item) for item in self.round_controller.listar_rodadas_disponiveis()]
        )
        self.max_partidas_input = QLineEdit("10")
        self.max_partidas_input.setMaximumWidth(70)
        carregar_button = QPushButton("Carregar rodada")
        carregar_button.clicked.connect(self._carregar_rodada)

        filters.addWidget(QLabel("Temporada"))
        filters.addWidget(self.temporada_combo)
        filters.addWidget(QLabel("Rodada"))
        filters.addWidget(self.rodada_combo)
        filters.addWidget(QLabel("Max. partidas"))
        filters.addWidget(self.max_partidas_input)
        filters.addWidget(carregar_button)
        filters.addStretch(1)
        layout.addLayout(filters)

        self.available_table = _table(["ID", "Jogador", "Time", "Pos", "Min", "Partida"])
        self.available_table.horizontalHeader().sectionClicked.connect(
            self._ordenar_jogadores_disponiveis
        )
        layout.addWidget(self.available_table, 1)
        add_button = QPushButton("Ir para mercado")
        add_button.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        self.round_status = QLabel("")
        footer = QHBoxLayout()
        footer.addWidget(add_button)
        footer.addWidget(self.round_status)
        footer.addStretch(1)
        layout.addLayout(footer)
        return tab

    def _build_market_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)

        catalog_col = QVBoxLayout()
        catalog_col.addWidget(QLabel("Jogadores disponiveis na rodada"))
        self.market_catalog_table = _table(["ID", "Jogador", "Time", "Pos", "Valor"])
        self.market_catalog_table.horizontalHeader().sectionClicked.connect(
            self._ordenar_jogadores_mercado
        )
        catalog_col.addWidget(self.market_catalog_table, 1)
        buy_button = QPushButton("Comprar selecionado")
        buy_button.clicked.connect(self._comprar_selecionado)
        catalog_col.addWidget(buy_button)

        roster_col = QVBoxLayout()
        self.market_status = QLabel("")
        roster_col.addWidget(self.market_status)
        self.market_roster_table = _table(["ID", "Jogador", "Time", "Pos", "Valor"])
        roster_col.addWidget(self.market_roster_table, 1)
        sell_button = QPushButton("Vender selecionado")
        sell_button.clicked.connect(self._vender_selecionado)
        roster_col.addWidget(sell_button)
        confirm_button = QPushButton("Confirmar elenco")
        confirm_button.clicked.connect(self._confirmar_elenco)
        roster_col.addWidget(confirm_button)
        self.transactions_text = QTextEdit()
        self.transactions_text.setReadOnly(True)
        self.transactions_text.setMaximumHeight(130)
        roster_col.addWidget(self.transactions_text)

        layout.addLayout(catalog_col, 3)
        layout.addLayout(roster_col, 2)
        return tab

    def _build_lineup_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.lineup_table = _table(["ID", "Jogador", "Time", "Pos", "Capitao"])
        layout.addWidget(self.lineup_table, 1)

        footer = QHBoxLayout()
        captain_button = QPushButton("Definir capitao")
        captain_button.clicked.connect(self._definir_capitao)
        remove_button = QPushButton("Remover")
        remove_button.clicked.connect(self._remover_escalado)
        score_button = QPushButton("Calcular pontuacao")
        score_button.clicked.connect(self._calcular_pontuacao)
        self.lineup_status = QLabel("0/11 jogadores")
        footer.addWidget(captain_button)
        footer.addWidget(remove_button)
        footer.addWidget(score_button)
        footer.addWidget(self.lineup_status)
        footer.addStretch(1)
        layout.addLayout(footer)

        self.score_text = QTextEdit()
        self.score_text.setReadOnly(True)
        self.score_text.setMaximumHeight(170)
        layout.addWidget(self.score_text)
        return tab

    def _build_ranking_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        refresh = QPushButton("Atualizar ranking")
        refresh.clicked.connect(self._atualizar_ranking)
        self.ranking_text = QTextEdit()
        self.ranking_text.setReadOnly(True)
        layout.addWidget(refresh, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.ranking_text, 1)
        return tab

    def _carregar_catalogo(self):
        temporada = int(self.temporada_combo.currentText())
        self.jogadores_catalogo = self.player_catalog_controller.carregar_jogadores_temporada(
            temporada=temporada
        )
        self.round_status.setText(f"Catalogo carregado: {len(self.jogadores_catalogo)} jogadores")

    def _carregar_rodada(self):
        try:
            temporada = int(self.temporada_combo.currentText())
            rodada = int(self.rodada_combo.currentText())
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
            self.round_status.setText(f"Rodada {rodada}: {cacheadas}/{total} partidas com estatisticas")
        except Exception as exc:
            self._erro(str(exc))

    def _listar_jogadores_rodada(self):
        try:
            temporada = int(self.temporada_combo.currentText())
            rodada = int(self.rodada_combo.currentText())
            self.jogadores_disponiveis = self.round_controller.listar_jogadores_disponiveis(
                temporada=temporada,
                numero_rodada=rodada,
            )
            _fill_table(
                self.available_table,
                [
                    [
                        item.get("api_id") or "",
                        item.get("nome") or "",
                        item.get("time") or "",
                        item.get("posicao") or "",
                        item.get("minutos") or 0,
                        item.get("partida") or "",
                    ]
                    for item in self.jogadores_disponiveis
                ],
            )
            self.round_status.setText(f"{len(self.jogadores_disponiveis)} atuacoes disponiveis")
            self._preencher_catalogo_mercado()
        except Exception as exc:
            self._erro(str(exc))

    def _preencher_escalacao(self):
        _fill_table(
            self.lineup_table,
            [
                [
                    jogador.api_id or "",
                    jogador.nome or "",
                    jogador.nome_time or "",
                    jogador.posicao or "",
                    "Sim" if jogador is self.capitao else "",
                ]
                for jogador in self.jogadores_escalados
            ],
        )
        self.lineup_status.setText(f"{len(self.jogadores_escalados)}/11 jogadores")

    def _definir_capitao(self):
        linhas = self._linhas_selecionadas(self.lineup_table)
        if not linhas:
            return
        self.capitao = self.jogadores_escalados[linhas[0]]
        self._preencher_escalacao()

    def _remover_escalado(self):
        linhas = self._linhas_selecionadas(self.lineup_table)
        if not linhas:
            return
        try:
            jogador = self.jogadores_escalados[linhas[0]]
            self.market_controller.vender(self.username, jogador)
            self._atualizar_mercado()
        except Exception as exc:
            self._erro(str(exc))

    def _calcular_pontuacao(self):
        try:
            if len(self.jogadores_escalados) != 11:
                raise RuntimeError("Voce precisa comprar exatamente 11 jogadores para a rodada.")

            if self.capitao is None:
                raise RuntimeError("Escolha um capitao antes de calcular a pontuacao.")

            temporada = int(self.temporada_combo.currentText())
            rodada = int(self.rodada_combo.currentText())
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
            self.score_text.setPlainText(
                "\n".join(
                    [
                        f"Rodada {rodada}: {pontuacao_total} pontos",
                        "",
                        *[
                            (
                                f"{item.jogador.nome}"
                                f"{' (capitao)' if item.capitao else ''}: "
                                f"{item.pontuacao} pontos"
                            )
                            for item in jogadores_calculados
                        ],
                    ]
                )
            )
            self._atualizar_ranking()
        except Exception as exc:
            self._erro(str(exc))

    def _comprar_selecionado(self):
        linhas = self._linhas_selecionadas(self.market_catalog_table)
        if not linhas:
            return
        try:
            self.market_controller.comprar(self.username, self.jogadores_mercado[linhas[0]])
            self._atualizar_mercado()
        except Exception as exc:
            self._erro(str(exc))

    def _vender_selecionado(self):
        linhas = self._linhas_selecionadas(self.market_roster_table)
        if not linhas:
            return
        try:
            elenco = self.market_controller.listar_elenco(self.username)
            self.market_controller.vender(self.username, elenco[linhas[0]])
            self._atualizar_mercado()
        except Exception as exc:
            self._erro(str(exc))

    def _confirmar_elenco(self):
        if len(self.jogadores_escalados) != 11:
            self._erro("Compre exatamente 11 jogadores antes de confirmar.")
            return

        self.tabs.setCurrentIndex(2)
        self.lineup_status.setText("11/11 jogadores. Escolha o capitao e calcule a pontuacao.")

    def _atualizar_mercado(self):
        elenco = self.market_controller.listar_elenco(self.username)
        self.jogadores_escalados = list(elenco)
        if self.capitao not in self.jogadores_escalados:
            self.capitao = None

        self._preencher_catalogo_mercado()
        self._preencher_tabela_players(self.market_roster_table, elenco)
        self.market_status.setText(
            f"Patrimonio: {self.market_controller.patrimonio(self.username):.2f} | "
            f"Elenco: {len(elenco)} jogadores"
        )
        self.transactions_text.setPlainText(
            "\n".join(
                [
                    (
                        f"{item.data_hora:%d/%m %H:%M} - {item.tipo.value}: "
                        f"{item.jogador.nome} ({item.valor:.2f})"
                    )
                    for item in self.market_controller.listar_transacoes(self.username)[-8:]
                ]
            )
        )
        self._preencher_escalacao()

    def _preencher_catalogo_mercado(self):
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
        self._preencher_tabela_players(self.market_catalog_table, self.jogadores_mercado)

    def _ordenar_jogadores_disponiveis(self, section):
        coluna = ["api_id", "nome", "time", "posicao", "minutos", "partida"][section]
        reverse = self._proxima_direcao_ordenacao(f"disponiveis:{coluna}")
        self.jogadores_disponiveis.sort(
            key=lambda jogador: self._valor_ordenacao(jogador.get(coluna)),
            reverse=reverse,
        )
        _fill_table(
            self.available_table,
            [
                [
                    item.get("api_id") or "",
                    item.get("nome") or "",
                    item.get("time") or "",
                    item.get("posicao") or "",
                    item.get("minutos") or 0,
                    item.get("partida") or "",
                ]
                for item in self.jogadores_disponiveis
            ],
        )
        self._preencher_catalogo_mercado()

    def _ordenar_jogadores_mercado(self, section):
        atributo = ["api_id", "nome", "nome_time", "posicao", "valor_mercado"][section]
        reverse = self._proxima_direcao_ordenacao(f"mercado:{atributo}")
        self.jogadores_mercado.sort(
            key=lambda jogador: self._valor_ordenacao(getattr(jogador, atributo, None)),
            reverse=reverse,
        )
        self._preencher_tabela_players(self.market_catalog_table, self.jogadores_mercado)

    def _proxima_direcao_ordenacao(self, chave):
        reverse = not self.sort_directions.get(chave, False)
        self.sort_directions[chave] = reverse
        return reverse

    def _valor_ordenacao(self, valor):
        if valor is None:
            return (1, "")

        if isinstance(valor, (int, float)):
            return (0, valor)

        try:
            return (0, float(valor))
        except (TypeError, ValueError):
            return (0, str(valor).casefold())

    def _reiniciar_elenco_rodada(self):
        self.capitao = None
        self.jogadores_escalados = []
        self.market_controller.limpar_elenco_rodada(self.username)
        self._atualizar_mercado()

    def _atualizar_ranking(self):
        self.ranking_text.setPlainText(self.ranking_controller.formatar_ranking_usuarios())

    def _preencher_tabela_players(self, table, jogadores):
        _fill_table(
            table,
            [
                [
                    jogador.api_id or "",
                    jogador.nome or "",
                    jogador.nome_time or "",
                    jogador.posicao or "",
                    f"{float(jogador.valor_mercado or 0):.2f}",
                ]
                for jogador in jogadores
            ],
        )

    def _max_partidas(self):
        valor = self.max_partidas_input.text().strip()
        return int(valor) if valor else None

    def _linhas_selecionadas(self, table):
        return sorted({item.row() for item in table.selectedItems()})

    def _erro(self, mensagem):
        QMessageBox.warning(self, "SofaFut", mensagem)


def _table(headers):
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    return table


def _fill_table(table, rows):
    table.setRowCount(len(rows))
    for row_index, values in enumerate(rows):
        for column_index, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            if column_index in {0, 3, 4}:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_index, column_index, item)
    table.resizeColumnsToContents()


_STYLE = """
QMainWindow, QWidget {
    background: #f7f4ef;
    color: #260d33;
}
QLabel[role="title"] {
    color: #003f69;
    font-size: 28px;
    font-weight: 800;
}
QLineEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #b3aca4;
    border-radius: 6px;
    padding: 7px 10px;
    min-height: 22px;
}
QPushButton {
    background: #003f69;
    color: #ffffff;
    border: 0;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 700;
}
QPushButton:hover {
    background: #106b87;
}
QTableWidget, QTextEdit {
    background: #ffffff;
    border: 1px solid #d5cec6;
    gridline-color: #e5ded7;
}
QHeaderView::section {
    background: #003f69;
    color: #ffffff;
    padding: 7px;
    border: 0;
    font-weight: 700;
}
QTabBar::tab {
    background: #b3aca4;
    color: #260d33;
    padding: 9px 16px;
    font-weight: 700;
}
QTabBar::tab:selected {
    background: #003f69;
    color: #ffffff;
}
"""
