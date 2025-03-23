from .abstract_node import AbstractNode

class FailedNode(AbstractNode):
    def  __init__(self, task:str):
        super().__init__(task)
        self.failure_reason: str = None
        self.execution_description : str = None

    def accept(self, visitor):
        return visitor.visit(self)