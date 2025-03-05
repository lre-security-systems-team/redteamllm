from typing import Optional
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from termcolor import colored
import json

def register(json_desc,cls):
    """_summary_
    Decorator to register a function at compile time

    Args:
        json_desc (_type_): _description_
    """    
    def decorator(func):
        cls.tool_descriptions.append(json_desc)
        cls.tools[json_desc["function"]["name"]] = func
        return func
    return decorator


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
        self.system_prompt = "You are an autonomous agent that will have complete access to a linux terminal with all the rights. You will be given a task and need to complete it. You need to be fully autonomous in your actions"
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
    


    def print_conversation(self):
        for e in self.messages:
            cont = e["content"]
            if e["role"] == "assistant":
                print(colored(f"ASSISTANT:\n{ cont}","white"))
            elif e["role"] == "user":
                print(colored(f"USER:\n{cont}","green"))
            elif e["role"] == "tool":
                print(colored(f"TOOL:\n{cont}","blue"))
            elif e["role"] == "developer":
                print(colored(f"DEVELOPER:\n{cont}","yellow"))
            else:
                print(colored("wrong role","red"))


    def override_system_prompt(self,prompt:str):
        """_summary_
        overrides system prompt
        Args:
            prompt (str): _description_
        """        
        self.system_prompt = prompt
        self.messages[0]["content"] = self.system_prompt

    
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
        self.total_tokens = usage.total_tokens
        self.total_input_tokens = usage.prompt_tokens
        self.total_completion_tokens = usage.completion_tokens
    


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
        self.__add_assistant_response(completion)
        # Increment token count
        self._increment_token_info(completion)
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
        # print("role:",content["role"])
        # print("content: ",content["content"])


    def _add_user_message(self,content:str) -> None:
        """_summary_
        [PROTECTED METHOD]
        add a user message to the list of messages (conversation)
        Args:
            content (str): user's message
        """        
        user_message ={"role":"user","content":content}
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

    def __add_assistant_response(self,completion:ChatCompletion) -> None:
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
     



