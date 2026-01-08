from abc import ABC, abstractmethod
from typing import Any, Dict
import inspect


class BaseTool(ABC):
    
    
    @property
    @abstractmethod
    def name(self)->str:
        pass
    
    @property
    @abstractmethod
    def descrption(self)->str:
        pass
    
    
    @abstractmethod
    def execute(self,**kwargs)-> str:
        pass
    
    @property
    def signature(self)->str:
        sig = inspect.signature(self.execute)
        params=[]
        
        for name,param in sig.parameters.items():
            if name=="self":
                continue
            
            params.append(f"{name}: {param.annotation.__name__}")
        return f"{self.name}({', '.join(params)})"
    
    
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "signature": self.signature
        }
    
    
    
            
        
        
        
    


