from typing import List, Dict, Optional, Callable
from config.prompt import AGENT_SYSTEM_PROMPT
from core.parser import ResponseParser
import logging

logger = logging.getLogger(__name__)

class TravelAgent:
    
    def __init__(self, llm_client, tools: Dict[str, Callable], config):
        self.llm_client = llm_client
        self.tools = tools
        self.config = config
        self.conversation_history: List[str] = []
        self.parser = ResponseParser()
        
    def add_to_history(self, content: str):
        self.conversation_history.append(content)
    
    def get_full_prompt(self) -> str:
        return "\n".join(self.conversation_history)
    
    def run(self, user_input: str) -> str:
        logger.info(f"user input: {user_input}")
        
        self.conversation_history = [f"user input: {user_input}"]
        
        print(f"user input: {user_input}\n" + "="*40)
        
        for iteration in range(self.config.max_iterations):
            logger.info(f"iterator {iteration + 1}")
            print(f"\n--- cycling {iteration + 1} ---")
            
            full_prompt = self.get_full_prompt()
            llm_output = self.llm_client.generate(
                prompt=full_prompt,
                system_prompt=AGENT_SYSTEM_PROMPT,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            llm_output = self.parser.truncate_multiple_actions(llm_output)
            print(f"model output:\n{llm_output}\n")
            self.add_to_history(llm_output)
            
            thought, action_str = self.parser.parse_llm_output(llm_output)
            
            if not action_str:
                logger.error("Can Not Find Valid Action")
                print("No Action was found!")
                break
            
            if action_str.startswith("finish"):
                _, kwargs = self.parser.parse_action(action_str)
                final_answer = kwargs.get("answer", "Task Finished")
                print(f"Task finished, here is the answer {final_answer}")
                return final_answer
            
            tool_name, kwargs = self.parser.parse_action(action_str)
            
            if tool_name in self.tools:
                logger.info(f"execute tool: {tool_name}, parameters: {kwargs}")
                observation = self.tools[tool_name](**kwargs)
            else:
                observation = f"Error: tool undefined '{tool_name}'"
                logger.error(observation)
            
            observation_str = f"Observation: {observation}"
            print(f"{observation_str}\n" + "="*40)
            self.add_to_history(observation_str)
        
        return "Error:Reach Max Iteration Times, Task not finished!"
    
    def reset(self):
        """Reset history"""
        self.conversation_history = []