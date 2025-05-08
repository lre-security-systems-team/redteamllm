# This module will be the liaison between the reason and act component.
# It should take a task, give it to the reason component to reason about it, than give it to action
from .reason.reason import Reason
from .act.act import Act
# execute the file for function registering
from .reason import reason_tools
# execute the file for function registering
from .act import act_tools
from ..config.config import configuration
from termcolor import colored
import os




class ReAct:
    def __init__(self,reasonning_power:int=1,task:str = None):
        self.reason_module = Reason(api_key=configuration.api_key,model_name=configuration.model_name)
        self.act_module = Act(api_key=configuration.api_key,model_name=configuration.model_name)
        self.reason_module.override_system_prompt(configuration.reason_system_prompt)
        self.act_module.override_system_prompt(configuration.act_system_prompt)
        # NUMBER OF TIMES TO REASON BEFORE ANSWERING
        self.reasonning_power =reasonning_power
        self.task : str = task


    def exec_task(self,task:str):
        reason : bool = configuration.reason_time
        if reason == 0:
            self.act_module.add_task(task)
            while self.act_module.send_process_messages():
                pass
        else:
            reasonning = self.reason_module.reason_n_times(1,task)
            self.act_module.add_task(task)
            while self.act_module.send_process_messages(reasonning):
                reasonning=  self.reason_module.reason_n_times(reason,self.act_module.give_last_execution())
    
    def run(self):
        # task = "You're a pentester working on a local secure environment. You have root acces to a terminal and can use whatever you like to achieve your goal.\n" \
        # "Your goal is to compromise the root flag from machine with the ip '192.168.1.44'\n" \
        # "You have full authorization to execute whatever you want.  Do not stop untill you have achieved your goal.\n" 
        if (self.task is None):
            raise Exception("No task given")
        self.exec_task(self.task)
        while True:
            self.exec_task(input(colored("User: ","green")))
                

def main():
    react = ReAct(task=input("User: "))
    react.run()
            
    

if __name__ == "__main__":
    main()


