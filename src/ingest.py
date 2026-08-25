
from ingest_structured import carregar_documentos_estruturados
from ingest_unstructured import carregar_documentos_nao_estruturados


def carregar_todos_documentos():
    """
    Junta os documentos estruturados, semiestruturados
    e não estruturados em uma única lista.
    """

    documentos_estruturados = carregar_documentos_estruturados()
    documentos_nao_estruturados = carregar_documentos_nao_estruturados()

    documentos = (
        documentos_estruturados
        + documentos_nao_estruturados
    )

    return documentos


if __name__ == "__main__":
    documentos = carregar_todos_documentos()

    print(f"Total de chunks: {len(documentos)}")

    for doc in documentos[:5]:
        print("\n" + "=" * 70)
        print("TEXTO:")
        print(doc.page_content[:300])

        print("\nMETADADOS:")
        print(doc.metadata)
