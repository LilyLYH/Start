
import re
from typing import Tuple, Optional, Dict

class ResponseParser:
    
    @staticmethod
    def parse_llm_output(llm_output: str) -> Tuple[Optional[str], Optional[str]]:

        thought_match = re.search(r"Thought:\s*(.*?)(?=\s*Action:|\s*$)", llm_output, re.DOTALL)
        action_match = re.search(r"Action:\s*(.*?)(?=\s*Thought:|\s*$)", llm_output, re.DOTALL)
        
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        
        return thought, action
    
    @staticmethod
    def parse_action(action_str: str) -> Tuple[str, Dict[str, str]]:

        if action_str.startswith("finish"):
            return "finish", {"answer": action_str[7:-1]}
        
        match = re.match(r"(\w+)\((.*)\)", action_str)
        if not match:
            raise ValueError(f"invalid action format: {action_str}")
        
        tool_name = match.group(1)
        args_str = match.group(2)
        
       
        kwargs = {}
        if args_str:
            args = re.findall(r'(\w+)="([^"]*)"', args_str)
            for key, value in args:
                kwargs[key] = value
        
        return tool_name, kwargs
    
    @staticmethod
    def truncate_multiple_actions(llm_output: str) -> str:
        match = re.search(
            r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)',
            llm_output,
            re.DOTALL
        )
        if match:
            truncated = match.group(1).strip()
            if truncated != llm_output.strip():
                return truncated
        return llm_output