# -*- coding: utf-8 -*-
"""
Sub-Agentes DS — Pacote de Qualificação Multi-Agente
Prática: Desenvolvimento de Soluções
Cenário 2: Maestro + 5 Sub-Agentes

Fluxo:
  SA1 (Extrator) → SA2 (Técnico) + SA3 (Riscos) + SA4 (Comercial) → SA5 (Decisor)
"""
from . import sa1_extrator
from . import sa2_analista_tecnico
from . import sa3_analista_riscos
from . import sa4_analista_comercial
from . import sa5_decisor
from .maestro import Maestro

__all__ = [
    "sa1_extrator",
    "sa2_analista_tecnico",
    "sa3_analista_riscos",
    "sa4_analista_comercial",
    "sa5_decisor",
    "Maestro",
]
