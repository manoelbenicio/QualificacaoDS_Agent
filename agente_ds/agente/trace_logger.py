# -*- coding: utf-8 -*-
"""
TRACE LOGGER — Enterprise Audit Trail & Explainability System
Sistema de rastreamento completo para qualificações DS.

Captura CADA passo do pipeline:
  - Upload do documento
  - Extração texto (chars, páginas)
  - Busca no Acervo (quais docs matcharam e por quê)
  - Cada sub-agente (input → análise → output)
  - Cálculo de cada farol (fórmula + variáveis)
  - Decisão final (regra aplicada)

Permite:
  - Habilitar/desabilitar via toggle
  - Exportar trace completo para compartilhar com cliente
  - Auditoria de cada score
"""
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class TraceEvent:
    """Um evento individual no trace."""
    def __init__(self, component: str, action: str, detail: str = "",
                 data: Dict = None, level: str = "INFO"):
        self.timestamp = datetime.now().isoformat()
        self.elapsed_ms = 0  # Set by logger
        self.component = component
        self.action = action
        self.detail = detail
        self.data = data or {}
        self.level = level  # INFO, DETAIL, MATCH, SCORE, DECISION, WARNING

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "elapsed_ms": self.elapsed_ms,
            "component": self.component,
            "action": self.action,
            "detail": self.detail,
            "data": self.data,
            "level": self.level,
        }


class TraceLogger:
    """
    Logger de trace para uma execução de qualificação.
    Cada qualificação gera um trace_id único.
    """

    # Diretório para persistir traces
    TRACES_DIR = Path(__file__).parent.parent / "traces"

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.trace_id = str(uuid.uuid4())[:12]
        self.events: List[TraceEvent] = []
        self.start_time = time.time()
        self.metadata: Dict = {}

        # Garantir diretório
        self.TRACES_DIR.mkdir(parents=True, exist_ok=True)

    def set_metadata(self, **kwargs):
        """Define metadados do trace (oportunidade, cliente, etc)."""
        self.metadata.update(kwargs)

    def log(self, component: str, action: str, detail: str = "",
            data: Dict = None, level: str = "INFO"):
        """Registra um evento no trace."""
        if not self.enabled:
            return

        event = TraceEvent(component, action, detail, data, level)
        event.elapsed_ms = round((time.time() - self.start_time) * 1000)
        self.events.append(event)

    def log_upload(self, filename: str, size_bytes: int, extension: str):
        """Registra upload do documento."""
        self.log("UPLOAD", "documento_recebido",
                 f"Arquivo: {filename} ({size_bytes:,} bytes, {extension})",
                 {"filename": filename, "size_bytes": size_bytes, "extension": extension})

    def log_extraction(self, chars: int, palavras: int, paginas: int, metadados: Dict = None):
        """Registra extração de texto."""
        self.log("EXTRACAO", "texto_extraido",
                 f"{chars:,} caracteres | {palavras:,} palavras | ~{paginas} páginas",
                 {"caracteres": chars, "palavras": palavras, "paginas": paginas, **(metadados or {})})

    def log_kb_search(self, query_preview: str, total_catalog: int, results_count: int):
        """Registra início da busca no acervo."""
        self.log("ACERVO", "busca_iniciada",
                 f"Buscando em {total_catalog:,} documentos do catálogo",
                 {"total_catalog": total_catalog, "results_found": results_count,
                  "query_preview": query_preview[:200]},
                 level="DETAIL")

    def log_kb_match(self, doc_titulo: str, doc_categoria: str, doc_path: str,
                     score: float, razao: str):
        """Registra cada documento do acervo que matchou."""
        self.log("ACERVO", "documento_match",
                 f"[{doc_categoria}] {doc_titulo} (score: {score:.2f})",
                 {"titulo": doc_titulo, "categoria": doc_categoria,
                  "path": doc_path, "score": score, "razao_match": razao},
                 level="MATCH")

    def log_agent_start(self, agent_id: str, agent_name: str, motor: str):
        """Registra início de um sub-agente."""
        self.log(agent_id, "agente_iniciado",
                 f"{agent_name} ({motor})",
                 {"agent_id": agent_id, "agent_name": agent_name, "motor": motor})

    def log_agent_analysis(self, agent_id: str, analise: str, dados: Dict = None):
        """Registra análise feita por um sub-agente."""
        self.log(agent_id, "analise",
                 analise, dados or {}, level="DETAIL")

    def log_agent_result(self, agent_id: str, resultado: str, dados: Dict = None):
        """Registra resultado de um sub-agente."""
        self.log(agent_id, "resultado",
                 resultado, dados or {})

    def log_tech_detection(self, tech: str, ocorrencias: int, peso: int):
        """Registra detecção de tecnologia."""
        self.log("SA2", "tech_detectada",
                 f"'{tech}' encontrada {ocorrencias}x (peso: {peso})",
                 {"tech": tech, "ocorrencias": ocorrencias, "peso": peso},
                 level="DETAIL")

    def log_risk_detection(self, risco: str, severidade: str, keyword: str, ocorrencias: int):
        """Registra detecção de risco."""
        self.log("SA3", "risco_detectado",
                 f"[{severidade}] {risco} (keyword: '{keyword}', {ocorrencias}x)",
                 {"risco": risco, "severidade": severidade, "keyword": keyword,
                  "ocorrencias": ocorrencias},
                 level="DETAIL")

    def log_farol_calc(self, farol_id: str, nome: str, score: float,
                       formula: str, variaveis: Dict):
        """Registra cálculo detalhado de um farol."""
        self.log("SA4", "farol_calculado",
                 f"{farol_id} '{nome}' = {score:.1f}/10",
                 {"farol_id": farol_id, "nome": nome, "score": score,
                  "formula": formula, "variaveis": variaveis},
                 level="SCORE")

    def log_decision(self, decisao: str, score: float, confianca: int,
                     regra: str, condicoes: List[str] = None):
        """Registra decisão final."""
        self.log("SA5", "decisao_final",
                 f"{decisao} (Score: {score:.2f}, Confiança: {confianca}%)",
                 {"decisao": decisao, "score": score, "confianca_pct": confianca,
                  "regra_aplicada": regra, "condicoes": condicoes or []},
                 level="DECISION")

    def log_warning(self, component: str, mensagem: str, dados: Dict = None):
        """Registra um warning."""
        self.log(component, "warning", mensagem, dados or {}, level="WARNING")

    # ═══ EXPORTAÇÃO ═══

    def to_dict(self) -> Dict:
        """Exporta trace completo como dict."""
        return {
            "trace_id": self.trace_id,
            "metadata": self.metadata,
            "total_events": len(self.events),
            "duration_ms": round((time.time() - self.start_time) * 1000),
            "created_at": datetime.now().isoformat(),
            "events": [e.to_dict() for e in self.events],
            "summary": self._gerar_resumo(),
        }

    def _gerar_resumo(self) -> Dict:
        """Gera resumo executivo do trace."""
        matches = [e for e in self.events if e.level == "MATCH"]
        scores = [e for e in self.events if e.level == "SCORE"]
        decisions = [e for e in self.events if e.level == "DECISION"]
        warnings = [e for e in self.events if e.level == "WARNING"]

        return {
            "total_events": len(self.events),
            "kb_matches": len(matches),
            "scores_calculated": len(scores),
            "decisions": len(decisions),
            "warnings": len(warnings),
            "duration_ms": round((time.time() - self.start_time) * 1000),
            "top_matches": [
                {"titulo": e.data.get("titulo", ""), "categoria": e.data.get("categoria", ""),
                 "score": e.data.get("score", 0)}
                for e in sorted(matches, key=lambda x: x.data.get("score", 0), reverse=True)[:10]
            ],
        }

    def save(self) -> str:
        """Salva trace no disco e retorna o path."""
        if not self.enabled:
            return ""

        filename = f"trace_{self.trace_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.TRACES_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

        return str(filepath)

    @classmethod
    def load(cls, trace_id: str) -> Optional[Dict]:
        """Carrega um trace salvo pelo ID."""
        for f in cls.TRACES_DIR.glob(f"trace_{trace_id}_*.json"):
            with open(f, "r", encoding="utf-8") as fp:
                return json.load(fp)
        return None

    @classmethod
    def list_traces(cls, limit: int = 50) -> List[Dict]:
        """Lista traces recentes."""
        traces = []
        for f in sorted(cls.TRACES_DIR.glob("trace_*.json"), reverse=True)[:limit]:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                traces.append({
                    "trace_id": data.get("trace_id", ""),
                    "metadata": data.get("metadata", {}),
                    "total_events": data.get("total_events", 0),
                    "duration_ms": data.get("duration_ms", 0),
                    "created_at": data.get("created_at", ""),
                    "summary": data.get("summary", {}),
                })
            except:
                pass
        return traces
