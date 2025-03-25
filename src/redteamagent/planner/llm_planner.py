from ..llm.llm_wrapper import LLM,register
from typing import Optional
from ..execution_tree import ExecutionNode
class LLMPlanner(LLM):

    llm_plan_result : Optional[ExecutionNode] = None
    tools : dict = {}
    tool_descriptions : list[dict]= []
    def __init__(self, model_name, api_key, system_prompt = None, max_completion_tokens = None, temperature = None):
        super().__init__(model_name, api_key, system_prompt, max_completion_tokens, temperature)
    
    def send_process_prompt(self, content = None):
        res = super().send_process_prompt(content)
        # reset messages
        self.messages : list[dict[str,str]] = [{"role" : "developer","content": self.system_prompt}]
        return res


    