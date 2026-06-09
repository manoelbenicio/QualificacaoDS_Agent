"""E2E Test com logs detalhados de cada Sub-Agente"""
import requests, json, time, sys, os

os.environ["PYTHONIOENCODING"] = "utf-8"
BASE = "http://localhost:8006"
RFP = r"C:\Users\mbenicios\Downloads\Email\ENC_ [PB_LIFERAY]RFP 7004591889 - Licenciamento de uso, na modalidade subscrição em nuvem, de solução para serviço de Sites e Portais e Serviços Associados.eml"

if not os.path.exists(RFP):
    print(f"ERRO: Arquivo nao encontrado: {RFP}")
    sys.exit(1)

print("=" * 70)
print("  E2E TEST — LOGS DETALHADOS DE CADA SUB-AGENTE")
print("  RFP: " + os.path.basename(RFP))
print("=" * 70)

# 1. Start job
print("\n[START] Enviando RFP para /api/qualificar/start...")
with open(RFP, "rb") as f:
    resp = requests.post(f"{BASE}/api/qualificar/start",
        files={"rfp": (os.path.basename(RFP), f)},
        data={"dados": json.dumps({
            "nome_oportunidade": "Petrobras Liferay Portal",
            "cliente": "Petrobras",
            "setor": "Energia & Utilities",
            "tipo_servico": "Sustentacao / AMS",
            "cenario": "2"
        })}
    )

start = resp.json()
if "job_id" not in start:
    print(f"ERRO: {start}")
    sys.exit(1)

job_id = start["job_id"]
print(f"[OK] Job iniciado: {job_id}")

# 2. Poll com logs detalhados
seen_events = 0
t0 = time.time()

for i in range(300):
    time.sleep(1)
    r = requests.get(f"{BASE}/api/job/{job_id}")
    data = r.json()
    events = data.get("events", [])
    
    # Mostrar novos eventos
    for evt in events[seen_events:]:
        elapsed = time.time() - t0
        event_name = evt.get("event", "?")
        pct = evt.get("pct", 0)
        detail = evt.get("detail", "")
        
        # Colorir por tipo
        prefix = ""
        if "sa1" in event_name: prefix = "[SA1-EXTRACAO]"
        elif "sa2" in event_name: prefix = "[SA2-TECNICO]"
        elif "sa3" in event_name: prefix = "[SA3-RISCOS]"
        elif "sa4" in event_name: prefix = "[SA4-COMERCIAL]"
        elif "sa5" in event_name or "decisao" in event_name or "farois" in event_name: prefix = "[SA5-DECISAO]"
        elif "llm" in event_name: prefix = "[LLM-ENRICH]"
        elif "acervo" in event_name: prefix = "[ACERVO-KB]"
        elif "upload" in event_name or "extracao" in event_name: prefix = "[UPLOAD]"
        elif "tokenizacao" in event_name: prefix = "[TOKENIZER]"
        elif "modo" in event_name: prefix = "[CONFIG]"
        else: prefix = f"[{event_name.upper()}]"
        
        print(f"  {elapsed:6.1f}s | {pct:3d}% | {prefix:18s} | {detail}")
    
    seen_events = len(events)
    
    if data["status"] == "done":
        resultado = data["result"]
        elapsed = time.time() - t0
        
        print(f"\n{'=' * 70}")
        print(f"  RESULTADO FINAL ({elapsed:.1f}s)")
        print(f"{'=' * 70}")
        
        parecer = resultado.get("parecer", {})
        print(f"\n  DECISAO:      {parecer.get('decisao', 'N/A')}")
        print(f"  SCORE:        {parecer.get('score_final', parecer.get('score_final_ponderado', 'N/A'))}/10")
        print(f"  CONFIANCA:    {parecer.get('confianca_pct', 'N/A')}%")
        print(f"  MOTOR:        {parecer.get('motor', resultado.get('motor', 'N/A'))}")
        print(f"  CENARIO:      {resultado.get('cenario', 'N/A')}")
        
        print(f"\n  JUSTIFICATIVA:")
        just = parecer.get("justificativa_decisao", "N/A")
        for line in just.split(". "):
            print(f"    {line.strip()}")
        
        # SA1
        oi = resultado.get("outputs_intermediarios", {})
        sa1 = oi.get("SA1_extracao", {})
        print(f"\n  --- SA1 EXTRACAO ---")
        ad = sa1.get("analise_documento", {})
        print(f"    Paginas:      {ad.get('total_paginas', 'N/A')}")
        print(f"    Palavras:     {ad.get('total_palavras', 'N/A')}")
        print(f"    Idioma:       {ad.get('idioma_detectado', 'N/A')}")
        
        # SA2
        sa2 = oi.get("SA2_tecnico", {})
        print(f"\n  --- SA2 TECNICO ---")
        print(f"    Tecnologias:  {sa2.get('total_tecnologias', 0)}")
        techs = sa2.get("tecnologias_identificadas", [])
        for t in techs[:10]:
            if isinstance(t, dict):
                print(f"      - {t.get('nome', t)}")
            else:
                print(f"      - {t}")
        print(f"    Complexidade: {sa2.get('complexidade', 'N/A')}")
        print(f"    Aderencia:    {sa2.get('aderencia_ds', 'N/A')}/10")
        dim = sa2.get("dimensionamento", {})
        print(f"    FTEs:         {dim.get('ftes_estimado', 'N/A')}")
        print(f"    Sprints:      {dim.get('total_sprints', 'N/A')}")
        print(f"    Meses:        {dim.get('duracao_meses', 'N/A')}")
        print(f"    Gaps:         {sa2.get('gaps_tecnicos', [])}")
        
        # SA3
        sa3 = oi.get("SA3_riscos", {})
        print(f"\n  --- SA3 RISCOS ---")
        print(f"    Total:        {sa3.get('total_riscos', 0)}")
        print(f"    Criticos:     {sa3.get('criticos', 0)}")
        print(f"    Risk Score:   {sa3.get('risk_score', 'N/A')}")
        for r in sa3.get("top_riscos", []):
            print(f"      [{r.get('severidade','?')}] {r.get('nome','?')} -> {r.get('mitigacao','?')}")
        
        # SA4
        sa4 = oi.get("SA4_comercial", {})
        print(f"\n  --- SA4 COMERCIAL ---")
        print(f"    Score Final:  {sa4.get('score_final_ponderado', 'N/A')}/10")
        print(f"    Nivel:        {sa4.get('nivel_geral', 'N/A')}")
        bsw = sa4.get("best_story_wins", parecer.get("best_story_wins", {}))
        if bsw:
            print(f"    Por que mudar:   {str(bsw.get('por_que_mudar',''))[:100]}...")
            print(f"    Por que agora:   {str(bsw.get('por_que_agora',''))[:100]}...")
            print(f"    Por que Minsait: {str(bsw.get('por_que_minsait',''))[:100]}...")
        
        # SA5 / Farois
        farois = parecer.get("farois_consolidados", sa4.get("farois", []))
        print(f"\n  --- SA5 FAROIS ---")
        for f in farois:
            cor = f.get("cor", "?")
            emoji = {"VERDE":"GRN","AMARELO":"YLW","VERMELHO":"RED"}.get(cor, "???")
            print(f"    [{emoji}] {f.get('nome','?')}: {f.get('valor','?')}")
        
        # Next steps
        ns = parecer.get("next_steps", [])
        print(f"\n  --- NEXT STEPS ---")
        for s in ns:
            print(f"    -> {s}")
        
        # Output file
        print(f"\n  OUTPUT: {resultado.get('output_salvo', 'N/A')}")
        print(f"  TRACE:  {resultado.get('trace_id', 'N/A')}")
        
        sys.exit(0)
    
    if data["status"] == "error":
        print(f"\n  ERRO: {json.dumps(data.get('result',{}), indent=2, ensure_ascii=False)}")
        sys.exit(1)

print("\n  TIMEOUT apos 300s")
sys.exit(1)
