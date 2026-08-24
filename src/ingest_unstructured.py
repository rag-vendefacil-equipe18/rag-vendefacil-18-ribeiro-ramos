
from pathlib import Path
import re

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from pypdf import PdfReader


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def identificar_doc_type(caminho: Path) -> str:
    """Identifica o tipo de documento pela pasta de origem."""

    partes = [parte.lower() for parte in caminho.parts]

    if "documentation" in partes:
        return "manual"

    if "meetings" in partes:
        return "ata"

    if "policies" in partes:
        return "policy"

    if "emails" in partes:
        return "email"

    return "outro"


def identificar_sensibilidade(caminho: Path) -> str:
    """Define uma classificação inicial de sensibilidade."""

    doc_type = identificar_doc_type(caminho)

    if doc_type == "email":
        return "restrito"

    return "interno"


def criar_metadata_base(caminho: Path, chunk_id: str) -> dict:
    """Cria os metadados básicos de cada chunk."""

    return {
        "source_file": str(caminho),
        "doc_type": identificar_doc_type(caminho),
        "chunk_id": chunk_id,
        "sensitivity": identificar_sensibilidade(caminho),
    }


# ============================================================
# LOADER MARKDOWN
# ============================================================

def carregar_markdown(caminho: Path) -> list[Document]:
    """
    Carrega Markdown preservando títulos e seções.
    Se uma seção for muito grande, aplica divisão recursiva.
    """

    texto = caminho.read_text(
        encoding="utf-8",
        errors="replace"
    )

    headers_to_split_on = [
        ("#", "titulo"),
        ("##", "secao"),
        ("###", "subsecao"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )

    secoes = markdown_splitter.split_text(texto)

    tamanho_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    documentos = []
    indice = 0

    for secao in secoes:

        if len(secao.page_content) > 1200:
            partes = tamanho_splitter.split_text(secao.page_content)
        else:
            partes = [secao.page_content]

        for parte in partes:

            if not parte.strip():
                continue

            chunk_id = f"{caminho.stem}_md_{indice:04d}"

            metadata = criar_metadata_base(
                caminho,
                chunk_id
            )

            section = (
                secao.metadata.get("subsecao")
                or secao.metadata.get("secao")
                or secao.metadata.get("titulo")
            )

            if section:
                metadata["section"] = section

            documentos.append(
                Document(
                    page_content=parte.strip(),
                    metadata=metadata,
                )
            )

            indice += 1

    return documentos


# ============================================================
# LOADER PDF
# ============================================================

def carregar_pdf(caminho: Path) -> list[Document]:
    """
    Extrai o texto de cada página do PDF e aplica
    chunking recursivo.
    """

    reader = PdfReader(str(caminho))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    documentos = []
    indice = 0

    for numero_pagina, pagina in enumerate(
        reader.pages,
        start=1
    ):

        texto = pagina.extract_text() or ""

        if not texto.strip():
            continue

        partes = splitter.split_text(texto)

        for parte in partes:

            if not parte.strip():
                continue

            chunk_id = f"{caminho.stem}_pdf_{indice:04d}"

            metadata = criar_metadata_base(
                caminho,
                chunk_id
            )

            metadata["page"] = numero_pagina

            documentos.append(
                Document(
                    page_content=parte.strip(),
                    metadata=metadata,
                )
            )

            indice += 1

    return documentos


# ============================================================
# LOADER TXT
# ============================================================

def separar_mensagens_email(texto: str) -> list[str]:
    """
    Tenta separar threads de e-mail em mensagens individuais.
    """

    padrao = r"(?=^(?:From|De|Remetente|Sender):)"

    mensagens = re.split(
        padrao,
        texto,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    mensagens = [
        mensagem.strip()
        for mensagem in mensagens
        if mensagem.strip()
    ]

    if not mensagens:
        return [texto.strip()]

    return mensagens


def carregar_txt(caminho: Path) -> list[Document]:
    """
    Carrega TXT tentando preservar cada mensagem de e-mail
    como uma unidade antes de aplicar chunking por tamanho.
    """

    texto = caminho.read_text(
        encoding="utf-8",
        errors="replace"
    )

    mensagens = separar_mensagens_email(texto)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    documentos = []
    indice = 0

    for numero_mensagem, mensagem in enumerate(
        mensagens,
        start=1
    ):

        if len(mensagem) > 1200:
            partes = splitter.split_text(mensagem)
        else:
            partes = [mensagem]

        for parte in partes:

            if not parte.strip():
                continue

            chunk_id = f"{caminho.stem}_txt_{indice:04d}"

            metadata = criar_metadata_base(
                caminho,
                chunk_id
            )

            metadata["message_index"] = numero_mensagem

            documentos.append(
                Document(
                    page_content=parte.strip(),
                    metadata=metadata,
                )
            )

            indice += 1

    return documentos


# ============================================================
# CARREGAR TODOS OS DOCUMENTOS NÃO ESTRUTURADOS
# ============================================================

def carregar_documentos_nao_estruturados(
    pasta="data/unstructured"
) -> list[Document]:

    pasta = Path(pasta)

    documentos = []

    # Markdown
    for caminho in pasta.rglob("*.md"):
        documentos.extend(
            carregar_markdown(caminho)
        )

    # PDF
    for caminho in pasta.rglob("*.pdf"):
        documentos.extend(
            carregar_pdf(caminho)
        )

    # TXT
    for caminho in pasta.rglob("*.txt"):
        documentos.extend(
            carregar_txt(caminho)
        )

    return documentos


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    documentos = carregar_documentos_nao_estruturados()

    print(
        f"Total de chunks gerados: {len(documentos)}"
    )

    for doc in documentos[:5]:

        print("\n" + "=" * 70)

        print("TEXTO:")
        print(doc.page_content[:500])

        print("\nMETADADOS:")
        print(doc.metadata)
