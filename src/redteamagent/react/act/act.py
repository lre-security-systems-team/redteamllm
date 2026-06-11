from termcolor import colored
from ...config.config import configuration
# this module will have the role of action
# It will take some input(reasonning, given by the reason component, chose an action to execute and do it)
# Many execution rounds can happen consecutively
from ...llm import LLM,register
from ..summarizer.summarizer import Summarizer
import json
import os

#WHY ARE WE REWRITING THIS FUNCTION, IT IS ALREADY IN LLM
# BECAUSE WE NEED TO CHANGE THE LLM. to Act. because we dont want conflict
# when setting different tools to different classes that inherits from LLM class

class Act(LLM):
    # were overriding these 2 attributes because if we dont,
    # every time someone that inherits from LLM add a tool, 
    # it will be added to the parent class
    tools : dict = {}
    tool_descriptions : list[dict]= []
    def __init__(self, model_name, api_key, system_prompt = None, max_completion_tokens = None, temperature = None):
        super().__init__(model_name, api_key, system_prompt, max_completion_tokens, temperature)
        # this attribute is a list of tool call execution.
        # the last tool call execution is always at the end of the list
        self.tool_call_execution = []
        self.summarizer = Summarizer(model_name=self.model_name,api_key=self.api_key)

        #######3



    def __add_reasonning(self,reasonning:str) -> None:
        """_summary_
        Function to add reasonning to the list of messages.
        Reasonning message will appear as an assitant message
        Args:
            reasonning (str): reasonning content
        """        

        reasonning_response = {"role":"assistant","content":reasonning}
        print(colored(f"Reasonning\n{reasonning}","yellow"))
        self._append_to_message(reasonning_response)


    def _add_user_message(self, content: str) -> None:
        """_summary_
        OVERRDING METHOD
        add print at the end
        Args:
            content (str): _description_
        """        
        super()._add_user_message(content) 
        print(colored(f"User:\n{content}","blue"))
    
    def _add_tool_call_message(self, tool_call_id:int, content:str)->None:
        """_summary_
        Overload to add the printing options
        Args:
            tool_call_id (int): _description_
            content (str): _description_
        """        
        super()._add_tool_call_message(tool_call_id, content)
        print(colored(f"{content}","red"))
    
    def _add_assistant_response(self, completion)->None:
        """_summary_
        Overloaded to add printing options
        Args:
            completion (ChatCompletion): _description_
        """        
        super()._add_assistant_response(completion)
        text = next((b.text for b in completion.content if b.type == "text"), "")
        print(colored(f"assistant:\n{text}"))

    


    
    
    def send_process_prompt(self,reasonning: str,content:str = None): 
        """_summary_
        Every process for act needs reasonning, this way we obblige the  process to have reasonning
        Args:
            reasonning (str): reasonning of the content(normally given by the REASON module)
            content (str, optional): user task. Defaults to None.

        Returns:
            _type_: _description_
        """        
        self.__add_reasonning(reasonning)
        return super().send_process_prompt(content)
    
    def give_last_execution(self) -> str:
        """
        Returns last tool execution (raw).
        """
        return self.tool_call_execution[-1]

    def give_last_execution_for_reason(self) -> str:
        """
        Returns a trimmed version of the last execution for the Reason session.
        Caps at 2000 chars to prevent Reason context from bloating on verbose
        tool output. Reason needs the conclusion, not the full raw result.
        """
        last = self.tool_call_execution[-1]
        if len(last) > 2000:
            return last[:2000] + "\n...[truncated for reasoning efficiency]"
        return last

    

    def _process_tool_call(self, completion)->None: 
        """_summary_
        overriding parent class function and adding tool_call_execution.
        At every tool processing,tool calls and results are appendend to
        self.tool_call_execution
        Args:
            completion (_type_): oepnai_completion

        Raises:
            Exception: _description_
        """        
        tool_call_execution = ""
        for block in completion.content:
            if block.type != "tool_use":
                continue
            # increment tool call nb
            self._increment_tool_call_count()
            function_name = block.name
            # check if the function name is present in the tools dict
            if not self.__class__.tools.get(function_name):
                raise Exception(f"LLM trying to call a missing function: {function_name}")

            # get the function to use
            func = self.__class__.tools[function_name]
            # get arguments (Anthropic provides input as a dict, not JSON string)
            args = block.input
            print(colored(f"Command: {args}",'red',"on_black"))
            # get the function result
            result = func(**args)
            # summarize result
            if len(result) > 3000 and configuration.activate_summary:
                # Inject engagement context so summarizer knows what to keep
                self.summarizer.set_engagement_context(
                    target=getattr(self, '_current_target', 'unknown'),
                    phase=getattr(self, '_current_phase', 'unknown'),
                    findings=getattr(self, '_current_findings', 'none established yet')
                )
                result = self.summarizer.send_process_prompt(
                    f"command:{args}\nresult:\n{result}"
                )

            # add results to tool_call_execution  
            tool_call_execution+= "Command:\n"+args["command"]+"\nresult:\n" + result +"\n" 
            #append the result
            self._add_tool_call_message(block.id,result)
        self.tool_call_execution.append(tool_call_execution)

    
    def add_task(self, task: str):
        """
        Add task to act.
        """
        self._add_user_message(task)

    def set_context(self, target: str = "", phase: str = "", findings: str = "") -> None:
        """
        Set engagement context so the summarizer can make informed decisions.
        Call this whenever the phase changes or a significant finding is made.

        Args:
            target   (str): target IP or hostname
            phase    (str): current phase (recon, enumeration, exploitation, post-exploit)
            findings (str): key findings so far, 1-5 lines
        """
        self._current_target = target
        self._current_phase = phase
        self._current_findings = findings

    def send_process_messages(self, reasonning:str = None)->bool: 
        """_summary_
        looks like 'send_process_messages' but with some twists.
        doesnt take any argument. Task is given before.
        And process tool calls just one time
        Args:
            Reasonning (str): reasonning to add
        Returns:
            bool:   True if last execution was a toolcall
                    False if last excution was a normal response
        """        
        if reasonning:
            self.__add_reasonning(reasonning)
        # send past messages and recieve answer
        completion = self._get_response()
        if any(b.type == "tool_use" for b in completion.content):
            self._process_tool_call(completion)
            return True
        return False
