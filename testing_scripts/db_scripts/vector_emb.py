from openai import OpenAI

with open("api_key") as f:
    api_key = f.read().strip()



client = OpenAI(api_key=api_key)


def create_embedding(txt_list:list[str]):
    response = client.embeddings.create(
        input=txt_list,
        model="text-embedding-3-small"
    )
    res = []
    emb_data = response.data
    for e in emb_data:
        res.append(e.embedding)
    return res
    
