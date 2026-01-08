from tavily import TavilyClient
import logging


logger = logging.getLogger(__name__)

class TabilyClientWrapper:
    def __init__(self,api_key:str):
        self.client= TavilyClient(api_key=api_key)
    
    def search(self,
        query: str,
        search_depth: str = "basic",
        include_answer: bool = True):
        try:
            self.client.search(query=query,search_depth=search_depth,include_answer=include_answer)
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return {"error": str(e)}
           
        
    