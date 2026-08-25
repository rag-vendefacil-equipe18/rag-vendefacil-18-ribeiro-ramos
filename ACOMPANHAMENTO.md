# Acompanhamento - Mini Desafio RAG VendeFácil

**Integrante 1:** Maria Eduarda Ribeiro da Silva - [@eduardaribs](https://github.com/eduardaribs)
**Integrante 2:** Eridalgo Ramos da Silva - [@EridalgoRamos](https://github.com/EridalgoRamos)

**Repositório:** `rag-vendefacil-18-ribeiro-ramos`

---

## Como preencher

- Um bloco por encontro, em **ordem cronológica** - o encontro mais recente vai no **fim** do arquivo.
- O relato individual é escrito **pelo próprio integrante**, em primeira pessoa. Não escreva pelo colega.
- Escrever entre **17:30 e 17:40**. `commit` + `push` até as **18:00**, mesmo que o dia não tenha fechado.
- Mensagem de commit: `acompanhamento: AAAA-MM-DD`

**Um relato útil responde:** o que eu implementei, qual decisão técnica eu tomei e por quê, onde travei, e como (ou se) resolvi.

<details>
<summary>Exemplo de relato individual bom × ruim</summary>

❌ *"Trabalhei na parte de ingestão junto com meu colega. Avançamos bastante e conseguimos carregar os arquivos."*

✅ *"Implementei os loaders de CSV e JSONL em `src/ingest.py`. Decidi serializar cada linha do `customers.csv` como frase em linguagem natural em vez de manter o formato separado por vírgula, porque nos primeiros testes de similaridade os chunks CSV crus não recuperavam nada - o embedding não separa campo de valor. Travei ~40 min no `tickets.jsonl`: o `state` estava indo para o texto do chunk mas não para os metadados, então o filtro voltava vazio. Resolvi movendo a extração para antes da criação do `Document`. Usei o Claude para gerar o esqueleto do parser de JSONL; ajustei o schema de metadados na mão."*

</details>

---

## Encontro 1 - 2026-08-24

**Etapa:** 1 - Ingestão heterogênea, metadados e indexação vetorial

### Relato individual - Maria Eduarda Ribeiro da Silva

Neste encontro, fiquei responsável pela ingestão dos dados estruturados e semiestruturados nos formatos CSV, JSON e JSONL. Inicialmente, inspecionei os arquivos disponíveis no repositório para compreender sua estrutura, os campos existentes e definir a estratégia de transformação dos registros em documentos para o pipeline RAG.

Implementei o arquivo `src/ingest_structured.py`, adotando a estratégia de um registro por chunk para os dados tabulares e um ticket por chunk para o arquivo JSONL. Na serialização, transformei os registros em textos descritivos em linguagem natural, buscando preservar as informações relevantes para a recuperação por embeddings.

Também implementei e padronizei os metadados obrigatórios `source_file`, `doc_type`, `chunk_id` e `sensitivity`. Quando aplicável, acrescentei metadados específicos, como `customer_id`, `state`, `module`, `priority`, `status` e `date`. Para os registros de funcionários, defini `sensitivity` como `restrito`, considerando a presença de informações sensíveis, como dados de identificação e remuneração.

Após finalizar meu loader, integrei os documentos estruturados e semiestruturados aos documentos não estruturados implementados pelo meu colega por meio do `src/ingest.py`. O pipeline integrado resultou em 5.721 chunks. Em seguida, validei a presença dos metadados obrigatórios e verifiquei a unicidade dos `chunk_id`.

Durante o desenvolvimento, utilizei o ChatGPT como apoio para estruturar inicialmente os loaders, compreender erros encontrados durante a execução e revisar a integração. As sugestões foram analisadas e ajustadas de acordo com a estrutura real dos arquivos do repositório e com os requisitos definidos no desafio.


### Relato individual - Eridalgo Ramos da Silva

Neste encontro, fiquei responsável pela ingestão dos documentos não estruturados nos formatos Markdown, PDF e TXT. Inicialmente, inspecionei os arquivos disponíveis no repositório para compreender a estrutura e definir uma estratégia de chunking adequada para cada formato.

Implementei o arquivo `src/ingest_unstructured.py`. Para os documentos Markdown, utilizei a estrutura de títulos e seções como referência para preservar a organização do conteúdo, com divisão adicional para seções maiores. Para os arquivos PDF, utilizei a extração do conteúdo textual e divisão respeitando a estrutura dos textos. Nos arquivos TXT, tratei as mensagens de e-mail de forma separada antes da divisão por tamanho.

Também apliquei aos documentos os metadados padronizados do projeto, incluindo `source_file`, `doc_type`, `chunk_id` e `sensitivity`, além de outros campos quando aplicáveis. Após os testes individuais, minha implementação foi integrada ao loader dos dados estruturados e semiestruturados desenvolvido pela Eduarda.

Na integração dos dois loaders, o pipeline completo resultou em 5.721 chunks. Também revisamos a presença dos metadados obrigatórios e a identificação dos chunks antes de avançar para a etapa de indexação vetorial.

Utilizei o ChatGPT como apoio durante a organização e revisão da implementação. As sugestões foram verificadas e adaptadas de acordo com a estrutura real dos documentos e com as estratégias de chunking exigidas no desafio.


### Resumo do dia (escrito em conjunto)

**Entregamos hoje:**
- Realizamos a inspeção inicial dos arquivos disponibilizados no repositório e dividimos as responsabilidades de implementação entre os integrantes.
- Implementamos os loaders para os seis formatos previstos na Etapa 1: CSV, JSON, JSONL, Markdown, PDF e TXT.
- Para os dados estruturados e semiestruturados, implementamos a ingestão de CSV, JSON e JSONL, adotando um registro por chunk e um ticket por chunk, conforme a natureza de cada fonte.
- Para os documentos não estruturados, implementamos estratégias específicas de processamento e chunking para Markdown, PDF e TXT, buscando preservar seções, parágrafos e mensagens.
- Padronizamos os metadados obrigatórios `source_file`, `doc_type`, `chunk_id` e `sensitivity`, acrescentando metadados específicos quando aplicáveis.
- Integramos os loaders estruturados, semiestruturados e não estruturados em um único fluxo de ingestão.
- O pipeline integrado gerou 5.721 chunks.
- Realizamos testes para verificar a presença dos metadados obrigatórios e a unicidade dos identificadores dos chunks.
- Cada integrante realizou commits próprios referentes à parte desenvolvida.

**Ficou pendente:**
- Gerar os embeddings dos documentos processados.
- Construir e popular o índice vetorial utilizando FAISS.
- Persistir o índice em disco utilizando `save_local`.
- Implementar e testar a recarga do índice com `load_local`, sem realizar nova indexação.
- Criar o script de sanidade da Etapa 1, contendo o total de chunks, a distribuição por `doc_type` e os cinco chunks mais similares para três perguntas de teste.
- Revisar as dependências do projeto e atualizar o `requirements.txt` conforme necessário.

**Bloqueios em aberto:**
- Não permanecemos com bloqueios técnicos relacionados à ingestão ao final das atividades.
- Durante o desenvolvimento, encontramos dificuldades relacionadas à instalação de dependências no Google Colab e à autenticação do GitHub para realização do `push`, mas esses problemas foram identificados e solucionados.
- A indexação vetorial ainda não foi concluída e será retomada na continuidade da Etapa 1.

**Próximo passo (início do encontro 2):**
- Finalizar os itens ainda pendentes da Etapa 1 antes de avançar para a Etapa 2.
- Gerar os embeddings dos 5.721 chunks, construir e persistir o índice FAISS e verificar sua recarga sem reindexação.
- Executar o script de sanidade com três perguntas de teste e analisar os cinco resultados mais similares retornados para cada consulta.
- Após validar o critério de pronto da Etapa 1, iniciar a implementação da busca híbrida, do Query Analyzer e da filtragem por metadados previstos para a Etapa 2.

**Uso de assistentes de IA:**
- Utilizamos o ChatGPT como ferramenta de apoio durante o desenvolvimento, principalmente na organização inicial dos loaders, interpretação de erros apresentados no Google Colab, revisão da integração entre os módulos e orientação sobre comandos Git.
- As sugestões geradas pela IA foram revisadas e adaptadas de acordo com a estrutura real dos arquivos disponibilizados no repositório e com os requisitos técnicos definidos no guia do desafio.
- Também utilizamos a IA como apoio para revisar a padronização dos metadados e organizar os testes de validação do pipeline integrado.

---

## Encontro 2 - AAAA-MM-DD

**Etapa:** 2 - Busca híbrida e filtragem por metadados

### Relato individual - [Nome do Integrante 1]

### Relato individual - [Nome do Integrante 2]

### Resumo do dia (escrito em conjunto)

**Entregamos hoje:**
-

**Ficou pendente:**
-

**Bloqueios em aberto:**
-

**Próximo passo (início do encontro 3):**
-

**Uso de assistentes de IA:**
-

---

## Encontro 3 - AAAA-MM-DD

**Etapa:** 3 - Síntese estruturada, evidência e guardrails de LGPD

### Relato individual - [Nome do Integrante 1]

### Relato individual - [Nome do Integrante 2]

### Resumo do dia (escrito em conjunto)

**Entregamos hoje:**
-

**Ficou pendente:**
-

**Bloqueios em aberto:**
-

**Próximo passo (início do encontro 4):**
-

**Uso de assistentes de IA:**
-

---

## Encontro 4 - AAAA-MM-DD

**Etapa:** 4 - Avaliação (RAG Triad), interface e relatório

### Relato individual - [Nome do Integrante 1]

### Relato individual - [Nome do Integrante 2]

### Resumo do dia (escrito em conjunto)

**Entregamos hoje:**
-

**Ficou pendente:**
-

**Bloqueios em aberto:**
-

**Preparação para o Demo Day:**
-

**Uso de assistentes de IA:**
-

---

*TIC em Trilhas · PUC-Rio · Instituto ECOA · MCTI Futuro · Softex*
