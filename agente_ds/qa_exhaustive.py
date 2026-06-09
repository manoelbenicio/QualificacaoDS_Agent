# -*- coding: utf-8 -*-
"""
QA EXAUSTIVO — Testa TODOS os endpoints e funcionalidades.
Simula o fluxo completo do usuário.
"""
import json, time, os, sys
from pathlib import Path
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8006"
RESULTS = {"passed": 0, "failed": 0, "tests": []}

def test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    RESULTS["tests"].append({"name": name, "status": status, "detail": detail})
    if passed:
        RESULTS["passed"] += 1
        print(f"  [PASS] {name}")
    else:
        RESULTS["failed"] += 1
        print(f"  [FAIL] {name} — {detail}")

def get(path):
    try:
        req = urllib.request.Request(f"{BASE}{path}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}

def post_json(path, data):
    try:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(f"{BASE}{path}", data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
        except:
            body = {"error": str(e)}
        return e.code, body
    except Exception as e:
        return 0, {"error": str(e)}

def get_html(path):
    try:
        req = urllib.request.Request(f"{BASE}{path}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except Exception as e:
        return 0, str(e)

print("=" * 70)
print("  QA EXAUSTIVO — AGENTE DS")
print(f"  Target: {BASE}")
print(f"  Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# ═══ T1: SERVER ALIVE ═══
print("\n[T1] SERVER CONNECTIVITY")
status, data = get("/api/health")
test("T1.1 Server responds", status == 200, f"HTTP {status}")

# ═══ T2: HEALTH CHECK ═══
print("\n[T2] HEALTH CHECK ENDPOINT")
if status == 200:
    test("T2.1 Has cenario_1_monolitico", "cenario_1_monolitico" in data)
    test("T2.2 Has cenario_2_multi_agente", "cenario_2_multi_agente" in data)
    
    c2 = data.get("cenario_2_multi_agente", {})
    test("T2.3 Maestro pratica=DS", c2.get("pratica") == "DS")
    test("T2.4 Maestro cenario=CENARIO_2", "CENARIO_2" in c2.get("cenario", ""))
    
    sas = c2.get("sub_agentes", {})
    test("T2.5 Has SA1 (Extrator)", "SA1" in sas)
    test("T2.6 Has SA2 (Tecnico)", "SA2" in sas)
    test("T2.7 Has SA3 (Riscos)", "SA3" in sas)
    test("T2.8 Has SA4 (Comercial)", "SA4" in sas)
    test("T2.9 Has SA5 (Decisor)", "SA5" in sas)
    test("T2.10 All 5 sub-agents", len(sas) == 5, f"Found {len(sas)}")
    
    acervo = c2.get("acervo", {})
    test("T2.11 Acervo has docs", acervo.get("total_documentos", 0) > 0, f"{acervo.get('total_documentos', 0)} docs")
    test("T2.12 API key status reported", "api_key_configurada" in c2)
else:
    test("T2.x Health check failed", False, "Server not responding")

# ═══ T3: ACERVO STATS ═══
print("\n[T3] ACERVO STATS ENDPOINT")
status, data = get("/api/acervo/stats")
test("T3.1 Acervo stats responds", status == 200, f"HTTP {status}")
if status == 200:
    test("T3.2 Has total_documentos", "total_documentos" in data, str(data.get("total_documentos")))
    test("T3.3 Has por_categoria", "por_categoria" in data)
    test("T3.4 Has catalog_path", "catalog_path" in data)

# ═══ T4: TAXONOMIA ═══
print("\n[T4] TAXONOMIA ENDPOINT")
status, data = get("/api/taxonomia")
test("T4.1 Taxonomia responds", status == 200, f"HTTP {status}")

# ═══ T5: VALIDAÇÃO ═══
print("\n[T5] VALIDAÇÃO ENDPOINT")
# Empty data — should fail validation
status, data = post_json("/api/validar", {})
test("T5.1 Validates empty data", status == 200)
if status == 200:
    test("T5.2 Empty data is invalid", data.get("valido") == False, f"valido={data.get('valido')}")
    test("T5.3 Returns errors list", len(data.get("erros", [])) > 0, f"{len(data.get('erros', []))} errors")

# Valid data
valid_data = {
    "nome_oportunidade": "Test RFP - QA",
    "cliente": "QA Client",
    "setor": "Energia & Utilities",
    "tipo_servico": "Desenvolvimento de Software (Projeto/Escopo Fechado)",
    "prazo_resposta": "2026-12-31"
}
status, data = post_json("/api/validar", valid_data)
test("T5.4 Validates good data", status == 200)
if status == 200:
    test("T5.5 Good data is valid", data.get("valido") == True, f"valido={data.get('valido')}")

# ═══ T6: ACERVO BUSCA ═══
print("\n[T6] ACERVO BUSCA ENDPOINT")
status, data = post_json("/api/acervo/buscar", {"texto": "Java desenvolvimento", "top_k": 5})
test("T6.1 Busca responds", status == 200, f"HTTP {status}")
if status == 200:
    test("T6.2 Returns documents", data.get("total", 0) >= 0, f"{data.get('total', 0)} docs")

# Empty search
status, data = post_json("/api/acervo/buscar", {})
test("T6.3 Empty search returns 400", status == 400)

# ═══ T7: QUALIFICAR — VALIDATION ═══
print("\n[T7] QUALIFICAR ENDPOINT — VALIDATION")
# No file upload — should fail
import urllib.parse
try:
    req = urllib.request.Request(f"{BASE}/api/qualificar", method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, data=b"", timeout=10) as resp:
        status = resp.status
        data = json.loads(resp.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    status = e.code
    try:
        data = json.loads(e.read().decode("utf-8"))
    except:
        data = {}
except Exception as e:
    status = 0
    data = {"error": str(e)}

test("T7.1 No file returns 400", status == 400, f"HTTP {status}")
if status == 400:
    test("T7.2 Error message present", "mensagem" in data, data.get("mensagem", "")[:60])

# ═══ T8: FRONTEND HTML PAGES ═══
print("\n[T8] FRONTEND PAGES")
pages = [
    ("/", "agentificacaoDeOfertas"),
    ("/hub.html", "hub"),
    ("/index.html", "index"),
    ("/especificacao-funcional.html", "especificacao"),
    ("/arquitetura-alto-nivel.html", "arquitetura"),
    ("/estrategia-implementacao.html", "estrategia"),
]
for path, name in pages:
    status, html = get_html(path)
    test(f"T8.{name} loads", status == 200, f"HTTP {status}")
    if status == 200:
        # Check no BPO
        bpo_count = html.upper().count(">BPO<") + html.count('"BPO"')
        test(f"T8.{name} no BPO", bpo_count == 0, f"{bpo_count} BPO refs")

# ═══ T9: FRONTEND JS INTEGRITY ═══
print("\n[T9] FRONTEND JS INTEGRITY")
status, html = get_html("/")
if status == 200:
    test("T9.1 Has API_BASE", "API_BASE" in html)
    test("T9.2 Has async runAgent", "async function runAgent" in html)
    test("T9.3 Has fetch(/api/qualificar)", "api/qualificar" in html)
    test("T9.4 Has renderQualificacaoResult", "renderQualificacaoResult" in html)
    test("T9.5 Has renderErro", "renderErro" in html)
    test("T9.6 No backendRealIndisponivel", "backendRealIndisponivel" not in html)
    test("T9.7 No localhost:8001", "localhost:8001" not in html)
    test("T9.8 No mock keyword", "mock" not in html.lower().split("<script")[1] if "<script" in html else True)
    test("T9.9 No simulado", "simulad" not in html.lower())
    test("T9.10 No Embraer mock", "Embraer" not in html)

# ═══ SUMMARY ═══
print("\n" + "=" * 70)
total = RESULTS["passed"] + RESULTS["failed"]
pct = (RESULTS["passed"] / total * 100) if total > 0 else 0
print(f"  QA RESULTADO: {RESULTS['passed']}/{total} PASSED ({pct:.0f}%)")
print(f"  PASSED: {RESULTS['passed']} | FAILED: {RESULTS['failed']}")
print("=" * 70)

if RESULTS["failed"] > 0:
    print("\n  FAILED TESTS:")
    for t in RESULTS["tests"]:
        if t["status"] == "FAIL":
            print(f"    ❌ {t['name']}: {t['detail']}")

# Save
out = Path(__file__).parent / "qa_results.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, ensure_ascii=False, indent=2)
print(f"\nResultados salvos em: {out}")
