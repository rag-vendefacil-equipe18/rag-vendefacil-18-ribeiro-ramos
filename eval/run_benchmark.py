import json
import sys
from pathlib import Path
from collections import defaultdict

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


BENCHMARK_PATH = ROOT_DIR / "benchmark" / "questions_and_ground_truth.json"
RESULTS_PATH = ROOT_DIR / "eval" / "results.json"


def calcular_context_relevance(chunks_recuperados, chunks_esperados):
    """
    Context Relevance:
    compara os chunk_ids recuperados com os chunk_ids esperados.

    Fórmula:
        chunks esperados encontrados / total de chunks esperados

    Retorna None quando a questão não possui chunks esperados,
    como pode ocorrer em recusas LGPD ou fora de escopo.
    """

    recuperados = set(str(x) for x in chunks_recuperados)
    esperados = set(str(x) for x in chunks_esperados)

    if not esperados:
        return None

    encontrados = recuperados.intersection(esperados)

    return round(
        len(encontrados) / len(esperados),
        4
    )


def carregar_benchmark(caminho=BENCHMARK_PATH):
    if not caminho.exists():
        raise FileNotFoundError(
            f"Benchmark não encontrado em: {caminho}"
        )

    with caminho.open("r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    if isinstance(dados, list):
        questoes = dados

    elif isinstance(dados, dict):
        questoes = (
            dados.get("questions")
            or dados.get("perguntas")
            or dados.get("benchmark")
        )

    else:
        questoes = None

    if not isinstance(questoes, list):
        raise ValueError(
            "Formato do benchmark não reconhecido."
        )

    if len(questoes) != 20:
        print(
            f"⚠️ Foram encontradas {len(questoes)} questões. "
            "O benchmark oficial esperado possui 20."
        )

    return questoes


def extrair_pergunta(item):
    return (
        item.get("question")
        or item.get("pergunta")
        or item.get("query")
    )


def extrair_id(item, indice):
    return str(
        item.get("id")
        or item.get("question_id")
        or f"Q{indice:02d}"
    )


def extrair_tipo(item):
    return (
        item.get("type")
        or item.get("tipo")
        or item.get("category")
        or item.get("categoria")
        or "nao_informado"
    )


def normalizar_chunk_ids(valor):
    if valor is None:
        return []

    if isinstance(valor, str):
        return [valor]

    if isinstance(valor, list):
        resultado = []

        for item in valor:
            if isinstance(item, str):
                resultado.append(item)

            elif isinstance(item, dict):
                chunk_id = (
                    item.get("chunk_id")
                    or item.get("id")
                )

                if chunk_id:
                    resultado.append(str(chunk_id))

        return resultado

    return []


def extrair_chunks_esperados(item):
    candidatos = [
        item.get("expected_chunk_ids"),
        item.get("chunk_ids"),
        item.get("relevant_chunk_ids"),
        item.get("expected_chunks"),
    ]

    ground_truth = item.get("ground_truth")

    if isinstance(ground_truth, dict):
        candidatos.extend([
            ground_truth.get("expected_chunk_ids"),
            ground_truth.get("chunk_ids"),
            ground_truth.get("relevant_chunk_ids"),
            ground_truth.get("expected_chunks"),
        ])

    for candidato in candidatos:
        chunks = normalizar_chunk_ids(candidato)

        if chunks:
            return chunks

    return []


def extrair_chunks_recuperados(resultado_busca):
    chunks = []

    for item in resultado_busca.get("rrf", []):
        if isinstance(item, (tuple, list)):
            doc = item[0]
        else:
            doc = item

        metadata = getattr(doc, "metadata", {}) or {}

        chunk_id = metadata.get("chunk_id")

        if chunk_id:
            chunks.append(str(chunk_id))

    return chunks


def extrair_contexto(resultado_busca):
    trechos = []

    for posicao, item in enumerate(
        resultado_busca.get("rrf", []),
        start=1
    ):
        if isinstance(item, (tuple, list)):
            doc = item[0]
        else:
            doc = item

        metadata = getattr(doc, "metadata", {}) or {}
        conteudo = getattr(doc, "page_content", "")

        trechos.append(
            f"[Trecho {posicao}]\n"
            f"chunk_id: {metadata.get('chunk_id')}\n"
            f"source_file: {metadata.get('source_file')}\n"
            f"{conteudo}"
        )

    return "\n\n".join(trechos)


def serializar_rag_response(resposta):
    if hasattr(resposta, "model_dump"):
        return resposta.model_dump()

    if hasattr(resposta, "dict"):
        return resposta.dict()

    raise TypeError(
        "Resposta do RAG não é um modelo Pydantic reconhecido."
    )


def executar_questao(item, indice, usar_judge=True):
    from retrieve import buscar_hibrido
    from generate import gerar_resposta

    pergunta = extrair_pergunta(item)

    if not pergunta:
        raise ValueError(
            f"Questão {indice} sem texto de pergunta."
        )

    questao_id = extrair_id(item, indice)
    tipo = extrair_tipo(item)

    chunks_esperados = extrair_chunks_esperados(item)

    resultado_busca = buscar_hibrido(
        pergunta,
        usar_filtros=True,
        k=5,
        fetch_k=500
    )

    chunks_recuperados = extrair_chunks_recuperados(
        resultado_busca
    )

    context_relevance = calcular_context_relevance(
        chunks_recuperados,
        chunks_esperados
    )

    contexto = extrair_contexto(resultado_busca)

    resposta = gerar_resposta(
        pergunta,
        usar_filtros=True,
        k=5,
        fetch_k=500
    )

    resposta_dict = serializar_rag_response(resposta)

    answer_relevance = None
    groundedness = None

    if usar_judge:
        from eval.judge import (
            evaluate_answer_relevance,
            evaluate_groundedness
        )

        answer_relevance = evaluate_answer_relevance(
            pergunta,
            resposta_dict.get("answer", "")
        )

        groundedness = evaluate_groundedness(
            contexto,
            resposta_dict.get("answer", "")
        )

    return {
        "id": questao_id,
        "type": tipo,
        "question": pergunta,

        "ground_truth": {
            "expected_chunk_ids": chunks_esperados
        },

        "retrieval": {
            "filters": resultado_busca.get("filtros", {}),
            "retrieved_chunk_ids": chunks_recuperados
        },

        "response": resposta_dict,

        "metrics": {
            "context_relevance": context_relevance,
            "answer_relevance": answer_relevance,
            "groundedness": groundedness
        }
    }


def media(valores):
    valores = [
        valor
        for valor in valores
        if isinstance(valor, (int, float))
    ]

    if not valores:
        return None

    return round(
        sum(valores) / len(valores),
        4
    )


def gerar_resumo(resultados):
    context_global = []
    answer_global = []
    grounded_global = []

    por_tipo = defaultdict(
        lambda: {
            "quantidade": 0,
            "context_relevance": [],
            "answer_relevance": [],
            "groundedness": []
        }
    )

    for resultado in resultados:
        tipo = resultado["type"]

        por_tipo[tipo]["quantidade"] += 1

        metricas = resultado["metrics"]

        contexto = metricas.get("context_relevance")

        if isinstance(contexto, (int, float)):
            context_global.append(contexto)
            por_tipo[tipo]["context_relevance"].append(contexto)

        answer = metricas.get("answer_relevance")

        if isinstance(answer, dict):
            score = answer.get("score")

            if isinstance(score, (int, float)):
                answer_global.append(score)
                por_tipo[tipo]["answer_relevance"].append(score)

        grounded = metricas.get("groundedness")

        if isinstance(grounded, dict):
            score = grounded.get("score")

            if isinstance(score, (int, float)):
                grounded_global.append(score)
                por_tipo[tipo]["groundedness"].append(score)

    resumo_por_tipo = {}

    for tipo, dados in por_tipo.items():
        resumo_por_tipo[tipo] = {
            "quantidade": dados["quantidade"],
            "context_relevance": media(
                dados["context_relevance"]
            ),
            "answer_relevance": media(
                dados["answer_relevance"]
            ),
            "groundedness": media(
                dados["groundedness"]
            )
        }

    return {
        "total_questions": len(resultados),

        "rag_triad": {
            "context_relevance": media(context_global),
            "answer_relevance": media(answer_global),
            "groundedness": media(grounded_global)
        },

        "by_type": resumo_por_tipo
    }


def salvar_resultados(resultados, resumo):
    payload = {
        "summary": resumo,
        "results": resultados
    }

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with RESULTS_PATH.open(
        "w",
        encoding="utf-8"
    ) as arquivo:
        json.dump(
            payload,
            arquivo,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"\n✅ Resultados salvos em: {RESULTS_PATH}"
    )


def executar_benchmark(
    usar_judge=True,
    limite=None
):
    questoes = carregar_benchmark()

    if limite is not None:
        questoes = questoes[:limite]

    resultados = []

    total = len(questoes)

    print(
        f"\nExecutando benchmark com {total} questões."
    )

    for indice, item in enumerate(
        questoes,
        start=1
    ):
        print(
            "\n"
            + "=" * 70
        )

        print(
            f"Questão {indice}/{total}"
        )

        try:
            resultado = executar_questao(
                item,
                indice,
                usar_judge=usar_judge
            )

            resultados.append(resultado)

            print(
                "ID:",
                resultado["id"]
            )

            print(
                "Tipo:",
                resultado["type"]
            )

            print(
                "Context Relevance:",
                resultado["metrics"][
                    "context_relevance"
                ]
            )

        except Exception as erro:
            print(
                f"❌ Erro na questão {indice}: {erro}"
            )

    resumo = gerar_resumo(resultados)

    salvar_resultados(
        resultados,
        resumo
    )

    print(
        "\n"
        + "=" * 70
    )

    print("RESUMO")

    print(
        json.dumps(
            resumo,
            ensure_ascii=False,
            indent=2
        )
    )

    return {
        "summary": resumo,
        "results": resultados
    }


if __name__ == "__main__":
    executar_benchmark()
