from .abstract_node import AbstractNode
from enum import Enum

class STATUS(Enum):
    PENDING = 0
    RUNNING = 1
    FAILED  = 2
    SUCCEEDED = 3

class ExecutionNode(AbstractNode):
    def __init__(self,task:str):
        super().__init__(task)
        # status of the task execution
        self.status:STATUS = STATUS.PENDING  
        # next node  ( next step )
        # full description of what happened
        # Will be the act message list
        self.execution_log : str = None
        # failure reason ||
        # WHY NOT FAILED NODE ??
        # Because a failed node is created only if its decomposed next. 
        self.failure_reason : str = None

        # what it needs from the previous node ( None if its the most left node)
        self.previous_task_resume: str = None 
        # current task resume
        self.task_resume : str = None




    def accept(self, visitor):
        return visitor.visit(self)
    
    def change_node_to_planning(self, new_node: AbstractNode,children:AbstractNode)->None:
        """_summary_
        Change an Execution node to a planning node. 
        When decomposing a task, we may need to change an execution node to a planning.
        This function does it for us.
        If the node is root, than the function caller must set the root node accordingly
        Args:
            new_node (AbstractNode): The new planning node created
            children (AbstractNode): first child of the planning node
        """        
        new_node.parent = self.parent
        new_node.next_node = self.next_node

        # calculate node number to insert in parent childrens list
        i = 0
        # parent node needs to point to it
        # check if parent is a planning node
        while self.parent != None and i < len(self.parent.children):
            # find the children position
            if self.parent.children[i] == self:
                # replace it with the new node
                self.parent.children[i] = new_node
                break
            i +=1
        
        # create children list
        children_list : list[AbstractNode] = []
        while children != None:
            # set the parent
            children.parent = new_node
            # set the lv;
            children.set_lvl(self.lvl+1)
            # add it to the list
            children_list.append(children)
            children= children.next_node
        # set the children of the planning node
        new_node.children = children_list
        self.notify()
        

        