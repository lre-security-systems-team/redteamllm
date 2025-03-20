from sqlalchemy import create_engine, String, ForeignKey, text, insert
from typing  import Optional
from sqlalchemy.orm import Session, DeclarativeBase, mapped_column, Mapped, relationship

from db_manager import create_root_example , create_embedding_lists, create_save_embeddings, create_vector_extension, drop_all_table,create_all_table
from models import Node, Embeddings
from vector_emb import create_embedding

db_url = "postgresql://postgres:test@127.0.0.1:5432/postgres"
engine =create_engine(db_url,echo=True)



with Session(engine) as session:
    with session.begin():
        drop_all_table(engine,session)
        # create_vector_extension(session)
        create_all_table(engine,session)
    
        # root =create_root_example()
        # session.add(root)
        # root = session.query(Node).where(Node.parent_id == None).first()
        # create_save_embeddings(root,session)


        # emb_list =  create_embedding("deployment")
        # vect = emb_list[0]

    

        # stmt = text("SELECT nodeid FROM embeddings ORDER BY embedding <=> CAST(:vect AS vector(1536)) LIMIT 3")
        # res = session.execute(stmt,dict(vect=vect))

        # node_id_list = []
        # for e in res.all():
        #     node_id_list.append(e[0])

        # res = session.query(Node).where(Node.id.in_(node_id_list)).all()
        # for e in res:
        #     print(e.task_description)






    