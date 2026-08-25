
from collections import Counter

from ingest import carregar_todos_documentos
from load_index import carregar_indice


PERGUNTAS = [
    "Quais problemas de sincronização de estoque aparecem nos tickets?",
    "O que a política de reembolso informa?",
    "Quais erros aparecem relacionados ao módulo de pagamento?"
]


def mostrar_distribuicao(documentos):

    distribuicao = Counter(
        doc.metadata["doc_type"]
        for doc in documentos
    )

    print("\nDistribuição por doc_type:")

    for tipo, quantidade in sorted(
        distribuicao.items()
    ):
        print(f"{tipo}: {quantidade}")


def executar_buscas(db):

    for pergunta in PERGUNTAS:

        print("\n" + "=" * 90)
        print(f"PERGUNTA: {pergunta}")

        resultados = db.similarity_search_with_score(
            pergunta,
            k=5
        )

        for posicao, (doc, score) in enumerate(
            resultados,
            start=1
        ):

            print(f"\nResultado {posicao}")
            print(f"Score: {score:.4f}")

            print(
                "Fonte:",
                doc.metadata.get("source_file")
            )

            print(
                "Tipo:",
                doc.metadata.get("doc_type")
            )

            print(
                "Chunk:",
                doc.metadata.get("chunk_id")
            )

            print(
                "Texto:",
                doc.page_content[:400]
            )


if __name__ == "__main__":

    documentos = carregar_todos_documentos()

    print(
        f"Total de chunks: {len(documentos)}"
    )

    mostrar_distribuicao(documentos)

    print("\nCarregando índice FAISS salvo...")

    db = carregar_indice()

    executar_buscas(db)
