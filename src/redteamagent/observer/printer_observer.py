from .observer import Observer
from ..execution_tree.abstract_node import AbstractNode
from ..printer.printer_visitor import PrinterVisitor
class PrinterObserver(Observer):
    def __init__(self,root_node:list[AbstractNode],printer_visiter:PrinterVisitor):
        # the root node to update
        self.root_node : list[AbstractNode] = root_node
        self.printer_visitor: PrinterVisitor = printer_visiter
    

    def update(self):
        # on update we print the tree again
        self.printer_visitor.clear_graph()
        self.root_node[0].accept(self.printer_visitor)
        self.printer_visitor.display()