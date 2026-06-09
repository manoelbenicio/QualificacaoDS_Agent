# -*- coding: utf-8 -*-
"""
MAESTRO — Orquestrador do Pipeline Multi-Agente DS
Coordena SA1→SA2+SA3+SA4 (paralelo)→SA5 conforme spec §3.2
Spec: 07_AGENTE_1_QUALIFICACAO_DS.md — Diagrama de Comunicação

MODOS:
  - Com Claude API Key: Usa Claude API para cada sub-agente (legado)
  - Com Gemini/OpenAI Key: Modo HYBRID — ADK Robô + LLM para justificativas
  - Sem API Key: Usa ADK Robô (motor determinístico Python) para TODOS os agentes
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from ..acervo import AcervoDS
from ..extracao import ExtratorDocumental
from ..validacao import ValidadorInput
from ..adk_robo import ADKRobo
from ..trace_logger import TraceLogger
from ..llm_client import LLMClient, LLMError

from . import sa1_extrator, sa2_analista_tecnico, sa3_analista_riscos, sa4_analista_comercial, sa5_decisor


class Maestro:
    """
    Orquestrador do Pipeline de Qualificação DS.
    
    Fluxo:
    ┌─────────┐     ┌──────┐     ┌───────────────┐     ┌──────┐
    │ INPUT   │────▶│ SA1  │────▶│ SA2 + SA3 +   │────▶│ SA5  │──▶ OUTPUT
    │ (RFP +  │     │Extrat│     │ SA4 (paralelo) │     │Decisor│
    │  form)  │     │      │     └───────────────┘     └──────┘
    └─────────┘     └──────┘

    Sem API Key → ADK Robô processa todos os agentes localmente.
    """

    # Sub-agentes e suas configs
    SUB_AGENTES = {
        "SA1": {"module": sa1_extrator, "nome": "Extrator Documental"},
        "SA2": {"module": sa2_analista_tecnico, "nome": "Analista Técnico"},
        "SA3": {"module": sa3_analista_riscos, "nome": "Analista de Riscos"},
        "SA4": {"module": sa4_analista_comercial, "nome": "Analista Comercial"},
        "SA5": {"module": sa5_decisor, "nome": "Decisor Estratégico"},
    }

    def __init__(self, api_key: str = None, model_override: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model_override = model_override
        self.extrator = ExtratorDocumental()
        self.acervo = AcervoDS()
        self.validador = ValidadorInput()
        self.adk = ADKRobo()
        self._client = None
        self.trace_enabled = os.getenv("TRACE_ENABLED", "true").lower() in ("true", "1", "yes")
        self._last_trace = None

        # LLM Client universal (Gemini/OpenAI)
        self.llm = LLMClient()

    @property
    def usa_llm(self) -> bool:
        """True se Claude API key válida está configurada."""
        return bool(self.api_key and len(self.api_key) > 10)

    @property
    def usa_hybrid(self) -> bool:
        """True se Gemini ou OpenAI está configurado (modo hybrid)."""
        return self.llm.is_available

    @property
    def modo(self) -> str:
        """Retorna o modo atual."""
        if self.usa_llm:
            return "LLM (Claude API)"
        elif self.usa_hybrid:
            return "HYBRID (ADK + " + "/".join(p.name for p in self.llm.providers[:2]) + ")"
        return "ADK Robô (Python)"

    @property
    def client(self):
        if self._client is None:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def qualificar(self, dados_formulario: Dict, caminho_rfp: str, trace_enabled: bool = None, on_progress=None) -> Dict:
        """
        Pipeline principal — Qualificação de RFP.
        
        Se API key disponível: usa Claude para cada sub-agente.
        Se não: usa ADK Robô (motor Python determinístico).
        
        Args:
            trace_enabled: Override para habilitar/desabilitar trace nesta execução.
            on_progress: Callback function(event, pct, detail, data) para progresso real-time.
        """
        inicio = time.time()
        _emit = on_progress or (lambda *a, **kw: None)  # no-op se não fornecido

        # ═══ TRACE LOGGER ═══
        use_trace = trace_enabled if trace_enabled is not None else self.trace_enabled
        trace = TraceLogger(enabled=use_trace)

        # ═══ ETAPA 0: VALIDAÇÃO ═══
        _emit("validacao", 3, "Validando campos do formulário...")
        valido, erros = self.validador.validar(dados_formulario)
        if not valido:
            trace.log("VALIDACAO", "erro", f"{len(erros)} erros de validação", {"erros": erros}, "WARNING")
            _emit("erro", 0, f"Validação falhou: {', '.join(erros[:3])}")
            return {"status": "erro_validacao", "erros": erros}

        dados = self.validador.normalizar(dados_formulario)
        trace.set_metadata(
            nome_oportunidade=dados.get("nome_oportunidade", ""),
            cliente=dados.get("cliente", ""),
            setor=dados.get("setor", ""),
            tipo_servico=dados.get("tipo_servico", ""),
        )
        trace.log("VALIDACAO", "ok", "Todos os campos validados com sucesso")
        self._log("E0", "Validação OK")
        _emit("validacao", 5, "✅ Campos validados com sucesso")

        # ═══ ETAPA 1: EXTRAÇÃO LOCAL DO DOCUMENTO ═══
        filename = Path(caminho_rfp).name
        file_size = Path(caminho_rfp).stat().st_size if Path(caminho_rfp).exists() else 0
        _emit("upload", 8, f"Recebendo arquivo: {filename} ({file_size / 1024 / 1024:.1f} MB)")
        self._log("E1", f"Extraindo documento: {caminho_rfp}")
        trace.log_upload(
            filename=filename,
            size_bytes=file_size,
            extension=Path(caminho_rfp).suffix,
        )

        _emit("extracao", 10, f"Extraindo texto de {filename}...")
        extracao = self.extrator.extrair(caminho_rfp)
        if extracao.get("status") != "ok":
            trace.log("EXTRACAO", "erro", extracao.get("mensagem", "Falha na extração"), level="WARNING")
            _emit("erro", 0, f"Falha na extração: {extracao.get('mensagem', 'erro')}")
            return {"status": "erro_extracao", "erro": extracao.get("mensagem")}

        texto_rfp = extracao.get("texto_consolidado", extracao.get("texto", ""))
        palavras = len(texto_rfp.split())
        paginas = max(1, len(texto_rfp) // 3000)
        trace.log_extraction(len(texto_rfp), palavras, paginas)
        self._log("E1", f"Extração local: {len(texto_rfp):,} chars")
        _emit("extracao", 15, f"✅ {len(texto_rfp):,} caracteres extraídos ({palavras:,} palavras, ~{paginas} páginas)")

        # ═══ DECIDIR MODO ═══
        if self.usa_llm:
            self._log("MODO", "LLM (Claude API)")
            trace.log("MODO", "llm_selecionado", "Claude API disponível")
            result = self._pipeline_llm(dados, texto_rfp, inicio)
        elif self.usa_hybrid:
            self._log("MODO", f"HYBRID ({self.modo})")
            trace.log("MODO", "hybrid_selecionado", f"ADK + LLM: {self.modo}")
            _emit("modo", 17, f"Modo: HYBRID — ADK Robô + {self.modo}")
            result = self._pipeline_hybrid(dados, texto_rfp, inicio, trace, _emit)
        else:
            self._log("MODO", "ADK Robô (Python determinístico)")
            trace.log("MODO", "adk_selecionado", "Sem API key — usando ADK Robô Python")
            _emit("modo", 17, "Modo: ADK Robô Python (determinístico)")
            result = self._pipeline_adk(dados, texto_rfp, inicio, trace, _emit)

        # ═══ SALVAR TRACE ═══
        trace_path = trace.save()
        result["trace_id"] = trace.trace_id
        result["trace_enabled"] = use_trace
        self._last_trace = trace

        _emit("completo", 100, f"✅ Concluído — {result.get('parecer', {}).get('decisao', 'N/A')}")
        return result

    # ═══════════════════════════════════════
    # PIPELINE HYBRID (ADK + Gemini/OpenAI)
    # ═══════════════════════════════════════

    def _pipeline_hybrid(self, dados: Dict, texto_rfp: str, inicio: float, trace: 'TraceLogger' = None, _emit=None) -> Dict:
        """
        Pipeline HYBRID:
        1. ADK Robô faz extração + KB match + scoring (determinístico)
        2. LLM (Gemini/OpenAI) enriquece com:
           - Justificativas inteligentes
           - Detecção de riscos semânticos
           - Resumo executivo contextual
        3. Se LLM falha → resultado ADK puro (fallback seguro)
        """
        if trace is None:
            trace = TraceLogger(enabled=False)
        _emit = _emit or (lambda *a, **kw: None)

        # ═══ PASSO 1: ADK Robô completo (base determinística) ═══
        self._log("HYBRID", "Passo 1/2: ADK Robô processando...")
        trace.log("HYBRID", "adk_start", "Iniciando pipeline ADK Robô para base determinística")
        adk_result = self._pipeline_adk(dados, texto_rfp, inicio, trace, _emit)

        # Se ADK falhou, retornar erro
        if adk_result.get("status") != "concluido":
            return adk_result

        # ═══ PASSO 2: LLM enriquece resultado ═══
        _emit("llm_inicio", 88, f"🧠 {self.modo} gerando justificativas...")
        self._log("HYBRID", "Passo 2/2: LLM enriquecendo análise...")
        trace.log("HYBRID", "llm_start", f"Enviando para {self.modo} para enriquecimento")

        try:
            parecer = adk_result.get("parecer", {})
            sa1 = adk_result.get("etapas", {}).get("SA1", {}).get("output", {})
            sa3 = adk_result.get("etapas", {}).get("SA3", {}).get("output", {})
            sa4 = adk_result.get("etapas", {}).get("SA4", {}).get("output", {})

            # Preparar contexto para LLM
            system_prompt = """Você é um especialista em qualificação de ofertas para a consultoria Minsait/Indra.
Analise os dados a seguir (resultado de uma análise prévia) e ENRIQUEÇA com:
1. Uma justificativa_decisao detalhada e contextual (3-5 frases explicando POR QUE a decisão é essa)
2. Um resumo_executivo para o Diretor (2-3 frases, direto ao ponto)
3. Riscos semânticos adicionais que a análise automática pode ter perdido
4. Recomendações específicas para next_steps

Retorne um JSON com: {"justificativa_decisao": "...", "resumo_executivo": "...", "riscos_adicionais": [...], "recomendacoes": [...]}"""

            # Texto resumido para LLM (não precisa enviar tudo, só contexto relevante)
            texto_resumo = texto_rfp[:8000]  # Primeiros 8K chars do RFP
            user_content = f"""DOCUMENTO RFP (primeiras páginas):
{texto_resumo}

---
RESULTADO DA ANÁLISE AUTOMÁTICA:
- Decisão: {parecer.get('decisao', 'N/A')}
- Score Final: {parecer.get('score_final_ponderado', 0)}/10
- Tecnologias: {', '.join(sa1.get('tecnologias_detectadas', [])[:10])}
- Escopo: {sa1.get('escopo_principal', 'N/A')}
- Complexidade: {sa1.get('complexidade_estimada', 'N/A')}
- Total Riscos: {sa3.get('total_riscos', 0)} ({sa3.get('riscos_criticos', 0)} críticos)
- KB Cobertura: {sa4.get('cobertura_score', 0)}/10
- Cliente: {dados.get('cliente', 'N/A')}
- Setor: {dados.get('setor', 'N/A')}
- Tipo: {dados.get('tipo_servico', 'N/A')}"""

            _emit("llm_thinking", 90, "Thinking: analisando requisitos vs. capacidades...")
            llm_result = self.llm.smart_analyze(
                system_prompt=system_prompt,
                user_content=user_content,
                temperature=0.3,
                max_tokens=4096
            )
            _emit("llm_fim", 93, f"✅ LLM: justificativa gerada ({llm_result.get('provider', 'N/A')}/{llm_result.get('model', 'N/A')})")

            llm_data = self.llm.parse_json_response(llm_result.get("text", "{}"))

            # Enriquecer parecer com output do LLM
            if llm_data.get("justificativa_decisao"):
                adk_result["parecer"]["justificativa_decisao"] = llm_data["justificativa_decisao"]
            if llm_data.get("resumo_executivo"):
                adk_result["parecer"]["resumo_executivo"] = llm_data["resumo_executivo"]
            if llm_data.get("riscos_adicionais"):
                adk_result["parecer"]["riscos_adicionais_llm"] = llm_data["riscos_adicionais"]
            if llm_data.get("recomendacoes"):
                adk_result["parecer"]["recomendacoes_llm"] = llm_data["recomendacoes"]

            # Metadata LLM
            adk_result["motor"] = f"HYBRID — ADK Robô + {llm_result.get('provider', 'LLM')}/{llm_result.get('model', 'N/A')}"
            adk_result["llm_stats"] = self.llm.get_stats()
            adk_result["tokens_totais"]["llm_input"] = llm_result.get("tokens_input", 0)
            adk_result["tokens_totais"]["llm_output"] = llm_result.get("tokens_output", 0)

            trace.log("HYBRID", "llm_success",
                      f"LLM enriqueceu com justificativa + resumo executivo ({llm_result.get('tokens_output', 0)} tokens)",
                      {"model": llm_result.get("model"), "provider": llm_result.get("provider")})

            self._log("HYBRID", f"LLM enriqueceu resultado ({llm_result.get('model')})")

        except (LLMError, Exception) as e:
            # Fallback: mantém resultado ADK puro
            self._log("HYBRID", f"LLM falhou, mantendo resultado ADK: {e}")
            trace.log("HYBRID", "llm_fallback", f"LLM indisponível: {e} — resultado ADK mantido", level="WARNING")
            adk_result["motor"] += " (LLM indisponível — fallback ADK)"

        return adk_result

    # ═══════════════════════════════════════
    # PIPELINE ADK ROBÔ (SEM LLM)
    # ═══════════════════════════════════════

    def _pipeline_adk(self, dados: Dict, texto_rfp: str, inicio: float, trace: 'TraceLogger' = None, _emit=None) -> Dict:
        """
        Pipeline completo usando ADK Robô.
        Cada sub-agente é executado via motor Python determinístico.
        Confronta RFP contra toda a base de conhecimento (Acervo DS).
        """
        if trace is None:
            trace = TraceLogger(enabled=False)
        _emit = _emit or (lambda *a, **kw: None)

        pipeline = {
            "status": "processando",
            "cenario": "CENARIO_2_ADK_ROBO",
            "pratica": "DS",
            "motor": "ADK Robô Python v2 — Sem dependência de API externa",
            "etapas": {},
            "timestamp_inicio": datetime.now().isoformat(),
        }

        # Tokenizar RFP
        _emit("tokenizacao", 20, "Tokenizando documento...")
        tokens_rfp = self.adk._tokenizar(texto_rfp)
        texto_lower = texto_rfp.lower()
        trace.log("TOKENIZACAO", "texto_tokenizado", f"{len(tokens_rfp)} tokens únicos extraídos", {"total_tokens": len(tokens_rfp)})
        _emit("tokenizacao", 22, f"✅ {len(tokens_rfp):,} tokens únicos extraídos")

        # ═══ SA1: EXTRAÇÃO ESTRUTURADA ═══
        _emit("sa1_inicio", 25, "SA1 — Extração Estruturada iniciada")
        trace.log_agent_start("SA1", "Extrator Documental", "ADK Robô")
        self._log("SA1", "ADK Robô — Extrator Documental")
        t1 = time.time()
        sa1_result = self.adk.sa1_extrair(dados, texto_rfp, tokens_rfp)
        d1 = round(time.time() - t1, 3)
        pipeline["etapas"]["E2_SA1_extracao"] = {"status": "ok", "motor": "ADK Robô", "duracao_s": d1}

        # Trace SA1 details
        doc_info = sa1_result.get("analise_documento", {})
        trace.log_agent_analysis("SA1", f"Documento: {doc_info.get('total_palavras', 0)} palavras, {doc_info.get('total_paginas_estimado', 0)} páginas", doc_info)
        techs = sa1_result.get("tecnologias_detectadas", {})
        tech_names = list(techs.keys())[:5]
        for tech, info in techs.items():
            trace.log_tech_detection(tech, info.get("ocorrencias", 0), info.get("peso", 0))
        escopo = sa1_result.get("escopo", {})
        trace.log_agent_result("SA1", f"Escopo: {escopo.get('principal', 'N/A')}, Complexidade: {sa1_result.get('complexidade_estimada', 'N/A')}", {"escopo": escopo, "complexidade": sa1_result.get("complexidade_estimada")})
        self._log("SA1", f"Concluído — {doc_info.get('total_palavras', 0)} palavras analisadas")
        _emit("sa1_fim", 35, f"✅ SA1 concluído: {len(techs)} tecnologias detectadas ({', '.join(tech_names)})")

        # ═══ CONSULTA ACERVO DS (Base de Conhecimento) ═══
        total_catalog = len(self.acervo.catalog) if hasattr(self.acervo, 'catalog') else 0
        _emit("acervo", 40, f"Consultando {total_catalog:,} documentos do acervo DS...")
        self._log("ACERVO", "Confrontando RFP contra base de conhecimento...")
        t_kb = time.time()
        trace.log_kb_search(texto_rfp[:200], total_catalog, 0)
        kb_match = self.adk._confrontar_acervo(texto_rfp, tokens_rfp, self.acervo)
        d_kb = round(time.time() - t_kb, 3)

        pipeline["etapas"]["E3_acervo"] = {
            "status": "ok",
            "total_docs_analisados": kb_match.get("total_docs_analisados", 0),
            "docs_relevantes": kb_match.get("docs_relevantes", 0),
            "cobertura_score": kb_match.get("cobertura_score", 0),
            "duracao_s": d_kb,
        }

        # Trace EACH matched document
        for cat_key in ["atestados", "cases", "capacidades", "propostas", "solucoes", "templates"]:
            for doc in kb_match.get(cat_key, []):
                trace.log_kb_match(
                    doc_titulo=doc.get("titulo", "N/A"),
                    doc_categoria=cat_key.upper()[:3],
                    doc_path=doc.get("path", ""),
                    score=kb_match.get("cobertura_score", 0),
                    razao=f"Match por categoria {cat_key} — mercado: {doc.get('mercado', 'N/A')}, práticas: {doc.get('praticas', [])}",
                )
        trace.log("ACERVO", "busca_concluida",
                  f"{kb_match.get('docs_relevantes', 0)} relevantes de {kb_match.get('total_docs_analisados', 0)} analisados (cobertura {kb_match.get('cobertura_score', 0):.1f}/10)",
                  {"por_categoria": kb_match.get("por_categoria", {}), "cobertura": kb_match.get("cobertura_score", 0)})
        self._log("ACERVO", f"{kb_match.get('docs_relevantes', 0)} docs relevantes (cobertura: {kb_match.get('cobertura_score', 0):.1f}/10)")
        _emit("acervo_fim", 50, f"✅ {kb_match.get('docs_relevantes', 0)} documentos relevantes (cobertura {kb_match.get('cobertura_score', 0):.1f}/10)")

        # ═══ SA2: ANALISTA TÉCNICO ═══
        _emit("sa2_inicio", 55, "SA2 — Análise Técnica iniciada")
        trace.log_agent_start("SA2", "Analista Técnico", "ADK Robô")
        self._log("SA2", "ADK Robô — Analista Técnico")
        t2 = time.time()
        sa2_result = self.adk.sa2_analisar_tecnico(texto_rfp, tokens_rfp, sa1_result, kb_match)
        d2 = round(time.time() - t2, 3)
        pipeline["etapas"]["E4_SA2_tecnico"] = {"status": "ok", "motor": "ADK Robô", "techs": sa2_result.get("total_tecnologias", 0), "aderencia_ds": sa2_result.get("aderencia_ds", 0), "duracao_s": d2}
        trace.log_agent_result("SA2", f"{sa2_result.get('total_tecnologias', 0)} tecnologias, aderência DS {sa2_result.get('aderencia_ds', 0)}/10",
                               {"tecnologias": sa2_result.get("tecnologias_identificadas", []), "aderencia": sa2_result.get("aderencia_ds"), "gaps": sa2_result.get("gaps_tecnicos", []), "dimensionamento": sa2_result.get("dimensionamento", {})})
        self._log("SA2", f"Concluído — {sa2_result.get('total_tecnologias', 0)} techs, aderência DS {sa2_result.get('aderencia_ds', 0)}/10")
        _emit("sa2_fim", 65, f"✅ SA2 concluído: {sa2_result.get('total_tecnologias', 0)} tecnologias, aderência DS {sa2_result.get('aderencia_ds', 0)}/10")

        # ═══ SA3: ANALISTA DE RISCOS ═══
        _emit("sa3_inicio", 68, "SA3 — Análise de Riscos iniciada")
        trace.log_agent_start("SA3", "Analista de Riscos", "ADK Robô")
        self._log("SA3", "ADK Robô — Analista de Riscos")
        t3 = time.time()
        sa3_result = self.adk.sa3_analisar_riscos(texto_rfp, texto_lower, sa1_result)
        d3 = round(time.time() - t3, 3)
        pipeline["etapas"]["E4_SA3_riscos"] = {"status": "ok", "motor": "ADK Robô", "total_riscos": sa3_result.get("total_riscos", 0), "criticos": sa3_result.get("criticos", 0), "risk_score": sa3_result.get("risk_score", 0), "duracao_s": d3}
        # Trace each risk
        for risco in sa3_result.get("riscos", []):
            trace.log_risk_detection(risco.get("nome", ""), risco.get("severidade", ""), risco.get("keyword", ""), risco.get("ocorrencias", 0))
        trace.log_agent_result("SA3", f"{sa3_result.get('total_riscos', 0)} riscos ({sa3_result.get('criticos', 0)} críticos, risk_score {sa3_result.get('risk_score', 0)}/10)",
                               {"riscos": sa3_result.get("riscos", []), "mitigacoes": sa3_result.get("mitigacoes_chave", [])})
        self._log("SA3", f"Concluído — {sa3_result.get('total_riscos', 0)} riscos ({sa3_result.get('criticos', 0)} críticos)")
        _emit("sa3_fim", 75, f"✅ SA3 concluído: {sa3_result.get('total_riscos', 0)} riscos ({sa3_result.get('criticos', 0)} críticos)")

        # ═══ SA4: ANALISTA COMERCIAL ═══
        _emit("sa4_inicio", 78, "SA4 — Análise Comercial (8 Faróis + BSW)...")
        trace.log_agent_start("SA4", "Analista Comercial (8 Faróis + BSW)", "ADK Robô")
        self._log("SA4", "ADK Robô — Analista Comercial (8 Faróis + BSW)")
        t4 = time.time()
        sa4_result = self.adk.sa4_analisar_comercial(dados, texto_rfp, texto_lower, sa1_result, sa2_result, sa3_result, kb_match)
        d4 = round(time.time() - t4, 3)
        pipeline["etapas"]["E4_SA4_comercial"] = {"status": "ok", "motor": "ADK Robô", "score_final": sa4_result.get("score_final_ponderado", 0), "nivel": sa4_result.get("nivel_geral", "N/A"), "duracao_s": d4}
        # Trace each farol with formula
        for f in sa4_result.get("farois", []):
            trace.log_farol_calc(
                f.get("id", ""), f.get("nome", ""), f.get("score", 0),
                f"peso={f.get('peso_pct')}% | nivel={f.get('nivel', 'N/A')}",
                {"peso_pct": f.get("peso_pct"), "justificativa": f.get("justificativa", "")},
            )
        trace.log_agent_result("SA4", f"Score final: {sa4_result.get('score_final_ponderado', 0):.2f}/10 ({sa4_result.get('nivel_geral', 'N/A')})",
                               {"score": sa4_result.get("score_final_ponderado"), "bsw": sa4_result.get("best_story_wins", {})})
        self._log("SA4", f"Concluído — Score {sa4_result.get('score_final_ponderado', 0):.2f}/10 ({sa4_result.get('nivel_geral', 'N/A')})")
        _emit("sa4_fim", 85, f"✅ SA4 concluído: Score {sa4_result.get('score_final_ponderado', 0):.2f}/10")

        # ═══ SA5: DECISOR ESTRATÉGICO ═══
        _emit("sa5_inicio", 95, "SA5 — Decisor Estratégico...")
        trace.log_agent_start("SA5", "Decisor Estratégico", "ADK Robô")
        self._log("SA5", "ADK Robô — Decisor Estratégico")
        t5 = time.time()
        sa5_result = self.adk.sa5_decidir(dados, sa1_result, sa2_result, sa3_result, sa4_result, kb_match)
        d5 = round(time.time() - t5, 3)
        pipeline["etapas"]["E5_SA5_decisao"] = {"status": "ok", "motor": "ADK Robô", "decisao": sa5_result.get("decisao", "N/A"), "score_final": sa5_result.get("score_final", 0), "confianca_pct": sa5_result.get("confianca_pct", 0), "duracao_s": d5}
        # Trace decision
        trace.log_decision(
            sa5_result.get("decisao", "N/A"), sa5_result.get("score_final", 0), sa5_result.get("confianca_pct", 0),
            sa5_result.get("justificativa_decisao", ""), sa5_result.get("next_steps", []),
        )
        self._log("SA5", f"Concluído — {sa5_result.get('decisao', 'N/A')} ({sa5_result.get('score_final', 0):.2f}/10, {sa5_result.get('confianca_pct', 0)}% confiança)")
        _emit("farois", 97, f"8 Faróis calculados — Score {sa5_result.get('score_final', 0):.1f}/10")
        _emit("decisao", 99, f"{'🟢' if sa5_result.get('decisao') == 'GO' else '🟡' if 'CONDICIONADO' in str(sa5_result.get('decisao', '')) else '🔴'} {sa5_result.get('decisao', 'N/A')} — Score {sa5_result.get('score_final', 0):.1f}/10, Confiança {sa5_result.get('confianca_pct', 0)}%")

        # ═══ RESULTADO FINAL ═══
        duracao = time.time() - inicio
        pipeline.update({
            "status": "concluido",
            "parecer": sa5_result,
            "outputs_intermediarios": {
                "SA1_extracao": sa1_result,
                "SA2_tecnico": sa2_result,
                "SA3_riscos": sa3_result,
                "SA4_comercial": sa4_result,
            },
            "kb_match": {
                "total_docs": kb_match.get("total_docs_analisados", 0),
                "relevantes": kb_match.get("docs_relevantes", 0),
                "cobertura": kb_match.get("cobertura_score", 0),
                "por_categoria": kb_match.get("por_categoria", {}),
            },
            "tokens_totais": {
                "input": len(texto_rfp),
                "output": 0,
                "total": len(texto_rfp),
            },
            "duracao_segundos": round(duracao, 2),
            "timestamp_fim": datetime.now().isoformat(),
        })

        self._log("MAESTRO", f"Pipeline ADK concluído em {duracao:.1f}s | Decisão: {sa5_result.get('decisao', 'N/A')}")
        return pipeline

    # ═══════════════════════════════════════
    # PIPELINE LLM (COM API KEY)
    # ═══════════════════════════════════════

    def _pipeline_llm(self, dados: Dict, texto_rfp: str, inicio: float) -> Dict:
        """Pipeline usando Claude API para cada sub-agente."""
        pipeline = {
            "status": "processando",
            "cenario": "CENARIO_2_MULTI_AGENTE",
            "pratica": "DS",
            "motor": "Claude API (Anthropic)",
            "etapas": {},
            "timestamp_inicio": datetime.now().isoformat(),
        }

        # ═══ SA1 ═══
        self._log("SA1", "Iniciando Extrator Documental (LLM)...")
        sa1_input = self._montar_input_sa1(dados, texto_rfp)
        sa1_result = self._invocar_sub_agente("SA1", sa1_input)
        pipeline["etapas"]["E2_SA1_extracao"] = {
            "status": "ok" if sa1_result else "erro",
            "tokens": sa1_result.get("_tokens", {}),
        }
        sa1_output = sa1_result.get("parsed", sa1_result.get("raw", ""))
        self._log("SA1", "Concluído")

        # ═══ ACERVO ═══
        contexto_rag = self.acervo.get_contexto_rag(texto_rfp, top_k=15)
        taxonomia = self.acervo.get_taxonomia_resumo()
        pipeline["etapas"]["E3_acervo"] = {
            "status": "ok",
            "docs_encontrados": len(self.acervo.buscar_relevantes(texto_rfp, top_k=15)),
        }
        self._log("ACERVO", f"RAG: {pipeline['etapas']['E3_acervo']['docs_encontrados']} docs relevantes")

        # ═══ SA2 ═══
        self._log("SA2", "Iniciando Analista Técnico (LLM)...")
        sa2_input = self._montar_input_sa234(sa1_output, "SA2", dados, contexto_rag)
        sa2_result = self._invocar_sub_agente("SA2", sa2_input)
        pipeline["etapas"]["E4_SA2_tecnico"] = {
            "status": "ok" if sa2_result else "erro",
            "tokens": sa2_result.get("_tokens", {}),
        }
        self._log("SA2", "Concluído")

        # ═══ SA3 ═══
        self._log("SA3", "Iniciando Analista de Riscos (LLM)...")
        sa3_input = self._montar_input_sa234(sa1_output, "SA3", dados, contexto_rag)
        sa3_result = self._invocar_sub_agente("SA3", sa3_input)
        pipeline["etapas"]["E4_SA3_riscos"] = {
            "status": "ok" if sa3_result else "erro",
            "tokens": sa3_result.get("_tokens", {}),
        }
        self._log("SA3", "Concluído")

        # ═══ SA4 ═══
        self._log("SA4", "Iniciando Analista Comercial (LLM)...")
        sa4_input = self._montar_input_sa234(sa1_output, "SA4", dados, contexto_rag)
        sa4_result = self._invocar_sub_agente("SA4", sa4_input)
        pipeline["etapas"]["E4_SA4_comercial"] = {
            "status": "ok" if sa4_result else "erro",
            "tokens": sa4_result.get("_tokens", {}),
        }
        self._log("SA4", "Concluído")

        # ═══ SA5 ═══
        self._log("SA5", "Iniciando Decisor Estratégico (LLM)...")
        sa5_input = self._montar_input_sa5(
            dados, sa1_output,
            sa2_result.get("parsed", sa2_result.get("raw", "")),
            sa3_result.get("parsed", sa3_result.get("raw", "")),
            sa4_result.get("parsed", sa4_result.get("raw", "")),
        )
        sa5_result = self._invocar_sub_agente("SA5", sa5_input)
        pipeline["etapas"]["E5_SA5_decisao"] = {
            "status": "ok" if sa5_result else "erro",
            "tokens": sa5_result.get("_tokens", {}),
        }
        self._log("SA5", "Concluído")

        # ═══ RESULTADO FINAL ═══
        duracao = time.time() - inicio
        total_tokens = {"input": 0, "output": 0}
        for etapa in pipeline["etapas"].values():
            tokens = etapa.get("tokens", {})
            total_tokens["input"] += tokens.get("input", 0)
            total_tokens["output"] += tokens.get("output", 0)
        total_tokens["total"] = total_tokens["input"] + total_tokens["output"]

        pipeline.update({
            "status": "concluido",
            "parecer": sa5_result.get("parsed", sa5_result.get("raw", "")),
            "outputs_intermediarios": {
                "SA1_extracao": sa1_output,
                "SA2_tecnico": sa2_result.get("parsed", ""),
                "SA3_riscos": sa3_result.get("parsed", ""),
                "SA4_comercial": sa4_result.get("parsed", ""),
            },
            "tokens_totais": total_tokens,
            "duracao_segundos": round(duracao, 2),
            "timestamp_fim": datetime.now().isoformat(),
        })

        self._log("MAESTRO", f"Pipeline LLM concluído em {duracao:.1f}s | {total_tokens['total']} tokens")
        return pipeline

    # ═══════════════════════════════════════
    # MONTAGEM DE INPUTS (LLM)
    # ═══════════════════════════════════════

    def _montar_input_sa1(self, dados: Dict, texto_rfp: str) -> str:
        max_chars = 80_000
        if len(texto_rfp) > max_chars:
            texto_rfp = texto_rfp[:max_chars] + f"\n[TRUNCADO — {len(texto_rfp)} chars total]"

        return f"""## OPORTUNIDADE
- Nome: {dados['nome_oportunidade']}
- Cliente: {dados['cliente']}
- Setor: {dados['setor']}
- Tipo: {dados['tipo_servico']}
- Prática: DS — Desenvolvimento de Soluções

## DOCUMENTO DA OPORTUNIDADE
{texto_rfp}

## INSTRUÇÃO
Extraia TODOS os dados estruturados conforme seu schema de output.
"""

    def _montar_input_sa234(self, sa1_output, sa_id: str, dados: Dict, contexto_rag: str) -> str:
        sa1_json = json.dumps(sa1_output, ensure_ascii=False, indent=2) if isinstance(sa1_output, dict) else str(sa1_output)

        base = f"""## OPORTUNIDADE
- Nome: {dados['nome_oportunidade']}
- Cliente: {dados['cliente']}
- Setor: {dados['setor']}
- Tipo: {dados['tipo_servico']}
- Prática: DS — Desenvolvimento de Soluções
- ACV Estimado: {dados.get('acv_estimado', 'Não informado')}

## EXTRACTION RESULT (output do Sub-Agente 1)
{sa1_json}
"""
        if sa_id == "SA4":
            base += f"""
## CONTEXTO DO ACERVO MINSAIT DS
{contexto_rag}

## ESTRUTURA DO ACERVO (Materiais_DS)
- A_Atestados/ — Atestados técnicos
- B_Cases/ — Cases de sucesso
- C_Capacidades_Portfolio/ — Portfolio de capacidades
- D_Defesas_Tecnicas/ — Defesas técnicas
- I_Institucional/ — Documentos institucionais
- M_Metodologias/ — Metodologias
- PT_Propostas_Tecnicas/ — Propostas técnicas
- S_Solucoes_Verticais/ — Soluções por vertical
- T_Templates_Proposta/ — Templates
- _ofertas_ativas/ — Projetos ativos
- _operacional/rates/ — Tabelas de rates e custos
"""

        base += "\n## INSTRUÇÃO\nAnalise conforme seu system prompt e produza o output JSON."
        return base

    def _montar_input_sa5(self, dados: Dict, sa1_out, sa2_out, sa3_out, sa4_out) -> str:
        def to_json(obj):
            if isinstance(obj, dict):
                return json.dumps(obj, ensure_ascii=False, indent=2)
            return str(obj)

        return f"""## OPORTUNIDADE
- Nome: {dados['nome_oportunidade']}
- Cliente: {dados['cliente']}
- Setor: {dados['setor']}
- Tipo: {dados['tipo_servico']}
- Prática: DS — Desenvolvimento de Soluções
- ACV Estimado: {dados.get('acv_estimado', 'Não informado')}

## OUTPUT SA1 — EXTRAÇÃO DOCUMENTAL
{to_json(sa1_out)}

## OUTPUT SA2 — ANÁLISE TÉCNICA
{to_json(sa2_out)}

## OUTPUT SA3 — ANÁLISE DE RISCOS
{to_json(sa3_out)}

## OUTPUT SA4 — ANÁLISE COMERCIAL
{to_json(sa4_out)}

## INSTRUÇÃO
Consolide TODOS os outputs acima e produza a decisão final GO/NO-GO/CONDICIONADO.
Gere o JSON estruturado completo + resumo executivo one-pager.
"""

    # ═══════════════════════════════════════
    # INVOCAÇÃO LLM
    # ═══════════════════════════════════════

    def _invocar_sub_agente(self, sa_id: str, user_message: str) -> Dict:
        """Invoca um sub-agente via Anthropic API."""
        sa = self.SUB_AGENTES[sa_id]
        config = sa["module"].CONFIG
        prompt = sa["module"].SYSTEM_PROMPT

        model = self.model_override or config.get("llm", "claude-sonnet-4-20250514")
        temp = config.get("temperatura", 0.3)
        max_tok = config.get("max_tokens", 4096)

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tok,
                temperature=temp,
                system=prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            texto = ""
            for block in response.content:
                if hasattr(block, "text"):
                    texto += block.text

            # Tentar parsear JSON
            import re
            parsed = None
            json_match = re.search(r'\{[\s\S]*\}', texto)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            return {
                "raw": texto,
                "parsed": parsed or {"raw_response": texto},
                "_tokens": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
            }

        except Exception as e:
            self._log(sa_id, f"ERRO: {str(e)}")
            return {
                "raw": f"ERRO: {str(e)}",
                "parsed": {"erro": str(e)},
                "_tokens": {},
            }

    # ═══════════════════════════════════════
    # HEALTH CHECK
    # ═══════════════════════════════════════

    def health_check(self) -> Dict:
        return {
            "maestro": "DS-MAESTRO-v2.0",
            "cenario": "CENARIO_2_MULTI_AGENTE",
            "pratica": "DS",
            "modo": "LLM (Claude)" if self.usa_llm else "ADK Robô (Python)",
            "sub_agentes": {
                sa_id: {
                    "nome": sa["nome"],
                    "llm": sa["module"].CONFIG.get("llm") if self.usa_llm else "ADK Robô",
                    "temperatura": sa["module"].CONFIG.get("temperatura") if self.usa_llm else "N/A",
                }
                for sa_id, sa in self.SUB_AGENTES.items()
            },
            "acervo": self.acervo.get_stats(),
            "api_key_configurada": self.usa_llm,
            "timestamp": datetime.now().isoformat(),
        }

    def _log(self, component: str, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}] [{component}] {message}")
