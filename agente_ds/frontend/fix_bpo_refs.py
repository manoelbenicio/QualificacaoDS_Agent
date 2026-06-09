# -*- coding: utf-8 -*-
"""
Removes ALL BPO references from DS frontend HTML files.
Replaces with DS-specific terminology.
"""
import os, re
from pathlib import Path

FRONTEND = Path(r"C:\VMs\Projetos\BPO_Agentificacao\Materiais_DS\agente_ds\frontend")

# ═══════════════════════════════════════════
# REPLACEMENT MAP — BPO → DS
# ═══════════════════════════════════════════
REPLACEMENTS = [
    # Specific first (longer patterns before shorter)
    ("BPO Processamento de Crédito — Cooperativa", "DS Portal de Autoatendimento — Energisa"),
    ("BPO Backoffice & WhatsApp", "DS Portal Web & App Mobile"),
    ("BPO Backoffice &amp; WhatsApp", "DS Portal Web &amp; App Mobile"),
    ("Qualificação de Oferta BPO — Neoenergia Backoffice & WhatsApp", "Qualificação de Oferta DS — Energisa Portal & App Mobile"),
    ("Qualificação de Oferta BPO — Neoenergia Backoffice &amp; WhatsApp", "Qualificação de Oferta DS — Energisa Portal &amp; App Mobile"),
    ("Qualificação RFP — Neoenergia Backoffice & WhatsApp", "Qualificação RFP — Energisa Portal & App Mobile"),
    ("Qualificação RFP — Neoenergia Backoffice &amp; WhatsApp", "Qualificação RFP — Energisa Portal &amp; App Mobile"),
    ("Neoenergia — Central de Backoffice & WhatsApp", "Energisa — Portal Autoatendimento & App Mobile"),
    ("Neoenergia — Central de Backoffice &amp; WhatsApp", "Energisa — Portal Autoatendimento &amp; App Mobile"),
    ("Neoenergia BPO Backoffice & WhatsApp", "Energisa DS Portal & App Mobile"),
    ("Neoenergia BPO Backoffice &amp; WhatsApp", "Energisa DS Portal &amp; App Mobile"),
    ("Neoenergia BPO", "Energisa DS"),
    ("Central de Backoffice", "Portal de Autoatendimento"),
    ("Backoffice & WhatsApp", "Portal Web & App Mobile"),
    ("Backoffice &amp; WhatsApp", "Portal Web &amp; App Mobile"),
    ("serviços de backoffice e", "serviços de desenvolvimento e"),
    ("Serviços mensais backoffice", "Serviços mensais desenvolvimento"),
    ("Processos — Backoffice", "Stack Tecnológico"),
    ("Backoffice", "Desenvolvimento"),
    ("backoffice", "desenvolvimento"),
    # BPO generic replacements
    ("Prática: BPO", "Prática: DS"),
    ("prática BPO", "prática DS"),
    ("pratica BPO", "pratica DS"),
    (">BPO<", ">DS<"),
    (">BPO/GU<", ">DS<"),
    ("BPO/GU", "DS"),
    ("Cyber e BPO", "Cyber e DS"),
    ("Data&amp;AI, Cyber e BPO", "Data&amp;AI, Cyber e DS"),
    ("(Tech, BPO, Consulting)", "(Tech, DS, Consulting)"),
    # Service type dropdown
    ("<option>BPO</option>", "<option>Desenvolvimento de Software (Projeto/Escopo Fechado)</option>"),
    # Business Process Outsourcing
    ("Business Process Outsourcing", "Desenvolvimento de Soluções"),
]

# ═══════════════════════════════════════════
# PROCESS
# ═══════════════════════════════════════════
total_fixes = 0
for html_file in FRONTEND.glob("*.html"):
    text = html_file.read_text(encoding="utf-8")
    original = text
    file_fixes = 0

    for old, new in REPLACEMENTS:
        count = text.count(old)
        if count > 0:
            text = text.replace(old, new)
            file_fixes += count

    if file_fixes > 0:
        html_file.write_text(text, encoding="utf-8")
        total_fixes += file_fixes
        print(f"  ✅ {html_file.name}: {file_fixes} substituições")
    else:
        print(f"  ⬜ {html_file.name}: limpo (0 refs)")

print(f"\n  TOTAL: {total_fixes} referências BPO removidas")

# ═══════════════════════════════════════════
# VERIFY — check for any remaining BPO refs
# ═══════════════════════════════════════════
print("\n  VERIFICAÇÃO FINAL:")
remaining = 0
for html_file in FRONTEND.glob("*.html"):
    text = html_file.read_text(encoding="utf-8")
    matches = re.findall(r'(?i)BPO|backoffice|Business Process Outsourcing', text)
    if matches:
        remaining += len(matches)
        print(f"  ⚠️  {html_file.name}: {len(matches)} restantes → {matches[:5]}")

if remaining == 0:
    print("  ✅ ZERO referências BPO restantes. Frontend 100% DS.")
else:
    print(f"  ⚠️  {remaining} referências restantes — requer revisão manual")
