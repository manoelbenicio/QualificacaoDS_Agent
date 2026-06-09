# Agente Qualificação DS — Gemma 4 + Multi-LLM

> Sistema de qualificação inteligente de ofertas para a prática de **Desenvolvimento de Soluções (DS)**, alimentado por **Gemma 4 12B** local via Ollama com fallback para Gemini/OpenAI.

## 🏗️ Arquitetura

```
QualificacaoDS-Agent/
├── agente_ds/               # Código principal
│   ├── agente/              # Core do agente
│   │   ├── llm_client.py    # Multi-LLM (Ollama/Gemini/OpenAI)
│   │   ├── agente_ds.py     # Orquestrador principal
│   │   ├── acervo.py        # RAG sobre o acervo DS
│   │   ├── adk_robo.py      # ADK robot fallback
│   │   ├── extracao.py      # Extração de dados RFP
│   │   ├── gerar_html.py    # Geração de relatório HTML
│   │   ├── gerar_painel.py  # Geração de painel one-page
│   │   ├── validacao.py     # Validação de output
│   │   ├── trace_logger.py  # Logging de traces
│   │   └── sub_agentes/     # Sub-agentes especializados
│   │       ├── maestro.py           # Orquestrador de sub-agentes
│   │       ├── sa1_extrator.py      # Extração de requisitos
│   │       ├── sa2_analista_tecnico.py  # Análise técnica
│   │       ├── sa3_analista_riscos.py   # Análise de riscos
│   │       ├── sa4_analista_comercial.py # Análise comercial
│   │       └── sa5_decisor.py           # Decisão final GO/NO-GO
│   ├── frontend/            # UI HTML do agente
│   ├── Arquitetura/         # Screenshots e docs de arquitetura
│   ├── server.py            # Flask server (porta 8006)
│   ├── requirements.txt     # Dependências Python
│   ├── .env.example         # Template de configuração
│   └── .env                 # Configuração local (NÃO commitar)
├── catalog.json             # Índice do acervo DS (RAG)
├── taxonomy.json            # Taxonomia de mercados/práticas
├── kb/                      # 📂 Knowledge Base (copiar manualmente)
│   └── (pastas A-Z do Materiais_DS)
└── docs/                    # Documentação
    ├── ACERVO_README.md
    └── PROMPT_CONTEXTO_AGENTES.md
```

## 🚀 Quick Start

### 1. Pré-requisitos
- Python 3.10+
- [Ollama](https://ollama.com/download/windows) instalado

### 2. Instalar Gemma 4
```bash
ollama pull gemma4:12b
```

### 3. Configurar ambiente
```bash
cd agente_ds
cp .env.example .env
# Editar .env se necessário (já vem pré-configurado para Ollama)

python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 4. Rodar
```bash
# Certificar que Ollama está rodando
ollama serve

# Em outro terminal
python server.py
```

O servidor estará em `http://localhost:8006`

## 🤖 LLM Providers

| Provider | Modelo | Custo | Prioridade |
|----------|--------|-------|:----------:|
| **Ollama** | gemma4:12b | R$0 | 1º (default) |
| Gemini | gemini-2.5-flash-lite | Cloud | 2º (fallback) |
| OpenAI | gpt-4o-mini | Cloud | 3º (fallback) |

Configuração em `.env`:
```env
LLM_PROVIDER=auto          # ollama → gemini → openai
OLLAMA_MODEL=gemma4:12b
OLLAMA_URL=http://localhost:11434
```

## 📂 Knowledge Base (kb/)

A pasta `kb/` é onde os materiais de referência devem ser copiados manualmente.
Copie as pastas relevantes do `Materiais_DS` original:

```
kb/
├── A_Atestados/
├── B_Cases/
├── C_Capacidades_Portfolio/
├── D_Defesas_Tecnicas/
├── I_Institucional/
├── M_Metodologias/
├── PT_Propostas_Tecnicas/
├── S_Solucoes_Verticais/
├── T_Templates_Proposta/
└── ...
```

O `catalog.json` na raiz já indexa todos esses documentos via caminhos relativos.

## 📋 Outputs

O agente gera **3 outputs** por qualificação:
1. **Painel One-Page** (PDF/HTML) — resumo executivo visual
2. **Análise Detalhada** (HTML) — relatório completo
3. **JSON estruturado** — dados para integração

## 📜 Licença

Uso interno corporativo.
