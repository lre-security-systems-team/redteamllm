from .abstract_node import AbstractNode

class FailedNode(AbstractNode):
    def  __init__(self, task:str):
        super().__init__(task)
        self.failure_reason: str = None
        self.execution_description : str = None

    def accept(self, visitor):
        return visitor.visit(self)
    
    def change_node_to_planning(self, node:AbstractNode):
        raise Exception("Can not change failed node to a planning node !")