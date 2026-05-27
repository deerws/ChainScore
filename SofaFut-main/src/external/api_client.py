import json
import subprocess


class SofaScoreApiClient:

    BASE_URL = "https://api.sofascore.com/api/v1"

    def __init__(self, timeout=15):
        self.timeout = timeout

    def _get(self, path: str, **params):
        url = f"{self.BASE_URL}{path}"

        if params:
            query_string = "&".join(f"{key}={value}" for key, value in params.items())
            url = f"{url}?{query_string}"

        cmd = [
            "curl",
            url,
            "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "-H", "Accept: application/json",
            "-H", "Accept-Language: en-US,en;q=0.9",
            "-H", "Referer: https://www.sofascore.com/",
            "-H", "Origin: https://www.sofascore.com",
            "--max-time", str(self.timeout),
            "-s"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Erro ao executar curl: {result.stderr}")

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(f"Resposta inválida da API:\n{result.stdout[:300]}")

        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(f"Erro da API: {data}")

        return data

    def search(self, query: str, page: int = 0):
        return self._get("/search/all", q=query, page=page)

    def get_live_events(self, sport: str = "football"):
        return self._get(f"/sport/{sport}/events/live")

    def get_events_by_date(self, dia: str, sport: str = "football"):
        return self._get(f"/sport/{sport}/scheduled-events/{dia}")

    def get_event(self, event_id: int):
        return self._get(f"/event/{event_id}")

    def get_event_statistics(self, event_id: int):
        return self._get(f"/event/{event_id}/statistics")

    def get_event_lineups(self, event_id: int):
        return self._get(f"/event/{event_id}/lineups")

    def get_event_incidents(self, event_id: int):
        return self._get(f"/event/{event_id}/incidents")

    def get_event_odds(self, event_id: int):
        return self._get(f"/event/{event_id}/odds/1/all")

    def get_player(self, player_id: int):
        return self._get(f"/player/{player_id}")

    def get_player_statistics(self, player_id: int):
        return self._get(f"/player/{player_id}/statistics/overall")

    def get_team(self, team_id: int):
        return self._get(f"/team/{team_id}")

    def get_team_players(self, team_id: int):
        return self._get(f"/team/{team_id}/players")