
import torch

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
INDEX_PATH = "index/faiss_index"


def criar_modelo_embeddings():
    """
    Carrega o mesmo modelo de embeddings utilizado
    durante a construção do índice.
    """

    device = "cuda" if torch.cuda.is_available() else "cpu"

    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device},
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 32,
        },
    )


def carregar_indice():
    """
    Recarrega o índice FAISS já persistido em disco,
    sem gerar novamente os embeddings dos documentos.
    """

    embeddings = criar_modelo_embeddings()

    db = FAISS.load_local(
        INDEX_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )

    return db


if __name__ == "__main__":

    db = carregar_indice()

    print(
        "Índice FAISS carregado com sucesso, sem reindexação."
    )
