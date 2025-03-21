from abc import ABC, abstractmethod
from .visitor.abstract_visitor import AbstractVisitor
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
    def __init__(self):
        self.parent = None

    @abstractmethod
    def accept(self,visitor:AbstractVisitor):
        pass
