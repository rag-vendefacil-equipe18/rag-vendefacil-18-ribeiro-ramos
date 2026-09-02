
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# CAMINHOS DO PROJETO
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

# Permite executar:
# python eval/run_benchmark.py
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


BENCHMARK_PATH = (
    ROOT_DIR
    / "benchmark"
    / "questions_and_ground_truth.json"
)

RESULTS_PATH = (
    ROOT_DIR
    / "eval"
    / "results.json"
)


# ============================================================
# UTILITÁRIOS
# ============================================================

def normalizar_caminho(valor: Any) -> str:
    """
    Normaliza caminhos para facilitar a comparação entre
    expected_sources e source_file dos documentos recuperados.
    """

    if valor is None:
        return ""

    caminho = str(valor).strip().replace("\\", "/")

    while caminho.startswith("./"):
        caminho = caminho[2:]

    return caminho.lower()


def nome_arquivo(valor: Any) -> str:
    """
    Retorna apenas o nome final do arquivo.
    Exemplo:
    data/structured/products.json -> products.json
    """

    caminho = normalizar_caminho(valor)

    if not caminho:
        return ""

    return caminho.split("/")[-1]


def serializar_pydantic(objeto: Any) -> Any:
    """
    Converte modelos Pydantic e outros objetos em estruturas
    serializáveis para JSON.
    """

    if objeto is None:
        return None

    if hasattr(objeto, "model_dump"):
        return objeto.model_dump()

    if hasattr(objeto, "dict"):
        return objeto.dict()

    return objeto


def media(valores: List[float]) -> Optional[float]:
    """
    Calcula média e retorna None caso a lista esteja vazia.
    """

    if not valores:
        return None

    return round(
        sum(valores) / len(valores),
        4
    )


# ============================================================
# LEITURA DO BENCHMARK OFICIAL
# ============================================================

def carregar_benchmark() -> List[Dict[str, Any]]:
    """
    Carrega o arquivo oficial disponibilizado para a Etapa 4.
    """

    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError(
            "Arquivo do benchmark não encontrado em:\n"
            f"{BENCHMARK_PATH}"
        )

    with BENCHMARK_PATH.open(
        "r",
        encoding="utf-8"
    ) as arquivo:
        dados = json.load(arquivo)

    if not isinstance(dados, dict):
        raise ValueError(
            "O benchmark oficial deve possuir um objeto JSON "
            "na raiz."
        )

    questoes = dados.get("questions")

    if not isinstance(questoes, list):
        raise ValueError(
            "Campo 'questions' não encontrado ou inválido "
            "no benchmark."
        )

    print(
        f"Benchmark: {dados.get('benchmark_name', 'N/A')}"
    )

    print(
        f"Versão: {dados.get('version', 'N/A')}"
    )

    print(
        f"Quantidade real de questões: {len(questoes)}"
    )

    # O texto da atividade menciona 20 questões,
    # porém o arquivo oficial atualmente possui 24.
    if len(questoes) != 20:
        print(
            "⚠️ Atenção: a orientação menciona 20 questões, "
            f"mas o arquivo contém {len(questoes)}."
        )

        print(
            "O script NÃO removerá questões automaticamente."
        )

    return questoes


# ============================================================
# EXTRAÇÃO DOS RESULTADOS DO RETRIEVER
# ============================================================

def extrair_documentos_rrf(
    resultado_busca: Dict[str, Any]
) -> List[Any]:
    """
    Recupera os documentos provenientes do ranking RRF.

    O buscar_hibrido retorna:
        rrf = [(Document, score), ...]
    """

    ranking = resultado_busca.get("rrf", [])

    documentos = []

    for item in ranking:

        if isinstance(item, (list, tuple)):

            if len(item) >= 1:
                documentos.append(item[0])

        else:
            documentos.append(item)

    return documentos


def extrair_chunk_ids(
    documentos: List[Any]
) -> List[str]:
    """
    Extrai os chunk_id dos documentos recuperados.
    """

    chunk_ids = []

    for documento in documentos:

        metadata = getattr(
            documento,
            "metadata",
            {}
        ) or {}

        chunk_id = metadata.get("chunk_id")

        if chunk_id is not None:
            chunk_ids.append(str(chunk_id))

    return chunk_ids


def extrair_sources_recuperados(
    documentos: List[Any]
) -> List[str]:
    """
    Extrai source_file dos documentos recuperados.
    """

    fontes = []

    for documento in documentos:

        metadata = getattr(
            documento,
            "metadata",
            {}
        ) or {}

        source_file = metadata.get(
            "source_file"
        )

        if source_file:
            fontes.append(str(source_file))

    return fontes


def documento_para_dict(
    documento: Any
) -> Dict[str, Any]:
    """
    Converte um Document do LangChain para uma estrutura
    simples e serializável.
    """

    metadata = getattr(
        documento,
        "metadata",
        {}
    ) or {}

    conteudo = getattr(
        documento,
        "page_content",
        ""
    )

    return {
        "chunk_id": metadata.get("chunk_id"),
        "source_file": metadata.get("source_file"),
        "doc_type": metadata.get("doc_type"),
        "sensitivity": metadata.get("sensitivity"),
        "metadata": metadata,
        "content": conteudo
    }


# ============================================================
# CONTEXT RELEVANCE
# ============================================================

def fonte_corresponde(
    fonte_recuperada: str,
    fonte_esperada: str
) -> bool:
    """
    Compara source_file recuperado com expected_source.

    Aceita tanto:
        data/structured/products.json

    quanto:
        products.json

    pois a ingestão pode armazenar caminhos em formatos diferentes.
    """

    recuperada = normalizar_caminho(
        fonte_recuperada
    )

    esperada = normalizar_caminho(
        fonte_esperada
    )

    if not recuperada or not esperada:
        return False

    # Correspondência exata
    if recuperada == esperada:
        return True

    # Correspondência pelo final do caminho
    if recuperada.endswith(esperada):
        return True

    if esperada.endswith(recuperada):
        return True

    # Correspondência pelo nome do arquivo
    return (
        nome_arquivo(recuperada)
        ==
        nome_arquivo(esperada)
    )


def calcular_context_relevance(
    sources_recuperados: List[str],
    sources_esperados: List[str]
) -> Optional[float]:
    """
    Calcula Context Relevance usando as fontes esperadas
    fornecidas pelo benchmark oficial.

    O benchmark disponibilizado não contém expected_chunk_ids.
    Por isso, nesta implementação, verificamos qual proporção
    das expected_sources apareceu entre os chunks recuperados.

    Fórmula:

        fontes esperadas recuperadas
        ----------------------------
        total de fontes esperadas

    Resultado:
        0.0 até 1.0

    Para perguntas fora do escopo, expected_sources é vazio.
    Nesses casos a métrica é None.
    """

    if not sources_esperados:
        return None

    encontradas = 0

    for fonte_esperada in sources_esperados:

        encontrou = any(
            fonte_corresponde(
                fonte_recuperada,
                fonte_esperada
            )
            for fonte_recuperada
            in sources_recuperados
        )

        if encontrou:
            encontradas += 1

    score = (
        encontradas
        /
        len(sources_esperados)
    )

    return round(score, 4)


# ============================================================
# EXECUÇÃO DE UMA QUESTÃO
# ============================================================

def executar_questao(
    item: Dict[str, Any],
    indice: int,
    usar_judge: bool = False
) -> Dict[str, Any]:
    """
    Executa recuperação + geração para uma questão.

    Nesta etapa individual da Eduarda:
    - executa o Retriever;
    - calcula Context Relevance;
    - executa a geração RAG;
    - deixa Answer Relevance e Groundedness como None.

    As duas métricas do LLM-as-judge serão integradas depois
    da parte do Eridalgo.
    """

    from retrieve import buscar_hibrido
    from generate import gerar_resposta

    questao_id = item.get(
        "id",
        f"Q{indice:02d}"
    )

    categoria = item.get(
        "category",
        "Sem categoria"
    )

    pergunta = item.get(
        "question",
        ""
    )

    expected_sources = item.get(
        "expected_sources",
        []
    ) or []

    expected_metadata = item.get(
        "expected_metadata",
        {}
    ) or {}

    ground_truth_answer = item.get(
        "ground_truth_answer",
        ""
    )

    key_points = item.get(
        "key_points_for_evaluation",
        []
    ) or []

    if not pergunta:
        raise ValueError(
            f"Questão {questao_id} sem campo 'question'."
        )

    # --------------------------------------------------------
    # 1. RETRIEVAL
    # --------------------------------------------------------

    busca = buscar_hibrido(
        pergunta,
        usar_filtros=True,
        k=5,
        fetch_k=500
    )

    documentos = extrair_documentos_rrf(
        busca
    )

    chunk_ids = extrair_chunk_ids(
        documentos
    )

    sources_recuperados = (
        extrair_sources_recuperados(
            documentos
        )
    )

    context_relevance = (
        calcular_context_relevance(
            sources_recuperados,
            expected_sources
        )
    )

    # --------------------------------------------------------
    # 2. GERAÇÃO RAG
    # --------------------------------------------------------

    resposta = gerar_resposta(
        pergunta,
        usar_filtros=True,
        k=5,
        fetch_k=500
    )

    resposta_serializada = (
        serializar_pydantic(
            resposta
        )
    )

    # --------------------------------------------------------
    # 3. RESULTADO
    # --------------------------------------------------------

    resultado = {
        "id": questao_id,
        "type": categoria,
        "question": pergunta,

        "ground_truth": {
            "expected_sources": expected_sources,
            "expected_metadata": expected_metadata,
            "ground_truth_answer": ground_truth_answer,
            "key_points_for_evaluation": key_points
        },

        "retrieval": {
            "filters": busca.get(
                "filtros",
                {}
            ),

            "retrieved_chunk_ids": chunk_ids,

            "retrieved_sources": (
                sources_recuperados
            ),

            "documents": [
                documento_para_dict(doc)
                for doc in documentos
            ]
        },

        "response": resposta_serializada,

        "metrics": {
            "context_relevance": (
                context_relevance
            ),

            "context_relevance_basis": (
                "expected_sources"
            ),

            # Serão preenchidos na integração
            # com o trabalho do Eridalgo.
            "answer_relevance": None,
            "groundedness": None
        }
    }

    return resultado


# ============================================================
# RESUMO
# ============================================================

def gerar_resumo(
    resultados: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Gera resumo global e por categoria.
    """

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

        contexto = metricas.get(
            "context_relevance"
        )

        if isinstance(
            contexto,
            (int, float)
        ):
            context_global.append(
                contexto
            )

            por_tipo[tipo][
                "context_relevance"
            ].append(contexto)

        answer = metricas.get(
            "answer_relevance"
        )

        if isinstance(answer, dict):

            score = answer.get("score")

            if isinstance(
                score,
                (int, float)
            ):
                answer_global.append(
                    score
                )

                por_tipo[tipo][
                    "answer_relevance"
                ].append(score)

        grounded = metricas.get(
            "groundedness"
        )

        if isinstance(
            grounded,
            dict
        ):

            score = grounded.get("score")

            if isinstance(
                score,
                (int, float)
            ):
                grounded_global.append(
                    score
                )

                por_tipo[tipo][
                    "groundedness"
                ].append(score)

    resumo_por_tipo = {}

    for tipo, dados in por_tipo.items():

        resumo_por_tipo[tipo] = {
            "quantidade": (
                dados["quantidade"]
            ),

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
        "total_questions": len(
            resultados
        ),

        "evaluation_status": (
            "partial_without_llm_judge"
        ),

        "context_relevance_basis": (
            "expected_sources"
        ),

        "rag_triad": {
            "context_relevance": media(
                context_global
            ),

            "answer_relevance": media(
                answer_global
            ),

            "groundedness": media(
                grounded_global
            )
        },

        "by_type": resumo_por_tipo
    }


# ============================================================
# SALVAR RESULTADOS
# ============================================================

def salvar_resultados(
    resultados: List[Dict[str, Any]],
    resumo: Dict[str, Any]
) -> None:

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
            indent=2,
            default=str
        )

    print(
        "\n✅ Resultados salvos em:"
    )

    print(
        RESULTS_PATH
    )


# ============================================================
# EXECUÇÃO DO BENCHMARK
# ============================================================

def executar_benchmark(
    usar_judge: bool = False,
    limite: Optional[int] = None
) -> Dict[str, Any]:
    """
    Executa todas as questões presentes no arquivo oficial.

    usar_judge permanece disponível para a integração futura,
    mas nesta versão individual não altera o processamento.
    """

    questoes = carregar_benchmark()

    if limite is not None:
        questoes = questoes[:limite]

    resultados = []

    total = len(questoes)

    print(
        f"\nExecutando benchmark com "
        f"{total} questões."
    )

    print(
        "Modo atual: Context Relevance "
        "+ geração RAG, sem LLM-as-judge."
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

        print(
            "ID:",
            item.get(
                "id",
                indice
            )
        )

        print(
            "Pergunta:",
            item.get(
                "question",
                ""
            )
        )

        try:

            resultado = executar_questao(
                item,
                indice,
                usar_judge=usar_judge
            )

            resultados.append(
                resultado
            )

            print(
                "Tipo:",
                resultado["type"]
            )

            print(
                "Chunks recuperados:",
                resultado[
                    "retrieval"
                ][
                    "retrieved_chunk_ids"
                ]
            )

            print(
                "Fontes recuperadas:",
                resultado[
                    "retrieval"
                ][
                    "retrieved_sources"
                ]
            )

            print(
                "Fontes esperadas:",
                resultado[
                    "ground_truth"
                ][
                    "expected_sources"
                ]
            )

            print(
                "Context Relevance:",
                resultado[
                    "metrics"
                ][
                    "context_relevance"
                ]
            )

        except Exception as erro:

            print(
                f"❌ Erro na questão "
                f"{indice}: {erro}"
            )

            resultados.append(
                {
                    "id": item.get(
                        "id",
                        f"Q{indice:02d}"
                    ),

                    "type": item.get(
                        "category",
                        "Sem categoria"
                    ),

                    "question": item.get(
                        "question",
                        ""
                    ),

                    "error": str(erro),

                    "metrics": {
                        "context_relevance": None,
                        "context_relevance_basis": (
                            "expected_sources"
                        ),
                        "answer_relevance": None,
                        "groundedness": None
                    }
                }
            )

    resumo = gerar_resumo(
        resultados
    )

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


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    executar_benchmark(
        usar_judge=False
    )
