# -*- coding: utf-8 -*-
"""
Servidor HTTP — Agente DS de Qualificação
API REST para upload de RFP e execução do agente.
Baseado em: 06_ARQUITETURA_REFERENCIA.md §2-§3
"""
import json
import os
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Carregar .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Tentar .env.example como fallback
    env_example = Path(__file__).parent / ".env.example"
    if env_example.exists():
        load_dotenv(env_example)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Adicionar o diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

from agente import AgenteDS, Maestro


# ════════════════════════════════════════════
# FLASK APP
# ════════════════════════════════════════════
app = Flask(__name__, static_folder="frontend")
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
CORS(app)

# Instâncias globais — Cenário 1 (monolítico) + Cenário 2 (multi-agente)
agente = AgenteDS()
maestro = Maestro()

# Diretório para uploads temporários
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Diretório para outputs
OUTPUT_DIR = Path(__file__).parent / "out"
OUTPUT_DIR.mkdir(exist_ok=True)


# ═══════════════════════════════════════
# ROTAS — API
# ═══════════════════════════════════════

@app.route("/api/health", methods=["GET"])
def health():
    """Health check — mostra status de ambos os cenários."""
    return jsonify({
        "cenario_1_monolitico": agente.health_check(),
        "cenario_2_multi_agente": maestro.health_check(),
    })


@app.route("/api/qualificar", methods=["POST"])
def qualificar():
    """
    Endpoint principal — Qualificação de RFP.
    
    Espera:
    - multipart/form-data com:
      - 'rfp': arquivo (PDF, DOCX, ZIP)
      - 'dados': JSON string com campos do formulário
    
    Retorna:
    - JSON com parecer completo (8 Faróis + BSW + dimensionamento)
    """
    try:
        # ── Validar upload ──
        if "rfp" not in request.files:
            return jsonify({"status": "erro", "mensagem": "Arquivo RFP obrigatório. Envie via campo 'rfp'."}), 400

        arquivo = request.files["rfp"]
        if not arquivo.filename:
            return jsonify({"status": "erro", "mensagem": "Nome do arquivo vazio."}), 400

        # ── Validar extensão ──
        ext = Path(arquivo.filename).suffix.lower()
        extensoes_aceitas = {".pdf", ".docx", ".xlsx", ".pptx", ".zip", ".txt", ".eml", ".msg", ".html", ".htm", ".csv", ".md"}
        if ext not in extensoes_aceitas:
            return jsonify({"status": "erro", "mensagem": f"Extensão {ext} não suportada. Use: PDF, DOCX, XLSX, PPTX, ZIP"}), 400

        # ── Salvar upload ──
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = f"{timestamp}_{arquivo.filename}"
        upload_path = UPLOAD_DIR / safe_name
        arquivo.save(str(upload_path))

        # ── Parsear dados do formulário ──
        dados_raw = request.form.get("dados", "{}")
        try:
            dados = json.loads(dados_raw)
        except json.JSONDecodeError:
            return jsonify({"status": "erro", "mensagem": "Campo 'dados' deve ser JSON válido."}), 400

        # ── Escolher cenário ──
        cenario = dados.get("cenario", request.form.get("cenario", "2"))
        
        if str(cenario) == "1":
            resultado = agente.qualificar(dados, str(upload_path))
        else:
            resultado = maestro.qualificar(dados, str(upload_path))

        # ── Salvar output ──
        output_file = OUTPUT_DIR / f"qualificacao_{timestamp}_C{cenario}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)

        resultado["output_salvo"] = str(output_file)
        return jsonify(resultado)

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "erro_interno",
            "mensagem": str(e),
            "traceback": traceback.format_exc(),
        }), 500


# ═══════════════════════════════════════
# SSE — REAL-TIME PROGRESS STREAMING
# ═══════════════════════════════════════

import threading
import queue
import uuid as _uuid

# Job store: job_id -> { "queue": Queue, "result": None|dict, "status": "running"|"done"|"error" }
_jobs = {}


@app.route("/api/qualificar/start", methods=["POST"])
def qualificar_start():
    """
    Inicia qualificação em background e retorna job_id.
    Frontend usa /api/progress/<job_id> (SSE) para acompanhar.
    """
    try:
        if "rfp" not in request.files:
            return jsonify({"status": "erro", "mensagem": "Arquivo RFP obrigatório."}), 400

        arquivo = request.files["rfp"]
        if not arquivo.filename:
            return jsonify({"status": "erro", "mensagem": "Nome do arquivo vazio."}), 400

        ext = Path(arquivo.filename).suffix.lower()
        extensoes_aceitas = {".pdf", ".docx", ".xlsx", ".pptx", ".zip", ".txt", ".eml", ".msg", ".html", ".htm", ".csv", ".md"}
        if ext not in extensoes_aceitas:
            return jsonify({"status": "erro", "mensagem": f"Extensão {ext} não suportada."}), 400

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = f"{timestamp}_{arquivo.filename}"
        upload_path = UPLOAD_DIR / safe_name
        arquivo.save(str(upload_path))

        dados_raw = request.form.get("dados", "{}")
        try:
            dados = json.loads(dados_raw)
        except json.JSONDecodeError:
            return jsonify({"status": "erro", "mensagem": "Campo 'dados' deve ser JSON válido."}), 400

        # Criar job
        job_id = str(_uuid.uuid4())[:8]
        progress_queue = queue.Queue()
        _jobs[job_id] = {"queue": progress_queue, "result": None, "status": "running", "events": []}

        def _on_progress(event, pct, detail, data=None):
            """Callback chamado pelo Maestro em cada etapa."""
            evt = {"event": event, "pct": pct, "detail": detail, "ts": datetime.now().isoformat()}
            if data:
                evt["data"] = data
            progress_queue.put(evt)
            _jobs[job_id]["events"].append(evt)

        def _run_job():
            try:
                cenario = dados.get("cenario", "2")
                if str(cenario) == "1":
                    resultado = agente.qualificar(dados, str(upload_path))
                else:
                    resultado = maestro.qualificar(dados, str(upload_path), on_progress=_on_progress)

                output_file = OUTPUT_DIR / f"qualificacao_{timestamp}_C{cenario}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(resultado, f, ensure_ascii=False, indent=2)
                resultado["output_salvo"] = str(output_file)

                # ── Output 2/3: Relatório HTML Detalhado (Spec §4.1.2 — 10 seções) ──
                try:
                    from agente.gerar_html import gerar_html
                    html_content = gerar_html(str(output_file))
                    html_file = OUTPUT_DIR / f"qualificacao_{timestamp}_C{cenario}.html"
                    with open(html_file, "w", encoding="utf-8") as hf:
                        hf.write(html_content)
                    resultado["html_salvo"] = str(html_file)
                except Exception as html_err:
                    print(f"[WARN] HTML report generation failed: {html_err}")

                # ── Output 3/3: Painel Executivo One-Pager (Spec §4.1.1) ──
                try:
                    from agente.gerar_painel import gerar_painel
                    painel_content = gerar_painel(str(output_file))
                    painel_file = OUTPUT_DIR / f"qualificacao_{timestamp}_C{cenario}_painel.html"
                    with open(painel_file, "w", encoding="utf-8") as pf:
                        pf.write(painel_content)
                    resultado["painel_salvo"] = str(painel_file)
                except Exception as painel_err:
                    print(f"[WARN] Painel one-pager generation failed: {painel_err}")

                _jobs[job_id]["result"] = resultado
                _jobs[job_id]["status"] = "done"
                progress_queue.put({"event": "result", "pct": 100, "detail": "Resultado final", "result": resultado})
            except Exception as e:
                import traceback as tb
                _jobs[job_id]["status"] = "error"
                _jobs[job_id]["result"] = {"status": "erro_interno", "mensagem": str(e)}
                progress_queue.put({"event": "error", "pct": 0, "detail": str(e), "traceback": tb.format_exc()})

        thread = threading.Thread(target=_run_job, daemon=True)
        thread.start()

        return jsonify({"job_id": job_id, "status": "started"})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "erro_interno", "mensagem": str(e)}), 500


@app.route("/api/progress/<job_id>", methods=["GET"])
def progress_stream(job_id):
    """SSE stream de progresso real-time."""
    job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": f"Job {job_id} não encontrado"}), 404

    def generate():
        # Enviar eventos já emitidos (para reconexão)
        for evt in job["events"]:
            yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"

        # Stream novos eventos
        while True:
            try:
                evt = job["queue"].get(timeout=120)  # 2 min timeout
                yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"
                if evt.get("event") in ("result", "error", "completo"):
                    break
            except queue.Empty:
                # Heartbeat para manter conexão viva
                yield f"data: {json.dumps({'event': 'heartbeat', 'pct': -1, 'detail': 'keepalive'})}\n\n"

    from flask import Response
    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@app.route("/api/job/<job_id>", methods=["GET"])
def job_status(job_id):
    """Polling fallback — retorna status e resultado se disponível."""
    job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": f"Job {job_id} não encontrado"}), 404

    response = {
        "job_id": job_id,
        "status": job["status"],
        "events": job["events"],
        "last_event": job["events"][-1] if job["events"] else None,
    }
    if job["status"] == "done":
        response["result"] = job["result"]

    return jsonify(response)


@app.route("/api/acervo/stats", methods=["GET"])
def acervo_stats():
    """Estatísticas do acervo DS."""
    return jsonify(agente.acervo.get_stats())


@app.route("/api/acervo/buscar", methods=["POST"])
def acervo_buscar():
    """Busca no acervo DS por texto."""
    body = request.get_json(silent=True) or {}
    texto = body.get("texto", "")
    top_k = body.get("top_k", 15)

    if not texto:
        return jsonify({"status": "erro", "mensagem": "Campo 'texto' obrigatório."}), 400

    docs = agente.acervo.buscar_relevantes(texto, top_k)
    return jsonify({
        "status": "ok",
        "total": len(docs),
        "documentos": docs,
    })


@app.route("/api/taxonomia", methods=["GET"])
def taxonomia():
    """Retorna a taxonomia completa."""
    return jsonify(agente.acervo.taxonomy)


@app.route("/api/validar", methods=["POST"])
def validar():
    """Valida dados do formulário sem executar o agente."""
    body = request.get_json(silent=True) or {}
    valido, erros = agente.validador.validar(body)
    return jsonify({
        "valido": valido,
        "erros": erros,
    })


# ═══════════════════════════════════════
# ROTA — FRONTEND (servir HTML estático)
# ═══════════════════════════════════════

@app.route("/")
def index():
    """Serve o frontend HTML principal."""
    frontend = Path(__file__).parent / "frontend"
    if (frontend / "agentificacaoDeOfertas.html").exists():
        return send_from_directory(str(frontend), "agentificacaoDeOfertas.html")
    return """
    <html>
    <head><title>Agente DS — Qualificação</title></head>
    <body style="font-family:sans-serif;background:#0a1628;color:#e0e6ed;display:grid;place-items:center;height:100vh;margin:0">
        <div style="text-align:center">
            <h1>🚀 Agente DS — Qualificação de Ofertas</h1>
            <p>Prática: Desenvolvimento de Soluções</p>
            <p>API ativa em <code>/api/health</code></p>
            <p><a href="/api/health" style="color:#00b0bd">Ver Health Check</a></p>
        </div>
    </body>
    </html>
    """


@app.route("/Arquitetura/<path:filename>")
def serve_arquitetura(filename):
    """Serve imagens de arquitetura."""
    arq_dir = Path(__file__).parent / "Arquitetura"
    return send_from_directory(str(arq_dir), filename)


@app.route("/<path:filename>")
def serve_frontend(filename):
    """Serve arquivos estáticos do frontend."""
    frontend = Path(__file__).parent / "frontend"
    return send_from_directory(str(frontend), filename)


# ═══════════════════════════════════════
# TRACE / AUDIT TRAIL API
# ═══════════════════════════════════════

from agente.trace_logger import TraceLogger

@app.route("/api/trace/list", methods=["GET"])
def trace_list():
    """Lista traces recentes."""
    limit = request.args.get("limit", 50, type=int)
    traces = TraceLogger.list_traces(limit=limit)
    return jsonify({"traces": traces, "total": len(traces)})


@app.route("/api/trace/<trace_id>", methods=["GET"])
def trace_get(trace_id):
    """Retorna trace completo por ID."""
    data = TraceLogger.load(trace_id)
    if not data:
        return jsonify({"error": f"Trace {trace_id} não encontrado"}), 404
    return jsonify(data)


@app.route("/api/trace/toggle", methods=["POST"])
def trace_toggle():
    """Habilita/desabilita trace para próximas execuções."""
    body = request.get_json(force=True, silent=True) or {}
    enabled = body.get("enabled", True)
    maestro.trace_enabled = bool(enabled)
    return jsonify({"trace_enabled": maestro.trace_enabled})


@app.route("/api/trace/diagnose/<trace_id>", methods=["GET"])
def trace_diagnose(trace_id):
    """Troubleshooting assistido — analisa o trace e sugere onde pode estar o problema."""
    data = TraceLogger.load(trace_id)
    if not data:
        return jsonify({"error": f"Trace {trace_id} não encontrado"}), 404

    events = data.get("events", [])
    steps = []
    warnings = []
    probable_issues = []

    # Step 1: Upload
    upload_events = [e for e in events if e.get("component") == "UPLOAD"]
    if upload_events:
        ev = upload_events[0]
        size = ev.get("data", {}).get("size_bytes", 0)
        ext = ev.get("data", {}).get("extension", "")
        steps.append({"step": 1, "name": "Upload do Documento", "status": "ok",
                       "detail": f"{ev.get('data', {}).get('filename', 'N/A')} ({size:,} bytes, {ext})"})
        if size < 100:
            warnings.append("Arquivo muito pequeno — pode não conter conteúdo suficiente para análise")
            probable_issues.append({"area": "Upload", "issue": "Arquivo com menos de 100 bytes", "severity": "ALTO"})
    else:
        steps.append({"step": 1, "name": "Upload do Documento", "status": "missing", "detail": "Evento de upload não encontrado"})
        probable_issues.append({"area": "Upload", "issue": "Evento de upload ausente no trace", "severity": "CRITICO"})

    # Step 2: Extração
    extract_events = [e for e in events if e.get("component") == "EXTRACAO"]
    if extract_events:
        ev = extract_events[0]
        chars = ev.get("data", {}).get("caracteres", 0)
        palavras = ev.get("data", {}).get("palavras", 0)
        steps.append({"step": 2, "name": "Extração de Texto", "status": "ok",
                       "detail": f"{chars:,} caracteres, {palavras:,} palavras extraídas"})
        if chars < 500:
            warnings.append(f"Texto muito curto ({chars} chars) — análise pode ser imprecisa")
            probable_issues.append({"area": "Extração", "issue": f"Apenas {chars} caracteres extraídos — documento pode estar protegido ou vazio", "severity": "ALTO"})
    else:
        steps.append({"step": 2, "name": "Extração de Texto", "status": "missing", "detail": "Extração não executada"})
        probable_issues.append({"area": "Extração", "issue": "Parser não conseguiu extrair texto", "severity": "CRITICO"})

    # Step 3: Tokenização
    token_events = [e for e in events if e.get("component") == "TOKENIZACAO"]
    if token_events:
        total = token_events[0].get("data", {}).get("total_tokens", 0)
        steps.append({"step": 3, "name": "Tokenização", "status": "ok", "detail": f"{total} tokens únicos"})
    else:
        steps.append({"step": 3, "name": "Tokenização", "status": "missing", "detail": "Tokenização não registrada"})

    # Step 4: SA1 — Extração Estruturada
    sa1_events = [e for e in events if e.get("component") == "SA1"]
    if sa1_events:
        result_ev = [e for e in sa1_events if e.get("action") == "resultado"]
        detail = result_ev[0].get("detail", "") if result_ev else "Processado"
        steps.append({"step": 4, "name": "SA1 — Extração Estruturada", "status": "ok", "detail": detail})
        # Check tech detections
        tech_events = [e for e in events if e.get("component") == "SA2" and e.get("action") == "tech_detectada"]
        if not tech_events:
            tech_events = [e for e in sa1_events if "tech" in e.get("action", "")]
        if not tech_events:
            warnings.append("Nenhuma tecnologia detectada no documento — score técnico pode ser baixo")
            probable_issues.append({"area": "SA1/SA2", "issue": "Zero tecnologias reconhecidas — documento pode não ser uma RFP técnica", "severity": "MEDIO"})
    else:
        steps.append({"step": 4, "name": "SA1 — Extração Estruturada", "status": "missing", "detail": "SA1 não executou"})
        probable_issues.append({"area": "SA1", "issue": "Sub-agente Extrator não executou", "severity": "CRITICO"})

    # Step 5: Acervo KB
    acervo_events = [e for e in events if e.get("component") == "ACERVO"]
    match_events = [e for e in events if e.get("level") == "MATCH"]
    if acervo_events:
        busca_concl = [e for e in acervo_events if e.get("action") == "busca_concluida"]
        cobertura = busca_concl[0].get("data", {}).get("cobertura", 0) if busca_concl else 0
        steps.append({"step": 5, "name": "Consulta Acervo DS", "status": "ok",
                       "detail": f"{len(match_events)} docs matcharam, cobertura {cobertura}/10"})
        if len(match_events) < 5:
            warnings.append(f"Apenas {len(match_events)} documentos relevantes encontrados na KB")
            probable_issues.append({"area": "Acervo", "issue": f"Baixa correspondência na KB ({len(match_events)} docs) — setor/tipo pode não ter cobertura", "severity": "MEDIO"})
        if cobertura < 3:
            probable_issues.append({"area": "Acervo", "issue": f"Cobertura KB muito baixa ({cobertura}/10) — faltam cases/atestados para este tipo de projeto", "severity": "ALTO"})
    else:
        steps.append({"step": 5, "name": "Consulta Acervo DS", "status": "missing", "detail": "Consulta ao acervo não executada"})
        probable_issues.append({"area": "Acervo", "issue": "Acervo DS não foi consultado", "severity": "CRITICO"})

    # Step 6: SA2+SA3+SA4
    for sa_id, sa_name in [("SA2", "Análise Técnica"), ("SA3", "Análise de Riscos"), ("SA4", "Análise Comercial")]:
        sa_events = [e for e in events if e.get("component") == sa_id]
        if sa_events:
            result_ev = [e for e in sa_events if e.get("action") == "resultado"]
            detail = result_ev[0].get("detail", "") if result_ev else "Processado"
            steps.append({"step": 6, "name": f"{sa_id} — {sa_name}", "status": "ok", "detail": detail})
        else:
            steps.append({"step": 6, "name": f"{sa_id} — {sa_name}", "status": "missing", "detail": f"{sa_id} não executou"})
            probable_issues.append({"area": sa_id, "issue": f"Sub-agente {sa_name} não executou", "severity": "CRITICO"})

    # Check risks
    risk_events = [e for e in events if e.get("level") == "DETAIL" and "risco" in e.get("action", "")]
    criticos = [e for e in risk_events if e.get("data", {}).get("severidade") == "ALTO"]
    if len(criticos) >= 3:
        warnings.append(f"{len(criticos)} riscos CRÍTICOS detectados — pode impactar decisão para NO_GO")

    # Step 7: Faróis
    farol_events = [e for e in events if e.get("level") == "SCORE"]
    if farol_events:
        low_farois = [e for e in farol_events if e.get("data", {}).get("score", 10) < 4]
        steps.append({"step": 7, "name": "Cálculo dos 8 Faróis", "status": "ok",
                       "detail": f"{len(farol_events)} faróis calculados, {len(low_farois)} abaixo de 4/10"})
        for lf in low_farois:
            probable_issues.append({"area": "Faróis", "issue": f"Farol '{lf.get('data', {}).get('nome', 'N/A')}' com score {lf.get('data', {}).get('score', 0)}/10 — puxa score final para baixo", "severity": "MEDIO"})
    else:
        steps.append({"step": 7, "name": "Cálculo dos 8 Faróis", "status": "missing", "detail": "Faróis não calculados"})

    # Step 8: Decisão
    decision_events = [e for e in events if e.get("level") == "DECISION"]
    if decision_events:
        dec = decision_events[0]
        steps.append({"step": 8, "name": "Decisão Final (SA5)", "status": "ok",
                       "detail": f"{dec.get('data', {}).get('decisao', 'N/A')} — Score {dec.get('data', {}).get('score', 0)}, Confiança {dec.get('data', {}).get('confianca_pct', 0)}%"})
    else:
        steps.append({"step": 8, "name": "Decisão Final (SA5)", "status": "missing", "detail": "Decisão não gerada"})
        probable_issues.append({"area": "SA5", "issue": "Decisor não gerou resultado final", "severity": "CRITICO"})

    return jsonify({
        "trace_id": trace_id,
        "steps": steps,
        "warnings": warnings,
        "probable_issues": probable_issues,
        "total_events": len(events),
        "kb_matches": len(match_events),
        "risks_detected": len(risk_events),
        "farois_calculated": len(farol_events),
        "duration_ms": data.get("duration_ms", 0),
    })


# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════

if __name__ == "__main__":
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8005"))
    debug = os.getenv("DEBUG", "true").lower() == "true"

    print(f"""
╔══════════════════════════════════════════════════════╗
║  AGENTE DS — QUALIFICAÇÃO DE OFERTAS                ║
║  Prática: Desenvolvimento de Soluções               ║
║  Versão: 1.0.0 | DSS Agents | Indra Minsait         ║
╠══════════════════════════════════════════════════════╣
║  Engine:  Maestro + 5 Sub-Agentes (Multi-Agente)     ║
╠══════════════════════════════════════════════════════╣
║  Servidor: http://{host}:{port}                       ║
║  API:      http://{host}:{port}/api/health            ║
║  Acervo:   {maestro.acervo.acervo_root}
║  Catalog:  {len(maestro.acervo.catalog)} documentos indexados
║  Sub-Agentes: SA1→SA2+SA3+SA4→SA5                    ║
╚══════════════════════════════════════════════════════╝
    """)

    app.run(host=host, port=port, debug=debug)
