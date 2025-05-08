from ..visitor import AbstractVisitor
from ..config.config import configuration
from typing import Optional
from multimethod import multimethod
from ..execution_tree import ExecutionNode,FailedNode,PlanningNode, AbstractNode
from .llm_planner import LLMPlanner

class PlannerVisitor(AbstractVisitor):

    def __init__(self,root_task_node:list[AbstractNode], memory_manager,plan_lvl=2):
        """_summary_
        Planner visitor. 
        Will handle creating the plan when given a task
        Args:
            task (str): the task to plan
            memory_manager (_type_): the memory manager
            plan_lvl (int, optional): Max level of planning. Defaults to 2.
        """        
        # task to do
        self.plan_lvl=plan_lvl
        self.root_task_node : list[AbstractNode] = root_task_node
        # mempry manager not yet installed
        self.memory_man = memory_manager
        
        self.llm_planner= LLMPlanner(api_key=configuration.api_key,model_name=configuration.model_name)


        
        prompt = "You are a planner. The user will give you a single task. Your job is to decide whether the task truly needs decomposition into subtasks considering that you (the LLM have full access to a terminal).\n"\
        "When to Decompose:\n"\
        "When the task is really big, only when its too complicated\n"\
        "When not to decompose\n"\
        "When the task can be executed by another LLM having acces to a terminal without too much difficulty.\n"
        "How to Output Decompositions:\n"\
        "If you decide the task should be decomposed, use the 'decompose_task' tool with a concise list of only essential subtasks.\n"\
        "If the task can be handled without formal decomposition, call the 'decompose_task' tool with a null argument (indicating no decomposition).\n"\
        "Important:\n"\
        "Every task must me decompose into MAXIMUM 5 subtasks.\n"\
        

        self.llm_planner.override_system_prompt(prompt)


    

    def __get_all_tasks(self,actual_node:AbstractNode)->str:
        """_summary_
        Get the whole tree plan and add an index to the actual node
        Args:
            actual_node (AbstractNode): actual node

        Returns:
            str: tree plan into text form:
            1- task
            1.2- task
            1.2 - task
        """        
        inital_task_prompt = ""
        def get_all_tasks(pref:str,node:AbstractNode)->str:
            context = pref+ f" - {node.task}"
            if node == actual_node:
                context += "( YOU ARE HERE )"
                # tells to look out for the variable outside the scope
                nonlocal inital_task_prompt
                inital_task_prompt += f"You have to chose to decompose or no the task : {pref}\nTASK: {node.task}\n"
            context += "\n"
            i = 1
            for e in node.children:
                child_pref = pref+f".{i}"
                res = get_all_tasks(child_pref,e) 
                context += res
                i+=1
            return context 
        tree_plan = get_all_tasks("1",self.root_task_node[0])
        return inital_task_prompt + f"Here is the plan made until now:\n{tree_plan}"



        




        










    @multimethod
    def visit(self, node:ExecutionNode):
        """_summary_
        if the node is an execution node, will gather the parent information(higher task)
        and ask the llm to decompose or not
        Args:
            node (ExecutionNode): node to visit

        Raises:
            Exception: _description_
        """        
        # input("DO YOU WANT TO CONTINUE  ? :  ")
        if node.lvl >= self.plan_lvl:
            print(f"Stopping decomposition lvl >= {self.plan_lvl}")
            return
        # plan representing the tree of tasks        
        from termcolor import colored
        tree_plan_prompt = self.__get_all_tasks(node)
        print(colored(tree_plan_prompt,"blue"))

        # create the prompt
        self.llm_planner.send_process_prompt(tree_plan_prompt)
        # check if response is null (just return)
        result_node = LLMPlanner.llm_plan_result
        if result_node == None:
            return
        ######################
        new_node = PlanningNode(node.task)
        new_node.set_lvl(node.lvl)
        # check if is the root task
        if new_node.lvl == 0:
            self.root_task_node[0] = new_node
        result_node = LLMPlanner.llm_plan_result
        ###################
        node.change_node_to_planning(new_node=new_node,children=result_node)
        # we created a new node so we visit it
        new_node.accept(self)
        
        

    @multimethod
    def visit(self, node:PlanningNode):
        for e in node.children:
            e.accept(self)
    
    @multimethod
    def visit(self, node:FailedNode):
        raise Exception("Planner shouldn't visit a Failed Node")
