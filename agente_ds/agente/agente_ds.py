# -*- coding: utf-8 -*-
"""
Agente DS — Qualificação de Ofertas (Desenvolvimento de Soluções)
Motor principal: recebe RFP + inputs, consulta acervo, invoca LLM, gera parecer.
Baseado em: 07_AGENTE_1_QUALIFICACAO_DS.md (Cenário 1 — Agente Único)
Indra Minsait Brasil — DSS Agents v1.0
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .acervo import AcervoDS
from .extracao import ExtratorDocumental
from .validacao import ValidadorInput


# ════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — AGENTE 1 DS (QUALIFICAÇÃO)
# Adaptado de 07_AGENTE_1_QUALIFICACAO_DS.md §3-§6
# ════════════════════════════════════════════════════════════════

SYSTEM_PROMPT_DS = """Você é o **Agente de Qualificação DS (Desenvolvimento de Soluções)** da Indra Minsait Brasil.

## SUA MISSÃO
Analisar documentos de oportunidades (RFPs, RFIs, Editais) de **Desenvolvimento de Soluções** e produzir um parecer estruturado Go/No-Go com dimensionamento técnico de equipe.

## PRÁTICA: DS — Desenvolvimento de Soluções
Escopo coberto:
- Desenvolvimento de software (Java, .NET, Python, JavaScript/TypeScript, Go)
- Frontend (React, Angular, Vue.js, Next.js)
- Mobile (Flutter, React Native, Swift, Kotlin)
- Fullstack e UI/UX Design
- QA e Testing automatizado
- Sustentação / AMS de aplicações

⚠️ ESCOPO CROSS-PRÁTICA: DevOps, Kubernetes, CI/CD pipeline, infraestrutura → DIC. Se a RFP tiver esses componentes, sinalize como cross-prática.

## ETAPAS DE ANÁLISE (execute todas sequencialmente)

### ETAPA 1 — EXTRAÇÃO E CATALOGAÇÃO
- Leia TODOS os documentos fornecidos
- Identifique: requisitos funcionais, não-funcionais, SLAs, prazos, modelo de contratação
- Catalogue por tipo: RFP principal, anexos técnicos, requisitos, termos contratuais

### ETAPA 2 — ANÁLISE DO ESCOPO DO PROJETO
- Identifique stack tecnológico exigido (linguagens, frameworks, DBs, cloud)
- Mapeie integrações com sistemas existentes
- Classifique arquitetura (monolito, microserviços, serverless, híbrido)
- Identifique ambientes necessários (dev, hml, prod)
- Sinalize componentes fora do escopo DS (cross-prática)

### ETAPA 3 — DIMENSIONAMENTO DE EQUIPE TÉCNICA
Estime a equipe necessária usando os perfis DS:
| Perfil | Senioridade | Quando alocar |
|--------|-------------|---------------|
| Tech Lead / Arquiteto | Sênior | Sempre |
| Dev Backend | Sr/Pl/Jr | Conforme complexidade |
| Dev Frontend | Sr/Pl | Se houver UI |
| Dev Mobile | Sr/Pl | Se houver app mobile |
| QA / Test Engineer | Sr/Pl | Sempre (mín. 1) |
| DevOps Engineer | Sr | Se CI/CD no escopo |
| UX/UI Designer | Sr/Pl | Se houver design |
| Scrum Master | - | Se squad dedicado |
| Product Owner | - | Se squad dedicado |

Para cada perfil, estime: quantidade FTE, horas/mês, duração em sprints.

### ETAPA 4 — RISCOS TÉCNICOS E CONTRATUAIS
Classifique cada risco como ALTO/MÉDIO/BAIXO:
- Riscos de stack (tecnologia desconhecida pela Minsait?)
- Riscos de escopo (requisitos vagos, scope creep)
- Riscos contratuais (multas, penalidades, SLAs agressivos)
- Riscos de PI (cessão de código-fonte, open source)
- Riscos de compliance (LGPD, SOX, ITAR)
- Riscos de capacidade (equipe disponível?)

### ETAPA 5 — OPORTUNIDADES DE DIFERENCIAÇÃO
- Cruzar com Acervo Minsait (cases similares, atestados, capacidades)
- Identificar alavancas Best Story Wins
- Mapear oportunidades de cross-selling entre práticas
- Identificar aceleradores Minsait (frameworks, assets reutilizáveis)

### ETAPA 6 — PARECER GO/NO-GO (8 FARÓIS + BEST STORY WINS)

#### 8 Critérios Faróis (pondere cada um de 1 a 10):
| # | Farol | Peso | Descrição |
|---|-------|------|-----------|
| 1 | Fit Estratégico | 15% | Alinhamento com estratégia Minsait 2026 |
| 2 | Capacidade Técnica | 20% | Stack tech + experiência da equipe |
| 3 | Competitividade | 15% | Posição vs. concorrentes prováveis |
| 4 | Rentabilidade | 15% | Margem esperada vs. esforço |
| 5 | Risco Contratual | 10% | Penalidades, SLAs, multas |
| 6 | Prazo | 10% | Viabilidade do cronograma |
| 7 | Relacionamento | 10% | Histórico com o cliente |
| 8 | Escalabilidade | 5% | Potencial de crescimento / cross-sell |

#### 4 Perguntas Best Story Wins:
1. **"Por que nós?"** — O que torna a Minsait a melhor escolha para ESTE projeto?
2. **"Por que agora?"** — Urgência do cliente e timing de mercado
3. **"Por que esta solução?"** — Diferencial técnico da abordagem proposta
4. **"O que nos faz únicos?"** — Asset, case ou capacidade exclusiva Minsait

#### Decisão Final:
- **GO** — Score ≥ 7.0 e nenhum farol CRÍTICO (≤ 3)
- **GO CONDICIONADO** — Score 5.0-6.9 ou 1+ farol em alerta. Liste condições de mitigação.
- **NO-GO** — Score < 5.0 ou 2+ faróis CRÍTICOS. Justifique com evidências.

## FORMATO DO OUTPUT
Produza um JSON com a seguinte estrutura:
```json
{
  "metadata": {
    "agente": "DS-QUALIFICACAO-v1.0",
    "data_analise": "YYYY-MM-DD HH:MM",
    "pratica": "DS",
    "versao": "1.0"
  },
  "oportunidade": {
    "nome": "...",
    "cliente": "...",
    "setor": "...",
    "tipo_servico": "..."
  },
  "analise_escopo": {
    "stack_tecnologico": [],
    "arquitetura": "...",
    "integracoes": [],
    "ambientes": [],
    "cross_pratica": []
  },
  "dimensionamento": {
    "equipe": [
      {"perfil": "...", "senioridade": "...", "fte": 0, "sprints": 0}
    ],
    "total_ftes": 0,
    "total_sprints": 0,
    "estimativa_horas": 0
  },
  "riscos": [
    {"titulo": "...", "severidade": "ALTO|MÉDIO|BAIXO", "impacto": "...", "mitigacao": "..."}
  ],
  "farois": [
    {"nome": "...", "score": 0, "peso": 0, "justificativa": "..."}
  ],
  "best_story_wins": {
    "por_que_nos": "...",
    "por_que_agora": "...",
    "por_que_esta_solucao": "...",
    "o_que_nos_faz_unicos": "..."
  },
  "score_final": 0.0,
  "decisao": "GO|NO-GO|GO_CONDICIONADO",
  "condicoes_mitigacao": [],
  "recomendacoes": [],
  "acervo_consultado": []
}
```

## REGRAS INQUEBRÁVEIS
1. NUNCA invente dados. Se não encontrar informação, diga "NÃO ENCONTRADO NA RFP".
2. SEMPRE justifique cada farol com evidências extraídas dos documentos.
3. SEMPRE dimensione a equipe em perfis DS (não use perfis genéricos).
4. Se a RFP mencionaar tecnologias fora do escopo DS, SINALIZE como cross-prática.
5. Use linguagem executiva, direta, sem jargão desnecessário.
"""


class AgenteDS:
    """
    Agente de Qualificação DS — Cenário 1 (Agente Único).
    Processa RFP + inputs + acervo → Parecer Go/No-Go.
    """

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        self.temperature = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "8192"))

        self.extrator = ExtratorDocumental()
        self.acervo = AcervoDS()
        self.validador = ValidadorInput()

        self._client = None

    @property
    def client(self):
        """Lazy-load Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise RuntimeError("anthropic não instalado. Execute: pip install anthropic")
        return self._client

    def qualificar(self, dados_formulario: Dict, caminho_rfp: str) -> Dict:
        """
        Pipeline principal de qualificação.
        
        Args:
            dados_formulario: Dict com campos do formulário (§2.1)
            caminho_rfp: Caminho para o arquivo RFP (PDF, DOCX ou ZIP)
            
        Returns:
            Dict com resultado da qualificação completa
        """
        inicio = time.time()
        resultado = {
            "status": "processando",
            "etapas": {},
            "timestamp_inicio": datetime.now().isoformat(),
        }

        # ── 1. VALIDAR INPUTS ──
        valido, erros = self.validador.validar(dados_formulario)
        if not valido:
            return {
                "status": "erro_validacao",
                "erros": erros,
                "mensagem": "Corrija os erros de validação antes de prosseguir.",
            }

        dados = self.validador.normalizar(dados_formulario)
        resultado["etapas"]["validacao"] = {"status": "ok", "dados": dados}

        # ── 2. EXTRAIR DOCUMENTOS ──
        extracao = self.extrator.extrair(caminho_rfp)
        if extracao.get("status") != "ok":
            return {
                "status": "erro_extracao",
                "erro": extracao.get("mensagem", "Falha na extração"),
            }

        texto_rfp = extracao.get("texto_consolidado", extracao.get("texto", ""))
        resultado["etapas"]["extracao"] = {
            "status": "ok",
            "documentos": extracao.get("total_documentos", 1),
            "caracteres": len(texto_rfp),
        }

        # ── 3. CONSULTAR ACERVO ──
        contexto_rag = self.acervo.get_contexto_rag(texto_rfp, top_k=15)
        taxonomia = self.acervo.get_taxonomia_resumo()
        resultado["etapas"]["acervo"] = {
            "status": "ok",
            "docs_encontrados": contexto_rag.count("["),
        }

        # ── 4. MONTAR PROMPT E INVOCAR LLM ──
        user_message = self._montar_user_message(dados, texto_rfp, contexto_rag, taxonomia)

        try:
            resposta_llm = self._invocar_llm(user_message)
            resultado["etapas"]["llm"] = {
                "status": "ok",
                "model": self.model,
                "tokens_usados": resposta_llm.get("tokens", {}),
            }
        except Exception as e:
            return {
                "status": "erro_llm",
                "erro": str(e),
                "mensagem": "Falha ao invocar o LLM. Verifique a API key e conectividade.",
            }

        # ── 5. PARSEAR RESULTADO ──
        try:
            parecer = self._parsear_resposta(resposta_llm.get("texto", ""))
        except Exception as e:
            parecer = {
                "raw_response": resposta_llm.get("texto", ""),
                "parse_error": str(e),
            }

        duracao = time.time() - inicio
        resultado.update({
            "status": "concluido",
            "parecer": parecer,
            "duracao_segundos": round(duracao, 2),
            "timestamp_fim": datetime.now().isoformat(),
        })

        return resultado

    def _montar_user_message(self, dados: Dict, texto_rfp: str, contexto_rag: str, taxonomia: str) -> str:
        """Monta a mensagem do usuário com todos os contextos."""
        # Truncar RFP se necessário (máx ~100K chars para caber na janela)
        max_chars = 100_000
        if len(texto_rfp) > max_chars:
            texto_rfp = texto_rfp[:max_chars] + f"\n\n[... DOCUMENTO TRUNCADO. Total: {len(texto_rfp)} caracteres. Primeiros {max_chars} incluídos.]"

        return f"""## DADOS DA OPORTUNIDADE (formulário do usuário)

- **Nome:** {dados['nome_oportunidade']}
- **Cliente:** {dados['cliente']}
- **Setor:** {dados['setor']}
- **Tipo de Serviço:** {dados['tipo_servico']}
- **Prática:** {dados['pratica']}
- **Modelo de Trabalho:** {dados.get('modelo_trabalho', 'Não informado')}
- **ACV Estimado:** {dados.get('acv_estimado', 'Não informado')}
- **Prazo Proposta:** {dados.get('prazo_entrega_proposta', 'Não informado')}
- **Stack Preferida:** {', '.join(dados.get('stack_preferida', [])) or 'Não informada'}
- **Concorrentes:** {', '.join(dados.get('concorrentes_conhecidos', [])) or 'Não informados'}
- **Observações:** {dados.get('observacoes', 'Nenhuma')}

---

## DOCUMENTO DA OPORTUNIDADE (RFP/RFI/EDITAL)

{texto_rfp}

---

## CONTEXTO DO ACERVO MINSAIT (documentos relevantes encontrados)

{contexto_rag}

---

{taxonomia}

---

## INSTRUÇÃO

Analise a oportunidade acima seguindo as 6 etapas definidas no seu system prompt.
Produza o output no formato JSON especificado.
Seja rigoroso na análise de stack tecnológico e dimensionamento de equipe DS.
"""

    def _invocar_llm(self, user_message: str) -> Dict:
        """Invoca o Claude via Anthropic API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=SYSTEM_PROMPT_DS,
            messages=[{"role": "user", "content": user_message}],
        )

        texto = ""
        for block in response.content:
            if hasattr(block, "text"):
                texto += block.text

        return {
            "texto": texto,
            "tokens": {
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
                "total": response.usage.input_tokens + response.usage.output_tokens,
            },
        }

    def _parsear_resposta(self, texto: str) -> Dict:
        """Tenta extrair JSON da resposta do LLM."""
        # Procurar bloco JSON na resposta
        import re
        json_match = re.search(r'\{[\s\S]*\}', texto)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Se não encontrou JSON válido, retornar texto raw
        return {"raw_response": texto, "parse_status": "json_not_found"}

    def health_check(self) -> Dict:
        """Verifica saúde do agente e dependências."""
        checks = {
            "agente": "DS-QUALIFICACAO-v1.0",
            "pratica": "DS",
            "acervo": self.acervo.get_stats(),
            "extrator_parsers": list(self.extrator._parsers.keys()),
            "llm_model": self.model,
            "api_key_configurada": bool(self.api_key),
            "timestamp": datetime.now().isoformat(),
        }
        return checks
