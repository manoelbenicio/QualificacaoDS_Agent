# -*- coding: utf-8 -*-
"""
AUDITORIA COMPLETA — Sistema Agente DS
Identifica TODOS os problemas antes de corrigir.
"""
import re, json, os, sys
from pathlib import Path

ROOT = Path(__file__).parent
FRONTEND = ROOT / "frontend"
RESULTS = {"issues": [], "ok": []}

def issue(cat, desc, file="", line=0):
    RESULTS["issues"].append({"cat": cat, "desc": desc, "file": str(file), "line": line})

def ok(cat, desc):
    RESULTS["ok"].append({"cat": cat, "desc": desc})

print("=" * 70)
print("  AUDITORIA COMPLETA — AGENTE DS v1.0")
print("=" * 70)

# ═══ 1. STRUCTURE ═══
print("\n[1] ESTRUTURA DE ARQUIVOS")
expected_files = [
    "server.py", ".env", "requirements.txt",
    "agente/__init__.py", "agente/agente_ds.py", "agente/acervo.py",
    "agente/extracao.py", "agente/validacao.py",
    "agente/sub_agentes/__init__.py", "agente/sub_agentes/maestro.py",
    "agente/sub_agentes/sa1_extrator.py", "agente/sub_agentes/sa2_analista_tecnico.py",
    "agente/sub_agentes/sa3_analista_riscos.py", "agente/sub_agentes/sa4_analista_comercial.py",
    "agente/sub_agentes/sa5_decisor.py",
    "frontend/agentificacaoDeOfertas.html",
]
for f in expected_files:
    p = ROOT / f
    if p.exists():
        ok("STRUCTURE", f"EXISTS: {f} ({p.stat().st_size:,}B)")
    else:
        issue("STRUCTURE", f"MISSING: {f}", f)

# ═══ 2. PYTHON IMPORTS ═══
print("\n[2] PYTHON IMPORTS")
try:
    sys.path.insert(0, str(ROOT))
    from agente import AgenteDS, Maestro
    ok("IMPORT", "AgenteDS + Maestro imported OK")
except Exception as e:
    issue("IMPORT", f"Failed: {e}")

try:
    from agente.sub_agentes import sa1_extrator, sa2_analista_tecnico, sa3_analista_riscos, sa4_analista_comercial, sa5_decisor
    ok("IMPORT", "All 5 sub-agents imported OK")
except Exception as e:
    issue("IMPORT", f"Sub-agents failed: {e}")

# ═══ 3. MAESTRO HEALTH ═══
print("\n[3] MAESTRO HEALTH")
try:
    m = Maestro()
    h = m.health_check()
    sa_count = len(h.get("sub_agentes", {}))
    doc_count = h.get("acervo", {}).get("total_documentos", 0)
    api_key = h.get("api_key_configurada", False)
    ok("MAESTRO", f"{sa_count} sub-agents, {doc_count} docs indexed")
    if not api_key:
        issue("CONFIG", "ANTHROPIC_API_KEY not configured in .env", ".env")
    else:
        ok("CONFIG", "API key configured")
except Exception as e:
    issue("MAESTRO", f"Health check failed: {e}")

# ═══ 4. SERVER.PY SYNTAX ═══
print("\n[4] SERVER SYNTAX")
try:
    import py_compile
    py_compile.compile(str(ROOT / "server.py"), doraise=True)
    ok("SERVER", "server.py compiles OK")
except Exception as e:
    issue("SERVER", f"server.py compile error: {e}", "server.py")

# ═══ 5. SERVER ROUTES ═══
print("\n[5] SERVER ROUTES")
srv_text = (ROOT / "server.py").read_text(encoding="utf-8")
routes = re.findall(r'@app\.route\(["\']([^"\']+)', srv_text)
for r in routes:
    ok("ROUTE", f"Endpoint: {r}")

# Check critical routes exist
for needed in ["/api/health", "/api/qualificar", "/api/acervo/stats", "/"]:
    if needed in routes:
        ok("ROUTE", f"Critical route {needed} EXISTS")
    else:
        issue("ROUTE", f"Critical route {needed} MISSING", "server.py")

# ═══ 6. FRONTEND — MOCK/PLACEHOLDER AUDIT ═══
print("\n[6] FRONTEND MOCK AUDIT")
html_path = FRONTEND / "agentificacaoDeOfertas.html"
if html_path.exists():
    html = html_path.read_text(encoding="utf-8-sig")
    
    # Critical mocks that MUST be zero
    critical_checks = {
        "backendRealIndisponivel": html.count("backendRealIndisponivel"),
        "localhost:8001": html.count("localhost:8001"),
        "localhost:8000": html.count("localhost:8000"),
        "mock": len(re.findall(r'\bmock\b', html, re.IGNORECASE)),
    }
    for kw, count in critical_checks.items():
        if count > 0:
            issue("FRONTEND_MOCK", f"'{kw}' found {count} times — MUST BE ZERO", "frontend/agentificacaoDeOfertas.html")
        else:
            ok("FRONTEND_MOCK", f"'{kw}' = 0 (clean)")
    
    # Simulado check (exclude CSS)
    simulad_count = len(re.findall(r'simulad', html, re.IGNORECASE))
    if simulad_count > 0:
        # Find lines
        for i, line in enumerate(html.split("\n"), 1):
            if re.search(r'simulad', line, re.IGNORECASE):
                issue("FRONTEND_MOCK", f"'simulad' on line {i}: {line.strip()[:80]}", "frontend/agentificacaoDeOfertas.html", i)
    else:
        ok("FRONTEND_MOCK", "'simulad' = 0 (clean)")
    
    # Check API connection
    if "API_BASE" in html and "fetch(" in html:
        ok("FRONTEND_API", "API_BASE + fetch() found — real connection")
    else:
        issue("FRONTEND_API", "No API_BASE or fetch() — frontend not connected", "frontend/agentificacaoDeOfertas.html")
    
    # Check async runAgent
    if "async function runAgent" in html:
        ok("FRONTEND_API", "runAgent is async (real API call)")
    else:
        issue("FRONTEND_API", "runAgent is NOT async — still mock?", "frontend/agentificacaoDeOfertas.html")
    
    # Check for dead code (old generateOutput with Embraer mock)
    if "Embraer" in html:
        embraer_count = html.count("Embraer")
        issue("FRONTEND_MOCK", f"'Embraer' hardcoded {embraer_count} times (dead mock data)", "frontend/agentificacaoDeOfertas.html")
    
    if "kimi-k2" in html.lower() or "moonshotai" in html.lower():
        issue("FRONTEND_MOCK", "'kimi-k2' or 'moonshotai' hardcoded (mock model refs)", "frontend/agentificacaoDeOfertas.html")
    
    # Check file input preservation (handleFile replaces DOM)
    if "handleFile" in html:
        # Check if file input is preserved after upload
        if "appendChild(fileInput)" in html:
            ok("FRONTEND_UX", "File input preserved after upload (appendChild)")
        else:
            issue("FRONTEND_UX", "File input may be lost after upload — runAgent won't find it", "frontend/agentificacaoDeOfertas.html")

    # BPO check
    bpo_count = len(re.findall(r'\bBPO\b', html))
    if bpo_count > 0:
        issue("FRONTEND_BPO", f"'BPO' still found {bpo_count} times", "frontend/agentificacaoDeOfertas.html")
    else:
        ok("FRONTEND_BPO", "Zero BPO references")

# ═══ 7. ENV CONFIG ═══
print("\n[7] ENV CONFIG")
env_path = ROOT / ".env"
if env_path.exists():
    env_text = env_path.read_text(encoding="utf-8")
    for line in env_text.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key = line.split("=")[0].strip()
            val = line.split("=", 1)[1].strip()
            if "KEY" in key.upper():
                if not val or val.startswith("sk-ant-your") or val == "":
                    issue("CONFIG", f"{key} not set (placeholder)", ".env")
                else:
                    ok("CONFIG", f"{key} configured")
            else:
                ok("CONFIG", f"{key} = {val}")

# ═══ 8. PORT CHECK ═══
print("\n[8] PORT CHECK")
import subprocess
try:
    result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=5)
    if ":8006" in result.stdout:
        ok("PORT", "Port 8006 is LISTENING")
    else:
        issue("PORT", "Port 8006 NOT listening — server may not be running")
except:
    issue("PORT", "Could not check port status")

# ═══ SUMMARY ═══
print("\n" + "=" * 70)
print(f"  RESULTADO: {len(RESULTS['ok'])} OK | {len(RESULTS['issues'])} ISSUES")
print("=" * 70)

if RESULTS["issues"]:
    print("\n  ISSUES ENCONTRADAS:")
    for i, iss in enumerate(RESULTS["issues"], 1):
        print(f"  [{i:02d}] [{iss['cat']}] {iss['desc']}")
        if iss["file"]:
            print(f"       File: {iss['file']}" + (f" L{iss['line']}" if iss['line'] else ""))

print("\n  ITEMS OK:")
for item in RESULTS["ok"]:
    print(f"  [OK] [{item['cat']}] {item['desc']}")

# Save results
out = ROOT / "audit_results.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, ensure_ascii=False, indent=2)
print(f"\nResultados salvos em: {out}")
