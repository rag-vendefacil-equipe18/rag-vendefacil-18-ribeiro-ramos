
from retrieve import buscar_hibrido


PERGUNTAS = [
    "Quais tickets de clientes de Minas Gerais estão relacionados ao módulo de estoque?",
    "Quais problemas do módulo de pagamento aparecem para clientes de São Paulo?",
    "Quais tickets críticos do módulo de pagamento existem para clientes do Rio de Janeiro?"
]


def mostrar_resultados(titulo, resultado):
    print("\n" + "=" * 100)
    print(titulo)
    print("=" * 100)

    print("\nPERGUNTA:")
    print(resultado["pergunta"])

    print("\nFILTROS:")
    print(resultado["filtros"])

    print("\nTOP RESULTADOS RRF:")

    if not resultado["rrf"]:
        print("Nenhum resultado encontrado.")
        return

    for posicao, (doc, score) in enumerate(
        resultado["rrf"],
        start=1
    ):
        print("\n" + "-" * 80)

        print(f"Resultado {posicao}")
        print(f"Score RRF: {score:.6f}")

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
            "Prioridade:",
            doc.metadata.get("priority")
        )

        print(
            "Status:",
            doc.metadata.get("status")
        )

        print(
            "Texto:",
            doc.page_content[:350]
        )


if __name__ == "__main__":

    for pergunta in PERGUNTAS:

        print("\n\n" + "#" * 110)
        print("COMPARATIVO")
        print("#" * 110)

        # ====================================================
        # BUSCA SEM FILTRO
        # ====================================================

        sem_filtro = buscar_hibrido(
            pergunta,
            usar_filtros=False,
            k=5,
            fetch_k=500,
        )

        # ====================================================
        # BUSCA COM FILTRO
        # ====================================================

        com_filtro = buscar_hibrido(
            pergunta,
            usar_filtros=True,
            k=5,
            fetch_k=500,
        )

        # ====================================================
        # EXIBIÇÃO
        # ====================================================

        mostrar_resultados(
            "BUSCA SEM FILTRO",
            sem_filtro
        )

        mostrar_resultados(
            "BUSCA COM FILTRO",
            com_filtro
        )
