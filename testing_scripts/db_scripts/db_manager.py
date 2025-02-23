from sqlalchemy.orm import Session
from sqlalchemy import text
from testing_scripts.db_scripts.models import Node, FailedNode, Base
from testing_scripts.db_scripts.vector_emb import create_embedding

def drop_all_table(engine,session:Session):
    # stmt= "DROP TABLE embeddings"
    # session.execute(text(stmt))
    Base.metadata.drop_all(engine)

def create_all_table(engine,session:Session):
    Base.metadata.create_all(engine)
    


def insert_embedding_list(val_list,session:Session):
    stmt = text("INSERT INTO embeddings (nodeid, embedding) VALUES(:nodeid, :embedding)")
    val_list = val_list
    session.execute(stmt,val_list)


def create_node(task_description:str,task_execution_summary:str,task_execution:str,suceeded:bool) -> Node:
    node = Node(task_description=task_description,task_execution_summary=task_execution_summary,task_execution=task_execution,suceeded=suceeded)
    return node



def create_root_example() -> Node:

    root = create_node(task_description="Create snake game",task_execution="blabla",task_execution_summary="blabla",suceeded=True)

    child1 = create_node(task_description="Set Up the Environment",task_execution="blabla",task_execution_summary="blabla",suceeded=True)
    child2 = create_node(task_description="Develop the Snake Game Logic",task_execution="blabla",task_execution_summary="blabla",suceeded=True)
    child3 = create_node(task_description="Test and Debug the game",task_execution="blabla",task_execution_summary="blabla",suceeded=True)
    child4 = create_node(task_description="Make it Hostable Locally",task_execution="blabla",task_execution_summary="blabla",suceeded=True)
    child5 = create_node(task_description="Deploy and Run on Linux",task_execution="blabla",task_execution_summary="blabla",suceeded=True)

    root.children.extend([child1,child2,child3,child4,child5])

    child2_1 = create_node(task_description="Initialize the Game Window",task_execution="blabla",task_execution_summary="blabla",suceeded=True)
    child2_2 = create_node(task_description="Implement Snake Movement",task_execution="blabla",task_execution_summary="blabla",suceeded=True)
    child2_3 = create_node(task_description="Implement Food and Scoring",task_execution="blabla",task_execution_summary="blabla",suceeded=True)
    child2_4 = create_node(task_description="Handle Collisions",task_execution="blabla",task_execution_summary="blabla",suceeded=True)
    child2_5 = create_node(task_description="Render and Update Game",task_execution="blabla",task_execution_summary="blabla",suceeded=True)

    child2.children.extend([child2_1,child2_2,child2_3,child2_4,child2_5])



    child4_1 = create_node(task_description="Convert Script into an Executable",task_execution="blabla",task_execution_summary="blabla",suceeded=True)
    child4_2 = create_node(task_description="Ensure Dependencies are Met",task_execution="blabla",task_execution_summary="blabla",suceeded=True)

    child4.children.extend([child4_1,child4_2])

    return root



def create_vector_extension(session:Session):
    session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    session.execute(text("CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE"))



def create_embedding_lists(root:Node,id_list:list[int],desc_list:list[str]) -> dict:
    """
    Returns 2 list:
        1 list of id
        1 list of str, to embedd later on
    """
    id_list.append(root.id)
    desc_list.append(root.task_description)
    for e in root.children:
        create_embedding_lists(e,id_list,desc_list)


def create_save_embeddings(root,session):
    id_list, description_list = [],[]
    # create pair nodeid - task_description
    create_embedding_lists(root,id_list,description_list)

    # create emb_list
    emb_list = create_embedding(description_list)

    # list of values to insert in the emb table
    values = []
    for e in range(len(id_list)):
        values.append(dict(nodeid=id_list[e],embedding=emb_list[e]))

    # save them
    insert_embedding_list(values,session)
    

    


def search_similar_vect(session:Session,vector)-> list[int]:
    stmt = text("SELECT nodeid FROM embeddings ORDER BY embedding <=> CAST(:vect AS vector(1536)) LIMIT 3")
    res = session.execute(stmt,vector).all()
    return res


