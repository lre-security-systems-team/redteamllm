from ..visitor import AbstractVisitor
from multimethod import multimethod
from ..execution_tree import ExecutionNode,PlanningNode,FailedNode
from graphviz import Digraph
class PrinterVisitor(AbstractVisitor):

    def __init__(self):
        self.dot = Digraph('wide')



    def clear_graph(self):
        self.dot.clear()
    
    def display(self):
        a = self.dot.unflatten(stagger=1)
        a.view()

    @multimethod
    def visit(self, node:ExecutionNode):
        self.dot.node(node.task)
        if node.parent != None:
            self.dot.edge(node.parent.task,node.task)
     

    @multimethod
    def visit(self, node:PlanningNode):
        self.dot.node(node.task)
        if node.parent != None:
            self.dot.edge(node.parent.task,node.task)
        for e in node.children:
            e.accept(self)
    
    @multimethod
    def visit(self, node:FailedNode):
        raise Exception("Printer visitor shouldn't have encountered failed node")