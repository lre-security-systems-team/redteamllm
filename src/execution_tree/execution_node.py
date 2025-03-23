from .abstract_node import AbstractNode
from enum import Enum

class STATUS(Enum):
    PENDING = 0
    RUNNING = 1
    FAILED  = 2
    SUCCEEDED = 3

class ExecutionNode(AbstractNode):
    def __init__(self,task:str):
        super().__init__(task)
        # status of the task execution
        self.status:STATUS = STATUS.PENDING  
        # next node  ( next step )
        self.next_node : AbstractNode = None
        # full description of what happened
        # Will be the act message list
        self.execution_log : str = None
        # failure reason ||
        # WHY NOT FAILED NODE ??
        # Because a failed node is created only if its decomposed next. 
        self.failure_reason : str = None

        # what it needs from the previous node ( None if its the most left node)
        self.previous_task_resume: str = None 
        # current task resume
        self.task_resume : str = None




    def accept(self, visitor):
        return visitor.visit(self)