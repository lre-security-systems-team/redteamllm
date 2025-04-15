from .planner.planner_visitor import PlannerVisitor
from .printer.printer_visitor import PrinterVisitor
from .execution_tree import AbstractNode, ExecutionNode
from .observer.printer_observer import PrinterObserver





class RedTeamAgent:
    def __init__(self,task:str):
        self.task:str = task
        self.root_task: list[AbstractNode] = [ExecutionNode(task)]
        self.root_task[0].set_lvl(0)
        self.planner = PlannerVisitor(self.root_task,None,5)
        self.printer_observer = PrinterObserver(self.root_task,PrinterVisitor())
        AbstractNode.attach(self.printer_observer)

    
    def plan(self) -> AbstractNode:
        """_summary_
        Give first plan from a task
        Returns:
            AbstractNode: return root node
        """        
        self.printer_observer.update()
        self.root_task[0].accept(self.planner)
        return self.root_task[0]


