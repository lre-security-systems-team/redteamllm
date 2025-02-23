from sqlalchemy import create_engine, String, ForeignKey, text, insert, column
from typing  import Optional
from pgvector.sqlalchemy.vector import VECTOR,Vector
from sqlalchemy.orm import Session, DeclarativeBase, mapped_column, Mapped, relationship




class Base(DeclarativeBase):
    pass



class Node(Base):
    __tablename__ = "node"

    id : Mapped[int] = mapped_column(primary_key=True)

    # parent (Null if root)
    parent_id : Mapped[int] = mapped_column(ForeignKey("node.id",ondelete="CASCADE"),nullable=True)
    parent : Mapped["Node"] = relationship("Node",back_populates="children",remote_side=[id],single_parent=True)

    # parent (empty list if leaf)
    children : Mapped[list["Node"]] = relationship("Node",back_populates="parent")

    # Order add order


    # task description
    task_description : Mapped[str] = mapped_column(nullable=False)
    #task execution summary
    # Node : A summary of what happened in every child
    # Leaf : A summary of the execution
    task_execution_summary : Mapped[str] = mapped_column(nullable=False)
    # Whole task execution the whole reasoning and action in the LLM
    task_execution : Mapped[str] = mapped_column(nullable=False)
    # Suceeded  : True
    # Failed    : False
    suceeded : Mapped[bool] = mapped_column(nullable=False)
    # Reason of failure
    failure_reason : Mapped[str]= mapped_column(nullable=True)

    # if the task fails once , it has this
    failed_node : Mapped["FailedNode"] = relationship(back_populates="node",cascade="all, delete-orphan")


# 2 method to decompose:
#   1 - Use an LLM to judge if a task needs decomposition or not. 
#   2 - Execute a task, and if it failed, we decompose.

class FailedNode(Base):
    __tablename__ = "failed_node"
    id : Mapped[int]  = mapped_column(primary_key=True)

    # main node id
    node_id : Mapped[int] = mapped_column(ForeignKey("node.id"))
    # main node
    node : Mapped["Node"] = relationship(back_populates="failed_node")

    task_execution_summary : Mapped[str] = mapped_column(nullable=False)
    # Whole task execution the whole reasoning and action in the LLM
    task_execution : Mapped[str] = mapped_column(nullable=False)
    # Suceeded  : True
    # Failed    : False
    suceeded : Mapped[bool] = mapped_column(nullable=False)
    # Reason of failure
    failure_reason : Mapped[str] = mapped_column(nullable=False)


class Embeddings(Base):
    __tablename__ = "embeddings"
    id : Mapped[int] = mapped_column(primary_key=True)
    nodeid : Mapped[int] = mapped_column(ForeignKey("node.id",ondelete="CASCADE"),unique=True)
    embedding :Mapped[Vector] = mapped_column(VECTOR(dim=1536))








    