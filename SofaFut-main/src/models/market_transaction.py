from datetime import datetime
from enum import Enum
from uuid import uuid4


class TipoTransacao(str, Enum):
    COMPRA = "compra"
    VENDA = "venda"


class TransacaoMercado:

    def __init__(
        self,
        jogador,
        tipo: TipoTransacao,
        valor: float,
        data_hora=None,
        id=None,
    ):
        self.id = id or str(uuid4())
        self.jogador = jogador
        self.tipo = tipo
        self.valor = valor
        self.data_hora = data_hora or datetime.now()
