from ..visitor import AbstractVisitor
from typing import Optional
from multimethod import multimethod
from ..execution_tree import ExecutionNode,FailedNode,PlanningNode, AbstractNode
from .llm_planner import LLMPlanner

class PlannerVisitor(AbstractVisitor):

    def __init__(self,task:str, memory_manager):
        # task to do
        self.root_task : str = task
        self.root_task_node : AbstractNode = None
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
        "How to Output Decompositions:\n"\
        "If you decide the task should be decomposed, use the 'decompose_task' tool with a concise list of only essential subtasks.\n"\
        "If the task can be handled without formal decomposition, call the 'decompose_task' tool with a null argument (indicating no decomposition).\n"\
        "Important:\n"\
        "DO NOT INCLUDE TASKS THAT AREN'T DIRECTLY TIED TO SOMETHING TECHNICAL (conception, design, framework decision.\n"\
        "Do not over-decompose tasks.\n"\
        "Choices of languages, frameworks, tools aren't subtasks, a subtask MUST NEVER BE TO CHOSE A TOOL or a METHOD\n"\
        
        print(prompt)

        prompt2 = ""
        "You are a planner. The user will give you a task and you will decide to decompose it or not.\n"
        "Considering you have full access to a terminal for the user given task,"
        "if you think that it needs to be decompose(you can't do it easily)"
        "than decompose the task using 'decompose_task' tool with a list of subtasks"
        "if you think that you can achieve this task with multiple iteration without decomposing it, use 'decompose_task' tool with null argument"
        "A task that is just commands on the terminal, aren't tasks needed for decomposition"
        "Dont include tasks that are user oriented (like chosing the framework, etc.. you should chose them directly)"
        self.llm_planner.override_system_prompt(prompt)

    def give_first_plan(self) -> AbstractNode:
        """_summary_
        When given a task, it creates the first node
        Raises:
            Exception: _description_
        """        
        # retrieve memory manger to plan
        # FIXME

        # than we make the first plan
        self.llm_planner.send_process_prompt(f"task: {self.root_task}")
        # if result is None than no need for decomposition
        # we create an execution Node
        if LLMPlanner.llm_plan_result == None:
            self.root_task_node = ExecutionNode(self.root_task)
            self.root_task_node.set_lvl(0)
            return self.root_task_node
        # create a planning node
        self.root_task_node = PlanningNode(self.root_task)
        self.root_task_node.set_lvl(0)
        actual_node = LLMPlanner.llm_plan_result
        # set its parent
        actual_node.parent = self.root_task_node
        #create children list to store later in the root
        children_list = []
        while actual_node != None:
            if not isinstance(actual_node,ExecutionNode):
                raise Exception("Didn't get an ExecutionNode")
            # set the parent
            actual_node.parent = self.root_task_node
            # set lvl
            actual_node.set_lvl(1)
            # add it to the list
            children_list.append(actual_node)
            actual_node = actual_node.next_node
        #set the children list
        self.root_task_node.children = children_list
        return self.root_task_node

    def get_higher_tasks(self,node:AbstractNode) -> list[str]:
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

    def format_higher_tasks(self,higher_tasks: list[AbstractNode]) -> str:
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
        print("-------------------------------")
        print(higher_tasks)
        print("-------------------------------")
        while i >=0 :
            formatted_version += higher_tasks[i] + " -> "
            i -= 1
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
        # gather parent tasks
        higher_tasks = self.get_higher_tasks(node)
        higher_tasks += node.task
        # formatted the tasks
        formatted_version =self.format_higher_tasks(higher_tasks)
        # add last task to formatted
        # create the prompt
        prompt = f"task: \'{node.task}\'\n{formatted_version}"
        # ask the llm to decompose or not.
        print(prompt)
        self.llm_planner.send_process_prompt(prompt)
        # check if response is null (just return)
        actual_node = LLMPlanner.llm_plan_result
        if actual_node == None:
            return
        plan_node = PlanningNode(node.task)
        # set its parent
        plan_node.parent = node.parent
        # plan node needs to point to next of node
        plan_node.next_node = node.next_node
        # set lvl
        plan_node.set_lvl(node.lvl)
        # node parent needs to point to it
        # check if parent is a planning node
        if not isinstance(node.parent,PlanningNode):
            raise Exception("Did not find a 'PlanningNode' in the parent")
        for e in range(len(node.parent.children)):
            # find the children position
            if node.parent.children[e] == node:
                # replace it with the new node
                node.parent.children[e] = plan_node
        actual_node = LLMPlanner.llm_plan_result
        #create children list
        children_list: list[ExecutionNode] = []
        while actual_node != None:
            if not isinstance(actual_node,ExecutionNode):
                raise Exception("Didn't get an ExecutionNode")
            # set the parent
            actual_node.parent = self.root_task_node
            # set lvl
            actual_node.set_lvl(node.lvl + 1)
            # add it to the list
            children_list.append(actual_node)
            actual_node = actual_node.next_node
        plan_node.children = children_list
        
        

        # we created a new node so we visit it
        plan_node.accept(self)
        
        

    @multimethod
    def visit(self, node:PlanningNode):
        for e in node.children:
            e.accept(self)
    
    @multimethod
    def visit(self, node:FailedNode):
        raise Exception("Planner shouldn't visit a Failed Node")
