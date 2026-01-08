
import logging

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('travel_agent.log')
        ]
    )

def validate_environment():
    required_vars = ["OPENAI_API_KEY", "TAVILY_API_KEY"]
    missing = []
    
    import os
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"lack of config: {', '.join(missing)}")
        print("please add it in .env file")
        for var in missing:
            print(f"{var}=your_value_here")
        return False
    
    return True