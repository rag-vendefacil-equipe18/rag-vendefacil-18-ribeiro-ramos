
import sys
from pathlib import Path

import streamlit as st


# ============================================================
# CAMINHOS DO PROJETO
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# ============================================================
# IMPORTAÇÃO DO PIPELINE RAG
# ============================================================

from src.generate import gerar_resposta


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="VendeFácil RAG",
    page_icon="💬",
    layout="centered",
)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def converter_resposta(resultado):
    """
    Converte a resposta Pydantic/dict para dicionário.
    """

    if resultado is None:
        return {}

    if hasattr(resultado, "model_dump"):
        return resultado.model_dump()

    if hasattr(resultado, "dict"):
        return resultado.dict()

    if isinstance(resultado, dict):
        return resultado

    return {
        "answer": str(resultado)
    }


def obter_primeiro(dados, nomes, padrao=None):
    """
    Procura o primeiro campo existente entre vários nomes possíveis.
    """

    for nome in nomes:
        if nome in dados:
            return dados[nome]

    return padrao


def formatar_citacao(citacao):
    """
    Formata uma citação/evidência para exibição.
    """

    if isinstance(citacao, str):
        return citacao

    if isinstance(citacao, dict):

        source = (
            citacao.get("source_file")
            or citacao.get("source")
            or citacao.get("file")
            or ""
        )

        chunk_id = (
            citacao.get("chunk_id")
            or citacao.get("id")
            or ""
        )

        trecho = (
            citacao.get("quote")
            or citacao.get("passage")
            or citacao.get("text")
            or citacao.get("content")
            or ""
        )

        partes = []

        if source:
            partes.append(f"Fonte: {source}")

        if chunk_id:
            partes.append(f"Chunk: {chunk_id}")

        if trecho:
            partes.append(f"Trecho: {trecho}")

        if partes:
            return "\n\n".join(partes)

    return str(citacao)


# ============================================================
# CABEÇALHO
# ============================================================

st.title("💬 VendeFácil RAG")

st.caption(
    "Assistente baseado na base de conhecimento da VendeFácil."
)

st.info(
    "As respostas são geradas com base nos documentos recuperados "
    "pelo sistema RAG e podem incluir evidências e recusas de segurança."
)


# ============================================================
# ESTADO DA CONVERSA
# ============================================================

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []


# ============================================================
# BOTÃO LIMPAR
# ============================================================

with st.sidebar:

    st.header("VendeFácil RAG")

    st.write(
        "Interface de demonstração do sistema de "
        "Retrieval-Augmented Generation."
    )

    if st.button(
        "Limpar conversa",
        use_container_width=True
    ):
        st.session_state.mensagens = []
        st.rerun()


# ============================================================
# HISTÓRICO
# ============================================================

for mensagem in st.session_state.mensagens:

    with st.chat_message(
        mensagem["role"]
    ):

        st.markdown(
            mensagem["content"]
        )

        if mensagem.get("details"):

            with st.expander(
                "Detalhes da resposta"
            ):
                st.json(
                    mensagem["details"]
                )


# ============================================================
# ENTRADA DO USUÁRIO
# ============================================================

pergunta = st.chat_input(
    "Digite sua pergunta sobre a VendeFácil..."
)


# ============================================================
# EXECUÇÃO DO RAG
# ============================================================

if pergunta:

    st.session_state.mensagens.append(
        {
            "role": "user",
            "content": pergunta
        }
    )

    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):

        with st.spinner(
            "Consultando a base de conhecimento..."
        ):

            try:

                resultado = gerar_resposta(
                    pergunta
                )

                dados = converter_resposta(
                    resultado
                )

                resposta = obter_primeiro(
                    dados,
                    [
                        "answer",
                        "resposta",
                        "response"
                    ],
                    "Não foi possível gerar uma resposta."
                )

                is_refusal = obter_primeiro(
                    dados,
                    [
                        "is_refusal",
                        "refusal"
                    ],
                    False
                )

                confidence = obter_primeiro(
                    dados,
                    [
                        "confidence",
                        "confianca"
                    ]
                )

                citacoes = obter_primeiro(
                    dados,
                    [
                        "citations",
                        "citacoes",
                        "evidence",
                        "evidencias"
                    ],
                    []
                )

                # --------------------------------------------
                # RESPOSTA PRINCIPAL
                # --------------------------------------------

                if is_refusal:
                    st.warning(
                        resposta
                    )
                else:
                    st.markdown(
                        resposta
                    )

                # --------------------------------------------
                # CONFIANÇA
                # --------------------------------------------

                if confidence is not None:

                    st.caption(
                        f"Confiança: {confidence}"
                    )

                # --------------------------------------------
                # EVIDÊNCIAS / CITAÇÕES
                # --------------------------------------------

                if citacoes:

                    st.markdown(
                        "#### Evidências"
                    )

                    if not isinstance(
                        citacoes,
                        list
                    ):
                        citacoes = [
                            citacoes
                        ]

                    for indice, citacao in enumerate(
                        citacoes,
                        start=1
                    ):

                        with st.expander(
                            f"Evidência {indice}"
                        ):

                            st.write(
                                formatar_citacao(
                                    citacao
                                )
                            )

                # --------------------------------------------
                # DETALHES TÉCNICOS
                # --------------------------------------------

                with st.expander(
                    "Detalhes técnicos"
                ):

                    st.json(
                        dados
                    )

                st.session_state.mensagens.append(
                    {
                        "role": "assistant",
                        "content": resposta,
                        "details": dados
                    }
                )

            except Exception as erro:

                mensagem_erro = (
                    "Não foi possível processar a pergunta. "
                    f"Detalhes técnicos: {erro}"
                )

                st.error(
                    mensagem_erro
                )

                st.session_state.mensagens.append(
                    {
                        "role": "assistant",
                        "content": mensagem_erro
                    }
                )
