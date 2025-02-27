from typing import Optional
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
import json

def register(json_desc):
    """_summary_
    Decorator to register a function at compile time

    Args:
        json_desc (_type_): _description_
    """    
    def decorator(func):
        LLM.tool_descriptions.append(json_desc)
        LLM.tools[json_desc["function"]["name"]] = func
        return func
    return decorator


class LLM():
    tools : dict = {}
    tool_descriptions : list[dict]= []

    def __init__(self,model_name:str,api_key: str,system_prompt:str=None,max_completion_tokens:int=None,temperature:float=None):
        """_summary_
        This is a wrapper arround LLM models
        Args:
            model_name (str): name of llm the model to use
            api_key (str): api_key 
            system_prompt (str, optional): Default system prompt to the LLM Defaults to None.
            max_completion_tokens (int, optional): maximum number of tokens in a single completion. Defaults to None.
            temperature (_type_, optional): controll the randomness of the answer. [0-2], 0 for deterministic and 2 for complete randomness. Defaults to None.
        """        
        self.system_prompt = "You are an autonomous agent that will have complete access to a linux terminal with all the rights. You will be given a task and need to complete it. You need to be fully autonomous in your actions"
        if system_prompt != None:
            self.system_prompt = LLM.system_prompt
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
    def override_sustem_prompt(self,prompt:str):
        """_summary_
        overrides system prompt
        Args:
            prompt (str): _description_
        """        
        self.system_prompt = prompt

    
    def increment_tool_call_count(self) -> None:
        """_summary_
        Increment tool call count
        """        
        self.tool_call_count += 1

    def increment_token_info(self,completion: ChatCompletion)->None:
        """_summary_
        Increment tokens count info from a completion response.
        After a completion response, we will store all tokens info in the class instance
        Args:
            completion (ChatCompletion): respone from a chatcompletion.create
        """        
        usage = completion.usage
        self.total_tokens = usage.total_tokens
        self.total_input_tokens = usage.prompt_tokens
        self.total_completion_tokens = usage.completion_tokens
    


    def get_response(self) -> ChatCompletion:
        """_summary_

        send a query to the LLM with the lists of message and return the response

        Args:
            content (str): the prompt
        Returns:
            ChatCompletion: A chat completion object(OpenAI's response)
        """        
        # send and get the response
        completion : ChatCompletion= self.client.chat.completions.create(
            model=self.model_name,
            messages=self.messages,
            tools=LLM.tool_descriptions,
            temperature=self.temperature,
            max_completion_tokens=self.max_completion_token
        )
        # append result to the messgae's list
        self.add_assistant_response(completion)
        # Increment token count
        self.increment_token_info(completion)
        return completion
    def add_user_message(self,content:str):
        """_summary_
        add a user message to the list of messages (conversation)
        Args:
            content (str): user's message
        """        
        self.messages.append({"role":"user","content":content})
    
    def add_tool_call_message(self,tool_call_id:int,content:str):
        """_summary_
        add a tool call response message to the list of messages
        Args:
            tool_call_id (int): id of the tool call
            content (str): result of the tool call
        """        
        self.messages.append({"role":"tool","tool_call_id":tool_call_id,"content":content})

    def add_assistant_response(self,completion:ChatCompletion):
        """_summary_
        add the llm response to the list of messages
        Args:
            completion (ChatCompletion): the chat completion (llm's response)
        """        
        message = completion.choices[0].message
        self.messages.append({"role":"assistant","content":message.content,"tool_calls":message.tool_calls})
    
    def process_tool_call(self,completion: ChatCompletion)-> None:
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
            self.increment_tool_call_count()
            #add the tool call to the list of messages
            function_name = tool_call.function.name
            # check if the function name is present in the tools dict
            if not LLM.tools[function_name]:
                raise Exception("LLM trying to call a missing function")
            
            # get the function to use
            func = LLM.tools[function_name]
            # get arguments of the func
            args = json.loads(tool_call.function.arguments)
            # get the function result 
            result = func(**args)
            #append the result
            self.add_tool_call_message(tool_call.id,result)


    
    def send_process_prompt(self,content:str) -> str:
        """_summary_
        Sends query to the LLM, until the answer isn't a tool call anymore.
        If the answer is a tool call, it calls the function and sends 
        a prompt with the result.

        Args:
            content (str):  the prompt to send
        Returns:
            Str: the final response
        """        
        # add the user message
        self.add_user_message(content)
        # send prompt and recieve answer
        completion : ChatCompletion =self.get_response()
        # while the answer is a tool call
        while completion.choices[0].message.tool_calls:
            # Increment token info
            response_message = completion.choices[0].message
            self.process_tool_call(completion)
            completion = self.get_response()
        return completion.choices[0].message.content





    



