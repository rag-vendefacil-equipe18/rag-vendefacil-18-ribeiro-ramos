
from retrieve import buscar_denso, buscar_bm25


TESTES = [
    {
        "pergunta": (
            "Como o sistema avisa automaticamente o caixa "
            "quando um pagamento instantâneo é confirmado?"
        ),
        "esperado": "pix_dinamico_webhooks_md_0000",
    },
    {
        "pergunta": (
            "O que acontece quando a confirmação de uma "
            "transferência instantânea deixa de chegar ao sistema?"
        ),
        "esperado": "2026-03-incident_prevention_game_day_md_0001",
    },
    {
        "pergunta": (
            "Como funciona a devolução de equipamentos de pagamento "
            "quando o contrato com a empresa termina?"
        ),
        "esperado": "reembolso_md_0002",
    },
]


def posicao(resultados, esperado):

    for i, doc in enumerate(resultados, start=1):

        if doc.metadata.get("chunk_id") == esperado:
            return i

    return None


for teste in TESTES:

    pergunta = teste["pergunta"]
    esperado = teste["esperado"]

    dense = buscar_denso(
        pergunta,
        filtros=None,
        k=5,
        fetch_k=500
    )

    bm25 = buscar_bm25(
        pergunta,
        filtros=None,
        k=5
    )

    pos_dense = posicao(dense, esperado)
    pos_bm25 = posicao(bm25, esperado)

    print("\n" + "=" * 90)

    print("PERGUNTA:")
    print(pergunta)

    print("\nDOCUMENTO ESPERADO:")
    print(esperado)

    print("\nDense:", pos_dense or "fora do TOP 5")
    print("BM25:", pos_bm25 or "fora do TOP 5")

    if pos_dense and not pos_bm25:

        print("✅ CASO BOM: Dense encontrou e BM25 não.")

    elif pos_dense and pos_bm25 and pos_dense < pos_bm25:

        print("✅ CASO BOM: Dense ranqueou melhor que BM25.")

    else:

        print("❌ Ainda não demonstra vantagem do Dense.")
