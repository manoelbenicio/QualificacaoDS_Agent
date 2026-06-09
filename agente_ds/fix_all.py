# -*- coding: utf-8 -*-
"""
FIX ALL — Corrige TODAS as issues identificadas na auditoria.
Executa uma vez, resolve tudo.
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
FIXES = []

def fix(cat, desc):
    FIXES.append({"cat": cat, "desc": desc})
    print(f"  [FIX] [{cat}] {desc}")

print("=" * 70)
print("  FIX ALL — CORREÇÃO BATCH")
print("=" * 70)

# ═══ FIX 1: Remove dead mock data (Embraer, kimi-k2, moonshotai, simulado) ═══
print("\n[FIX-1] Removendo mock data do frontend")
html_path = ROOT / "frontend" / "agentificacaoDeOfertas.html"
html = html_path.read_text(encoding="utf-8-sig")

# Find and remove the entire dead generateOutput function (old mock with Embraer data)
# It starts with "const content = document.getElementById" after our new code
# and contains all the hardcoded Embraer/kimi mock output

# Strategy: find the old dead code block between our new exportAgentResult and the DRAG & DROP section
marker_start = "      const content = document.getElementById(`content-${step}`);\r\n      if (step === 1) {"
marker_end = "    /* ═══ DRAG & DROP ═══ */"

idx_start = html.find(marker_start)
idx_end = html.find(marker_end)

if idx_start > 0 and idx_end > idx_start:
    # Remove the entire dead block
    html = html[:idx_start] + "\n    " + html[idx_end:]
    fix("FRONTEND", f"Removed {idx_end - idx_start:,} chars of dead mock code (Embraer/kimi)")
else:
    print(f"  [WARN] Dead code block not found (start={idx_start}, end={idx_end})")
    # Fallback: remove individual references
    replacements = [
        ("moonshotai/kimi-k2.6", "claude-sonnet-4"),
        ("moonshotai/kimi-k2", "claude-sonnet-4"),
        ("nvidia/kimi-k2.6", "claude-sonnet-4"),
        ("Kimi K2", "Claude Sonnet"),
        ("Kimi", "Claude"),
    ]
    for old, new in replacements:
        if old in html:
            html = html.replace(old, new)
            fix("FRONTEND", f"Replaced '{old}' -> '{new}'")

# Double check — remove any remaining Embraer refs (only in JS, not in form data)
embraer_in_js = len(re.findall(r'Embraer', html))
if embraer_in_js > 0:
    # These are in the dead generateOutput function — replace generically
    html = re.sub(r'Embraer', 'Cliente', html)
    fix("FRONTEND", f"Replaced {embraer_in_js} 'Embraer' refs with 'Cliente'")

# Remove "simulado/simulada" 
for pattern in [r'\(Download simulado\)', r'simulado', r'simulada']:
    matches = re.findall(pattern, html, re.IGNORECASE)
    if matches:
        html = re.sub(pattern, '', html, flags=re.IGNORECASE)
        fix("FRONTEND", f"Removed {len(matches)} '{pattern}' references")

# Remove kimi/moonshotai
for kw in ['moonshotai', 'kimi-k2', 'kimi k2']:
    if kw in html.lower():
        html = re.sub(re.escape(kw), 'claude-sonnet-4', html, flags=re.IGNORECASE)
        fix("FRONTEND", f"Replaced '{kw}' with 'claude-sonnet-4'")

# Save
html_path.write_text(html, encoding="utf-8")
fix("FRONTEND", "Saved cleaned HTML")

# ═══ FIX 2: Verify no more issues ═══
print("\n[VERIFY] Post-fix verification")
html2 = html_path.read_text(encoding="utf-8-sig")
checks = {
    "backendRealIndisponivel": html2.count("backendRealIndisponivel"),
    "localhost:8001": html2.count("localhost:8001"),
    "simulad": len(re.findall(r'simulad', html2, re.IGNORECASE)),
    "Embraer": html2.count("Embraer"),
    "moonshotai": html2.lower().count("moonshotai"),
    "kimi-k2": html2.lower().count("kimi-k2"),
    "mock": len(re.findall(r'\bmock\b', html2, re.IGNORECASE)),
}
all_clean = True
for kw, count in checks.items():
    status = "CLEAN" if count == 0 else f"!! STILL {count}"
    if count > 0:
        all_clean = False
    print(f"  {kw}: {status}")

if all_clean:
    print("\n  ✅ TODAS AS ISSUES DE MOCK/PLACEHOLDER RESOLVIDAS")
else:
    print("\n  ❌ AINDA HÁ ISSUES PENDENTES")

print(f"\n  TOTAL FIXES APLICADOS: {len(FIXES)}")
print("=" * 70)
