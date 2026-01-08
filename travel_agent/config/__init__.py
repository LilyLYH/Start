
from dataclasses import dataclass
import os
from typing import Optional

@dataclass
class OpenAiConfig:
    api_key: str
    base_url: str
    model_id:str
    
    @classmethod
    def from_env(cls)->Optional[OpenAiConfig]:
        api_key=os.getenv("API_KEY")
        base_url=os.getenv("BASE_URL")
        model_id = os.getenv("MODEL_ID")
        
        if not api_key:
            return None

        else :
            return cls(api_key=api_key,base_url = base_url,model_id=model_id)
        
    
@dataclass
class TavilyApiConfig:
    api_key:str=""
    
    @classmethod
    def from_env(cls)->Optional[TavilyApiConfig]:
        api_key=os.getenv("TAVILY_API_KEY")
        if not api_key:
            return None
        else:
            return cls(api_key)
    
    
@dataclass
class AgentConfig:
    """智能体配置"""
    max_iterations: int = 5
    temperature: float = 0.7
    max_tokens: int = 1000
    
    @classmethod
    def from_env(cls) -> 'AgentConfig':
        return cls(
            max_iterations=int(os.getenv("MAX_ITERATIONS", "5")),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("MAX_TOKENS", "1000"))
        )

class ConfigManager:
      def __init__(self):
          self.openai = OpenAiConfig.from_env()
          self.tavily=TavilyApiConfig.from_env()
          self.agent = AgentConfig.from_env()
          
      def validate(self)->False:
          if not self.openai or not self.openai.api_key:
              print("openai config is not validated!")
              return False
          elif not self.tavily or not self.tavily.api_key:
              print("tavily config is not validated")
              return False
          
          return True
      

          
          
    
