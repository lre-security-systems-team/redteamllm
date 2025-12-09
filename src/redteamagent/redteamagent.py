from .planner.planner_visitor import PlannerVisitor
from .printer.printer_visitor import PrinterVisitor
from .execution_tree import AbstractNode, ExecutionNode
from .observer.printer_observer import PrinterObserver
from .security.logger import (
    initialize_logger, get_logger, SecurityEvent, ComponentType, 
    RiskLevel, EventCategory
)
from datetime import datetime


class RedTeamAgent:
    def __init__(self, task: str):
        self.task: str = task
        self.root_task: list[AbstractNode] = [ExecutionNode(task)]
        self.root_task[0].set_lvl(0)
        self.planner = PlannerVisitor(self.root_task, None, 5)
        self.printer_observer = PrinterObserver(self.root_task, PrinterVisitor())
        AbstractNode.attach(self.printer_observer)
        
        # Initialize security logger
        self.logger = get_logger()
        self._log_agent_initialization()
    
    def _log_agent_initialization(self):
        """Log agent initialization event"""
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            component=ComponentType.REDTEAM_AGENT,
            event_type='AGENT_START',
            description=f'RedTeamAgent initialized with task: {self.task}',
            risk_level=RiskLevel.LOW
        )
        event.enrich_with_classification(EventCategory.AGENT_INITIALIZED)
        self.logger.log_event(event)

    
    def plan(self) -> AbstractNode:
        """_summary_
        Give first plan from a task
        Returns:
            AbstractNode: return root node
        """
        # Log planning start
        plan_event = SecurityEvent(
            timestamp=datetime.utcnow(),
            component=ComponentType.REDTEAM_AGENT,
            event_type='PLANNING_START',
            description=f'Planning initiated for task: {self.task}',
            risk_level=RiskLevel.LOW
        )
        plan_event.enrich_with_classification(EventCategory.PLAN_GENERATED)
        self.logger.log_event(plan_event)
        
        self.printer_observer.update()
        self.root_task[0].accept(self.planner)
        
        # Log planning complete
        complete_event = SecurityEvent(
            timestamp=datetime.utcnow(),
            component=ComponentType.REDTEAM_AGENT,
            event_type='PLANNING_COMPLETE',
            description='Planning phase completed',
            risk_level=RiskLevel.LOW
        )
        complete_event.enrich_with_classification(EventCategory.TASK_COMPLETED)
        self.logger.log_event(complete_event)
        
        return self.root_task[0]


