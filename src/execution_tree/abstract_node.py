from abc import ABC, abstractmethod
from ..visitor.abstract_visitor import AbstractVisitor
class AbstractNode(ABC):
    """_summary_
    This class will represent the nodes in our execution graph
    3 types of nodes:
        - ExecNode:
            This node's role is to be executed
        - PlanningNode:
            This nodes' role is to plan multiple ExecNode
        - Failed Node:
            This nodes' role is to represent a Failed Node
    """
    def __init__(self,task:str):
        """_summary_
        ABSTRACT
        class representing a node
        Args:
            task (str): task given to the node
            lvl (int): depth of the node (0 being root)
            dependance (str) : What this node needs to suceed
        """        
        # task description
        self.task:str = task
        # parent (None if its root)
        self.parent: AbstractNode = None
        # node lvl (depth)
        self.lvl: int = 0
    

    def set_lvl(self,lvl:int) -> None:
        """_summary_
        set node lvl
        Args:
            lvl (int): _description_
        """        
        self.lvl = lvl

    @abstractmethod
    def accept(self,visitor:AbstractVisitor):
        pass
