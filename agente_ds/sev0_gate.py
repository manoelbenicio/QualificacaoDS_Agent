# -*- coding: utf-8 -*-
"""
SEV-0 VALIDATION GATE — Protocolo de Verificação Obrigatório
Executa TODOS os testes de regressão após qualquer mudança de código.
Nenhuma mudança é considerada "pronta" até que este script passe 100%.

Protocolo SEV-0:
  1. Compilação / Import ✓
  2. Validação Backend (API endpoints) ✓
  3. Validação Frontend (HTML integrity) ✓
  4. Cross-validation (Frontend ↔ Backend alignment) ✓
  5. Regression (nenhum teste anterior quebrou) ✓
  6. E2E Smoke Test (upload + qualificar simulado) ✓
  7. CI Quality Gate (SKIP — requer aprovação do usuário)
"""
import sys
import json
import time
import re
import traceback
from pathlib import Path
from datetime import datetime

BASE = "http://127.0.0.1:8006"
RESULTS = {"passed": 0, "failed": 0, "tests": []}
TIMESTAMP = datetime.now().isoformat()


def log(test_id, desc, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    RESULTS["passed" if passed else "failed"] += 1
    RESULTS["tests"].append({"id": test_id, "desc": desc, "status": status, "detail": detail})
    print(f"  [{status}] {test_id} {desc}" + (f" — {detail}" if detail and not passed else ""))


def get(path):
    from urllib.request import urlopen, Request
    try:
        r = urlopen(Request(f"{BASE}{path}"), timeout=10)
        return r.getcode(), json.loads(r.read())
    except Exception as e:
        return 0, {"error": str(e)}


def post_json(path, data):
    from urllib.request import urlopen, Request
    body = json.dumps(data).encode()
    try:
        req = Request(f"{BASE}{path}", data=body, headers={"Content-Type": "application/json"})
        r = urlopen(req, timeout=10)
        return r.getcode(), json.loads(r.read())
    except Exception as e:
        code = getattr(e, 'code', 0)
        try:
            resp = json.loads(e.read()) if hasattr(e, 'read') else {}
        except:
            resp = {"error": str(e)}
        return code, resp


def get_html(path):
    from urllib.request import urlopen
    try:
        r = urlopen(f"{BASE}{path}", timeout=10)
        return r.getcode(), r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return 0, str(e)


# ═══════════════════════════════════════
# GATE 1: COMPILAÇÃO / IMPORT
# ═══════════════════════════════════════
print("\n[GATE 1] COMPILAÇÃO / IMPORT")
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from agente.validacao import ValidadorInput, SETORES_VALIDOS, TIPOS_SERVICO_DS
    log("G1.1", "ValidadorInput imports OK", True)
except Exception as e:
    log("G1.1", "ValidadorInput imports", False, str(e))

try:
    from agente.extracao import ExtratorDocumental
    ext = ExtratorDocumental()
    log("G1.2", "ExtratorDocumental imports OK", True)
    log("G1.3", f"Parsers: {len(ext._parsers)} types", len(ext._parsers) >= 10, f"{list(ext._parsers.keys())}")
except Exception as e:
    log("G1.2", "ExtratorDocumental imports", False, str(e))

try:
    from agente.adk_robo import ADKRobo
    adk = ADKRobo()
    log("G1.4", "ADKRobo imports OK", True)
except Exception as e:
    log("G1.4", "ADKRobo imports", False, str(e))

try:
    from agente.sub_agentes.maestro import Maestro
    m = Maestro()
    log("G1.5", "Maestro imports OK", True)
    log("G1.6", f"Maestro modo: {m.health_check().get('modo', 'N/A')}", True)
except Exception as e:
    log("G1.5", "Maestro imports", False, str(e))

try:
    from agente.acervo import AcervoDS
    acervo = AcervoDS()
    n = len(acervo.catalog)
    log("G1.7", f"AcervoDS loaded: {n} docs", n > 100, f"Only {n} docs!")
except Exception as e:
    log("G1.7", "AcervoDS imports", False, str(e))

# ═══════════════════════════════════════
# GATE 2: VALIDAÇÃO BACKEND (API)
# ═══════════════════════════════════════
print("\n[GATE 2] VALIDAÇÃO BACKEND (API)")
code, data = get("/api/health")
log("G2.1", "Health responds", code == 200)
log("G2.2", "Has cenario_2", "cenario_2_multi_agente" in data)
if "cenario_2_multi_agente" in data:
    c2 = data["cenario_2_multi_agente"]
    log("G2.3", "Maestro pratica=DS", c2.get("pratica") == "DS")
    sas = c2.get("sub_agentes", {})
    log("G2.4", "5 sub-agents", len(sas) == 5, f"Found {len(sas)}")
    log("G2.5", f"Acervo docs: {c2.get('acervo', {}).get('total_documentos', 0)}", c2.get("acervo", {}).get("total_documentos", 0) > 100)

code, data = get("/api/acervo/stats")
log("G2.6", "Acervo stats OK", code == 200)
log("G2.7", f"Total docs: {data.get('total_documentos', 0)}", data.get("total_documentos", 0) > 100)

code, data = get("/api/taxonomia")
log("G2.8", "Taxonomia OK", code == 200)

# ═══════════════════════════════════════
# GATE 3: VALIDAÇÃO FRONTEND (HTML)
# ═══════════════════════════════════════
print("\n[GATE 3] VALIDAÇÃO FRONTEND (HTML)")
code, html = get_html("/")
log("G3.1", "Main page loads", code == 200)
log("G3.2", "No BPO in page", "BPO" not in html)
log("G3.3", "Has API_BASE", "API_BASE" in html)
log("G3.4", "Has async runAgent", "async function runAgent" in html)
log("G3.5", "Has fetch(/api/qualificar)", "fetch" in html and "/api/qualificar" in html)
log("G3.6", "No backendRealIndisponivel", "backendRealIndisponivel" not in html)
log("G3.7", "No localhost:8001", "localhost:8001" not in html)
log("G3.8", "Has suggestAutoFill", "suggestAutoFill" in html)
log("G3.9", "Has executeAutoFill", "executeAutoFill" in html)
log("G3.10", "Has dismissAutoFill", "dismissAutoFill" in html)

# ═══════════════════════════════════════
# GATE 4: CROSS-VALIDATION (Frontend ↔ Backend)
# ═══════════════════════════════════════
print("\n[GATE 4] CROSS-VALIDATION (Frontend ↔ Backend)")

# Check that dropdown values match validator enums
for setor in SETORES_VALIDOS:
    # HTML encodes & as &amp; in some contexts, but select option text is raw
    found = setor in html or setor.replace("&", "&amp;") in html
    log(f"G4.S", f"Setor '{setor}' in dropdown", found, f"Not found in HTML!")

for tipo in TIPOS_SERVICO_DS:
    found = tipo in html or tipo.replace("&", "&amp;") in html
    log(f"G4.T", f"Tipo '{tipo}' in dropdown", found, f"Not found in HTML!")

# Validate that good data passes
valid_data = {
    "nome_oportunidade": "Test Oportunidade QA",
    "cliente": "Cliente QA Test",
    "setor": "Energia & Utilities",
    "tipo_servico": "Desenvolvimento de Software (Projeto/Escopo Fechado)",
    "prazo_resposta": "2026-12-31",
}
code, data = post_json("/api/validar", valid_data)
log("G4.V1", "Valid data passes validation", code == 200 and data.get("valido") == True, f"valido={data.get('valido')}, erros={data.get('erros')}")

# Test every setor
for setor in SETORES_VALIDOS:
    test = {**valid_data, "setor": setor}
    code, data = post_json("/api/validar", test)
    log("G4.VS", f"Setor '{setor}' validates", data.get("valido") == True, f"erros={data.get('erros')}")

# Test every tipo_servico
for tipo in TIPOS_SERVICO_DS:
    test = {**valid_data, "tipo_servico": tipo}
    code, data = post_json("/api/validar", test)
    log("G4.VT", f"Tipo '{tipo}' validates", data.get("valido") == True, f"erros={data.get('erros')}")

# ═══════════════════════════════════════
# GATE 5: REGRESSION (Previous tests)
# ═══════════════════════════════════════
print("\n[GATE 5] REGRESSION")

# Empty data invalid
code, data = post_json("/api/validar", {})
log("G5.1", "Empty data is invalid", data.get("valido") == False)

# No file returns 400
from urllib.request import urlopen, Request
from urllib.error import HTTPError
try:
    req = Request(f"{BASE}/api/qualificar", data=b"", headers={"Content-Type": "application/json"}, method="POST")
    urlopen(req, timeout=10)
    log("G5.2", "No file returns 400", False, "Got 200!")
except HTTPError as e:
    log("G5.2", "No file returns 400", e.code == 400, f"Got {e.code}")

# Busca works
code, data = post_json("/api/acervo/buscar", {"texto": "java cloud", "top_k": 5})
log("G5.3", "Busca returns results", code == 200 and data.get("total", 0) > 0, f"total={data.get('total')}")

# Empty busca returns 400
code, data = post_json("/api/acervo/buscar", {"texto": ""})
log("G5.4", "Empty busca returns 400", code == 400)

# All pages load
for page in ["hub.html", "index.html", "especificacao-funcional.html", "arquitetura-alto-nivel.html", "estrategia-implementacao.html"]:
    code, _ = get_html(f"/{page}")
    log("G5.P", f"Page {page} loads", code == 200)

# ═══════════════════════════════════════
# GATE 6: E2E SMOKE TEST
# ═══════════════════════════════════════
print("\n[GATE 6] E2E SMOKE TEST")

# Create test file
import tempfile, os
test_file = Path(tempfile.gettempdir()) / "sev0_test_rfp.txt"
test_file.write_text("""
RFP - Desenvolvimento de Plataforma Digital
Cliente: Energisa
Escopo: Desenvolvimento de portal de autoatendimento com integração SAP e mobile.
Tecnologias: Java, Spring Boot, React, PostgreSQL, Docker, Kubernetes, AWS.
Prazo: 6 meses. SLA: 99.5% uptime.
Valor estimado: R$ 3.500.000,00
Requisitos: RF001 - Login SSO, RF002 - Dashboard, RF003 - Relatórios.
Compliance: LGPD obrigatório. Multa por atraso: 2% ao mês.
""", encoding="utf-8")

# Simulate multipart upload
import io
boundary = "----SEV0TestBoundary"
body_parts = []

# File part
body_parts.append(f"--{boundary}")
body_parts.append(f'Content-Disposition: form-data; name="rfp"; filename="sev0_test_rfp.txt"')
body_parts.append("Content-Type: text/plain")
body_parts.append("")
body_parts.append(test_file.read_text(encoding="utf-8"))

# Dados part
dados = json.dumps({
    "nome_oportunidade": "SEV-0 Test - Portal Energisa",
    "cliente": "Energisa",
    "setor": "Energia & Utilities",
    "tipo_servico": "Desenvolvimento de Software (Projeto/Escopo Fechado)",
    "prazo_resposta": "2026-12-31",
    "acv_estimado": "3500000",
    "cenario": "2",
})
body_parts.append(f"--{boundary}")
body_parts.append('Content-Disposition: form-data; name="dados"')
body_parts.append("")
body_parts.append(dados)
body_parts.append(f"--{boundary}--")

body = "\r\n".join(body_parts).encode("utf-8")

try:
    req = Request(
        f"{BASE}/api/qualificar",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    r = urlopen(req, timeout=30)
    result = json.loads(r.read())

    log("G6.1", "Qualificar returns 200", True)
    log("G6.2", f"Status: {result.get('status')}", result.get("status") == "concluido")
    log("G6.3", f"Motor: {result.get('motor', 'N/A')[:40]}", "ADK" in result.get("motor", "") or "Claude" in result.get("motor", ""))

    parecer = result.get("parecer", {})
    log("G6.4", f"Decisao: {parecer.get('decisao', 'N/A')}", parecer.get("decisao") in ("GO", "NO_GO", "GO_CONDICIONADO"))
    log("G6.5", f"Score: {parecer.get('score_final', 0)}", parecer.get("score_final", 0) > 0)
    log("G6.6", "Has farois", len(parecer.get("farois_consolidados", [])) == 8, f"Found {len(parecer.get('farois_consolidados', []))}")
    log("G6.7", "Has BSW", bool(parecer.get("best_story_wins")))
    log("G6.8", "Has dimensionamento", bool(parecer.get("dimensionamento_final")))
    log("G6.9", "Has riscos", bool(parecer.get("riscos_consolidados")))
    log("G6.10", "Has next_steps", len(parecer.get("next_steps", [])) > 0)

    # Check intermediários
    inter = result.get("outputs_intermediarios", {})
    log("G6.11", "Has SA1 output", bool(inter.get("SA1_extracao")))
    log("G6.12", "Has SA2 output", bool(inter.get("SA2_tecnico")))
    log("G6.13", "Has SA3 output", bool(inter.get("SA3_riscos")))
    log("G6.14", "Has SA4 output", bool(inter.get("SA4_comercial")))

    # Check KB match
    kb = result.get("kb_match", {})
    log("G6.15", f"KB docs analyzed: {kb.get('total_docs', 0)}", kb.get("total_docs", 0) > 100)
    log("G6.16", f"KB relevant: {kb.get('relevantes', 0)}", kb.get("relevantes", 0) > 0)

except HTTPError as e:
    resp = e.read().decode() if hasattr(e, 'read') else str(e)
    log("G6.1", f"Qualificar failed: {e.code}", False, resp[:200])
except Exception as e:
    log("G6.1", "Qualificar exception", False, str(e)[:200])

# Cleanup
test_file.unlink(missing_ok=True)


# ═══════════════════════════════════════
# RESULTADO FINAL
# ═══════════════════════════════════════
total = RESULTS["passed"] + RESULTS["failed"]
pct = round(RESULTS["passed"] / total * 100, 1) if total > 0 else 0

print(f"""
{'='*70}
  SEV-0 VALIDATION GATE — RESULTADO
  Timestamp: {TIMESTAMP}
  Total: {total} | Passed: {RESULTS['passed']} | Failed: {RESULTS['failed']} | Score: {pct}%
{'='*70}""")

if RESULTS["failed"] > 0:
    print("\n  FAILED TESTS:")
    for t in RESULTS["tests"]:
        if t["status"] == "FAIL":
            print(f"    ❌ {t['id']} {t['desc']}: {t['detail']}")

# Save
out = Path(__file__).parent / "sev0_results.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump({"timestamp": TIMESTAMP, "total": total, "passed": RESULTS["passed"],
               "failed": RESULTS["failed"], "pct": pct, "tests": RESULTS["tests"]}, f, ensure_ascii=False, indent=2)
print(f"\nResultados: {out}")

if RESULTS["failed"] > 0:
    print("\n⛔ SEV-0 GATE FAILED — MUDANÇAS NÃO PODEM SER PROMOVIDAS")
    sys.exit(1)
else:
    print("\n✅ SEV-0 GATE PASSED — MUDANÇAS APROVADAS PARA PROMOÇÃO")
    sys.exit(0)
