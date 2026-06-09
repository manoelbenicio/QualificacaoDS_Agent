# -*- coding: utf-8 -*-
"""
Agente DS — Pacote de Qualificação de Ofertas
Prática: Desenvolvimento de Soluções (DS)
Indra Minsait Brasil — DSS Agents v1.0

Dois cenários disponíveis:
  - Cenário 1 (Monolítico): AgenteDS — agente único
  - Cenário 2 (Multi-Agente): Maestro + 5 Sub-Agentes
"""
from .agente_ds import AgenteDS
from .extracao import ExtratorDocumental
from .acervo import AcervoDS
from .validacao import ValidadorInput
from .sub_agentes.maestro import Maestro

__version__ = "1.0.0"
__pratica__ = "DS"
__all__ = ["AgenteDS", "Maestro", "ExtratorDocumental", "AcervoDS", "ValidadorInput"]
