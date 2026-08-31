# --- eval/judge_prompt.py ---

# Rubrica para Answer Relevance (Relevância da Resposta)
PROMPT_ANSWER_RELEVANCE = """
Você é um juiz rigoroso avaliando um sistema de IA.
Sua tarefa é avaliar a RELEVÂNCIA DA RESPOSTA (Answer Relevance).

Pergunta do Usuário: {pergunta}
Resposta da IA: {resposta}

A resposta fornecida atendeu de forma direta e correta ao que foi perguntado? 
Responda APENAS com um objeto JSON válido, sem formatação markdown adicional, contendo:
- "score": 1 (se atendeu plenamente) ou 0 (se não atendeu, foi evasiva ou incorreta).
- "justificativa": "Uma explicação curta de no máximo 2 linhas justificando a nota."
"""

# Rubrica para Groundedness (Fundamentação)
PROMPT_GROUNDEDNESS = """
Você é um juiz rigoroso avaliando um sistema RAG (Retrieval-Augmented Generation).
Sua tarefa é avaliar a FUNDAMENTAÇÃO (Groundedness) da resposta gerada.

Contexto Recuperado do Banco de Dados:
{contexto}

Resposta gerada pela IA: 
{resposta}

Avalie: Cada afirmação presente na resposta da IA está estritamente sustentada pelos trechos citados no contexto? A IA inventou ou deduziu alguma informação (alucinação)?
Responda APENAS com um objeto JSON válido, sem formatação markdown adicional, contendo:
- "score": 1 (se está 100% fundamentada no contexto) ou 0 (se há qualquer nível de alucinação ou informação não presente no contexto).
- "justificativa": "Uma explicação curta focada em apontar qual informação faltou no contexto ou sobrou na resposta."
"""
