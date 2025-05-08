from typing import Optional
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from termcolor import colored
from ..config.config import configuration
import os
import json
class SingletonMeta(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]



def register(json_desc,cls):
    """_summary_
    Decorator to register a function at compile time

    Args:
        json_desc (_type_): function description
    """    
    def decorator(func):
        cls.tool_descriptions.append(json_desc)
        cls.tools[json_desc["function"]["name"]] = func
        return func
    return decorator




class FileSaver(metaclass=SingletonMeta):
    def __init__(self):
        i = 1
        while True:
            dir_name = f"saved_{i}"
            try:
                os.mkdir(dir_name)
                self.dir_name = dir_name
                break
            except FileExistsError:
                i += 1
    def give_dir_name(self)->str:
        """_summary_
        Returns the dir created
        Returns:
            str: dir created
        """        
        return self.dir_name
        


class LLM():
    tools : dict = {}
    tool_descriptions : list[dict]= []

    def __init__(self,model_name:str,api_key: str,system_prompt:str=None,max_completion_tokens:int=None,temperature:float=None):
        """_summary_
        This is a wrapper arround LLM models
        Inits all the variables present
        Args:
            model_name (str): name of llm the model to use
            api_key (str): api_key 
            system_prompt (str, optional): Default system prompt to the LLM Defaults to None.
            max_completion_tokens (int, optional): maximum number of tokens in a single completion. Defaults to None.
            temperature (_type_, optional): controll the randomness of the answer. [0-2], 0 for deterministic and 2 for complete randomness. Defaults to None.
        """        
        self.system_prompt = configuration.base_prompt
        if system_prompt != None:
            self.system_prompt = system_prompt
        # message parametre
        self.model_name :str = model_name
        self.api_key : str= api_key
        self.max_completion_token: Optional[int] = max_completion_tokens
        self.temperature : Optional[int]=temperature

        self.messages : list[dict[str,str]] = [{"role" : "developer","content": self.system_prompt}]
        try:
            self.client : OpenAI = OpenAI(api_key=self.api_key)
        except Exception as e:
            raise Exception(f"Couldn't create openai client:\n{e}")
        
        # tokens info
        self.total_tokens : int= 0
        self.total_input_tokens : int = 0
        self.total_completion_tokens : int = 0
        # tool calls
        self.tool_call_count : int= 0
        self.user_input_count : int = 0
        # api cllas
        self.api_calls : int = 0
        self.file_saver = FileSaver()

    def give_base_messages(self)->list[dict[str,str]]:
        """_summary_
        Return the base messages of the llm:
        Role: "dev"
        content" sys prompt
        Returns:
            list[dict[str,str]]: _description_
        """        

        return [{"role" : "developer","content": self.system_prompt}]

    

    def save_conversation(self)->None:
        """_summary_
        Save conversation to a file with metrics
        """        
        file_path = os.path.join(self.file_saver.give_dir_name(),self.__class__.__name__+".txt")
        with open(file_path,"w") as file:
            file.write(self.give_metrics()+"\n"+self.give_conversation())

            


    def give_metrics(self)->str:
        """_summary_
        Return formatted version of all tokens cmetrics
        Returns:
            str: _description_
        """        
        to_print = "" \
        f"TOTAL_INPUT_TOKEN: {self.total_input_tokens}\n"\
        f"TOTAL_COMPLETION_TOKENS: {self.total_completion_tokens}\n"\
        f"TOTAL_TOKEN: {self.total_tokens}\n"\
        f"TOTAL_TOOL_CALL: {self.tool_call_count}\n"\
        f"TOTAL_API_CALLS: {self.api_calls}\n"\
        f"TOTAL_USER_INPUT: {self.total_input_tokens}\n"

        return to_print
    


    def return_conversation(self)->str:
        """_summary_
        Returns messages as a string
        Returns:
            str: _description_
        """        
        to_ret = ""
        for e in self.messages:
            cont = e["content"]
            if e["role"] == "assistant":
                to_ret+= f"ASSISTANT:\n{ cont}\n"
            elif e["role"] == "user":
                to_ret += f"USER:\n{cont}\n"
            elif e["role"] == "tool":
                to_ret+=f"TOOL:\n{cont}\n"
            elif e["role"] == "developer":
                to_ret+= f"DEVELOPER:\n{cont}\n"
        return to_ret
    
    def give_conversation(self)->str:
        conv = ""
        for e in self.messages:
            cont = e["content"]
            if cont == None:
                cont = ""
            conv += e["role"] + ":\n" + cont +"\n"
        return conv


    def override_system_prompt(self,prompt:str):
        """_summary_
        overrides system prompt
        Args:
            prompt (str): _description_
        """        
        self.system_prompt = prompt
        self.messages[0]["content"] = self.system_prompt
    
    def _increment_user_input(self) -> None:
        self.user_input_count += 1
    
    def _increment_tool_call_count(self) -> None:
        """_summary_
        [PROTECTED METHOD]
        Increment tool call count
        """        
        self.tool_call_count += 1

    def _increment_token_info(self,completion: ChatCompletion)->None:
        """_summary_
        [PROTECTED METHOD]
        Increment tokens count info from a completion response.
        After a completion response, we will store all tokens info in the class instance
        Args:
            completion (ChatCompletion): respone from a chatcompletion.create
        """        
        usage = completion.usage
        self.total_tokens += usage.total_tokens
        self.total_input_tokens +=  usage.prompt_tokens
        self.total_completion_tokens += usage.completion_tokens
    def _increment_api_call(self)->None:
        """_summary_
        Increment api calls
        """        
        self.api_calls+=1
    


    def _get_response(self) -> ChatCompletion:
        """_summary_
        [PROTECTED METHOD]
        send a query to the LLM with the lists of message and return the response
        Returns:
            ChatCompletion: A chat completion object(OpenAI's response)
        """        
        # send and get the response
        completion : ChatCompletion= self.client.chat.completions.create(
            model=self.model_name,
            messages=self.messages,
            tools=self.__class__.tool_descriptions,
            temperature=self.temperature,
            max_completion_tokens=self.max_completion_token
        )
        # append result to the messgae's list
        self._add_assistant_response(completion)
        # Increment token count
        self._increment_token_info(completion)
        self._increment_api_call()
        self.save_conversation()
        return completion


    def _append_to_message(self,content:dict) -> None:
        """_summary_
        [PROTECTED METHOD]
        Append a message (tool_call, user_message or LLM's response) 
        to the list of messages
        Args:
            content (dict): _description_
        """        
        self.messages.append(content)


    def _add_user_message(self,content:str) -> None:
        """_summary_
        [PROTECTED METHOD]
        add a user message to the list of messages (conversation)
        Args:
            content (str): user's message
        """        
        user_message ={"role":"user","content":content}
        self._increment_user_input()
        self._append_to_message(user_message)
    
    def _add_tool_call_message(self,tool_call_id:int,content:str) -> None:
        """_summary_
        [PROTECTED METHOD]
        add a tool call response message to the list of messages
        Args:
            tool_call_id (int): id of the tool call
            content (str): result of the tool call
        """        
        tool_call_message = {"role":"tool","tool_call_id":tool_call_id,"content":content}
        self._append_to_message(tool_call_message)

    def _add_assistant_response(self,completion:ChatCompletion) -> None:
        """_summary_
        add the llm response to the list of messages
        Args:
            completion (ChatCompletion): the chat completion (llm's response)
        """        
        message = completion.choices[0].message
        assistant_response = {"role":"assistant","content":message.content,"tool_calls":message.tool_calls}
        self._append_to_message(assistant_response)
    
    def _process_tool_call(self,completion: ChatCompletion)-> None:
        """_summary_
        Given a completion response, process all tool calls:
        Iterate through every tool_call request, call the function and
        append the result to the message list
        Args:
            completion (ChatCompletion): the chat completion (llm's response)

        Raises:
            Exception: _description_
        """        
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
            # get the function result 
            result = func(**args)
            #append the result
            self._add_tool_call_message(tool_call.id,result)


    
    def send_process_prompt(self,content:str = None) -> str:
        """_summary_
        Sends query to the LLM, until the answer isn't a tool call anymore.
        If the answer is a tool call, it calls the function and sends 
        a prompt with the result.

        Args:
            content (str, optional):    the prompt to send, if it is none,
                                        we will get a response on previous 
                                        prompts
        Returns:
            Str: the final response
        """        
        # add the user message
        if content:
            self._add_user_message(content)
        # send prompt and recieve answer
        completion : ChatCompletion =self._get_response()
        # while the answer is a tool call
        while completion.choices[0].message.tool_calls:
            # treat the tool calls
            self._process_tool_call(completion)
            # get response from the LLM
            completion = self._get_response()
        return completion.choices[0].message.content
     




class test(LLM):
    
    def __init__(self, model_name, api_key, system_prompt = None, max_completion_tokens = None, temperature = None):
        super().__init__(model_name, api_key, system_prompt, max_completion_tokens, temperature)
        # this attribute is a list of tool call execution.
        # the last tool call execution is always at the end of the list
        self.tool_call_execution = []
        tool: dict = {}
        self.system_prompt = ""
        self.messages : list[dict[str,str]] = [{"role" : "developer","content": self.system_prompt}]


