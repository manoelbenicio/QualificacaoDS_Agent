# -*- coding: utf-8 -*-
"""
Validador de Inputs — Agente DS
Valida formulário do usuário antes de enviar ao agente.
Baseado em: 07_AGENTE_1_QUALIFICACAO_DS.md §2.1
"""
from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime


# Setores/Verticais aceitos (§2.1.1 — mesmos do BPO)
SETORES_VALIDOS = [
    "Energia & Utilities",
    "Telecomunicações",
    "Indústria & Consumo",
    "Serviços Financeiros",
    "Administração Pública",
    "Saúde",
    "Varejo",
    "Logística & Transporte",
    "Educação",
    "Oil & Gas",
    "Seguros",
    "Outros",
]

# Tipos de serviço DS (§2.1.2)
TIPOS_SERVICO_DS = [
    "Desenvolvimento de Software (Projeto/Escopo Fechado)",
    "Fábrica de Software (Demanda Contínua)",
    "Sustentação / AMS (Application Management Services)",
    "Squad Dedicado (Outsourcing Ágil)",
    "Body Shop (Alocação de Profissionais)",
    "Consultoria Técnica / Assessment",
    "Modernização / Migração de Legado",
    "Multi-serviço (combinação)",
]

# Modelos de trabalho
MODELOS_TRABALHO = ["Presencial", "Remoto", "Híbrido", "Offshore"]


class ValidadorInput:
    """Valida inputs do formulário de qualificação DS."""

    @staticmethod
    def validar(dados: Dict) -> Tuple[bool, List[str]]:
        """
        Valida campos do formulário.
        Campos não preenchidos recebem defaults.
        Returns: (valido: bool, erros: list[str])
        """
        erros = []

        # ── Campos com defaults (nada é obrigatório) ──
        nome = dados.get("nome_oportunidade", "").strip()
        if not nome:
            dados["nome_oportunidade"] = "Análise RFP"

        cliente = dados.get("cliente", "").strip()
        if not cliente:
            dados["cliente"] = "N/A"

        setor = dados.get("setor", "").strip()
        if setor and setor not in SETORES_VALIDOS:
            # Aceitar valor customizado sem erro
            pass

        tipo = dados.get("tipo_servico", "").strip()
        if tipo and tipo not in TIPOS_SERVICO_DS:
            # Aceitar valor customizado sem erro
            pass

        pratica = dados.get("pratica", "DS").strip()
        # Default to DS — form doesn't send this field

        # ── Campos opcionais (warnings, não erros) ──
        warnings = []

        modelo = dados.get("modelo_trabalho", "").strip()
        if modelo and modelo not in MODELOS_TRABALHO:
            warnings.append(f"modelo_trabalho: valor não padrão '{modelo}'")

        acv = dados.get("acv_estimado")
        if acv is not None and str(acv).strip():
            try:
                acv_num = float(acv)
                if acv_num < 0:
                    erros.append("acv_estimado: deve ser >= 0")
            except (ValueError, TypeError):
                # Ignorar valor inválido, usar 0
                dados["acv_estimado"] = "0"

        prazo = dados.get("prazo_entrega_proposta", "").strip()
        if prazo:
            try:
                dt = datetime.strptime(prazo, "%Y-%m-%d")
                if dt.date() < datetime.now().date():
                    erros.append("prazo_entrega_proposta: deve ser data futura")
            except ValueError:
                erros.append("prazo_entrega_proposta: formato YYYY-MM-DD")

        obs = dados.get("observacoes", "").strip()
        if obs and len(obs) > 2000:
            erros.append("observacoes: máximo 2.000 caracteres")

        stack = dados.get("stack_preferida", [])
        if isinstance(stack, list) and len(stack) > 15:
            erros.append("stack_preferida: máximo 15 itens")

        concorrentes = dados.get("concorrentes_conhecidos", [])
        if isinstance(concorrentes, list) and len(concorrentes) > 10:
            erros.append("concorrentes_conhecidos: máximo 10 itens")

        return (len(erros) == 0, erros)

    @staticmethod
    def normalizar(dados: Dict) -> Dict:
        """Normaliza e preenche defaults nos dados do formulário."""
        normalizado = {
            "nome_oportunidade": dados.get("nome_oportunidade", "").strip(),
            "cliente": dados.get("cliente", "").strip(),
            "setor": dados.get("setor", "").strip(),
            "tipo_servico": dados.get("tipo_servico", "").strip(),
            "pratica": "DS",
            "modelo_trabalho": dados.get("modelo_trabalho", "Híbrido").strip(),
            "acv_estimado": dados.get("acv_estimado"),
            "prazo_entrega_proposta": (dados.get("prazo_entrega_proposta") or dados.get("prazo_resposta", "")).strip(),
            "observacoes": dados.get("observacoes", "").strip(),
            "stack_preferida": dados.get("stack_preferida", []),
            "concorrentes_conhecidos": dados.get("concorrentes_conhecidos", []),
            "champion_interno_cliente": dados.get("champion_interno_cliente", "").strip(),
        }
        return normalizado
