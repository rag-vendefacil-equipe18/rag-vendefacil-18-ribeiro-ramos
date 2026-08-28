
from typing import Callable, Optional

from pydantic import ValidationError
from langchain_groq import ChatGroq

from retrieve import buscar_hibrido
from schema import RAGResponse, SourceEvidence


# ============================================================
# CONFIGURAÇÃO DO LLM
# ============================================================

MODELO_LLM = "openai/gpt-oss-120b"

llm = ChatGroq(
    model=MODELO_LLM,
    temperature=0
)


# ============================================================
# FUNÇÕES AUXILIARES DE METADADOS
# ============================================================

def obter_filepath(doc) -> str:
    """
    Recupera o caminho do arquivo de origem do documento.
    """
    return str(
        doc.metadata.get(
            "source_file",
            doc.metadata.get(
                "source",
                "fonte_desconhecida"
            )
        )
    )


def obter_chunk_id(doc) -> str:
    """
    Recupera o identificador único do chunk.
    """
    return str(
        doc.metadata.get(
            "chunk_id",
            "chunk_desconhecido"
        )
    )


# ============================================================
# CITAÇÕES LITERAIS AUTORIZADAS
# ============================================================

def gerar_citacoes_autorizadas(
    doc,
    tamanho: int = 280,
    sobreposicao: int = 60
) -> list[str]:
    """
    Divide o conteúdo original do chunk em trechos LITERAIS.

    Esses trechos serão apresentados ao LLM como citações
    autorizadas.

    Nenhum trecho ultrapassa o limite de 500 caracteres
    definido pelo schema Pydantic.
    """

    texto = doc.page_content.strip()

    if not texto:
        return []

    if len(texto) <= tamanho:
        return [texto]

    citacoes = []

    inicio = 0

    while inicio < len(texto):

        fim = min(
            inicio + tamanho,
            len(texto)
        )

        trecho = texto[inicio:fim]

        if trecho:
            citacoes.append(trecho)

        if fim >= len(texto):
            break

        inicio = fim - sobreposicao

    return citacoes


def construir_catalogo_citacoes(documentos) -> dict:
    """
    Cria um catálogo:

    chunk_id -> lista de quotations literais autorizadas.
    """

    catalogo = {}

    for doc in documentos:

        chunk_id = obter_chunk_id(doc)

        catalogo[chunk_id] = (
            gerar_citacoes_autorizadas(doc)
        )

    return catalogo


# ============================================================
# EVIDÊNCIAS
# ============================================================

def construir_evidencias(
    documentos,
    max_evidencias: int = 5
) -> list[SourceEvidence]:
    """
    Constrói evidências seguras diretamente dos documentos.

    Útil principalmente para testes.
    """

    evidencias = []

    for doc in documentos[:max_evidencias]:

        citacoes = gerar_citacoes_autorizadas(
            doc
        )

        if not citacoes:
            continue

        evidencias.append(
            SourceEvidence(
                filepath=obter_filepath(doc),
                chunk_id=obter_chunk_id(doc),
                quotation=citacoes[0]
            )
        )

    return evidencias


# ============================================================
# CONTEXTO PARA O LLM
# ============================================================

def construir_contexto(
    documentos,
    max_documentos: int = 5
) -> str:
    """
    Monta o contexto enviado ao LLM.

    Além do conteúdo completo, apresenta quotations
    autorizadas que podem ser copiadas literalmente.
    """

    blocos = []

    for indice, doc in enumerate(
        documentos[:max_documentos],
        start=1
    ):

        filepath = obter_filepath(doc)
        chunk_id = obter_chunk_id(doc)

        citacoes = gerar_citacoes_autorizadas(
            doc
        )

        citacoes_formatadas = []

        for numero, citacao in enumerate(
            citacoes,
            start=1
        ):
            citacoes_formatadas.append(
                f"CITAÇÃO {numero}:\n{citacao}"
            )

        bloco_citacoes = "\n\n".join(
            citacoes_formatadas
        )

        bloco = f"""
============================================================
EVIDÊNCIA {indice}
============================================================

filepath:
{filepath}

chunk_id:
{chunk_id}

CONTEÚDO COMPLETO:
{doc.page_content.strip()}

CITAÇÕES LITERAIS AUTORIZADAS:

{bloco_citacoes}
""".strip()

        blocos.append(bloco)

    return "\n\n".join(blocos)


# ============================================================
# RECUSAS
# ============================================================

def criar_resposta_recusada(
    motivo: str,
    mensagem: str
) -> RAGResponse:
    """
    Cria uma resposta de recusa compatível com o schema.
    """

    return RAGResponse(
        answer=mensagem,
        confidence_level="recusado",
        sources_used=[],
        reasoning=(
            "A consulta foi recusada de acordo "
            "com as regras definidas para o sistema."
        ),
        is_refusal=True,
        refusal_reason=motivo
    )


def criar_resposta_sem_evidencia() -> RAGResponse:
    """
    Recusa por ausência de evidências.
    """

    return RAGResponse(
        answer=(
            "Não foram encontradas evidências suficientes "
            "na base da VendeFácil para responder à pergunta."
        ),
        confidence_level="recusado",
        sources_used=[],
        reasoning=(
            "A recuperação não forneceu evidências suficientes "
            "para produzir uma resposta fundamentada."
        ),
        is_refusal=True,
        refusal_reason="sem_evidencia"
    )


# ============================================================
# RETRY GENÉRICO
# ============================================================

def validar_com_retry(
    gerador: Callable,
    tentativas: int = 2
) -> RAGResponse:
    """
    Executa uma função geradora e valida a resposta por Pydantic.

    Mantida também para testes isolados do mecanismo de retry.
    """

    ultimo_erro = None

    for tentativa in range(
        1,
        tentativas + 1
    ):

        try:

            resposta = gerador()

            if isinstance(
                resposta,
                RAGResponse
            ):
                return resposta

            return RAGResponse.model_validate(
                resposta
            )

        except ValidationError as erro:

            ultimo_erro = erro

            print(
                "Falha de validação Pydantic "
                f"na tentativa {tentativa}/{tentativas}."
            )

        except Exception as erro:

            ultimo_erro = erro

            print(
                "Falha na geração estruturada "
                f"na tentativa {tentativa}/{tentativas}: "
                f"{type(erro).__name__}"
            )

    raise ValueError(
        "Não foi possível gerar uma resposta válida "
        f"após {tentativas} tentativas."
    ) from ultimo_erro


# ============================================================
# VALIDAÇÃO DAS EVIDÊNCIAS
# ============================================================

def validar_evidencias_da_resposta(
    resposta: RAGResponse,
    documentos
) -> None:
    """
    Verifica se cada fonte citada pelo LLM é realmente
    pertencente aos documentos recuperados.

    Valida:
    - chunk_id
    - filepath
    - quotation literal
    - tamanho da quotation
    """

    if resposta.is_refusal:
        return

    documentos_por_chunk = {}

    for doc in documentos:

        documentos_por_chunk[
            obter_chunk_id(doc)
        ] = doc

    for evidencia in resposta.sources_used:

        # ----------------------------------------------------
        # CHUNK
        # ----------------------------------------------------

        if (
            evidencia.chunk_id
            not in documentos_por_chunk
        ):
            raise ValueError(
                "O LLM citou um chunk_id não recuperado: "
                f"{evidencia.chunk_id}"
            )

        doc_original = documentos_por_chunk[
            evidencia.chunk_id
        ]

        # ----------------------------------------------------
        # FILEPATH
        # ----------------------------------------------------

        filepath_original = obter_filepath(
            doc_original
        )

        if (
            evidencia.filepath
            != filepath_original
        ):
            raise ValueError(
                "O filepath citado não corresponde "
                "ao chunk recuperado. "
                f"Esperado: {filepath_original}. "
                f"Recebido: {evidencia.filepath}."
            )

        # ----------------------------------------------------
        # QUOTATION
        # ----------------------------------------------------

        quotation = evidencia.quotation

        if not quotation:
            raise ValueError(
                "Quotation vazia."
            )

        if len(quotation) > 500:
            raise ValueError(
                "Quotation superior a 500 caracteres."
            )

        # Precisa ser literalmente parte do chunk.
        if (
            quotation
            not in doc_original.page_content
        ):
            raise ValueError(
                "A quotation informada não corresponde "
                "a um trecho literal do chunk "
                f"{evidencia.chunk_id}."
            )


# ============================================================
# PROMPT
# ============================================================

def construir_prompt(
    pergunta: str,
    contexto: str,
    feedback_erro: Optional[str] = None
) -> str:
    """
    Constrói o prompt do LLM.

    Caso seja uma nova tentativa, o modelo também recebe
    informação sobre o erro cometido anteriormente.
    """

    feedback = ""

    if feedback_erro:

        feedback = f"""
============================================================
ATENÇÃO: CORREÇÃO DA TENTATIVA ANTERIOR
============================================================

A resposta anterior foi rejeitada pela validação.

Motivo:

{feedback_erro}

Corrija obrigatoriamente esse problema nesta nova tentativa.

IMPORTANTE:
Se o erro estiver relacionado à quotation, NÃO reescreva,
não resuma e não corrija o trecho.

Copie EXATAMENTE uma das CITAÇÕES LITERAIS AUTORIZADAS
fornecidas nas evidências abaixo.
"""

    return f"""
Você é o Assistente de Knowledge Base da empresa fictícia
VendeFácil Tecnologia Ltda.

Sua tarefa é responder à pergunta utilizando EXCLUSIVAMENTE
as evidências recuperadas pelo sistema RAG.

Você não pode utilizar conhecimento externo.

{feedback}

============================================================
REGRAS OBRIGATÓRIAS
============================================================

1. Não invente informações.

2. Responda somente com fatos presentes nas evidências.

3. Não invente filepath.

4. Não invente chunk_id.

5. Toda resposta não recusada deve possuir pelo menos
   uma fonte em sources_used.

6. filepath deve ser copiado EXATAMENTE da evidência.

7. chunk_id deve ser copiado EXATAMENTE da evidência.

8. quotation deve ser um TRECHO LITERAL.

9. Para quotation, prefira copiar EXATAMENTE uma das
   "CITAÇÕES LITERAIS AUTORIZADAS" apresentadas no contexto.

10. NÃO resuma a quotation.

11. NÃO reescreva a quotation.

12. NÃO corrija ortografia ou pontuação da quotation.

13. NÃO altere espaços, pontos, acentos ou palavras
    da quotation.

14. quotation nunca pode possuir mais de 500 caracteres.

15. As citações autorizadas já foram preparadas com
    tamanho seguro.

16. Utilize somente as fontes necessárias para
    sustentar a resposta.

17. Se as evidências responderem diretamente:
        confidence_level = "alta"

18. Se responderem parcialmente:
        confidence_level = "media"

19. Se houver grande incerteza:
        confidence_level = "baixa"

20. Em resposta normal:
        is_refusal = false
        refusal_reason = null

21. Se nenhuma evidência recuperada sustentar a pergunta:
        is_refusal = true
        confidence_level = "recusado"
        sources_used = []
        refusal_reason = "sem_evidencia"

22. Não exponha cadeia de pensamento.

23. reasoning deve conter apenas uma justificativa curta
    de por que as evidências sustentam a resposta.

============================================================
PERGUNTA
============================================================

{pergunta}

============================================================
EVIDÊNCIAS RECUPERADAS
============================================================

{contexto}

============================================================
INSTRUÇÃO FINAL
============================================================

Produza uma resposta estruturada exatamente de acordo com
o schema RAGResponse.
""".strip()


# ============================================================
# CHAMADA DO LLM
# ============================================================

def gerar_com_llm(
    pergunta: str,
    documentos,
    feedback_erro: Optional[str] = None
) -> RAGResponse:
    """
    Executa o LLM com saída estruturada.
    """

    contexto = construir_contexto(
        documentos
    )

    prompt = construir_prompt(
        pergunta=pergunta,
        contexto=contexto,
        feedback_erro=feedback_erro
    )

    llm_estruturado = (
        llm.with_structured_output(
            RAGResponse
        )
    )

    resposta = llm_estruturado.invoke(
        prompt
    )

    if not isinstance(
        resposta,
        RAGResponse
    ):
        resposta = (
            RAGResponse.model_validate(
                resposta
            )
        )

    validar_evidencias_da_resposta(
        resposta=resposta,
        documentos=documentos
    )

    return resposta


# ============================================================
# RETRY DO LLM COM FEEDBACK
# ============================================================

def gerar_com_retry_llm(
    pergunta: str,
    documentos,
    tentativas: int = 2
) -> RAGResponse:
    """
    Retry específico para o LLM.

    Diferentemente de simplesmente executar o mesmo prompt,
    a tentativa seguinte recebe o motivo da falha anterior.
    """

    ultimo_erro = None
    feedback_erro = None

    for tentativa in range(
        1,
        tentativas + 1
    ):

        try:

            resposta = gerar_com_llm(
                pergunta=pergunta,
                documentos=documentos,
                feedback_erro=feedback_erro
            )

            return resposta

        except Exception as erro:

            ultimo_erro = erro

            print(
                "Falha na geração/validação "
                f"na tentativa {tentativa}/{tentativas}: "
                f"{type(erro).__name__}"
            )

            print(
                f"Motivo: {erro}"
            )

            feedback_erro = str(
                erro
            )

    raise ValueError(
        "Não foi possível gerar uma resposta estruturada "
        f"e validada após {tentativas} tentativas."
    ) from ultimo_erro


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

def gerar_resposta(
    pergunta: str,
    usar_filtros: bool = True,
    k: int = 5,
    fetch_k: int = 500,
    tentativas: int = 2,
    funcao_llm: Optional[Callable] = None
) -> RAGResponse:
    """
    Pipeline principal da Etapa 3.

    Fluxo:

        pergunta
            ↓
        busca híbrida
            ↓
        Dense + BM25
            ↓
        RRF
            ↓
        documentos recuperados
            ↓
        contexto
            ↓
        LLM
            ↓
        RAGResponse
            ↓
        Pydantic
            ↓
        validação de evidências
            ↓
        retry com feedback em caso de erro

    Os guardrails de LGPD e fora de escopo serão integrados
    posteriormente.
    """

    # --------------------------------------------------------
    # PERGUNTA VAZIA
    # --------------------------------------------------------

    if (
        not pergunta
        or not pergunta.strip()
    ):
        return (
            criar_resposta_sem_evidencia()
        )

    # --------------------------------------------------------
    # RECUPERAÇÃO
    # --------------------------------------------------------

    resultado_busca = buscar_hibrido(
        pergunta=pergunta,
        usar_filtros=usar_filtros,
        k=k,
        fetch_k=fetch_k
    )

    ranking_rrf = resultado_busca.get(
        "rrf",
        []
    )

    documentos = []

    for item in ranking_rrf:

        if not item:
            continue

        doc = item[0]

        if doc is not None:
            documentos.append(
                doc
            )

    # --------------------------------------------------------
    # SEM EVIDÊNCIA
    # --------------------------------------------------------

    if not documentos:
        return (
            criar_resposta_sem_evidencia()
        )

    # --------------------------------------------------------
    # FUNÇÃO CUSTOMIZADA PARA TESTES
    # --------------------------------------------------------

    if funcao_llm is not None:

        def executar_customizado():

            contexto = construir_contexto(
                documentos
            )

            resposta = funcao_llm(
                pergunta=pergunta,
                contexto=contexto,
                documentos=documentos
            )

            if not isinstance(
                resposta,
                RAGResponse
            ):
                resposta = (
                    RAGResponse.model_validate(
                        resposta
                    )
                )

            validar_evidencias_da_resposta(
                resposta=resposta,
                documentos=documentos
            )

            return resposta

        return validar_com_retry(
            gerador=executar_customizado,
            tentativas=tentativas
        )

    # --------------------------------------------------------
    # LLM REAL + RETRY COM FEEDBACK
    # --------------------------------------------------------

    return gerar_com_retry_llm(
        pergunta=pergunta,
        documentos=documentos,
        tentativas=tentativas
    )


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    pergunta_teste = (
        "Quais tickets de clientes de Minas Gerais estão "
        "relacionados ao módulo de estoque?"
    )

    resposta_teste = gerar_resposta(
        pergunta_teste
    )

    print(
        resposta_teste.model_dump_json(
            indent=2
        )
    )
