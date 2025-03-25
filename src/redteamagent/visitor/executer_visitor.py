from .abstract_visitor import AbstractVisitor
from multimethod import multimethod
from ..execution_tree import ExecutionNode,FailedNode,PlanningNode


class ExecuterVisitor(AbstractVisitor):
    @multimethod
    def visit(self,node: ExecutionNode):
        print("exec node")
        return None
    
    @multimethod
    def visit(self,node: FailedNode):
        print("failed node")
        return None
    
    @multimethod
    def visit(self,node:PlanningNode):
        print("planning node")
        return None


