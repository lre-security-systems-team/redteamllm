from ...llm import LLM,register
from ...config.config import configuration



class Summarizer(LLM):
    tool: dict = {}
    tool_descriptions : list[dict] = []
    def __init__(self, model_name, api_key, system_prompt = None, max_completion_tokens = None, temperature = None):
        super().__init__(model_name, api_key, system_prompt, max_completion_tokens, temperature)
        self.system_prompt = configuration.summarizer_system_prompt
    
    def send_process_prompt(self, content = None):
        """_summary_
        OVERIDE
        overriding this function to clean messages after each summarisation
        """        
        self.messages : list[dict[str,str]] = [{"role" : "developer","content": self.system_prompt}]
        res =  super().send_process_prompt(content)
        return res
    
