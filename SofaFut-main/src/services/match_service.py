from external.api_client import SofaScoreApiClient

'''
Classe que vai chamar a API
'''

class MatchService():

    def __init__(self, sofa_api : SofaScoreApiClient):
        self.sofa_api = sofa_api

    def get_match_info(self, event_id):
        
        evento = self.sofa_api.get_event(event_id)

        estatisticas = self.sofa_api.get_event_statistics(event_id)

        return {
            "evento" : evento,
            "estatisticas" : estatisticas
        }