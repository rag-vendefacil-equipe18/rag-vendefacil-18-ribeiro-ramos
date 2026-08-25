
from pathlib import Path
import torch

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from ingest import carregar_todos_documentos


EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
INDEX_PATH = "index/faiss_index"


def criar_modelo_embeddings():
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Dispositivo utilizado: {device}")

    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device},
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 32
        },
    )


def construir_indice():
    print("Carregando documentos...")

    documentos = carregar_todos_documentos()

    print(f"Total de chunks recebidos: {len(documentos)}")

    if not documentos:
        raise ValueError("Nenhum documento foi carregado.")

    print("Carregando modelo de embeddings...")

    embeddings = criar_modelo_embeddings()

    print("Gerando embeddings e construindo índice FAISS...")

    db = FAISS.from_documents(
        documents=documentos,
        embedding=embeddings,
    )

    Path("index").mkdir(
        parents=True,
        exist_ok=True
    )

    print("Salvando índice em disco...")

    db.save_local(INDEX_PATH)

    print(f"Índice FAISS salvo em: {INDEX_PATH}")

    return db


if __name__ == "__main__":
    construir_indice()
