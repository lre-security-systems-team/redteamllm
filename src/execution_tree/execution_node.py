from .abstract_node import AbstractNode
class ExecutionNode(AbstractNode):
    def accept(self, visitor):
        return visitor.visit(self)