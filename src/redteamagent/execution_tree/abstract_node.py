from abc import ABC, abstractmethod
from ..visitor.abstract_visitor import AbstractVisitor
from ..observer.observer import Observer
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
    # Observer's list
    _observers : list[Observer] = []
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
        self.children: list[AbstractNode] = []
        self.next_node : AbstractNode = None
    @staticmethod
    def attach(observer:Observer):
        """_summary_
        add an observer to the list of observers
        Args:
            observer (Observer): the observer to add
        """        
        if observer not in AbstractNode._observers:
            AbstractNode._observers.append(observer)

    @staticmethod
    def detach(self,observer:Observer):
        """_summary_
        remove an observer from the list of observers
        Args:
            observer (Observer): the observer to remove
        """        
        if observer in AbstractNode._observers:
            AbstractNode._observers.remove(observer)

    

    def set_lvl(self,lvl:int) -> None:
        """_summary_
        set node lvl
        Args:
            lvl (int): _description_
        """        
        self.lvl = lvl
    
    
    def notify(self):
        for obsever in AbstractNode._observers:
            obsever.update()

    @abstractmethod
    def accept(self,visitor:AbstractVisitor):
        pass
    
    @abstractmethod
    def change_node_to_planning(self,node:"AbstractNode"):
        pass
    
