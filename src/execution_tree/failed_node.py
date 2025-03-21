from .abstract_node import AbstractNode

class FailedNode(AbstractNode):
    def accept(self, visitor):
        return visitor.visit_(self)