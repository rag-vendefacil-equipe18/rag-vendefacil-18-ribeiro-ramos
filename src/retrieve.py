from rank_bm25 import BM25Okapi
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from src.ingest import carregar_todos_documents
from src.query_analyzer import analisar_pergunta

print("1. Configurando Busca Densa (FAISS)...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
db_denso = FAISS.load_local("index/faiss_index", embeddings, allow_dangerous_deserialization=True)

print("2. Configurando Busca Esparsa (BM25)...")
documentos = carregar_todos_documents()
retriever_esparso = BM25Retriever.from_documents(documentos)
retriever_esparso.k = 5

print("3. Preparando o algoritmo de Fusão (RRF)...")
def reciprocal_rank_fusion(dense_results, sparse_results, k=60):
    fused_scores = {}
    
    for rank, doc in enumerate(dense_results):
        doc_str = doc.page_content
        if doc_str not in fused_scores:
            fused_scores[doc_str] = {"doc": doc, "score": 0.0}
        fused_scores[doc_str]["score"] += 1.0 / (k + (rank + 1))
        
    for rank, doc in enumerate(sparse_results):
        doc_str = doc.page_content
        if doc_str not in fused_scores:
            fused_scores[doc_str] = {"doc": doc, "score": 0.0}
        fused_scores[doc_str]["score"] += 1.0 / (k + (rank + 1))
        
    sorted_docs = sorted(fused_scores.values(), key=lambda x: x["score"], reverse=True)
    return [(item["doc"], item["score"]) for item in sorted_docs]

def buscar_hibrido(pergunta: str):
    # Extrai os filtros usando o Query Analyzer da Eduarda
    filtros_extraidos = analisar_pergunta(pergunta)
    
    # Busca Densa com filtros e fetch_k para segurança
    resultados_densos = db_denso.similarity_search(
        pergunta, 
        k=5, 
        filter=filtros_extraidos if filtros_extraidos else None,
        fetch_k=500
    )
    
    # Busca Esparsa
    resultados_esparsos = retriever_esparso.invoke(pergunta)
    
    # Fusão RRF
    return reciprocal_rank_fusion(resultados_densos, resultados_esparsos, k=60)
