"""
主程序入口
"""
import sys
from config import ConfigManager
from clients.openai_client import OpenaiClientWrapper
from clients.tavily_client import TabilyClientWrapper
from tools.weather_tool import WeatherTool
from tools.attraction_tool import AttractionTool
from core.agent import TravelAgent
from utils.helpers import setup_logging, validate_environment

def main():
    # set up logging
    setup_logging()
    
    # validate config
    if not validate_environment():
        sys.exit(1)
    
    # loading config
    config_manager = ConfigManager()
    if not config_manager.validate():
        sys.exit(1)
    
    try:
        # initialize client
        openai_client = OpenaiClientWrapper(config_manager.openai)
        tavily_client = TabilyClientWrapper(config_manager.tavily.api_key)
        
        # initialize tools 
        weather_tool = WeatherTool()
        attraction_tool = AttractionTool(tavily_client)
        
        # tool dic
        tools = {
            weather_tool.name: weather_tool.execute,
            attraction_tool.name: attraction_tool.execute
        }
        
        agent = TravelAgent(
            llm_client=openai_client,
            tools=tools,
            config=config_manager.agent
        )
        
        print("🤖 旅行智能体已启动 (输入 'quit' 退出)")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n请输入您的旅行需求: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q', '退出']:
                    print("再见！")
                    break
                
                if not user_input:
                    continue
                
                result = agent.run(user_input)
                print(f"\n🎯 final result:\n{result}")
                
            except KeyboardInterrupt:
                print("\n\n Interrupt")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"failed to initialize: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()