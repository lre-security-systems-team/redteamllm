# This module will be the liaison between the reason and act component.
# It should take a task, give it to the reason component to reason about it, than give it to action
from .reason.reason import Reason
from .act.act import Act
# execute the file for function registering
from .reason import reason_tools
# execute the file for function registering
from .act import act_tools
from termcolor import colored
import os




class ReAct:
    def __init__(self,reasonning_power:int=1,task:str = None):
        self.reason_module = Reason(api_key="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",model_name="gpt-4o")
        self.act_module = Act(api_key="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",model_name="gpt-4o")
        self.reason_module.override_system_prompt("" \
        "You are a reasonner. Your only goal is to reason on a task." \
        "You will be given a task with or without examples or context and you will reason on this task.\n" \
        "You have root acces to a linux terminal and have completely control over it.\n" \
        "Your reasonning will be given to an execution agent, so make your output understandable.\n" \
        "Reasonning includes 'brainstorming','concluding', 'taking decisions', " \
        "\'thinking out loud\', \'explaining your thought process and why you came to a conclusion" \
        "and what are the next steps to take.\n" \
        "For example when giving a task, you can start thinking about the task, to make sure you understand it," \
        "you can talk about different way to complete it and than chose the right way. You can also" \
        "weigh your choices to chose the best one.\n"\
        "Finally:\n" \
        "1- Never forget your main goal\n" \
        "2- Keep your answer concise but precise\n" \
        "3- You can use interactive commands but not nano,vim or commands that require arrows\n or commands that run indefinetly\n" \
        "")
        self.act_module.override_system_prompt("You're a PENTESTER.\n" \
        "You will be provided with tasks and you will execute them.\n" \
        "You have access to a non interactive terminal with root acces.\n" \
        "You have full authorisation do execute whatever command you need\n")
        # NUMBER OF TIMES TO REASON BEFORE ANSWERING
        self.reasonning_power =reasonning_power
        self.task : str = task


    def exec_task(self,task:str):
        # reasonning = self.reason_module.reason_n_times(1,task)
        self.act_module.add_task(task)
        while self.act_module.send_process_messages():
            a = 2
            # reasonning=  self.reason_module.reason_n_times(1,self.act_module.give_last_execution())
    
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


