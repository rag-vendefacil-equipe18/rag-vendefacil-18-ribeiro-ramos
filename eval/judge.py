import json
import os
from google import genai
from google.genai import types
from eval.judge_prompt import PROMPT_ANSWER_RELEVANCE, PROMPT_GROUNDEDNESS

client = genai.Client()

def evaluate_answer_relevance(pergunta: str, resposta: str) -> dict:
    """Mede se a resposta atendeu ao que foi perguntado."""
    prompt = PROMPT_ANSWER_RELEVANCE.format(pergunta=pergunta, resposta=resposta)
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Erro no LLM-as-judge (Answer Relevance): {e}")
        return {"score": 0, "justificativa": "Erro na avaliação."}

def evaluate_groundedness(contexto: str, resposta: str) -> dict:
    """Mede se a resposta se apoia estritamente nos documentos recuperados."""
    prompt = PROMPT_GROUNDEDNESS.format(contexto=contexto, resposta=resposta)
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Erro no LLM-as-judge (Groundedness): {e}")
        return {"score": 0, "justificativa": "Erro na avaliação."}
