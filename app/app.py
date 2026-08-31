import gradio as gr
import time

def responder_faq(mensagem, historico):
    """
    Função MOCK (Simulada). 
    Quando o pipeline de recuperação estiver pronto, substituiremos o 
    retorno desta função pela chamada real ao LangChain/Vetor.
    """
    # Resposta provisória para testarmos a tela
    resposta = f"Olá! Entendi que você perguntou: '{mensagem}'. Como a inteligência da VendeFácil ainda está sendo conectada, esta é uma resposta provisória para testes visuais!"
    
    # Pausa de 1 segundo para simular o bot "pensando"
    time.sleep(1)
    
    return resposta

# Montando a tela do chat sem o parâmetro theme
demo = gr.ChatInterface(
    fn=responder_faq,
    title="Chatbot VendeFácil 🛒",
    description="Assistente virtual para tirar dúvidas sobre a plataforma."
)

if __name__ == "__main__":
    demo.launch()
    # O share=True cria um link público acessível de qualquer lugar!
    demo.launch(share=True)
