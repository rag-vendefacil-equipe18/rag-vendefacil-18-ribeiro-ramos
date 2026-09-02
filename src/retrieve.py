
import re

from langchain_community.retrievers import BM25Retriever

from ingest import carregar_todos_documentos
from load_index import carregar_indice
try:
    from .query_analyzer import analisar_e_validar
except ImportError:
    from query_analyzer import analisar_e_validar


# ============================================================
# TOKENIZAÇÃO DO BM25
# ============================================================

def tokenizar_bm25(texto: str):
    """
    Tokenização lexical para o BM25.

    - converte para minúsculas;
    - remove pontuação externa;
    - preserva códigos com hífen.

    Exemplos preservados:
    TCK-1057
    PAY-200
    PDV-500
    """

    if texto is None:
        return []

    return re.findall(
        r"[a-zA-ZÀ-ÿ0-9]+(?:-[a-zA-ZÀ-ÿ0-9]+)*",
        str(texto).lower()
    )


# ============================================================
# CARREGAMENTO INICIAL
# ============================================================

print("1. Carregando documentos...")

documentos = carregar_todos_documentos()

print(
    f"Total de documentos: {len(documentos)}"
)


print("2. Carregando índice FAISS...")

db_denso = carregar_indice()


print("3. Configurando BM25...")

retriever_esparso = BM25Retriever.from_documents(
    documentos,
    preprocess_func=tokenizar_bm25
)

retriever_esparso.k = 5


# ============================================================
# FILTRO DE METADADOS
# ============================================================

def documento_atende_filtros(
    doc,
    filtros: dict
) -> bool:
    """
    Verifica se um documento satisfaz todos
    os filtros de metadados.
    """

    if not filtros:
        return True

    for campo, valor_esperado in filtros.items():

        valor_documento = doc.metadata.get(
            campo
        )

        if valor_documento is None:
            return False

        if (
            str(valor_documento).strip().lower()
            != str(valor_esperado).strip().lower()
        ):
            return False

    return True


def filtrar_documentos(
    documentos,
    filtros: dict
):
    """
    Pré-filtra os documentos antes da busca BM25.

    Isso evita que documentos incompatíveis
    com os filtros retornem no ranking lexical.
    """

    if not filtros:
        return documentos

    return [
        doc
        for doc in documentos
        if documento_atende_filtros(
            doc,
            filtros
        )
    ]


# ============================================================
# RECIPROCAL RANK FUSION
# ============================================================

def reciprocal_rank_fusion(
    dense_results,
    sparse_results,
    k=60
):
    """
    Combina os rankings Dense e BM25 usando
    Reciprocal Rank Fusion.

    score_RRF =
        soma de 1 / (k + posição)

    O chunk_id é utilizado como identificador
    principal do documento.
    """

    fused_scores = {}

    # --------------------------------------------------------
    # DENSE
    # --------------------------------------------------------

    for rank, doc in enumerate(
        dense_results,
        start=1
    ):

        doc_id = doc.metadata.get(
            "chunk_id",
            doc.page_content
        )

        if doc_id not in fused_scores:

            fused_scores[doc_id] = {
                "doc": doc,
                "score": 0.0
            }

        fused_scores[doc_id]["score"] += (
            1.0 / (k + rank)
        )

    # --------------------------------------------------------
    # BM25
    # --------------------------------------------------------

    for rank, doc in enumerate(
        sparse_results,
        start=1
    ):

        doc_id = doc.metadata.get(
            "chunk_id",
            doc.page_content
        )

        if doc_id not in fused_scores:

            fused_scores[doc_id] = {
                "doc": doc,
                "score": 0.0
            }

        fused_scores[doc_id]["score"] += (
            1.0 / (k + rank)
        )

    # --------------------------------------------------------
    # ORDENAÇÃO
    # --------------------------------------------------------

    ordenados = sorted(
        fused_scores.values(),
        key=lambda item: item["score"],
        reverse=True
    )

    return [
        (
            item["doc"],
            item["score"]
        )
        for item in ordenados
    ]


# ============================================================
# BUSCA DENSA
# ============================================================

def buscar_denso(
    pergunta: str,
    filtros: dict = None,
    k: int = 5,
    fetch_k: int = 500
):
    """
    Busca semântica com embeddings + FAISS.

    Quando existem filtros, usa fetch_k maior
    porque o FAISS recupera candidatos primeiro
    e o filtro é aplicado depois.
    """

    resultados = db_denso.similarity_search(
        pergunta,
        k=k,
        fetch_k=fetch_k,
        filter=(
            filtros
            if filtros
            else None
        )
    )

    return resultados


# ============================================================
# BUSCA BM25
# ============================================================

def buscar_bm25(
    pergunta: str,
    filtros: dict = None,
    k: int = 5
):
    """
    Busca lexical com BM25.

    Para consultas filtradas, os documentos
    são pré-filtrados antes da criação
    do retriever.
    """

    documentos_filtrados = filtrar_documentos(
        documentos,
        filtros or {}
    )

    if not documentos_filtrados:
        return []

    retriever = BM25Retriever.from_documents(
        documentos_filtrados,
        preprocess_func=tokenizar_bm25
    )

    retriever.k = min(
        k,
        len(documentos_filtrados)
    )

    return retriever.invoke(
        pergunta
    )


# ============================================================
# BUSCA HÍBRIDA
# ============================================================

def buscar_hibrido(
    pergunta: str,
    usar_filtros: bool = True,
    k: int = 5,
    fetch_k: int = 500
):
    """
    Pipeline completo de recuperação:

    pergunta
        ↓
    Query Analyzer
        ↓
    filtros validados
        ↓
    Dense + BM25
        ↓
    RRF
        ↓
    ranking final
    """

    # --------------------------------------------------------
    # FILTROS
    # --------------------------------------------------------

    if usar_filtros:

        filtros = analisar_e_validar(
            pergunta,
            documentos
        )

    else:

        filtros = {}

    # --------------------------------------------------------
    # DENSE
    # --------------------------------------------------------

    resultados_densos = buscar_denso(
        pergunta=pergunta,
        filtros=filtros,
        k=k,
        fetch_k=fetch_k
    )

    # --------------------------------------------------------
    # BM25
    # --------------------------------------------------------

    resultados_esparsos = buscar_bm25(
        pergunta=pergunta,
        filtros=filtros,
        k=k
    )

    # --------------------------------------------------------
    # RRF
    # --------------------------------------------------------

    ranking_final = reciprocal_rank_fusion(
        resultados_densos,
        resultados_esparsos,
        k=60
    )

    return {
        "pergunta": pergunta,
        "filtros": filtros,
        "dense": resultados_densos,
        "bm25": resultados_esparsos,
        "rrf": ranking_final[:k],
    }


# ============================================================
# EXIBIÇÃO AUXILIAR
# ============================================================

def mostrar_resultados(
    titulo,
    docs
):
    print("\n" + "=" * 90)

    print(titulo)

    print("=" * 90)

    if not docs:

        print(
            "Nenhum resultado encontrado."
        )

        return

    for posicao, doc in enumerate(
        docs,
        start=1
    ):

        print("\n" + "-" * 70)

        print(
            f"Resultado {posicao}"
        )

        print(
            "Chunk:",
            doc.metadata.get("chunk_id")
        )

        print(
            "Fonte:",
            doc.metadata.get("source_file")
        )

        print(
            "Tipo:",
            doc.metadata.get("doc_type")
        )

        print(
            "Estado:",
            doc.metadata.get("state")
        )

        print(
            "Módulo:",
            doc.metadata.get("module")
        )

        print(
            "Texto:",
            doc.page_content[:300]
        )


# ============================================================
# TESTE LOCAL
# ============================================================

if __name__ == "__main__":

    pergunta = (
        "Quais tickets de clientes de Minas Gerais "
        "estão relacionados ao módulo de estoque?"
    )

    resultado = buscar_hibrido(
        pergunta,
        usar_filtros=True,
        k=5,
        fetch_k=500
    )

    print("\n" + "#" * 90)

    print("PERGUNTA")

    print("#" * 90)

    print(
        resultado["pergunta"]
    )

    print("\nFILTROS:")

    print(
        resultado["filtros"]
    )

    # --------------------------------------------------------
    # DENSE
    # --------------------------------------------------------

    mostrar_resultados(
        "DENSE",
        resultado["dense"]
    )

    # --------------------------------------------------------
    # BM25
    # --------------------------------------------------------

    mostrar_resultados(
        "BM25",
        resultado["bm25"]
    )

    # --------------------------------------------------------
    # RRF
    # --------------------------------------------------------

    print("\n" + "=" * 90)

    print("RRF")

    print("=" * 90)

    if not resultado["rrf"]:

        print(
            "Nenhum resultado encontrado."
        )

    else:

        for posicao, (
            doc,
            score
        ) in enumerate(
            resultado["rrf"],
            start=1
        ):

            print("\n" + "-" * 70)

            print(
                f"Resultado {posicao}"
            )

            print(
                f"Score RRF: {score:.6f}"
            )

            print(
                "Chunk:",
                doc.metadata.get(
                    "chunk_id"
                )
            )

            print(
                "Fonte:",
                doc.metadata.get(
                    "source_file"
                )
            )

            print(
                "Tipo:",
                doc.metadata.get(
                    "doc_type"
                )
            )

            print(
                "Estado:",
                doc.metadata.get(
                    "state"
                )
            )

            print(
                "Módulo:",
                doc.metadata.get(
                    "module"
                )
            )

            print(
                "Texto:",
                doc.page_content[:300]
            )
