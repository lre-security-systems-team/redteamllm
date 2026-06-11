from .abstract_node import AbstractNode

class PlanningNode(AbstractNode):

    def __init__(self, task:str):
        super().__init__(task)
        # list of the nodes that failed
        self.failed_nodes : list[int] = []
        # what it needs from the previous node ( None if its the most left node)
        self.previous_task_resume: str = None 
        # current task resume
        self.task_resume : str = None

    def accept(self, visitor):
        return visitor.visit(self)
    

    def change_node_to_planning(self, node:AbstractNode):
        raise Exception("Can not change planning node to planning node !")