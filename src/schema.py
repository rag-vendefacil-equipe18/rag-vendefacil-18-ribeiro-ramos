"""
Modelos Pydantic utilizados na saída estruturada do Assistente RAG
da VendeFácil.

A resposta final deve sempre ser validada por este schema antes
de ser apresentada ao usuário.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SourceEvidence(BaseModel):
    """
    Evidência utilizada para fundamentar uma resposta do RAG.
    """

    filepath: str = Field(
        ...,
        description="Arquivo de origem do trecho citado",
    )

    chunk_id: str = Field(
        ...,
        description="Identificador único do chunk recuperado",
    )

    quotation: str = Field(
        ...,
        max_length=500,
        description="Trecho literal que sustenta a resposta",
    )


class RAGResponse(BaseModel):
    """
    Estrutura obrigatória da resposta final do Assistente RAG.
    """

    answer: str = Field(
        ...,
        description="Resposta final apresentada ao usuário",
    )

    confidence_level: Literal[
        "alta",
        "media",
        "baixa",
        "recusado",
    ]

    sources_used: list[SourceEvidence] = Field(
        default_factory=list,
        description="Evidências utilizadas para construir a resposta",
    )

    reasoning: str = Field(
        ...,
        description="Breve justificativa da resposta com base nas evidências",
    )

    is_refusal: bool = Field(
        ...,
        description="Indica se a consulta foi recusada",
    )

    refusal_reason: Literal[
        "lgpd",
        "fora_de_escopo",
        "sem_evidencia",
        None,
    ] = None

    @model_validator(mode="after")
    def validar_consistencia(self):
        """
        Aplica as regras de consistência exigidas para a saída do RAG.

        Recusas:
        - não podem possuir fontes;
        - devem ter confiança 'recusado';
        - devem possuir refusal_reason.

        Respostas normais:
        - precisam possuir pelo menos uma evidência;
        - não podem utilizar confiança 'recusado';
        - não devem possuir refusal_reason.
        """

        if self.is_refusal:
            if self.sources_used:
                raise ValueError(
                    "Uma resposta recusada não pode possuir sources_used."
                )

            if self.confidence_level != "recusado":
                raise ValueError(
                    "Uma resposta recusada deve possuir "
                    "confidence_level='recusado'."
                )

            if self.refusal_reason is None:
                raise ValueError(
                    "Uma resposta recusada deve possuir refusal_reason."
                )

        else:
            if not self.sources_used:
                raise ValueError(
                    "Uma resposta não recusada deve possuir "
                    "pelo menos uma evidência."
                )

            if self.confidence_level == "recusado":
                raise ValueError(
                    "Uma resposta não recusada não pode possuir "
                    "confidence_level='recusado'."
                )

            if self.refusal_reason is not None:
                raise ValueError(
                    "Uma resposta não recusada não deve possuir "
                    "refusal_reason."
                )

        return self
