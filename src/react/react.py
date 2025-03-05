# This module will be the liaison between the reason and act component.
# It should take a task, give it to the reason component to reason about it, than give it to action
from .reason.reason import Reason
from .act.act import Act
# execute the file for function registering
from .reason import reason_tools
# execute the file for function registering
from .act import act_tools
from termcolor import colored




class ReAct:
    def __init__(self,reasonning_power:int=1):
        self.reason_module = Reason(api_key="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",model_name="gpt-4o")
        self.act_module = Act(api_key="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",model_name="gpt-4o")
        self.reason_module.override_system_prompt("Youre a reasonner. You're only goal is to reason on a task. You will be given a task with or without examples or context and you will reason on this task. Reasonning includes brainstorming,concluding, taking decisions.You need to take in consideration that all the tasks given will be executed through a terminal on linux. Finally, the output you will create will be given to another agent, so make your output understandable. You're answer should be concise")
        self.act_module.override_system_prompt("You're an agent that execute actions. You will be given a task and you will execute it. You have access to a non-interactive terminal with all rights.")
        # NUMBER OF TIMES TO REASON BEFORE ANSWERING
        self.reasonning_power =reasonning_power


    def exec_task(self,task:str):
        reasonning = self.reason_module.reason_n_times(1,task)
        self.act_module.add_task(task)
        while self.act_module.send_process_messages(reasonning):
            reasonning = self.reason_module.reason_n_times(1,self.act_module.give_last_execution())
    
    def run(self):
        while True:
            self.exec_task(input("Enter the task you want"))
    


react = ReAct()
react.run()


