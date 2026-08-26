
from retrieve import (
    buscar_denso,
    buscar_bm25,
    reciprocal_rank_fusion,
)


# ============================================================
# PERGUNTAS DE TESTE
# ============================================================

TESTES = [
    {
        "nome": "Busca por código exato - vantagem do BM25",
        "pergunta": "O que aconteceu no ticket TCK-1057?",
        "esperado": "tickets_TCK-1057",
    },
    {
        "nome": "Busca semântica por paráfrase - vantagem do Dense",
        "pergunta": (
            "O pagamento foi aceito pelo equipamento, "
            "mas o sistema de frente de loja não concluiu a compra."
        ),
        "esperado": "tickets_TCK-1005",
    },
]


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def obter_chunk_id(doc):
    """
    Retorna o identificador do chunk.
    """
    return doc.metadata.get("chunk_id", "SEM_CHUNK_ID")


def encontrar_posicao(documentos, chunk_esperado):
    """
    Procura um chunk específico no ranking.

    Retorna:
        1, 2, 3... caso encontrado
        None caso não esteja no ranking
    """

    for posicao, doc in enumerate(documentos, start=1):

        if obter_chunk_id(doc) == chunk_esperado:
            return posicao

    return None


# ============================================================
# EXIBIÇÃO DOS RESULTADOS
# ============================================================

def mostrar_documentos(titulo, documentos):

    print("\n" + "=" * 90)
    print(titulo)
    print("=" * 90)

    if not documentos:
        print("\nNenhum resultado encontrado.")
        return

    for posicao, doc in enumerate(documentos, start=1):

        metadata = doc.metadata

        print(
            f"\n{posicao}. "
            f"{metadata.get('chunk_id')}"
        )

        print(
            "Tipo:",
            metadata.get("doc_type")
        )

        print(
            "Estado:",
            metadata.get("state")
        )

        print(
            "Módulo:",
            metadata.get("module")
        )

        print(
            "Prioridade:",
            metadata.get("priority")
        )

        print(
            "Status:",
            metadata.get("status")
        )

        print(
            "Fonte:",
            metadata.get("source_file")
        )

        print(
            "Texto:",
            doc.page_content[:300]
        )


# ============================================================
# EXIBIÇÃO DO RRF
# ============================================================

def mostrar_rrf(resultados):

    print("\n" + "=" * 90)
    print("RRF - RESULTADO DA FUSÃO")
    print("=" * 90)

    if not resultados:
        print("\nNenhum resultado encontrado.")
        return

    for posicao, (doc, score) in enumerate(
        resultados,
        start=1
    ):

        metadata = doc.metadata

        print(
            f"\n{posicao}. "
            f"{metadata.get('chunk_id')} "
            f"| score RRF = {score:.6f}"
        )

        print(
            "Tipo:",
            metadata.get("doc_type")
        )

        print(
            "Estado:",
            metadata.get("state")
        )

        print(
            "Módulo:",
            metadata.get("module")
        )

        print(
            "Prioridade:",
            metadata.get("priority")
        )

        print(
            "Status:",
            metadata.get("status")
        )

        print(
            "Fonte:",
            metadata.get("source_file")
        )

        print(
            "Texto:",
            doc.page_content[:300]
        )


# ============================================================
# COMPARAÇÃO AUTOMÁTICA
# ============================================================

def mostrar_comparacao(
    chunk_esperado,
    dense,
    bm25,
    rrf
):

    pos_dense = encontrar_posicao(
        dense,
        chunk_esperado
    )

    pos_bm25 = encontrar_posicao(
        bm25,
        chunk_esperado
    )

    documentos_rrf = [
        doc
        for doc, score in rrf
    ]

    pos_rrf = encontrar_posicao(
        documentos_rrf,
        chunk_esperado
    )

    print("\n" + "-" * 90)
    print("ANÁLISE DO DOCUMENTO ESPERADO")
    print("-" * 90)

    print(
        f"Documento esperado: {chunk_esperado}"
    )

    print(
        "Posição no Dense:",
        pos_dense if pos_dense else "não apareceu no TOP 5"
    )

    print(
        "Posição no BM25:",
        pos_bm25 if pos_bm25 else "não apareceu no TOP 5"
    )

    print(
        "Posição no RRF:",
        pos_rrf if pos_rrf else "não apareceu no TOP 5"
    )

    # --------------------------------------------------------
    # INTERPRETAÇÃO
    # --------------------------------------------------------

    print("\nINTERPRETAÇÃO:")

    if pos_dense and not pos_bm25:

        print(
            "Dense apresentou vantagem: "
            "encontrou o documento relevante enquanto "
            "o BM25 não o colocou no TOP 5."
        )

    elif pos_bm25 and not pos_dense:

        print(
            "BM25 apresentou vantagem: "
            "encontrou o documento relevante enquanto "
            "o Dense não o colocou no TOP 5."
        )

    elif pos_dense and pos_bm25:

        if pos_dense < pos_bm25:

            print(
                "Dense apresentou vantagem: "
                f"documento na posição {pos_dense}, "
                f"contra posição {pos_bm25} do BM25."
            )

        elif pos_bm25 < pos_dense:

            print(
                "BM25 apresentou vantagem: "
                f"documento na posição {pos_bm25}, "
                f"contra posição {pos_dense} do Dense."
            )

        else:

            print(
                "Dense e BM25 colocaram o documento "
                "na mesma posição."
            )

    else:

        print(
            "Nenhum dos recuperadores encontrou "
            "o documento esperado no TOP 5."
        )

    if pos_rrf:

        print(
            f"O ranking híbrido RRF colocou o documento "
            f"na posição {pos_rrf}."
        )


# ============================================================
# EXECUÇÃO DOS TESTES
# ============================================================

if __name__ == "__main__":

    for teste in TESTES:

        pergunta = teste["pergunta"]
        chunk_esperado = teste["esperado"]

        print(
            "\n\n" + "#" * 100
        )

        print(
            teste["nome"]
        )

        print(
            "#" * 100
        )

        print("\nPERGUNTA:")
        print(pergunta)

        print("\nDOCUMENTO ESPERADO:")
        print(chunk_esperado)

        # ----------------------------------------------------
        # BUSCA DENSE
        # ----------------------------------------------------

        dense = buscar_denso(
            pergunta=pergunta,
            filtros=None,
            k=5,
            fetch_k=500
        )

        # ----------------------------------------------------
        # BUSCA BM25
        # ----------------------------------------------------

        bm25 = buscar_bm25(
            pergunta=pergunta,
            filtros=None,
            k=5
        )

        # ----------------------------------------------------
        # FUSÃO RRF
        # ----------------------------------------------------

        rrf = reciprocal_rank_fusion(
            dense,
            bm25,
            k=60
        )[:5]

        # ----------------------------------------------------
        # MOSTRAR RESULTADOS
        # ----------------------------------------------------

        mostrar_documentos(
            "DENSE - EMBEDDINGS",
            dense
        )

        mostrar_documentos(
            "BM25 - BUSCA LEXICAL",
            bm25
        )

        mostrar_rrf(
            rrf
        )

        # ----------------------------------------------------
        # COMPARAÇÃO AUTOMÁTICA
        # ----------------------------------------------------

        mostrar_comparacao(
            chunk_esperado,
            dense,
            bm25,
            rrf
        )


    # ========================================================
    # FIM
    # ========================================================

    print(
        "\n\n" + "=" * 100
    )

    print(
        "FIM DO COMPARATIVO DENSE + BM25 + RRF"
    )

    print(
        "=" * 100
    )
