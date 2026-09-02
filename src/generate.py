
import os
from typing import Callable, Optional

from pydantic import ValidationError
from langchain_groq import ChatGroq

from src.schema import RAGResponse, SourceEvidence
from src.retrieve import buscar_hibrido
from src.guardrails import (
    aplicar_guardrails_lgpd,
    verificar_fora_de_escopo,
)


# ============================================================
# CONFIGURAÇÃO DO LLM
# ============================================================

MODELO_LLM = "openai/gpt-oss-120b"

llm = ChatGroq(
    model=MODELO_LLM,
    temperature=0,
)

llm_estruturado = llm.with_structured_output(
    RAGResponse
)


# ============================================================
# HELPERS DE METADADOS
# ============================================================

def obter_filepath(doc) -> str:
    """
    Obtém o caminho do arquivo de origem do documento.
    """

    return str(
        doc.metadata.get(
            "source_file",
            "desconhecido"
        )
    )


def obter_chunk_id(doc) -> str:
    """
    Obtém o identificador único do chunk.
    """

    return str(
        doc.metadata.get(
            "chunk_id",
            "desconhecido"
        )
    )


# ============================================================
# CITAÇÕES LITERAIS AUTORIZADAS
# ============================================================

def gerar_citacoes_autorizadas(
    doc,
    tamanho: int = 280,
    sobreposicao: int = 60,
) -> list[str]:
    """
    Divide o conteúdo do documento em trechos literais menores.

    Esses trechos são disponibilizados ao LLM para evitar
    citações inventadas ou citações maiores que o limite
    definido no schema.

    Citações que contenham dados que precisariam ser
    mascarados ou recusados pelo guardrail são evitadas.
    """

    texto = str(
        doc.page_content
    ).strip()

    if not texto:
        return []

    citacoes = []

    inicio = 0

    while inicio < len(texto):

        fim = min(
            inicio + tamanho,
            len(texto)
        )

        trecho = texto[
            inicio:fim
        ].strip()

        if trecho:

            resultado_guardrail = aplicar_guardrails_lgpd(
                trecho
            )

            # Só disponibilizamos como evidência literal
            # trechos que podem ser exibidos sem mascaramento.
            if (
                resultado_guardrail.get("status")
                == "permitido"
            ):
                citacoes.append(
                    trecho
                )

        if fim >= len(texto):
            break

        inicio = max(
            fim - sobreposicao,
            inicio + 1
        )

    # Caso nenhuma citação segura tenha sido encontrada,
    # tenta trechos menores.
    if not citacoes:

        tamanho_reduzido = 140
        inicio = 0

        while inicio < len(texto):

            fim = min(
                inicio + tamanho_reduzido,
                len(texto)
            )

            trecho = texto[
                inicio:fim
            ].strip()

            if trecho:

                resultado_guardrail = aplicar_guardrails_lgpd(
                    trecho
                )

                if (
                    resultado_guardrail.get("status")
                    == "permitido"
                ):
                    citacoes.append(
                        trecho
                    )

            if fim >= len(texto):
                break

            inicio = fim

    return citacoes


def construir_catalogo_citacoes(
    documentos
) -> dict:
    """
    Cria catálogo:

    chunk_id -> lista de citações literais autorizadas.
    """

    catalogo = {}

    for doc in documentos:

        chunk_id = obter_chunk_id(
            doc
        )

        catalogo[
            chunk_id
        ] = gerar_citacoes_autorizadas(
            doc
        )

    return catalogo


# ============================================================
# CONTEXTO PARA O LLM
# ============================================================

def construir_contexto(
    documentos
) -> str:
    """
    Constrói o contexto enviado ao LLM.

    O conteúdo original é apresentado junto das citações
    literais autorizadas para cada chunk.
    """

    blocos = []

    for indice, doc in enumerate(
        documentos,
        start=1
    ):

        filepath = obter_filepath(
            doc
        )

        chunk_id = obter_chunk_id(
            doc
        )

        citacoes = gerar_citacoes_autorizadas(
            doc
        )

        citacoes_formatadas = []

        for numero, citacao in enumerate(
            citacoes,
            start=1
        ):

            citacoes_formatadas.append(
                f"Citação {numero}: {citacao}"
            )

        bloco = f"""
DOCUMENTO {indice}

filepath:
{filepath}

chunk_id:
{chunk_id}

conteúdo:
{doc.page_content}

CITAÇÕES LITERAIS AUTORIZADAS:
{chr(10).join(citacoes_formatadas) if citacoes_formatadas else "Nenhuma citação segura disponível."}
"""

        blocos.append(
            bloco.strip()
        )

    return "\n\n" + "\n\n".join(
        blocos
    )


# ============================================================
# RESPOSTAS DE RECUSA
# ============================================================

def criar_recusa(
    motivo: str,
    reasoning: str,
    answer: Optional[str] = None,
) -> RAGResponse:
    """
    Cria uma RAGResponse válida de recusa.
    """

    mensagens = {
        "lgpd": (
            "Não posso fornecer essa informação porque "
            "ela envolve dados pessoais sensíveis ou restritos."
        ),
        "fora_de_escopo": (
            "Não posso responder essa pergunta porque ela "
            "está fora do escopo da VendeFácil."
        ),
        "sem_evidencia": (
            "Não encontrei evidências suficientes nos "
            "documentos disponíveis para responder com segurança."
        ),
    }

    return RAGResponse(
        answer=(
            answer
            or mensagens.get(
                motivo,
                "Não foi possível responder à solicitação."
            )
        ),
        confidence_level="recusado",
        sources_used=[],
        reasoning=reasoning,
        is_refusal=True,
        refusal_reason=motivo,
    )


# ============================================================
# RETRY GENÉRICO
# ============================================================

def validar_com_retry(
    gerador: Callable,
    tentativas: int = 2,
) -> RAGResponse:
    """
    Executa uma função geradora e valida sua saída com Pydantic.

    Se a validação falhar, uma nova tentativa é feita.

    Não utiliza except: pass.
    """

    ultimo_erro = None

    for tentativa in range(
        1,
        tentativas + 1
    ):

        try:

            resultado = gerador()

            if isinstance(
                resultado,
                RAGResponse
            ):
                return resultado

            return RAGResponse.model_validate(
                resultado
            )

        except ValidationError as erro:

            ultimo_erro = erro

            print(
                f"Falha de validação Pydantic "
                f"na tentativa {tentativa}/{tentativas}."
            )

    raise RuntimeError(
        "Não foi possível produzir uma resposta válida "
        f"após {tentativas} tentativas. "
        f"Último erro: {ultimo_erro}"
    )


# ============================================================
# VALIDAÇÃO DE EVIDÊNCIAS
# ============================================================

def validar_evidencias_da_resposta(
    resposta: RAGResponse,
    documentos,
) -> None:
    """
    Garante que cada evidência citada:

    - pertence a um chunk recuperado;
    - utiliza o filepath correto;
    - possui quotation literal;
    - possui no máximo 500 caracteres.
    """

    if resposta.is_refusal:
        return

    documentos_por_chunk = {
        obter_chunk_id(doc): doc
        for doc in documentos
    }

    if not resposta.sources_used:
        raise ValueError(
            "Resposta não recusada precisa apresentar evidências."
        )

    for evidencia in resposta.sources_used:

        if evidencia.chunk_id not in documentos_por_chunk:
            raise ValueError(
                f"Chunk citado não foi recuperado: "
                f"{evidencia.chunk_id}"
            )

        doc = documentos_por_chunk[
            evidencia.chunk_id
        ]

        filepath_real = obter_filepath(
            doc
        )

        if evidencia.filepath != filepath_real:
            raise ValueError(
                f"filepath incorreto para "
                f"{evidencia.chunk_id}. "
                f"Esperado: {filepath_real}"
            )

        quotation = evidencia.quotation.strip()

        if not quotation:
            raise ValueError(
                "A quotation não pode estar vazia."
            )

        if len(quotation) > 500:
            raise ValueError(
                "A quotation ultrapassa 500 caracteres."
            )

        if quotation not in doc.page_content:
            raise ValueError(
                f"A quotation do chunk "
                f"{evidencia.chunk_id} "
                "não é um trecho literal do documento."
            )

        # A citação não pode expor dados que deveriam
        # ser recusados ou mascarados.
        verificacao_lgpd = aplicar_guardrails_lgpd(
            quotation
        )

        if verificacao_lgpd.get("status") != "permitido":
            raise ValueError(
                f"A evidência do chunk "
                f"{evidencia.chunk_id} contém dado "
                "que não pode ser exibido diretamente."
            )


# ============================================================
# PROMPT
# ============================================================

def construir_prompt(
    pergunta: str,
    documentos,
    feedback_erro: Optional[str] = None,
) -> str:
    """
    Cria o prompt utilizado para geração estruturada.
    """

    contexto = construir_contexto(
        documentos
    )

    feedback = ""

    if feedback_erro:

        feedback = f"""
ATENÇÃO — A TENTATIVA ANTERIOR FOI INVÁLIDA.

Erro encontrado:
{feedback_erro}

Corrija obrigatoriamente esse problema nesta nova tentativa.
"""

    return f"""
Você é o assistente RAG interno da empresa VendeFácil.

Sua tarefa é responder SOMENTE com base nas evidências recuperadas.

REGRAS OBRIGATÓRIAS:

1. Não invente informações.

2. Se as evidências recuperadas não forem suficientes:
   - is_refusal = true
   - confidence_level = "recusado"
   - sources_used = []
   - refusal_reason = "sem_evidencia"

3. Se responder normalmente:
   - is_refusal = false
   - refusal_reason = null
   - sources_used deve possuir pelo menos uma evidência.

4. Toda evidência deve conter:
   - filepath
   - chunk_id
   - quotation

5. A quotation deve ser COPIADA LITERALMENTE de uma das
   "CITAÇÕES LITERAIS AUTORIZADAS" fornecidas no contexto.

6. NÃO reescreva, resuma, corrija nem adapte a quotation.

7. NÃO crie uma quotation por conta própria.

8. Use quotation com no máximo 500 caracteres.

9. Prefira quotation curta e diretamente relacionada
   à resposta.

10. Não inclua nas citações dados pessoais que precisem
    ser mascarados.

11. O campo reasoning deve explicar resumidamente por que
    as evidências sustentam a resposta.

12. confidence_level deve ser:
    - "alta": evidência direta e clara;
    - "media": evidência suficiente, mas parcialmente indireta;
    - "baixa": evidência limitada;
    - "recusado": somente para recusas.

{feedback}

PERGUNTA:
{pergunta}

CONTEXTO RECUPERADO:
{contexto}
""".strip()


# ============================================================
# GERAÇÃO COM LLM
# ============================================================

def gerar_com_llm(
    pergunta: str,
    documentos,
    feedback_erro: Optional[str] = None,
) -> RAGResponse:
    """
    Executa uma tentativa de geração estruturada.
    """

    prompt = construir_prompt(
        pergunta=pergunta,
        documentos=documentos,
        feedback_erro=feedback_erro,
    )

    resposta = llm_estruturado.invoke(
        prompt
    )

    if not isinstance(
        resposta,
        RAGResponse
    ):

        resposta = RAGResponse.model_validate(
            resposta
        )

    return resposta


def gerar_com_retry_llm(
    pergunta: str,
    documentos,
    tentativas: int = 3,
) -> RAGResponse:
    """
    Executa geração estruturada com retry real.

    Em caso de erro de Pydantic ou evidência inválida,
    o erro é devolvido ao LLM na tentativa seguinte.
    """

    ultimo_erro = None

    for tentativa in range(
        1,
        tentativas + 1
    ):

        try:

            feedback = (
                str(ultimo_erro)
                if ultimo_erro
                else None
            )

            resposta = gerar_com_llm(
                pergunta=pergunta,
                documentos=documentos,
                feedback_erro=feedback,
            )

            validar_evidencias_da_resposta(
                resposta,
                documentos
            )

            return resposta

        except (
            ValidationError,
            ValueError,
            Exception,
        ) as erro:

            ultimo_erro = erro

            print(
                f"Falha na tentativa "
                f"{tentativa}/{tentativas}: "
                f"{type(erro).__name__}: {erro}"
            )

    raise RuntimeError(
        "Não foi possível gerar uma resposta estruturada "
        f"válida após {tentativas} tentativas. "
        f"Último erro: {ultimo_erro}"
    )


# ============================================================
# PÓS-PROCESSAMENTO LGPD
# ============================================================

def aplicar_guardrail_na_resposta(
    resposta: RAGResponse,
) -> RAGResponse:
    """
    Verifica a resposta final produzida pelo LLM.

    - Se houver dado proibido -> recusa LGPD.
    - Se houver dado mascarável -> mascara a resposta.
    - Caso contrário -> mantém resposta.
    """

    if resposta.is_refusal:
        return resposta

    resultado = aplicar_guardrails_lgpd(
        resposta.answer
    )

    status = resultado.get(
        "status"
    )

    # --------------------------------------------------------
    # RECUSA
    # --------------------------------------------------------

    if status == "recusado":

        return criar_recusa(
            motivo="lgpd",
            reasoning=(
                "A resposta recuperada continha informação "
                "classificada como restrita pelas regras de LGPD."
            ),
        )

    # --------------------------------------------------------
    # MASCARAMENTO
    # --------------------------------------------------------

    if status == "mascarado":

        resposta.answer = resultado.get(
            "resposta_segura",
            resposta.answer
        )

    return resposta


# ============================================================
# PIPELINE FINAL
# ============================================================

def gerar_resposta(
    pergunta: str,
    usar_filtros: bool = True,
    k: int = 5,
    fetch_k: int = 500,
    tentativas: int = 3,
    funcao_geradora: Optional[Callable] = None,
) -> RAGResponse:
    """
    Pipeline completo da Etapa 3:

    pergunta
        ↓
    fora de escopo
        ↓
    LGPD na pergunta
        ↓
    retrieval híbrido
        ↓
    geração estruturada
        ↓
    validação Pydantic
        ↓
    validação das evidências
        ↓
    guardrail LGPD na resposta
        ↓
    RAGResponse final
    """

    # ========================================================
    # 1. FORA DE ESCOPO
    # ========================================================

    verificacao_escopo = verificar_fora_de_escopo(
        pergunta
    )

    if not verificacao_escopo.get(
        "permitido",
        True
    ):

        return criar_recusa(
            motivo="fora_de_escopo",
            answer=verificacao_escopo.get(
                "mensagem"
            ),
            reasoning=(
                "A pergunta não pertence ao domínio "
                "operacional da VendeFácil."
            ),
        )

    # ========================================================
    # 2. LGPD NA PERGUNTA
    # ========================================================

    verificacao_lgpd = aplicar_guardrails_lgpd(
        pergunta
    )

    if verificacao_lgpd.get(
        "status"
    ) == "recusado":

        return criar_recusa(
            motivo="lgpd",
            reasoning=(
                verificacao_lgpd.get(
                    "motivo",
                    "A pergunta solicita dado restrito."
                )
            ),
        )

    # ========================================================
    # 3. RETRIEVAL
    # ========================================================

    resultado_busca = buscar_hibrido(
        pergunta,
        usar_filtros=usar_filtros,
        k=k,
        fetch_k=fetch_k,
    )

    ranking = resultado_busca.get(
        "rrf",
        []
    )

    documentos = [
        doc
        for doc, _score in ranking
    ]

    # ========================================================
    # 4. SEM EVIDÊNCIA
    # ========================================================

    if not documentos:

        return criar_recusa(
            motivo="sem_evidencia",
            reasoning=(
                "Nenhum documento relevante foi recuperado "
                "para responder à pergunta."
            ),
        )

    # ========================================================
    # 5. FUNÇÃO CUSTOMIZADA PARA TESTES
    # ========================================================

    if funcao_geradora is not None:

        resposta = validar_com_retry(
            gerador=funcao_geradora,
            tentativas=tentativas,
        )

        if not resposta.is_refusal:

            validar_evidencias_da_resposta(
                resposta,
                documentos
            )

    # ========================================================
    # 6. GERAÇÃO REAL COM LLM
    # ========================================================

    else:

        resposta = gerar_com_retry_llm(
            pergunta=pergunta,
            documentos=documentos,
            tentativas=tentativas,
        )

    # ========================================================
    # 7. GUARDRAIL NA RESPOSTA
    # ========================================================

    resposta = aplicar_guardrail_na_resposta(
        resposta
    )

    return resposta


# ============================================================
# TESTE MANUAL
# ============================================================

if __name__ == "__main__":

    pergunta = (
        "O que aconteceu no ticket TCK-1057?"
    )

    resposta = gerar_resposta(
        pergunta
    )

    print(
        resposta.model_dump_json(
            indent=2
        )
    )
