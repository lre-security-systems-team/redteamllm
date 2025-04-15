
from ...llm import LLM,register



class Summarizer(LLM):
    tool: dict = {}
    tool_descriptions : list[dict] = []
    def __init__(self, model_name, api_key, system_prompt = None, max_completion_tokens = None, temperature = None):
        super().__init__(model_name, api_key, system_prompt, max_completion_tokens, temperature)
        self.system_prompt = "" \
        "You are a summarizer. Your goal is to summarize results of executed shell command" \
        "following 2 simple rules:\n" \
        "1 - If the result of the command is not long, leave it as it is.\n" \
        "2 - If the result of the command is really long you'll have to summarize" \
        "it keeping everything that is important\n" 
    
    def send_process_prompt(self, content = None):
        """_summary_
        OVERIDE
        overriding this function to clean messages after each summarisation
        """        
        self.messages : list[dict[str,str]] = [{"role" : "developer","content": self.system_prompt}]
        res =  super().send_process_prompt(content)
        return res
    
