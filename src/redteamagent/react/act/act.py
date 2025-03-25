from termcolor import colored
# this module will have the role of action
# It will take some input(reasonning, given by the reason component, chose an action to execute and do it)
# Many execution rounds can happen consecutively
from ...llm import LLM,register
from openai.types.chat.chat_completion import ChatCompletion
import json

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
        print(colored(f"Command:\n{content}","red"))
    
    def _add_assistant_response(self, completion:ChatCompletion)->None:
        """_summary_
        Overloaded to add printing options
        Args:
            completion (ChatCompletion): _description_
        """        
        super()._add_assistant_response(completion)
        print(colored(f"assistant:\n{completion.choices[0].message.content}"))

    


    
    
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
        """_summary_
        Returns last tool execution
        Returns:
            str: commands and result of the last tool execution
        """        
        return self.tool_call_execution[-1]

    

    def _process_tool_call(self, completion:ChatCompletion)->None: 
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
        response_message = completion.choices[0].message
        for tool_call in response_message.tool_calls:
            # increment tool call nb
            self._increment_tool_call_count()
            #add the tool call to the list of messages
            function_name = tool_call.function.name
            # check if the function name is present in the tools dict
            if not self.__class__.tools[function_name]:
                raise Exception("LLM trying to call a missing function")
            
            # get the function to use
            func = self.__class__.tools[function_name]
            # get arguments of the func
            args = json.loads(tool_call.function.arguments)
            # add args to tool_call_execution
 #           do = input(colored(f"Want to execute {function_name} with {args} ? ","red"))
#            if do != "y" and do !="yes":
  #              raise Exception("USER DIDNT WANT TO EXECUTE COMMAND")
            # get the function result 
            result = func(**args)
            # add results to tool_call_execution
            tool_call_execution+= "result:\n" + result +"\n" 
            #append the result
            self._add_tool_call_message(tool_call.id,result)
        self.tool_call_execution.append(tool_call_execution)

    
    def add_task(self,task:str):
        """_summary_
        add task to act
        Args:
            task (str): _description_
        """        
        self._add_user_message(task)

    def send_process_messages(self,reasonning:str)->bool: 
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
        self.__add_reasonning(reasonning)
        # send past messages and recieve answer
        completion : ChatCompletion =self._get_response()
        # while the answer is a tool call
        if completion.choices[0].message.tool_calls:
            # treat the tool calls
            self._process_tool_call(completion)
            return True
        return False
