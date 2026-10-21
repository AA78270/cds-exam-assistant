from functools import lru_cache
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from src.config import COLLECTION_NAME, VECTORSTORE_DIR


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTORSTORE_DIR),
    )


def search(query: str, subject: str = "", year: str = "", topic: str = "", k: int = 5):
    conditions = []
    if subject:
        conditions.append({"subject": subject.lower()})
    if year:
        conditions.append({"year": year})
    if topic:
        conditions.append({"topic": topic})

    if len(conditions) > 1:
        where = {"$and": conditions}
    elif conditions:
        where = conditions[0]
    else:
        where = None

    return get_vectorstore().similarity_search(query, k=k, filter=where)


def get_by_number(subject: str, year: str, number: int):
    where = {"$and": [
        {"subject": subject.lower()},
        {"year": year},
        {"question_number": number},
    ]}
    res = get_vectorstore().get(where=where, include=["documents", "metadatas"])
    return list(zip(res["documents"], res["metadatas"]))