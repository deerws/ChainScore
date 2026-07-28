from src.models.market_transaction import TipoTransacao
from src.models.market_transaction import TransacaoMercado
from src.models.player import Player
from src.models.user import User


class MarketService:

    def __init__(self):
        self.mercado_aberto = True

    def comprar(self, user: User, jogador: Player):
        self._validar_mercado_aberto()
        team = user.team_fantasy

        if len(team.elenco) >= 11:
            raise ValueError("O elenco da rodada ja possui 11 jogadores.")

        if self._buscar_no_elenco(team.elenco, jogador) is not None:
            raise ValueError("Jogador ja esta no elenco.")

        valor = self._valor_jogador(jogador)
        if team.patrimonio < valor:
            raise ValueError("Saldo insuficiente para comprar jogador.")

        team.patrimonio -= valor
        team.elenco.append(jogador)
        team.transacoes.append(
            TransacaoMercado(
                jogador=jogador,
                tipo=TipoTransacao.COMPRA,
                valor=valor,
            )
        )
        return team

    def limpar_elenco_rodada(self, user: User):
        team = user.team_fantasy
        team.elenco = []
        team.transacoes = []
        team.patrimonio = 110.0
        return team

    def vender(self, user: User, jogador: Player):
        self._validar_mercado_aberto()
        team = user.team_fantasy
        jogador_elenco = self._buscar_no_elenco(team.elenco, jogador)

        if jogador_elenco is None:
            raise ValueError("Jogador nao pertence ao elenco.")

        valor = self._valor_jogador(jogador_elenco)
        team.elenco.remove(jogador_elenco)
        team.patrimonio += valor
        team.transacoes.append(
            TransacaoMercado(
                jogador=jogador_elenco,
                tipo=TipoTransacao.VENDA,
                valor=valor,
            )
        )
        return team

    def abrir_mercado(self):
        self.mercado_aberto = True

    def fechar_mercado(self):
        self.mercado_aberto = False

    def _validar_mercado_aberto(self):
        if not self.mercado_aberto:
            raise ValueError("Mercado fechado para transacoes.")

    def _buscar_no_elenco(self, elenco, jogador):
        for jogador_elenco in elenco:
            if jogador_elenco is jogador:
                return jogador_elenco

            if jogador.api_id is not None and jogador_elenco.api_id == jogador.api_id:
                return jogador_elenco

            mesma_chave = (
                self._normalizar(jogador_elenco.nome) == self._normalizar(jogador.nome)
                and self._normalizar(jogador_elenco.nome_time)
                == self._normalizar(jogador.nome_time)
            )
            if mesma_chave:
                return jogador_elenco

        return None

    def _valor_jogador(self, jogador):
        return float(jogador.valor_mercado or 0)

    def _normalizar(self, valor):
        return (valor or "").casefold().strip()
