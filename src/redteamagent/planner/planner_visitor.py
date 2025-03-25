from ..visitor import AbstractVisitor
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
        self.llm_planner= LLMPlanner(api_key="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",model_name="gpt-4o")

        
        prompt = "You are a planner. The user will give you a single task. Your job is to decide whether the task truly needs decomposition into subtasks considering that you (the LLM have full access to a terminal).\n"\
        "When to Decompose:\n"\
        "When the task is really big, only when its too complicated\n"\
        "When not to decompose\n"\
        "Installing something shouldn't be a subtask"\
        "setting up an environment shouldn't be a subtask"\
        "Chosing a tool shouldn't be a subtask"\
        "Detailing an implementation"
        "How to Output Decompositions:\n"\
        "If you decide the task should be decomposed, use the 'decompose_task' tool with a concise list of only essential subtasks.\n"\
        "If the task can be handled without formal decomposition, call the 'decompose_task' tool with a null argument (indicating no decomposition).\n"\
        "Important:\n"\
        "You need to decompose a subtask into MAXIMUM 5 subtasks.\n"\
        "A subtask shouldn't be created to detail an implementation\n"\
        "DO NOT INCLUDE TASKS THAT AREN'T DIRECTLY TIED TO SOMETHING TECHNICAL (conception, design, framework decision.\n"\
        "Do not over-decompose tasks.\n"\
        "Choices of languages, frameworks, tools aren't subtasks, a subtask MUST NEVER BE TO CHOSE A TOOL or a METHOD\n"\
        

        self.llm_planner.override_system_prompt(prompt)

    def __get_higher_tasks_list(self,node:AbstractNode) -> list[str]:
        """_summary_
        From a node, get all the parent tasks recursively
        Args:
            node (AbstractNode): node

        Returns:
            list[str]: list of parent tasks. The left of the list
            is the lowest task, the right of the list is the highest task
        """        
        higher_tasks : list[str]= []
        act_node = node.parent
        while act_node:
            higher_tasks.append(act_node.task)
            act_node = act_node.parent
        return higher_tasks

    def __format_higher_tasks(self,higher_tasks: list[str]) -> str:
        """_summary_
        Format the higher task into a (hopefully) comprehensive version 
        for the llm
        Args:
            higher tasks (list[AbstractNode]): higher tasks list (top right is highes)

        Returns:
            str : formatted version
            The task derives from:\n
            subtask 1 -> subtask 2 -> subtask 3 -> .... subtask n -> 
        """        
        formatted_version: str = "The task derives from:\n"
        i = len(higher_tasks) - 1
        while i >=0 :
            formatted_version += higher_tasks[i] + " -> "
            i -= 1
        return formatted_version
    
    def __get_higher_tasks(self,node:AbstractNode)->str:
        """_summary_
        for a given node x, give all its dependancy
        ex:
        root_task->child1_task->x_task
        Args:
            task (str): _description_

        Returns:
            str: _description_
        """        
        # gather parent tasks
        higher_tasks = self.__get_higher_tasks_list(node)
        # formatted the tasks
        formatted_version =self.__format_higher_tasks(higher_tasks)
        if len(formatted_version) != 0:
            formatted_version+=node.task
        return formatted_version











    @multimethod
    def visit(self, node:ExecutionNode):
        """_summary_
        if the node is an execution node, will gather the parent information(higher task)
        and ask the llm to decompose or not
        Args:
            node (ExecutionNode): _description_

        Raises:
            Exception: _description_
        """        
        # input("DO YOU WANT TO CONTINUE  ? :  ")
        if node.lvl >= self.plan_lvl:
            print(f"Stopping decomposition lvl >= {self.plan_lvl}")
            return
        higher_tasks = self.__get_higher_tasks(node)
        # create the prompt
        prompt = f"task: \'{node.task}\'\n{higher_tasks}"
        self.llm_planner.send_process_prompt(prompt)
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
