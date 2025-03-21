from abc import ABC,abstractmethod

class AbstractVisitor(ABC): 
    @abstractmethod
    def visit(node):
        pass