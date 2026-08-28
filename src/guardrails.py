import re

def verificar_fora_de_escopo(pergunta: str) -> dict:
    """Identifica se a pergunta está fora do domínio da VendeFácil."""
    termos_fora = ["receita de bolo", "futebol", "previsão do tempo", "política", "filme"]
    pergunta_lower = pergunta.lower()
    
    for termo in termos_fora:
        if termo in pergunta_lower:
            return {
                "permitido": False,
                "refusal_reason": "fora_de_escopo",
                "mensagem": "Desculpe, mas só posso responder dúvidas relacionadas aos sistemas, logs e operações da VendeFácil."
            }
    return {"permitido": True}

def aplicar_guardrails_lgpd(texto: str) -> dict:
    """Aplica as regras de mascaramento ou recusa (LGPD)."""
    texto_lower = texto.lower()

    # 1. RECUSAR (Credenciais, Saúde, CPF, Finanças e PIX)
    termos_recusa = ["senha", "password", "token", "credencial", "diagnóstico", "doença", "prontuário", "salário", "remuneração"]
    if any(termo in texto_lower for termo in termos_recusa):
        return {
            "status": "recusado",
            "motivo": "Violação de política: presença de credenciais, termos de saúde ou financeiros.",
            "resposta_segura": None
        }

    # Bloqueio imediato se encontrar CPF, Salário (R$) ou PIX/Banco via Regex
    if re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', texto) or \
       re.search(r'[Rr]\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?', texto) or \
       re.search(r'(?i)(pix:|agência|conta bancária)[ \t]*[\w\.-]+', texto):
        return {
            "status": "recusado",
            "motivo": "Violação de política: identificação direta de CPF, valores financeiros ou dados bancários/PIX.",
            "resposta_segura": None
        }

    # 2. MASCARAR (E-mail, telefone, endereço, cartão de crédito)
    texto_mascarado = texto
    texto_mascarado = re.sub(r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}', '****.****.****.****', texto_mascarado)
    texto_mascarado = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[E-MAIL_REMOVIDO]', texto_mascarado)
    texto_mascarado = re.sub(r'\(\d{2}\)\s?\d{4,5}-\d{4}', '(__) _____-____', texto_mascarado)
    texto_mascarado = re.sub(r'(?i)(rua|avenida|av\.)[ \t]+[A-Za-z0-9 ]+', r'\1 [ENDEREÇO_OCULTO]', texto_mascarado)

    # 3. RESPONDER
    return {
        "status": "mascarado" if texto_mascarado != texto else "permitido",
        "resposta_segura": texto_mascarado
    }
