"""Explorador da API (nao-oficial) do SofaScore.

IMPORTANTE
----------
A SofaScore NAO publica uma API oficial. Os endpoints usados aqui
sao os mesmos que o site https://www.sofascore.com consome no
navegador (engenharia reversa). Use com moderacao:
  * respeite o Robots/ToS do site;
  * limite o volume de requisicoes;
  * use apenas para fins pessoais/educacionais.

A SofaScore protege o dominio com Cloudflare. Algumas regioes
ou IPs de datacenter podem ser bloqueados com HTTP 403 mesmo
enviando um User-Agent valido.

Requisito:  pip install requests

Executar:
    python3 sofascore_api.py                 # mostra o menu
    python3 sofascore_api.py live            # eventos ao vivo
    python3 sofascore_api.py date 2026-04-19 # eventos de um dia
    python3 sofascore_api.py event 12345678  # detalhe do evento
    python3 sofascore_api.py search "haaland"
"""

from __future__ import annotations

import json
import sys
from datetime import date

import requests


BASE = "https://api.sofascore.com/api/v1"

HEADERS = {
    # User-Agent de browser comum; sem isso costuma voltar 403.
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
}


# ---------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------

def get(path: str, **params) -> dict:
    url = f"{BASE}{path}"
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(
            f"HTTP {r.status_code} em {r.url}\n{r.text[:200]}"
        )
    return r.json()


def pp(obj, limit: int = 1800):
    """Pretty-print truncado para nao poluir o terminal."""
    txt = json.dumps(obj, indent=2, ensure_ascii=False)
    if len(txt) > limit:
        txt = txt[:limit] + f"\n... (+{len(txt) - limit} chars truncados)"
    print(txt)


# ---------------------------------------------------------------
# Endpoints demonstrados
# ---------------------------------------------------------------

def live_events(sport: str = "football") -> None:
    """Todos os eventos ao vivo de um esporte."""
    data = get(f"/sport/{sport}/events/live")
    evs = data.get("events", [])
    print(f"-- {len(evs)} eventos ao vivo em '{sport}' --")
    for e in evs[:20]:
        home = e["homeTeam"]["name"]
        away = e["awayTeam"]["name"]
        hs = e.get("homeScore", {}).get("current", "-")
        as_ = e.get("awayScore", {}).get("current", "-")
        minuto = e.get("time", {}).get("currentPeriodStartTimestamp")
        status = e.get("status", {}).get("description", "")
        torneio = e.get("tournament", {}).get("name", "")
        print(
            f"  [{e['id']:>10}] {home} {hs} x {as_} {away}"
            f"  ({status})  -  {torneio}"
        )


def events_by_date(dia: str, sport: str = "football") -> None:
    """Eventos programados/finalizados em uma data (YYYY-MM-DD)."""
    data = get(f"/sport/{sport}/scheduled-events/{dia}")
    evs = data.get("events", [])
    print(f"-- {len(evs)} eventos em {dia} ({sport}) --")
    for e in evs[:25]:
        home = e["homeTeam"]["name"]
        away = e["awayTeam"]["name"]
        hs = e.get("homeScore", {}).get("current", "-")
        as_ = e.get("awayScore", {}).get("current", "-")
        status = e.get("status", {}).get("type", "")
        torneio = e.get("tournament", {}).get("name", "")
        print(
            f"  [{e['id']:>10}] {home} {hs} x {as_} {away}"
            f"  ({status})  -  {torneio}"
        )


def event_detail(event_id: int) -> None:
    """Resumo de um evento + alguns sub-recursos disponiveis."""
    print(f"\n### /event/{event_id}  (resumo)")
    pp(get(f"/event/{event_id}"))

    print(f"\n### /event/{event_id}/statistics")
    try:
        pp(get(f"/event/{event_id}/statistics"))
    except RuntimeError as e:
        print(f"  (indisponivel: {e})")

    print(f"\n### /event/{event_id}/lineups")
    try:
        pp(get(f"/event/{event_id}/lineups"))
    except RuntimeError as e:
        print(f"  (indisponivel: {e})")

    print(f"\n### /event/{event_id}/incidents   (gols, cartoes, ...)")
    try:
        pp(get(f"/event/{event_id}/incidents"))
    except RuntimeError as e:
        print(f"  (indisponivel: {e})")

    print(f"\n### /event/{event_id}/odds/1/all  (odds principais)")
    try:
        pp(get(f"/event/{event_id}/odds/1/all"))
    except RuntimeError as e:
        print(f"  (indisponivel: {e})")


def search(q: str) -> None:
    """Busca por jogadores, times, torneios."""
    data = get(f"/search/all", q=q, page=0)
    results = data.get("results", [])
    print(f"-- {len(results)} resultados para '{q}' --")
    for r in results[:15]:
        typ = r.get("type")
        entity = r.get("entity", {})
        nome = entity.get("name") or entity.get("shortName") or "?"
        eid = entity.get("id")
        extra = ""
        if typ == "player":
            team = entity.get("team", {}).get("name", "")
            extra = f"  [{team}]"
        elif typ == "team":
            country = entity.get("country", {}).get("name", "")
            extra = f"  ({country})"
        print(f"  {typ:<10} id={eid:<10} {nome}{extra}")


def player(player_id: int) -> None:
    """Dados do jogador + estatisticas da temporada atual."""
    print(f"\n### /player/{player_id}")
    pp(get(f"/player/{player_id}"))

    print(f"\n### /player/{player_id}/statistics/overall")
    try:
        pp(get(f"/player/{player_id}/statistics/overall"))
    except RuntimeError as e:
        print(f"  (indisponivel: {e})")


def team(team_id: int) -> None:
    print(f"\n### /team/{team_id}")
    pp(get(f"/team/{team_id}"))

    print(f"\n### /team/{team_id}/players")
    try:
        pp(get(f"/team/{team_id}/players"))
    except RuntimeError as e:
        print(f"  (indisponivel: {e})")


# ---------------------------------------------------------------
# Catalogo (o que da' pra fazer com a API)
# ---------------------------------------------------------------

CATALOGO = """
============================================================
O QUE DA' PRA FAZER COM A API (nao-oficial) DA SOFASCORE
============================================================

Dominio base:  https://api.sofascore.com/api/v1

-- Esportes & categorias --
  GET /sport/-/categories                       lista de esportes
  GET /config/default-unique-tournaments/BR/football
                                                torneios padrao de um pais

-- Eventos (partidas) --
  GET /sport/{sport}/events/live                todos ao vivo
  GET /sport/{sport}/scheduled-events/{YYYY-MM-DD}
                                                por dia
  GET /event/{id}                               detalhe
  GET /event/{id}/statistics                    estatisticas
  GET /event/{id}/lineups                       escalacoes + notas
  GET /event/{id}/incidents                     gols/cartoes/subs
  GET /event/{id}/graph                         "momentum" grafico
  GET /event/{id}/shotmap                       mapa de chutes
  GET /event/{id}/heatmap/{playerId}            heatmap de 1 jogador
  GET /event/{id}/h2h/events                    confronto direto
  GET /event/{id}/odds/1/all                    odds pre-jogo

-- Times --
  GET /team/{id}                                dados do time
  GET /team/{id}/players                        elenco
  GET /team/{id}/events/last/0                  ultimos jogos
  GET /team/{id}/events/next/0                  proximos jogos
  GET /team/{id}/performance                    forma recente

-- Jogadores --
  GET /player/{id}                              dados
  GET /player/{id}/statistics/overall           stats consolidadas
  GET /player/{id}/events/last/0                ultimos jogos
  GET /player/{id}/transfers                    historico de transferencias

-- Torneios / temporadas --
  GET /unique-tournament/{id}/seasons           temporadas
  GET /unique-tournament/{id}/season/{sid}/standings/total
                                                tabela
  GET /unique-tournament/{id}/season/{sid}/top-players/overall
                                                artilheiros/assistencias
  GET /unique-tournament/{id}/season/{sid}/top-teams/overall
                                                melhores ataques/defesas
  GET /unique-tournament/{id}/season/{sid}/events/round/{n}
                                                jogos por rodada

-- Busca --
  GET /search/all?q={termo}                     busca global

-- Rankings --
  GET /rankings/type/{n}                        rankings FIFA, UEFA etc.

Observacoes:
  * Todos retornam JSON.
  * Alguns caminhos precisam de cabecalhos extras (X-NewRelic-ID
    dispensavel mas User-Agent/Referer sao necessarios).
  * Endpoints podem mudar sem aviso; o site e' a "fonte da verdade".
============================================================
"""


# ---------------------------------------------------------------
# CLI
# ---------------------------------------------------------------

def usage() -> None:
    print(CATALOGO)
    print("Exemplos de uso deste script:")
    print("  python3 sofascore_api.py live")
    print("  python3 sofascore_api.py live tennis")
    print(f"  python3 sofascore_api.py date {date.today().isoformat()}")
    print("  python3 sofascore_api.py event 12345678")
    print("  python3 sofascore_api.py search haaland")
    print("  python3 sofascore_api.py player 795232")
    print("  python3 sofascore_api.py team 2672        # Flamengo")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        usage()
        return 0

    cmd = argv[1]
    try:
        if cmd == "live":
            live_events(argv[2] if len(argv) > 2 else "football")
        elif cmd == "date":
            events_by_date(argv[2], argv[3] if len(argv) > 3 else "football")
        elif cmd == "event":
            event_detail(int(argv[2]))
        elif cmd == "search":
            search(" ".join(argv[2:]))
        elif cmd == "player":
            player(int(argv[2]))
        elif cmd == "team":
            team(int(argv[2]))
        elif cmd in {"help", "-h", "--help"}:
            usage()
        else:
            print(f"Comando desconhecido: {cmd}\n")
            usage()
            return 2
    except RuntimeError as e:
        print(f"Erro na chamada HTTP: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
