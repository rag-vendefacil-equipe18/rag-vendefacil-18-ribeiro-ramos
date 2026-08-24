
from pathlib import Path
import json
import pandas as pd

from langchain_core.documents import Document


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def limpar_valor(valor):
    """
    Converte valores ausentes em string vazia
    e padroniza os demais como texto.
    """
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def criar_metadata_base(
    caminho: Path,
    doc_type: str,
    chunk_id: str,
    sensitivity: str = "interno",
):
    """
    Metadados mínimos exigidos para todos os chunks.
    """
    return {
        "source_file": str(caminho),
        "doc_type": doc_type,
        "chunk_id": chunk_id,
        "sensitivity": sensitivity,
    }


def serializar_registro(registro: dict) -> str:
    """
    Transforma um registro estruturado em texto
    compreensível pelo modelo de embeddings.
    """
    partes = []

    for chave, valor in registro.items():

        if valor is None:
            continue

        if isinstance(valor, list):
            valor = ", ".join(str(item) for item in valor)

        elif isinstance(valor, dict):
            valor = "; ".join(
                f"{k}: {v}"
                for k, v in valor.items()
            )

        partes.append(f"{chave}: {valor}")

    return ". ".join(partes) + "."


# ============================================================
# CUSTOMERS.CSV
# 1 cliente = 1 chunk
# ============================================================

def carregar_customers(caminho: Path):

    df = pd.read_csv(caminho)
    documentos = []

    for _, row in df.iterrows():

        customer_id = limpar_valor(row["customer_id"])

        texto = (
            f"Cliente {customer_id}: {limpar_valor(row['company_name'])}. "
            f"CNPJ: {limpar_valor(row['cnpj'])}. "
            f"Localização: {limpar_valor(row['city'])}, "
            f"{limpar_valor(row['state'])}. "
            f"Segmento: {limpar_valor(row['segment'])}. "
            f"Plano: {limpar_valor(row['plan'])}. "
            f"Produto principal: {limpar_valor(row['main_product'])}. "
            f"MRR: R$ {limpar_valor(row['mrr'])}. "
            f"Status: {limpar_valor(row['status'])}. "
            f"E-mail de contato: {limpar_valor(row['contact_email'])}."
        )

        metadata = criar_metadata_base(
            caminho=caminho,
            doc_type="customer",
            chunk_id=f"customers_{customer_id}",
            sensitivity="interno",
        )

        metadata.update({
            "customer_id": customer_id,
            "state": limpar_valor(row["state"]),
            "status": limpar_valor(row["status"]),
            "plan": limpar_valor(row["plan"]),
        })

        documentos.append(
            Document(
                page_content=texto,
                metadata=metadata,
            )
        )

    return documentos


# ============================================================
# EMPLOYEES.CSV
# 1 funcionário = 1 chunk
#
# O arquivo possui informações sensíveis, inclusive salário.
# Mantemos o conteúdo para permitir os testes de LGPD
# das próximas etapas, mas classificamos como "restrito".
# ============================================================

def carregar_employees(caminho: Path):

    df = pd.read_csv(caminho)
    documentos = []

    for _, row in df.iterrows():

        employee_id = limpar_valor(row["id"])

        texto = (
            f"Funcionário {employee_id}: {limpar_valor(row['name'])}. "
            f"E-mail: {limpar_valor(row['email'])}. "
            f"Departamento: {limpar_valor(row['department'])}. "
            f"Cargo: {limpar_valor(row['role'])}. "
            f"Data de contratação: {limpar_valor(row['hire_date'])}. "
            f"Salário: R$ {limpar_valor(row['salary'])}. "
            f"Status: {limpar_valor(row['status'])}."
        )

        metadata = criar_metadata_base(
            caminho=caminho,
            doc_type="employee",
            chunk_id=f"employees_{employee_id}",
            sensitivity="restrito",
        )

        metadata.update({
            "department": limpar_valor(row["department"]),
            "status": limpar_valor(row["status"]),
        })

        documentos.append(
            Document(
                page_content=texto,
                metadata=metadata,
            )
        )

    return documentos


# ============================================================
# SALES.CSV
# 1 venda = 1 chunk
# ============================================================

def carregar_sales(caminho: Path):

    df = pd.read_csv(caminho)
    documentos = []

    for _, row in df.iterrows():

        sale_id = limpar_valor(row["sale_id"])
        customer_id = limpar_valor(row["customer_id"])

        texto = (
            f"Venda {sale_id}. "
            f"Cliente: {customer_id} - {limpar_valor(row['company_name'])}. "
            f"Loja: {limpar_valor(row['store_id'])} - "
            f"{limpar_valor(row['store_name'])}. "
            f"Localização: {limpar_valor(row['city'])}, "
            f"{limpar_valor(row['state'])}. "
            f"Produto: {limpar_valor(row['product_id'])} - "
            f"{limpar_valor(row['product_name'])}. "
            f"Data: {limpar_valor(row['date'])}. "
            f"Forma de pagamento: {limpar_valor(row['payment_method'])}. "
            f"Valor: R$ {limpar_valor(row['amount_brl'])}. "
            f"Terminal: {limpar_valor(row['pos_terminal'])}. "
            f"Status: {limpar_valor(row['status'])}."
        )

        metadata = criar_metadata_base(
            caminho=caminho,
            doc_type="sale",
            chunk_id=f"sales_{sale_id}",
            sensitivity="interno",
        )

        metadata.update({
            "customer_id": customer_id,
            "state": limpar_valor(row["state"]),
            "date": limpar_valor(row["date"]),
            "status": limpar_valor(row["status"]),
        })

        documentos.append(
            Document(
                page_content=texto,
                metadata=metadata,
            )
        )

    return documentos


# ============================================================
# SYSTEM_LOGS.CSV
# 1 evento de log = 1 chunk
# ============================================================

def carregar_logs(caminho: Path):

    df = pd.read_csv(caminho)
    documentos = []

    for indice, row in df.iterrows():

        texto = (
            f"Log do serviço {limpar_valor(row['service'])}. "
            f"Data e hora: {limpar_valor(row['timestamp'])}. "
            f"Nível: {limpar_valor(row['level'])}. "
            f"Módulo: {limpar_valor(row['module'])}. "
            f"Cliente: {limpar_valor(row['customer_id'])}. "
            f"Evento: {limpar_valor(row['event'])}. "
            f"Código de erro: {limpar_valor(row['error_code'])}. "
            f"Mensagem: {limpar_valor(row['message'])}."
        )

        metadata = criar_metadata_base(
            caminho=caminho,
            doc_type="log",
            chunk_id=f"system_logs_{indice:05d}",
            sensitivity="interno",
        )

        metadata.update({
            "customer_id": limpar_valor(row["customer_id"]),
            "module": limpar_valor(row["module"]).lower(),
            "level": limpar_valor(row["level"]),
            "error_code": limpar_valor(row["error_code"]),
            "date": limpar_valor(row["timestamp"]),
        })

        documentos.append(
            Document(
                page_content=texto,
                metadata=metadata,
            )
        )

    return documentos


# ============================================================
# PRODUCTS.JSON
#
# O JSON possui:
# - informações gerais
# - pricing_plans
# - products
#
# Cada produto = 1 chunk.
# Cada plano de preço = 1 chunk.
# ============================================================

def carregar_products(caminho: Path):

    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)

    documentos = []

    company = dados.get("company", "")
    last_updated = dados.get("last_updated", "")

    # --------------------------------------------------------
    # Produtos
    # --------------------------------------------------------

    for produto in dados.get("products", []):

        product_id = produto["product_id"]

        texto = (
            f"Produto {product_id}: {produto.get('name', '')}. "
            f"Categoria: {produto.get('category', '')}. "
            f"Descrição: {produto.get('description', '')}. "
            f"Tech lead: {produto.get('tech_lead', '')}. "
            f"Product manager: {produto.get('product_manager', '')}. "
            f"Preço mensal avulso: R$ "
            f"{produto.get('standalone_monthly_price_brl', '')}. "
            f"Funcionalidades: "
            f"{', '.join(produto.get('features', []))}. "
            f"Sistemas suportados: "
            f"{', '.join(produto.get('supported_os', []))}. "
            f"SLA de disponibilidade: {produto.get('sla_uptime', '')}."
        )

        # Ex.: PROD-ESTOQUE -> estoque
        module = product_id.replace("PROD-", "").lower()

        metadata = criar_metadata_base(
            caminho=caminho,
            doc_type="product",
            chunk_id=f"products_{product_id}",
            sensitivity="interno",
        )

        metadata.update({
            "module": module,
            "record_type": "product",
            "date": last_updated,
        })

        documentos.append(
            Document(
                page_content=texto,
                metadata=metadata,
            )
        )

    # --------------------------------------------------------
    # Planos de preço
    # --------------------------------------------------------

    for plano, dados_plano in dados.get(
        "pricing_plans", {}
    ).items():

        texto = (
            f"Plano {plano} da {company}. "
            f"Mensalidade: R$ "
            f"{dados_plano.get('monthly_fee_brl', '')}. "
            f"Terminais incluídos: "
            f"{dados_plano.get('included_terminals', '')}. "
            f"Valor por terminal adicional: R$ "
            f"{dados_plano.get('extra_terminal_fee_brl', '')}. "
            f"Descrição: {dados_plano.get('description', '')}."
        )

        metadata = criar_metadata_base(
            caminho=caminho,
            doc_type="product",
            chunk_id=f"products_plan_{plano.lower()}",
            sensitivity="interno",
        )

        metadata.update({
            "plan": plano,
            "record_type": "pricing_plan",
            "date": last_updated,
        })

        documentos.append(
            Document(
                page_content=texto,
                metadata=metadata,
            )
        )

    return documentos


# ============================================================
# STORES.JSON
# 1 loja = 1 chunk
# ============================================================

def carregar_stores(caminho: Path):

    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)

    documentos = []

    for loja in dados.get("network_stores", []):

        store_id = loja["store_id"]

        modulos = loja.get("active_modules", [])

        texto = (
            f"Loja {store_id}: {loja.get('store_name', '')}. "
            f"Cliente: {loja.get('customer_id', '')} - "
            f"{loja.get('company_name', '')}. "
            f"Localização: {loja.get('city', '')}, "
            f"{loja.get('state', '')}. "
            f"Quantidade de terminais POS: "
            f"{loja.get('pos_terminals_count', '')}. "
            f"Módulos ativos: {', '.join(modulos)}."
        )

        metadata = criar_metadata_base(
            caminho=caminho,
            doc_type="store",
            chunk_id=f"stores_{store_id}",
            sensitivity="interno",
        )

        metadata.update({
            "customer_id": loja.get("customer_id", ""),
            "state": loja.get("state", ""),
            "modules": ",".join(
                modulo
                .replace("VendeFácil ", "")
                .lower()
                for modulo in modulos
            ),
        })

        documentos.append(
            Document(
                page_content=texto,
                metadata=metadata,
            )
        )

    return documentos


# ============================================================
# TICKETS.JSONL
# 1 ticket = 1 chunk
# ============================================================

def carregar_tickets(caminho: Path):

    documentos = []

    with open(caminho, "r", encoding="utf-8") as f:

        for linha in f:

            if not linha.strip():
                continue

            ticket = json.loads(linha)

            ticket_id = ticket["ticket_id"]

            texto = (
                f"Ticket {ticket_id}: "
                f"{ticket.get('title', '')}. "
                f"Cliente: {ticket.get('customer_name', '')} "
                f"({ticket.get('customer_id', '')}). "
                f"Estado: {ticket.get('state', '')}. "
                f"Módulo: {ticket.get('module', '')}. "
                f"Categoria: {ticket.get('category', '')}. "
                f"Prioridade: {ticket.get('priority', '')}. "
                f"Status: {ticket.get('status', '')}. "
                f"Data de criação: "
                f"{ticket.get('created_at', '')}. "
                f"Descrição: {ticket.get('description', '')}."
            )

            if ticket.get("resolution"):
                texto += (
                    f" Resolução: {ticket['resolution']}."
                )

            if ticket.get("sentiment"):
                texto += (
                    f" Sentimento do cliente: "
                    f"{ticket['sentiment']}."
                )

            metadata = criar_metadata_base(
                caminho=caminho,
                doc_type="ticket",
                chunk_id=f"tickets_{ticket_id}",
                sensitivity="interno",
            )

            metadata.update({
                "customer_id": ticket.get(
                    "customer_id", ""
                ),
                "state": ticket.get(
                    "state", ""
                ),
                "module": ticket.get(
                    "module", ""
                ).lower(),
                "priority": ticket.get(
                    "priority", ""
                ),
                "status": ticket.get(
                    "status", ""
                ),
                "date": ticket.get(
                    "created_at", ""
                ),
            })

            documentos.append(
                Document(
                    page_content=texto,
                    metadata=metadata,
                )
            )

    return documentos


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def carregar_documentos_estruturados():

    documentos = []

    documentos.extend(
        carregar_customers(
            Path("data/structured/customers.csv")
        )
    )

    documentos.extend(
        carregar_employees(
            Path("data/structured/employees.csv")
        )
    )

    documentos.extend(
        carregar_sales(
            Path("data/structured/sales.csv")
        )
    )

    documentos.extend(
        carregar_logs(
            Path(
                "data/semi_structured/system_logs.csv"
            )
        )
    )

    documentos.extend(
        carregar_products(
            Path("data/structured/products.json")
        )
    )

    documentos.extend(
        carregar_stores(
            Path("data/structured/stores.json")
        )
    )

    documentos.extend(
        carregar_tickets(
            Path(
                "data/semi_structured/tickets.jsonl"
            )
        )
    )

    return documentos


# ============================================================
# TESTE LOCAL
# ============================================================

if __name__ == "__main__":

    documentos = carregar_documentos_estruturados()

    print(
        f"Total de chunks gerados: "
        f"{len(documentos)}"
    )

    for doc in documentos[:5]:

        print("\n" + "=" * 70)

        print("TEXTO:")
        print(doc.page_content[:500])

        print("\nMETADADOS:")
        print(doc.metadata)
