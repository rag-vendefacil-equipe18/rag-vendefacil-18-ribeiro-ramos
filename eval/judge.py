import json
import os
import google.generativeai as genai
from eval.judge_prompt import PROMPT_ANSWER_RELEVANCE, PROMPT_GROUNDEDNESS

# Configuração do LLM (Garante que ele retorne um JSON válido)
# Certifique-se de que a variável de ambiente GEMINI_API_KEY esteja configurada no seu sistema
model = genai.GenerativeModel(
    'gemini-1.5-flash',
    generation_config={"response_mime_type": "application/json"}
)

def evaluate_answer_relevance(pergunta: str, resposta: str) -> dict:
    """Mede se a resposta atendeu ao que foi perguntado."""
    prompt = PROMPT_ANSWER_RELEVANCE.format(pergunta=pergunta, resposta=resposta)
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"Erro no LLM-as-judge (Answer Relevance): {e}")
        return {"score": 0, "justificativa": "Erro na avaliação."}

def evaluate_groundedness(contexto: str, resposta: str) -> dict:
    """Mede se a resposta se apoia estritamente nos documentos recuperados."""
    prompt = PROMPT_GROUNDEDNESS.format(contexto=contexto, resposta=resposta)
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"Erro no LLM-as-judge (Groundedness): {e}")
        return {"score": 0, "justificativa": "Erro na avaliação."}
