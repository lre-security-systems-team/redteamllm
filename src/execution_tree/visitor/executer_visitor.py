from .abstract_visitor import AbstractVisitor
from multimethod import multimethod
from .. import ExecutionNode,FailedNode,PlanningNode


class ExecuterVisitor(AbstractVisitor):
    @multimethod
    def visit(node: ExecutionNode):
        print("exec node")
        return None
    
    @multimethod
    def visit(node: FailedNode):
        print("failed node")
        return None
    
    @multimethod
    def visit(node:PlanningNode):
        print("planning node")
        return None


