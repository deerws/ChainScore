"""
Serviço responsável por calcular e expor o ranking de usuários.

Regras de negócio aplicadas
---------------------------
RN-06 : A posição é definida pela soma de pontos acumulados.
        Em caso de empate em pontos, o critério de desempate é o saldo
        de moedas (maior saldo = melhor posição).
RF12  : O sistema deve disponibilizar um ranking da pontuação dos
        usuários registrados.
"""

from src.models.ranking_entry import RankingEntry
from src.repositories.ranking_repository import RankingRepository


class RankingService:
    """
    Orquestra o cálculo do ranking e expõe consultas.

    Parâmetros
    ----------
    ranking_repository : RankingRepository
        Repositório que provê e persiste os dados.
    """

    def __init__(self, ranking_repository: RankingRepository):
        self.ranking_repository = ranking_repository

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _ordenar(self, entradas: list[RankingEntry]) -> list[RankingEntry]:
        """
        Ordena por pontuação DESC; em empate, por saldo DESC (RN-06).
        Atribui o número de posição a cada entrada.
        """
        ordenadas = sorted(
            entradas,
            key=lambda e: (e.pontuacao, e.saldo),
            reverse=True,
        )
        for idx, entrada in enumerate(ordenadas, start=1):
            entrada.posicao = idx
        return ordenadas

    # ------------------------------------------------------------------
    # Casos de uso públicos
    # ------------------------------------------------------------------

    def calcular_ranking(self) -> list[RankingEntry]:
        """
        Carrega todos os usuários, aplica a ordenação com desempate
        (RN-06) e retorna a lista completa ordenada.
        """
        entradas = self.ranking_repository.listar_entradas()

        if not entradas:
            return []

        return self._ordenar(entradas)

    def obter_top(self, n: int) -> list[RankingEntry]:
        """
        Retorna os N primeiros colocados do ranking.

        Parâmetros
        ----------
        n : int — quantidade de posições desejadas (ex.: top 10)
        """
        if n <= 0:
            raise ValueError("n deve ser maior que zero.")

        ranking = self.calcular_ranking()
        return ranking[:n]

    def obter_posicao_usuario(self, username: str) -> RankingEntry | None:
        """
        Retorna a entrada do usuário informado com sua posição calculada.
        Retorna None se o usuário não estiver no ranking.

        Parâmetros
        ----------
        username : str — nome do usuário buscado
        """
        ranking = self.calcular_ranking()
        for entrada in ranking:
            if entrada.username == username:
                return entrada
        return None

    def salvar_ranking(self) -> None:
        """Calcula e persiste o ranking atual no repositório."""
        ranking = self.calcular_ranking()
        self.ranking_repository.salvar_entradas(ranking)
