"""E2E Test — Qualificação Pipeline via SSE"""
import requests, json, time, glob, sys

BASE = "http://localhost:8006"

print("=" * 60)
print("  E2E TEST — QUALIFICAÇÃO DE OFERTAS")
print("=" * 60)

# 1. Health check
print("\n[1] Health check...")
try:
    r = requests.get(f"{BASE}/api/health", timeout=3)
    print(f"    OK: {r.status_code}")
except Exception as e:
    print(f"    FAIL: {e}")
    sys.exit(1)

# 2. Find RFP file
print("\n[2] Localizando RFP...")
rfps = glob.glob("uploads/*.eml") + glob.glob("uploads/*.pdf") + glob.glob("uploads/*.docx")
if not rfps:
    print("    FAIL: Nenhum arquivo em uploads/")
    sys.exit(1)
rfp = rfps[0]
print(f"    File: {rfp}")

# 3. Start job
print("\n[3] Iniciando job (/api/qualificar/start)...")
with open(rfp, "rb") as f:
    resp = requests.post(f"{BASE}/api/qualificar/start",
        files={"rfp": (rfp.split("\\")[-1].split("/")[-1], f)},
        data={"dados": json.dumps({
            "nome_oportunidade": "E2E Test",
            "cliente": "AEGEA",
            "setor": "Energia & Utilities",
            "tipo_servico": "Desenvolvimento de Software (Projeto/Escopo Fechado)",
            "cenario": "2"
        })}
    )

print(f"    Status: {resp.status_code}")
result = resp.json()
print(f"    Response: {json.dumps(result, indent=2)}")

if "job_id" not in result:
    print("    FAIL: No job_id returned")
    sys.exit(1)

job_id = result["job_id"]

# 4. Poll for progress
print(f"\n[4] Polling progresso (/api/job/{job_id})...")
for i in range(120):
    time.sleep(1)
    r = requests.get(f"{BASE}/api/job/{job_id}")
    data = r.json()
    last = data.get("last_event") or {}
    pct = last.get("pct", 0)
    evt = last.get("event", "")
    detail = last.get("detail", "")
    print(f"    [{i+1:3d}s] {pct:3d}% | {evt:20s} | {detail}")

    if data["status"] == "done":
        resultado = data["result"]
        parecer = resultado.get("parecer", {})
        
        print("\n" + "=" * 60)
        print("  ✅ E2E SUCCESS")
        print("=" * 60)
        print(f"  Decisão:   {parecer.get('decisao', 'N/A')}")
        print(f"  Score:     {parecer.get('score_final', parecer.get('score_final_ponderado', 'N/A'))}")
        print(f"  Pipeline:  {resultado.get('pipeline_usado', 'N/A')}")
        print(f"  Tempo:     {resultado.get('tempo_processamento', 'N/A')}")
        print(f"  Output:    {resultado.get('output_salvo', 'N/A')}")
        print(f"  Cenário:   {resultado.get('cenario', 'N/A')}")
        print(f"  LLM:       {resultado.get('llm_provider', 'N/A')}")
        print(f"  Eventos:   {len(data.get('events', []))}")
        
        # Verificar qualidade do resultado
        checks = []
        if parecer.get("decisao"): checks.append("✅ Decisão presente")
        else: checks.append("❌ Decisão ausente")
        
        if parecer.get("score_final") or parecer.get("score_final_ponderado"):
            checks.append("✅ Score calculado")
        else: checks.append("❌ Score ausente")
        
        if resultado.get("analise_tecnica"): checks.append("✅ SA2 análise técnica")
        else: checks.append("⚠️ SA2 vazio")
        
        if resultado.get("analise_riscos"): checks.append("✅ SA3 riscos")
        else: checks.append("⚠️ SA3 vazio")
        
        if resultado.get("analise_comercial"): checks.append("✅ SA4 comercial")
        else: checks.append("⚠️ SA4 vazio")
        
        print("\n  Quality Checks:")
        for c in checks:
            print(f"    {c}")
        
        sys.exit(0)

    if data["status"] == "error":
        print("\n" + "=" * 60)
        print("  ❌ E2E FAILED")
        print("=" * 60)
        print(json.dumps(data.get("result", {}), indent=2, ensure_ascii=False))
        sys.exit(1)

print("\n  ⏰ TIMEOUT after 120s")
sys.exit(1)
