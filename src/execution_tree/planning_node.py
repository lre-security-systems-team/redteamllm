from .abstract_node import AbstractNode

class PlanningNode(AbstractNode):
    def accept(self, visitor):
        return visitor.visit(self)