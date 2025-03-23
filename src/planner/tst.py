
from .llm_planner import LLMPlanner
from .planner_visitor import PlannerVisitor

a = PlannerVisitor("create a webserver to play snake",None)
node = a.give_first_plan()
print(type(node))
node.accept(a)

