from base import BaseTool
from clients.tavily_client import TabilyClientWrapper
import logging

logger = logging.getLogger(__name__)


class AttractionTool(BaseTool):
    
    def __init__(self,api_key:str):
        self.client = TabilyClientWrapper(api_key=api_key)
    
    @property
    def name()->str:
        return "get_attraction"
    
    @property
    def description()->str:
        return "attractions according to weather and city"
    
    def execute(self, city:str,weather:str)->str:
        
        
        logger.info(f"search city: {city}, weather: {weather}")
        
        query = f"Top tourist attractions to visit in {city} during {weather} weather"
        
        try:
            response = self.client.search(query=query)
            
            if "error" in response:
                    return f"search failed: {response['error']}"
                
            if response.get("answer"):
                    return response["answer"]
                
            formatted_results = []
            for result in response.get("results", []):
                    formatted_results.append(
                        f"📌 {result.get('title', 'no title')}\n"
                        f"   {result.get('content', 'no content')}\n"
                        f"   🔗 {result.get('url', 'no link')}\n"
                    )
                
            if not formatted_results:
                    return f"Sorry, can not find tourist attractions {city} during {weather}"
                
            return "Based on the search results, here are the recommended attractions:\n\n" + "\n".join(formatted_results)
                
        except Exception as e:
                error_msg = f"tool executed with error: {e}"
                logger.error(error_msg)
                return error_msg