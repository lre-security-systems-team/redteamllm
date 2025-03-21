from . import ExecutionNode
from .visitor import ExecuterVisitor



a = ExecutionNode()
vis = ExecuterVisitor()

a.accept(vis)