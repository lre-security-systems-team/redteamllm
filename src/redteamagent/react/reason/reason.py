# this component will be given a task. It will reason about it and give the result, usually to the act component
from ...llm import LLM, register


#WHY ARE WE REWRITING THIS FUNCTION, IT IS ALREADY IN LLM
# BECAUSE WE NEED TO CHANGE THE LLM. to Reason. because we dont want conflict
# when setting different tools to different classes that inherits from LLM class

# def register(json_desc):
#     """_summary_
#     Reason
#     Decorator to register a function to the class

#     Args:
#         json_desc (_type_): description of the function
#     """    
#     def decorator(func):
#         Reason.tool_descriptions.append(json_desc)
#         Reason.tools[json_desc["function"]["name"]] = func
#         return func
#     return decorator

class Reason(LLM):
    # were overriding these 2 attributes because if we dont,
    # every time someone that inherits from LLM add a tool, 
    # it will be added to the parent class
    tools : dict = {}
    tool_descriptions : list[dict]= []


    def __process_n_times(self,n:int)-> str:
        """_summary_
        This is a method special for reasonning. It will run the LLM n times.
        It is principally used for multiple times reasonning.
        for example, if you give the reason module  a task, 'send_process_prompt',
        it will just reason 1 time. If you want it to reason multiple times (multiple call),
        you can use this function.
        Args:
            n (int): number of api calls to reason on
        Returns:
            str: a concatenation of the reasonning over the n responses
        """        
        assert(n >0)
        reasonning = ""
        for e in range(n):
            reasonning += "\n"+self.send_process_prompt()
        return reasonning
    
    def reason_n_times(self,n:int,content:str)->str:
        """_summary_
        This function will add the content to the messages as a user message.
        and reason n times via process_n_times function
        Args:
            n (int): number of reasonning times
            content (str): task or context from user

        Returns:
            str: _description_
        """        
        assert(n>0)
        self._add_user_message(content)
        reasonning = self.__process_n_times(n)
        return reasonning

