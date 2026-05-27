"""
Representa a entrada de um usuário no ranking de uma rodada.
Armazena nome, pontuação e saldo para aplicar a regra de desempate (RN-06).
"""


class RankingEntry:
    """
    Entrada de um usuário no ranking.

    Atributos
    ----------
    username   : str   — nome do usuário
    pontuacao  : int   — pontos acumulados até a rodada
    saldo      : float — saldo em moedas (critério de desempate, RN-06)
    posicao    : int   — posição calculada no ranking (preenchida pelo RankingService)
    """

    def __init__(self, username: str, pontuacao: int, saldo: float):
        self.username = username
        self.pontuacao = pontuacao
        self.saldo = saldo
        self.posicao: int = 0          # preenchida após ordenação

    def __repr__(self) -> str:
        return (
            f"RankingEntry(pos={self.posicao}, "
            f"user='{self.username}', "
            f"pts={self.pontuacao}, "
            f"saldo={self.saldo:.2f})"
        )
