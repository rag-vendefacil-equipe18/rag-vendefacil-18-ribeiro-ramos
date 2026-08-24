# Acompanhamento - Mini Desafio RAG VendeFácil

**Integrante 1:** Maria Eduarda Ribeiro da Silva - [@eduardaribs](https://github.com/eduardaribs)
**Integrante 2:** Nome Completo - [@usuario-github](https://github.com/usuario-github)

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


### Relato individual - [Nome do Integrante 2]

<!-- Escreva você mesmo, em primeira pessoa. O que implementou, que decisão tomou e por quê, onde travou. -->

### Resumo do dia (escrito em conjunto)

**Entregamos hoje:**
-

**Ficou pendente:**
-

**Bloqueios em aberto:**
-

**Próximo passo (início do encontro 2):**
-

**Uso de assistentes de IA:**
-

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
