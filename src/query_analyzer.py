
import re
import unicodedata
from typing import Optional


# ============================================================
# VOCABULÁRIO PERMITIDO
# ============================================================

VALID_DOC_TYPES = {
    "customer",
    "employee",
    "product",
    "store",
    "ticket",
    "log",
    "manual",
    "ata",
    "policy",
    "email",
}

VALID_STATES = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES",
    "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR",
    "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
}

VALID_MODULES = {
    "estoque",
    "pdv",
    "pay",
    "ecommerce",
    "analytics",
}

VALID_PRIORITIES = {
    "baixa",
    "media",
    "alta",
    "critica",
}


# ============================================================
# SINÔNIMOS DE ESTADOS
# ============================================================

STATE_SYNONYMS = {
    "acre": "AC",
    "ac": "AC",

    "alagoas": "AL",
    "al": "AL",

    "amapa": "AP",
    "ap": "AP",

    "amazonas": "AM",
    "am": "AM",

    "bahia": "BA",
    "ba": "BA",

    "ceara": "CE",
    "ce": "CE",

    "distrito federal": "DF",
    "df": "DF",

    "espirito santo": "ES",
    "es": "ES",

    "goias": "GO",
    "go": "GO",

    "maranhao": "MA",
    "ma": "MA",

    "mato grosso": "MT",
    "mt": "MT",

    "mato grosso do sul": "MS",
    "ms": "MS",

    "minas gerais": "MG",
    "mg": "MG",

    "para": "PA",
    "pa": "PA",

    "paraiba": "PB",
    "pb": "PB",

    "parana": "PR",
    "pr": "PR",

    "pernambuco": "PE",
    "pe": "PE",

    "piaui": "PI",
    "pi": "PI",

    "rio de janeiro": "RJ",
    "rj": "RJ",

    "rio grande do norte": "RN",
    "rn": "RN",

    "rio grande do sul": "RS",
    "rs": "RS",

    "rondonia": "RO",
    "ro": "RO",

    "roraima": "RR",
    "rr": "RR",

    "santa catarina": "SC",
    "sc": "SC",

    "sao paulo": "SP",
    "sp": "SP",

    "sergipe": "SE",
    "se": "SE",

    "tocantins": "TO",
    "to": "TO",
}


# ============================================================
# SINÔNIMOS DE MÓDULOS
# ============================================================

MODULE_SYNONYMS = {
    "controle de estoque": "estoque",
    "gestao de estoque": "estoque",
    "estoque": "estoque",

    "ponto de venda": "pdv",
    "frente de caixa": "pdv",
    "pdv": "pdv",

    "pagamentos": "pay",
    "pagamento": "pay",
    "vendefacil pay": "pay",
    "pay": "pay",

    "e-commerce": "ecommerce",
    "e commerce": "ecommerce",
    "loja virtual": "ecommerce",
    "ecommerce": "ecommerce",

    "analises": "analytics",
    "analise": "analytics",
    "relatorios": "analytics",
    "analytics": "analytics",
}


# ============================================================
# SINÔNIMOS DE PRIORIDADE
# ============================================================

PRIORITY_SYNONYMS = {
    "baixa prioridade": "baixa",
    "prioridade baixa": "baixa",
    "baixas": "baixa",
    "baixos": "baixa",
    "baixa": "baixa",
    "baixo": "baixa",

    "media prioridade": "media",
    "prioridade media": "media",
    "medias": "media",
    "medios": "media",
    "media": "media",
    "medio": "media",

    "alta prioridade": "alta",
    "prioridade alta": "alta",
    "altas": "alta",
    "altos": "alta",
    "alta": "alta",
    "alto": "alta",

    "critica prioridade": "critica",
    "prioridade critica": "critica",
    "criticas": "critica",
    "criticos": "critica",
    "critica": "critica",
    "critico": "critica",
}


# ============================================================
# SINÔNIMOS DE STATUS
# ============================================================

STATUS_SYNONYMS = {
    "abertos": "Aberto",
    "abertas": "Aberto",
    "aberto": "Aberto",
    "aberta": "Aberto",

    "fechados": "Fechado",
    "fechadas": "Fechado",
    "fechado": "Fechado",
    "fechada": "Fechado",

    "resolvidos": "Resolvido",
    "resolvidas": "Resolvido",
    "resolvido": "Resolvido",
    "resolvida": "Resolvido",

    "pendentes": "Pendente",
    "pendente": "Pendente",

    "ativos": "Ativo",
    "ativas": "Ativo",
    "ativo": "Ativo",
    "ativa": "Ativo",

    "inativos": "Inativo",
    "inativas": "Inativo",
    "inativo": "Inativo",
    "inativa": "Inativo",
}


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto para facilitar as comparações.

    - converte para minúsculas;
    - remove acentos;
    - remove espaços duplicados.
    """

    texto = str(texto).lower().strip()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto


# ============================================================
# BUSCA DE SINÔNIMOS
# ============================================================

def encontrar_sinonimo(
    texto: str,
    dicionario: dict
) -> Optional[str]:
    """
    Procura palavras ou expressões completas.
    Expressões maiores são verificadas primeiro.
    """

    termos = sorted(
        dicionario.keys(),
        key=len,
        reverse=True
    )

    for termo in termos:

        termo_normalizado = normalizar_texto(
            termo
        )

        padrao = (
            rf"(?<!\w)"
            rf"{re.escape(termo_normalizado)}"
            rf"(?!\w)"
        )

        if re.search(padrao, texto):
            return dicionario[termo]

    return None


# ============================================================
# EXTRAÇÃO DE STATE
# ============================================================

def extrair_state(texto: str) -> Optional[str]:

    valor = encontrar_sinonimo(
        texto,
        STATE_SYNONYMS
    )

    if valor in VALID_STATES:
        return valor

    return None


# ============================================================
# EXTRAÇÃO DE MODULE
# ============================================================

def extrair_module(texto: str) -> Optional[str]:

    valor = encontrar_sinonimo(
        texto,
        MODULE_SYNONYMS
    )

    if valor in VALID_MODULES:
        return valor

    return None


# ============================================================
# EXTRAÇÃO DE DOC_TYPE
# ============================================================

def extrair_doc_type(texto: str) -> Optional[str]:
    """
    Identifica o tipo principal de documento solicitado.

    A lógica evita interpretar "clientes" como customer
    quando a palavra aparece apenas como complemento.

    Exemplo:
    "tickets de clientes de MG"
    -> ticket

    "problemas para clientes de SP"
    -> nenhum doc_type específico

    "quais clientes de SP estão ativos?"
    -> customer
    """

    # --------------------------------------------------------
    # Tipos explícitos de documento
    # --------------------------------------------------------

    prioridades = [
        (
            "ticket",
            ["tickets", "ticket", "chamados", "chamado"]
        ),
        (
            "log",
            ["logs", "log"]
        ),
        (
            "policy",
            ["politicas", "politica"]
        ),
        (
            "manual",
            ["manuais", "manual"]
        ),
        (
            "ata",
            ["atas", "ata"]
        ),
        (
            "email",
            ["emails", "email"]
        ),
        (
            "product",
            ["produtos", "produto"]
        ),
        (
            "store",
            ["lojas", "loja"]
        ),
        (
            "employee",
            ["funcionarios", "funcionario"]
        ),
    ]

    for doc_type, termos in prioridades:

        for termo in termos:

            padrao = (
                rf"(?<!\w)"
                rf"{re.escape(termo)}"
                rf"(?!\w)"
            )

            if re.search(padrao, texto):

                if doc_type in VALID_DOC_TYPES:
                    return doc_type

    # --------------------------------------------------------
    # CUSTOMER É TRATADO SEPARADAMENTE
    # --------------------------------------------------------
    #
    # Só inferimos customer quando a pergunta claramente
    # solicita os próprios clientes.
    #
    # Evita:
    # "tickets de clientes"
    # "problemas para clientes"
    # "erros dos clientes"
    # --------------------------------------------------------

    padroes_customer = [
        r"\bquais clientes\b",
        r"\bqual cliente\b",
        r"\bliste os clientes\b",
        r"\blistar clientes\b",
        r"\bmostre os clientes\b",
        r"\bmostrar clientes\b",
        r"\bdados dos clientes\b",
        r"\binformacoes dos clientes\b",
        r"\bcadastro de clientes\b",
    ]

    for padrao in padroes_customer:

        if re.search(padrao, texto):
            return "customer"

    return None


# ============================================================
# EXTRAÇÃO DE PRIORITY
# ============================================================

def extrair_priority(texto: str) -> Optional[str]:

    valor = encontrar_sinonimo(
        texto,
        PRIORITY_SYNONYMS
    )

    if valor in VALID_PRIORITIES:
        return valor

    return None


# ============================================================
# EXTRAÇÃO DE STATUS
# ============================================================

def extrair_status(texto: str) -> Optional[str]:

    return encontrar_sinonimo(
        texto,
        STATUS_SYNONYMS
    )


# ============================================================
# QUERY ANALYZER
# ============================================================

def analisar_pergunta(pergunta: str) -> dict:
    """
    Recebe uma pergunta em linguagem natural e extrai
    os filtros estruturados identificados.
    """

    texto = normalizar_texto(
        pergunta
    )

    filtros = {}

    state = extrair_state(texto)
    module = extrair_module(texto)
    doc_type = extrair_doc_type(texto)
    priority = extrair_priority(texto)
    status = extrair_status(texto)

    if state:
        filtros["state"] = state

    if module:
        filtros["module"] = module

    if doc_type:
        filtros["doc_type"] = doc_type

    if priority:
        filtros["priority"] = (
            priority.capitalize()
        )

    if status:
        filtros["status"] = status

    return filtros


# ============================================================
# VALORES EXISTENTES NOS DOCUMENTOS
# ============================================================

def obter_valores_validos(documentos) -> dict:
    """
    Obtém os valores realmente existentes nos metadados
    dos documentos carregados.
    """

    campos = [
        "doc_type",
        "state",
        "module",
        "priority",
        "status",
    ]

    valores_validos = {}

    for campo in campos:

        valores_validos[campo] = {
            normalizar_texto(
                str(doc.metadata[campo])
            )
            for doc in documentos
            if doc.metadata.get(campo)
            not in (None, "")
        }

    return valores_validos


# ============================================================
# VALIDAÇÃO DOS FILTROS
# ============================================================

def validar_filtros(
    filtros: dict,
    documentos
) -> dict:
    """
    Mantém somente filtros cujos valores realmente
    existem nos metadados dos documentos.
    """

    valores_validos = obter_valores_validos(
        documentos
    )

    filtros_validados = {}

    for campo, valor in filtros.items():

        if campo not in valores_validos:
            continue

        valor_normalizado = normalizar_texto(
            str(valor)
        )

        if (
            valor_normalizado
            in valores_validos[campo]
        ):
            filtros_validados[campo] = valor

    return filtros_validados


# ============================================================
# ANALISAR + VALIDAR
# ============================================================

def analisar_e_validar(
    pergunta: str,
    documentos
) -> dict:
    """
    Fluxo completo do Query Analyzer:

    pergunta
        ↓
    normalização
        ↓
    extração
        ↓
    validação contra valores reais
        ↓
    filtros finais
    """

    filtros = analisar_pergunta(
        pergunta
    )

    return validar_filtros(
        filtros,
        documentos
    )


# ============================================================
# TESTE LOCAL
# ============================================================

if __name__ == "__main__":

    perguntas = [
        (
            "Quais tickets de clientes de Minas Gerais "
            "estão relacionados ao módulo de estoque?"
        ),
        (
            "Quais problemas do módulo de pagamento "
            "aparecem para clientes de São Paulo?"
        ),
        (
            "Quais tickets críticos do módulo PDV existem "
            "para clientes do Rio de Janeiro?"
        ),
        (
            "Quais chamados de alta prioridade "
            "existem em MG?"
        ),
        (
            "Quais políticas falam sobre segurança?"
        ),
        (
            "Mostre os produtos relacionados ao estoque."
        ),
        (
            "Quais clientes de Minas Gerais estão ativos?"
        ),
    ]

    for pergunta in perguntas:

        print("\n" + "=" * 80)

        print("PERGUNTA:")
        print(pergunta)

        print("FILTROS:")
        print(
            analisar_pergunta(pergunta)
        )
