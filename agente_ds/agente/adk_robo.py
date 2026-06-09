# -*- coding: utf-8 -*-
"""
ADK ROBÔ — Motor de Análise Determinística para Qualificação DS
Processa RFPs usando NLP/regex/heurísticas em Python puro.
ANALISA O DOCUMENTO CONTRA TODA A BASE DE CONHECIMENTO (Acervo DS).
Substitui a API Claude quando não disponível.
"""
import re
import json
import math
from collections import Counter
from typing import Dict, List, Tuple
from datetime import datetime
from pathlib import Path


class ADKRobo:
    """
    Analytical Development Kit — Motor robótico de qualificação.
    Analisa RFP word-by-word contra toda a KB do Acervo DS.
    """

    # ═══ DICIONÁRIOS DE ANÁLISE ═══

    TECH_KEYWORDS = {
        "java": 3, "spring": 3, "spring boot": 3, "python": 3,
        "django": 2, "flask": 2, "fastapi": 2,
        "react": 3, "angular": 3, "vue": 2, "next.js": 2, "nuxt": 2,
        "node": 3, "node.js": 3, "typescript": 2, "javascript": 2,
        ".net": 3, "c#": 3, "asp.net": 2,
        "sql": 2, "oracle": 2, "postgresql": 2, "mysql": 2,
        "mongodb": 2, "redis": 1, "kafka": 2, "rabbitmq": 1,
        "docker": 2, "kubernetes": 3, "k8s": 3,
        "aws": 3, "azure": 3, "gcp": 3, "cloud": 2,
        "terraform": 2, "jenkins": 1, "ci/cd": 2, "devops": 2,
        "microserviço": 3, "microservice": 3, "microsserviços": 3,
        "api": 2, "rest": 2, "restful": 2,
        "graphql": 2, "grpc": 1, "sap": 3, "salesforce": 2,
        "power bi": 2, "tableau": 2, "qlik": 2,
        "machine learning": 3, "ml": 2, "ia": 3, "ai": 3,
        "inteligência artificial": 3, "deep learning": 3,
        "mobile": 2, "ios": 2, "android": 2, "flutter": 2, "react native": 2,
        "agile": 1, "scrum": 1, "kanban": 1, "jira": 1,
        "outsourcing": 2, "sustentação": 2, "ams": 2,
        "body shop": 2, "fábrica de software": 3,
        "erp": 2, "crm": 2, "bi": 2, "etl": 2, "data lake": 2,
        "big data": 2, "data warehouse": 2, "spark": 2,
    }

    RISK_PATTERNS = {
        "multa": ("Penalidades contratuais", "ALTO", "Negociar caps de multa e cláusula de cure period"),
        "penalidade": ("Penalidades contratuais", "ALTO", "Incluir limites de responsabilidade no contrato"),
        "sla": ("SLA rigoroso", "MEDIO", "Definir SLAs realistas com buffer operacional"),
        "lgpd": ("Conformidade LGPD", "MEDIO", "Incluir DPO e assessment de privacidade no projeto"),
        "compliance": ("Requisitos de compliance", "MEDIO", "Mapear framework regulatório antes do kick-off"),
        "itar": ("Restrição ITAR/exportação", "ALTO", "Validar restrições com jurídico antes de propor"),
        "sigilo": ("Requisitos de sigilo", "MEDIO", "Estabelecer NDA e controles de acesso"),
        "confidencial": ("Confidencialidade", "BAIXO", "Incluir termos padrão de confidencialidade"),
        "deadline": ("Prazo apertado", "MEDIO", "Propor quick wins iniciais + roadmap faseado"),
        "prazo apertado": ("Prazo apertado", "ALTO", "Alocar equipe senior para fast ramp-up"),
        "urgente": ("Urgência do projeto", "ALTO", "Apresentar time pronto e start imediato"),
        "legado": ("Integração com legado", "MEDIO", "Assessment de legado antes de dimensionar"),
        "legacy": ("Integração com legado", "MEDIO", "Assessment de legado antes de dimensionar"),
        "migração": ("Migração de sistemas", "MEDIO", "Plano de migração faseado com rollback"),
        "migration": ("Migração de sistemas", "MEDIO", "Plano de migração faseado com rollback"),
        "offshore": ("Modelo offshore", "MEDIO", "Garantir overlap de horário e gestão local"),
        "turnover": ("Risco de turnover", "ALTO", "Cláusula de backup e knowledge transfer"),
        "escopo aberto": ("Escopo indefinido", "ALTO", "Propor discovery phase antes de escopo fechado"),
        "licitação": ("Processo licitatório", "MEDIO", "Compliance com lei de licitações"),
        "concorrência": ("Alta concorrência", "MEDIO", "Diferenciação por cases e capacidade técnica"),
        "exclusividade": ("Cláusula de exclusividade", "MEDIO", "Avaliar impacto em outros contratos"),
        "downtime": ("Risco de indisponibilidade", "ALTO", "Plano de DR e alta disponibilidade"),
        "disponibilidade": ("Requisitos de disponibilidade", "MEDIO", "SLA de uptime com monitoramento"),
        "integração": ("Complexidade de integração", "MEDIO", "Mapear pontos de integração na discovery"),
        "restrição orçamentária": ("Orçamento limitado", "ALTO", "Proposta em fases com MVPs priorizados"),
    }

    SETORES_MINSAIT = {
        "energia & utilities": {"peso": 9, "cases": True},
        "energia": {"peso": 9, "cases": True},
        "utilities": {"peso": 9, "cases": True},
        "financeiro & seguros": {"peso": 8, "cases": True},
        "financeiro": {"peso": 8, "cases": True},
        "banco": {"peso": 8, "cases": True},
        "seguros": {"peso": 7, "cases": True},
        "governo & setor público": {"peso": 7, "cases": True},
        "governo": {"peso": 7, "cases": True},
        "telecom & mídia": {"peso": 8, "cases": True},
        "telecom": {"peso": 8, "cases": True},
        "saúde": {"peso": 6, "cases": True},
        "indústria & manufatura": {"peso": 7, "cases": True},
        "varejo": {"peso": 6, "cases": True},
        "transporte & logística": {"peso": 7, "cases": True},
        "óleo & gás": {"peso": 7, "cases": True},
        "mineração": {"peso": 6, "cases": True},
        "agronegócio": {"peso": 5, "cases": False},
        "data & analytics / ia": {"peso": 9, "cases": True},
    }

    # ═══ PIPELINE PRINCIPAL ═══

    def analisar(self, dados: Dict, texto_rfp: str, acervo=None) -> Dict:
        """
        Pipeline completo de análise determinística.
        Confronta o documento RFP contra toda a base de conhecimento.
        """
        inicio = datetime.now()

        # Tokenizar documento inteiro
        tokens_rfp = self._tokenizar(texto_rfp)
        texto_lower = texto_rfp.lower()

        # ═══ CONSULTAR ACERVO DS (Base de Conhecimento) ═══
        kb_match = self._confrontar_acervo(texto_rfp, tokens_rfp, acervo)

        # SA1: Extração Documental
        extracao = self.sa1_extrair(dados, texto_rfp, tokens_rfp)

        # SA2: Análise Técnica (contra KB)
        tecnico = self.sa2_analisar_tecnico(texto_rfp, tokens_rfp, extracao, kb_match)

        # SA3: Análise de Riscos
        riscos = self.sa3_analisar_riscos(texto_rfp, texto_lower, extracao)

        # SA4: Análise Comercial (8 Faróis + BSW)
        comercial = self.sa4_analisar_comercial(dados, texto_rfp, texto_lower, extracao, tecnico, riscos, kb_match)

        # SA5: Decisão Final
        decisao = self.sa5_decidir(dados, extracao, tecnico, riscos, comercial, kb_match)

        duracao = (datetime.now() - inicio).total_seconds()

        return {
            "status": "concluido",
            "cenario": "CENARIO_2_ADK_ROBO",
            "pratica": "DS",
            "motor": "ADK Robô Python v2 — Análise Determinística contra Acervo DS",
            "parecer": decisao,
            "outputs_intermediarios": {
                "SA1_extracao": extracao,
                "SA2_tecnico": tecnico,
                "SA3_riscos": riscos,
                "SA4_comercial": comercial,
            },
            "kb_match": kb_match,
            "tokens_totais": {
                "input": len(texto_rfp),
                "output": 0,
                "total": len(texto_rfp),
                "palavras_analisadas": len(tokens_rfp),
            },
            "duracao_segundos": round(duracao, 2),
            "timestamp_inicio": inicio.isoformat(),
            "timestamp_fim": datetime.now().isoformat(),
        }

    # ═══ CONFRONTAR ACERVO DS ═══

    def _confrontar_acervo(self, texto_rfp: str, tokens_rfp: set, acervo) -> Dict:
        """
        Confronta o texto da RFP contra TODA a base de conhecimento.
        Retorna documentos relevantes, atestados, cases, e score de cobertura.
        """
        if acervo is None:
            return {"status": "acervo_indisponivel", "docs_relevantes": [], "cobertura": 0}

        # Buscar documentos relevantes
        docs = acervo.buscar_relevantes(texto_rfp, top_k=30)

        # Classificar por categoria
        por_categoria = {}
        for doc in docs:
            cat = doc.get("categoria", "?")
            if cat not in por_categoria:
                por_categoria[cat] = []
            por_categoria[cat].append({
                "titulo": doc.get("titulo", ""),
                "mercado": doc.get("mercado", ""),
                "praticas": doc.get("praticas", []),
                "path": doc.get("path", ""),
            })

        # Atestados encontrados
        atestados = por_categoria.get("A", [])
        cases = por_categoria.get("B", [])
        capacidades = por_categoria.get("C", [])
        propostas = por_categoria.get("PT", [])
        solucoes = por_categoria.get("S", [])
        templates = por_categoria.get("T", [])

        # Score de cobertura da KB (quão bem o acervo cobre os requisitos da RFP)
        cobertura_score = min(10, (
            len(atestados) * 1.5 +
            len(cases) * 2.0 +
            len(capacidades) * 1.0 +
            len(propostas) * 1.5 +
            len(solucoes) * 1.0 +
            len(templates) * 0.5
        ))

        # Taxonomia
        taxonomia = acervo.get_taxonomia_resumo() if hasattr(acervo, 'get_taxonomia_resumo') else ""

        # Contexto RAG completo
        contexto_rag = acervo.get_contexto_rag(texto_rfp, top_k=15) if hasattr(acervo, 'get_contexto_rag') else ""

        return {
            "status": "ok",
            "total_docs_analisados": len(acervo.catalog) if hasattr(acervo, 'catalog') else 0,
            "docs_relevantes": len(docs),
            "por_categoria": {k: len(v) for k, v in por_categoria.items()},
            "atestados": atestados,
            "cases": cases,
            "capacidades": capacidades,
            "propostas": propostas,
            "solucoes": solucoes,
            "templates": templates,
            "cobertura_score": round(cobertura_score, 1),
            "taxonomia": taxonomia,
            "contexto_rag": contexto_rag,
        }

    # ═══ SA1: EXTRATOR DOCUMENTAL ═══

    def sa1_extrair(self, dados: Dict, texto: str, tokens: set) -> Dict:
        """Extrai dados estruturados do texto da RFP — palavra por palavra."""
        texto_lower = texto.lower()
        palavras = list(tokens)
        total_chars = len(texto)
        total_palavras = len(palavras)
        total_linhas = texto.count('\n') + 1
        total_paginas = max(1, total_chars // 3000)  # ~3000 chars por página

        # Detectar valores monetários
        valores = re.findall(r'R\$\s*[\d.,]+(?:\s*(?:mil|milhões|milhão|bilhões|bi))?', texto, re.IGNORECASE)
        valores += re.findall(r'(?:USD|BRL|EUR|U\$)\s*[\d.,]+(?:\s*(?:thousand|million|billion|k|M|B))?', texto, re.IGNORECASE)

        # Parsear valores para estimativa ACV
        acv_estimado = self._estimar_acv(valores, dados)

        # Detectar datas
        datas = re.findall(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4}', texto)

        # Detectar e-mails e contatos
        emails = re.findall(r'[\w.-]+@[\w.-]+\.\w+', texto)
        telefones = re.findall(r'(?:\+55\s?)?\(?\d{2}\)?\s?\d{4,5}[-.\s]?\d{4}', texto)

        # Detectar tecnologias mencionadas (word-by-word)
        techs_encontradas = {}
        for tech, peso in self.TECH_KEYWORDS.items():
            count = texto_lower.count(tech)
            if count > 0:
                techs_encontradas[tech] = {"ocorrencias": count, "peso": peso}

        # Detectar escopo
        escopos = {
            "desenvolvimento novo": texto_lower.count("desenvolvimento") + texto_lower.count("novo sistema"),
            "sustentação/AMS": texto_lower.count("sustentação") + texto_lower.count("ams") + texto_lower.count("manutenção"),
            "modernização": texto_lower.count("modernização") + texto_lower.count("modernizar") + texto_lower.count("legacy"),
            "migração": texto_lower.count("migração") + texto_lower.count("migrar") + texto_lower.count("migration"),
            "outsourcing": texto_lower.count("outsourcing") + texto_lower.count("terceirização"),
            "body shop": texto_lower.count("body shop") + texto_lower.count("alocação"),
            "consultoria": texto_lower.count("consultoria") + texto_lower.count("assessment") + texto_lower.count("diagnóstico"),
            "integração": texto_lower.count("integração") + texto_lower.count("integration"),
            "fábrica de software": texto_lower.count("fábrica") + texto_lower.count("factory"),
            "squad dedicado": texto_lower.count("squad") + texto_lower.count("dedicado"),
        }
        escopo_principal = max(escopos, key=escopos.get) if any(escopos.values()) else "não identificado"

        # Requisitos funcionais vs não-funcionais
        req_func = sum(1 for line in texto.split('\n')
                       if re.search(r'(?:RF|REQ|requisito)\s*\d', line, re.IGNORECASE))
        req_nfunc = sum(1 for kw in ['performance', 'segurança', 'disponibilidade', 'escalabilidade',
                                      'usabilidade', 'manutenibilidade', 'portabilidade']
                        if kw in texto_lower)

        complexidade = self._estimar_complexidade(total_chars, len(techs_encontradas), escopos)

        return {
            "nome_oportunidade": dados.get("nome_oportunidade", ""),
            "cliente": dados.get("cliente", ""),
            "setor_informado": dados.get("setor", ""),
            "tipo_servico": dados.get("tipo_servico", ""),
            "analise_documento": {
                "total_caracteres": total_chars,
                "total_palavras": total_palavras,
                "total_linhas": total_linhas,
                "total_paginas_estimado": total_paginas,
            },
            "dados_financeiros": {
                "valores_encontrados": valores[:10],
                "acv_estimado": acv_estimado,
            },
            "dados_temporais": {
                "datas_encontradas": datas[:10],
                "prazo_resposta": dados.get("prazo_resposta", ""),
            },
            "contatos": {
                "emails": emails[:5],
                "telefones": telefones[:5],
            },
            "tecnologias_detectadas": techs_encontradas,
            "escopo": {
                "principal": escopo_principal,
                "detalhado": {k: v for k, v in escopos.items() if v > 0},
            },
            "requisitos": {
                "funcionais_detectados": req_func,
                "nao_funcionais_detectados": req_nfunc,
            },
            "complexidade_estimada": complexidade,
        }

    # ═══ SA2: ANALISTA TÉCNICO ═══

    def sa2_analisar_tecnico(self, texto: str, tokens: set, extracao: Dict, kb_match: Dict) -> Dict:
        """Analisa aspectos técnicos contra a base de conhecimento."""
        techs = extracao.get("tecnologias_detectadas", {})
        complexidade = extracao.get("complexidade_estimada", "MEDIA")
        n_techs = len(techs)
        tech_score = sum(t.get("peso", 0) * min(3, t.get("ocorrencias", 1)) for t in techs.values())

        # Dimensionamento
        dim_map = {
            "BAIXA": {"ftes_min": 3, "ftes_max": 6, "sprints": 6, "meses": 3},
            "MEDIA": {"ftes_min": 6, "ftes_max": 12, "sprints": 12, "meses": 6},
            "ALTA": {"ftes_min": 10, "ftes_max": 20, "sprints": 20, "meses": 10},
            "MUITO_ALTA": {"ftes_min": 18, "ftes_max": 35, "sprints": 30, "meses": 15},
        }
        dim = dim_map.get(complexidade, dim_map["MEDIA"])

        # Perfis
        perfis = self._dimensionar_perfis(techs)

        # Aderência DS usando KB
        aderencia = self._calcular_aderencia_ds(techs, kb_match)

        # Cases do acervo que match
        cases_match = kb_match.get("cases", [])
        atestados_match = kb_match.get("atestados", [])

        # Gaps
        gaps = self._identificar_gaps(texto.lower(), list(techs.keys()))

        return {
            "tecnologias_identificadas": list(techs.keys()),
            "total_tecnologias": n_techs,
            "tech_score": tech_score,
            "complexidade": complexidade,
            "dimensionamento": {
                "ftes_estimado": f"{dim['ftes_min']}-{dim['ftes_max']}",
                "total_sprints": dim["sprints"],
                "duracao_meses": dim["meses"],
                "perfis_chave": perfis,
            },
            "aderencia_ds": aderencia,
            "cobertura_kb": {
                "score": kb_match.get("cobertura_score", 0),
                "cases_relevantes": len(cases_match),
                "atestados_relevantes": len(atestados_match),
                "cases": [c.get("titulo", "") for c in cases_match[:5]],
                "atestados": [a.get("titulo", "") for a in atestados_match[:5]],
            },
            "gaps_tecnicos": gaps,
        }

    # ═══ SA3: ANALISTA DE RISCOS ═══

    def sa3_analisar_riscos(self, texto: str, texto_lower: str, extracao: Dict) -> Dict:
        """Identifica e classifica riscos com mitigações."""
        riscos_encontrados = []

        for keyword, (descricao, severidade, mitigacao) in self.RISK_PATTERNS.items():
            count = texto_lower.count(keyword)
            if count > 0:
                riscos_encontrados.append({
                    "nome": descricao,
                    "severidade": severidade,
                    "keyword": keyword,
                    "ocorrencias": count,
                    "mitigacao": mitigacao,
                })

        # Dedup by nome
        seen = set()
        unique_riscos = []
        for r in riscos_encontrados:
            if r["nome"] not in seen:
                seen.add(r["nome"])
                unique_riscos.append(r)

        criticos = [r for r in unique_riscos if r["severidade"] == "ALTO"]
        medios = [r for r in unique_riscos if r["severidade"] == "MEDIO"]
        baixos = [r for r in unique_riscos if r["severidade"] == "BAIXO"]

        risk_score = min(10, len(criticos) * 2.5 + len(medios) * 1.2 + len(baixos) * 0.4)

        return {
            "total_riscos": len(unique_riscos),
            "criticos": len(criticos),
            "medios": len(medios),
            "baixos": len(baixos),
            "risk_score": round(risk_score, 1),
            "riscos": unique_riscos,
            "top_riscos": sorted(unique_riscos, key=lambda x: {"ALTO": 3, "MEDIO": 2, "BAIXO": 1}.get(x["severidade"], 0), reverse=True)[:5],
            "mitigacoes_chave": [r["mitigacao"] for r in criticos[:3]] + [r["mitigacao"] for r in medios[:2]],
        }

    # ═══ SA4: ANALISTA COMERCIAL (8 FARÓIS + BSW) ═══

    def sa4_analisar_comercial(self, dados: Dict, texto: str, texto_lower: str,
                                extracao: Dict, tecnico: Dict, riscos: Dict, kb_match: Dict) -> Dict:
        """
        Calcula os 8 Faróis DS + Best Story Wins.
        Spec: 07_AGENTE_1_QUALIFICACAO_DS.md §6.1 + §4.1.1
        8 Faróis = 4 Critérios do Cliente + 4 Critérios Minsait
        Pesos: iguais (12.5% cada) conforme spec §6 Configurações
        Níveis: ALTO / MEDIO_ALTO / MEDIO / MEDIO_BAIXO / BAIXO
        """
        complexidade = extracao.get("complexidade_estimada", "MEDIA")
        risk_score = riscos.get("risk_score", 5)
        n_techs = tecnico.get("total_tecnologias", 0)
        aderencia = tecnico.get("aderencia_ds", 5)
        cobertura_kb = kb_match.get("cobertura_score", 0)
        total_palavras = extracao.get("analise_documento", {}).get("total_palavras", 0)
        setor = dados.get("setor", "").lower()
        cliente = dados.get("cliente", "o cliente")
        tipo = dados.get("tipo_servico", "").lower()

        # Peso do setor na Minsait
        setor_info = self.SETORES_MINSAIT.get(setor, {"peso": 5, "cases": False})
        setor_peso = setor_info["peso"]

        # ── Indicadores de contexto extraídos do texto da RFP ──
        tem_rfp_formal = total_palavras > 500
        tem_budget = any(kw in texto_lower for kw in ["orçamento", "budget", "valor estimado", "preço", "r$", "brl"])
        tem_prazo = any(kw in texto_lower for kw in ["prazo", "deadline", "cronograma", "entrega"])
        tem_champion = any(kw in texto_lower for kw in ["sponsor", "champion", "cto", "cio", "gerente", "diretor", "head"])
        tem_decisor = any(kw in texto_lower for kw in ["comitê", "decisor", "aprovação", "procurement", "compras", "licitação"])
        escopo_claro = total_palavras > 3000
        tem_substituicao = any(kw in texto_lower for kw in ["substituição", "migração de fornecedor", "troca de fornecedor", "incumbent"])
        tem_cross = any(kw in texto_lower for kw in ["infraestrutura", "cloud", "devops", "data", "analytics", "ia", "ai", "sap", "segurança", "cyber"])
        champion_input = dados.get("champion_interno_cliente", "")

        # ═══════════════════════════════════════════════════════════════
        # 8 FARÓIS DS — Spec 07_AGENTE_1_QUALIFICACAO_DS.md §6.1
        # Pesos iguais: 12.5% cada (conf. §6 Configurações ajustáveis)
        # ═══════════════════════════════════════════════════════════════

        farois = [
            # ── CRITÉRIOS DO CLIENTE (4 faróis) ──
            {
                "id": "F1",
                "grupo": "CRITÉRIOS DO CLIENTE",
                "nome": "Evento Envolvente",
                "descricao": "Urgência e concretude da demanda — RFP formal? Projeto aprovado? Budget alocado? Substituição de fornecedor?",
                "peso_pct": 12.5,
                "score": min(10, max(1, round(
                    3
                    + (2.5 if tem_rfp_formal else 0)
                    + (1.5 if escopo_claro else 0)
                    + (1.5 if tem_substituicao else 0)
                    + (1.0 if tem_prazo else 0)
                , 1))),
                "justificativa": "",
            },
            {
                "id": "F2",
                "grupo": "CRITÉRIOS DO CLIENTE",
                "nome": "Orçamento",
                "descricao": "Capacidade financeira e aderência — ACV estimado, modelo de pagamento, capacidade financeira do cliente",
                "peso_pct": 12.5,
                "score": min(10, max(1, round(
                    4
                    + (2.0 if tem_budget else 0)
                    + (1.5 if escopo_claro else 0)
                    + (1.0 if complexidade in ("ALTA", "MUITO_ALTA") else 0.5)
                , 1))),
                "justificativa": "",
            },
            {
                "id": "F3",
                "grupo": "CRITÉRIOS DO CLIENTE",
                "nome": "Aliado / Champion",
                "descricao": "Sponsor interno mapeado — CTO/CIO/Head de TI como champion? Relacionamento prévio?",
                "peso_pct": 12.5,
                "score": min(10, max(1, round(
                    (6.0 if champion_input else 3.5)
                    + (2.0 if tem_champion else 0)
                    + (1.0 if setor_info.get("cases") else 0)
                , 1))),
                "justificativa": "",
            },
            {
                "id": "F4",
                "grupo": "CRITÉRIOS DO CLIENTE",
                "nome": "Decisores Acessíveis",
                "descricao": "Acesso ao comitê decisor — CIO + CFO + Procurement? Temos acesso?",
                "peso_pct": 12.5,
                "score": min(10, max(1, round(
                    4
                    + (2.0 if tem_decisor else 0)
                    + (1.0 if "licitação" in texto_lower else 0)
                    + (1.0 if champion_input else 0)
                , 1))),
                "justificativa": "",
            },

            # ── CRITÉRIOS MINSAIT (4 faróis) ──
            {
                "id": "F5",
                "grupo": "CRITÉRIOS MINSAIT",
                "nome": "Ajuste Estratégico",
                "descricao": "Alinhamento com portfólio Minsait — Vertical prioritária? Tamanho ideal? Aderência a capabilities DS?",
                "peso_pct": 12.5,
                "score": min(10, max(1, round(
                    aderencia * 0.4
                    + setor_peso * 0.4
                    + cobertura_kb * 0.15
                    + (0.5 if complexidade in ("ALTA", "MUITO_ALTA") else 0)
                , 1))),
                "justificativa": "",
            },
            {
                "id": "F6",
                "grupo": "CRITÉRIOS MINSAIT",
                "nome": "Engajamento de Práticas",
                "descricao": "Cross-selling entre práticas — DS + DIC + Data&AI + SGE + Cyber? Portfólio 360°?",
                "peso_pct": 12.5,
                "score": min(10, max(1, round(
                    4
                    + (2.0 if tem_cross else 0)
                    + (1.0 if n_techs > 10 else 0.5)
                    + (1.0 if any(kw in texto_lower for kw in ["sap", "erp", "salesforce"]) else 0)
                , 1))),
                "justificativa": "",
            },
            {
                "id": "F7",
                "grupo": "CRITÉRIOS MINSAIT",
                "nome": "Cases / Referências",
                "descricao": "Experiência comprovável — Cases similares em vertical/tecnologia? Referências ativas?",
                "peso_pct": 12.5,
                "score": min(10, max(1, round(
                    3
                    + cobertura_kb * 0.3
                    + (2.0 if setor_info.get("cases") else 0)
                    + aderencia * 0.2
                , 1))),
                "justificativa": "",
            },
            {
                "id": "F8",
                "grupo": "CRITÉRIOS MINSAIT",
                "nome": "Competitividade",
                "descricao": "Posicionamento vs. concorrência — Qual alavanca? Preço? Qualidade? Prazo?",
                "peso_pct": 12.5,
                "score": min(10, max(1, round(
                    5
                    + cobertura_kb * 0.15
                    + (1.5 if setor_info.get("cases") else -0.5)
                    + aderencia * 0.1
                    - risk_score * 0.1
                , 1))),
                "justificativa": "",
            },
        ]

        # ── Gerar nível (5 faixas conforme spec), cor e justificativas ──
        for f in farois:
            s = f["score"]
            if s >= 8:
                f["nivel"] = "ALTO"
                f["cor"] = "#44B757"
            elif s >= 6.5:
                f["nivel"] = "MEDIO_ALTO"
                f["cor"] = "#A9E8A7"
            elif s >= 5:
                f["nivel"] = "MEDIO"
                f["cor"] = "#8661F5"
            elif s >= 3.5:
                f["nivel"] = "MEDIO_BAIXO"
                f["cor"] = "#FFA96E"
            else:
                f["nivel"] = "BAIXO"
                f["cor"] = "#E56813"
            f["justificativa"] = self._justificar_farol_ds(f, dados, tecnico, riscos, kb_match, extracao)

        score_final = sum(f["score"] * f["peso_pct"] / 100 for f in farois)

        # Contagem de níveis para decisão (spec §3.4)
        alto_count = sum(1 for f in farois if f["nivel"] in ("ALTO", "MEDIO_ALTO"))
        baixo_criticos = any(f["nivel"] == "BAIXO" and f["nome"] in ("Orçamento", "Decisores Acessíveis") for f in farois)

        # ═══ BEST STORY WINS (4 Perguntas DS — Spec §6.2) ═══
        nome = dados.get("nome_oportunidade", "esta oportunidade")
        setor_nome = dados.get("setor", "o setor")
        cases = kb_match.get("cases", [])
        atestados = kb_match.get("atestados", [])
        dim = tecnico.get("dimensionamento", {})

        bsw = {
            "por_que_mudar": self._gerar_bsw_mudar(cliente, setor_nome, texto_lower, extracao),
            "por_que_agora": self._gerar_bsw_agora(nome, dados, extracao),
            "por_que_minsait": self._gerar_bsw_minsait(setor_nome, tecnico, cases, atestados, kb_match),
            "por_que_confiar": self._gerar_bsw_confiar(aderencia, dim, cases, atestados),
        }

        # Decisão conforme spec §3.4
        if alto_count >= 6:
            nivel_geral = "GO"
        elif alto_count <= 3 or baixo_criticos:
            nivel_geral = "NO_GO"
        else:
            nivel_geral = "GO_CONDICIONADO"

        return {
            "farois": farois,
            "score_final_ponderado": round(score_final, 2),
            "nivel_geral": nivel_geral,
            "alto_count": alto_count,
            "best_story_wins": bsw,
        }

    # ═══ SA5: DECISOR ESTRATÉGICO ═══

    def sa5_decidir(self, dados: Dict, extracao: Dict, tecnico: Dict,
                     riscos: Dict, comercial: Dict, kb_match: Dict) -> Dict:
        """Gera decisão GO/NO-GO/CONDICIONADO com base em dados reais."""
        score = comercial.get("score_final_ponderado", 5)
        risk_score = riscos.get("risk_score", 5)
        criticos = riscos.get("criticos", 0)
        farois = comercial.get("farois", [])
        bsw = comercial.get("best_story_wins", {})
        dim = tecnico.get("dimensionamento", {})
        cobertura = kb_match.get("cobertura_score", 0)

        # Decisão
        if score >= 7.0 and risk_score <= 4:
            decisao = "GO"
            confianca = min(95, int(score * 10 + cobertura * 2))
            justificativa = (
                f"Score elevado ({score:.1f}/10) com risco controlado ({risk_score:.1f}/10). "
                f"Cobertura de KB: {cobertura:.0f}/10. "
                f"Recomendação: prosseguir com pursuit em ritmo acelerado."
            )
            next_steps = [
                "Formar equipe de proposta com Tech Lead + Commercial Lead",
                "Agendar due diligence técnica com o cliente",
                f"Preparar proposta com dimensionamento {dim.get('ftes_estimado', 'N/A')} FTEs",
                "Ativar cases/atestados relevantes do acervo DS",
            ]
        elif score < 4.0 or (criticos >= 4 and score < 5.5):
            decisao = "NO_GO"
            confianca = min(90, int((10 - score) * 10))
            justificativa = (
                f"Score insuficiente ({score:.1f}/10) com {criticos} riscos críticos. "
                f"Cobertura de KB: {cobertura:.0f}/10. "
                f"Recomendação: não prosseguir neste momento."
            )
            next_steps = [
                "Comunicar decisão NO_GO ao sponsor",
                "Documentar razões para lições aprendidas",
                "Monitorar se condições mudam para reavaliação futura",
            ]
        else:
            decisao = "GO_CONDICIONADO"
            confianca = min(80, int(score * 8))
            condicoes = []
            if risk_score > 5:
                condicoes.append("Mitigar riscos críticos identificados antes do kick-off")
            farois_baixos = [f["nome"] for f in farois if f["score"] < 4]
            if farois_baixos:
                condicoes.append(f"Endereçar faróis baixos: {', '.join(farois_baixos)}")
            if cobertura < 4:
                condicoes.append("Complementar acervo DS com cases/atestados adicionais")
            if not condicoes:
                condicoes.append("Validar alinhamento comercial com liderança antes do pursuit")

            justificativa = (
                f"Score moderado ({score:.1f}/10). {len(condicoes)} condição(ões) para GO pleno. "
                f"Cobertura de KB: {cobertura:.0f}/10."
            )
            next_steps = [
                f"Resolver condições: {'; '.join(condicoes)}",
                "Reunião de alinhamento com sponsor para validar condições",
                f"Dimensionar equipe preliminar: {dim.get('ftes_estimado', 'N/A')} FTEs",
            ] + [r["mitigacao"] for r in riscos.get("top_riscos", [])[:2]]

        return {
            "decisao": decisao,
            "score_final": round(score, 2),
            "confianca_pct": confianca,
            "justificativa_decisao": justificativa,
            "farois_consolidados": farois,
            "best_story_wins": bsw,
            "dimensionamento_final": dim,
            "riscos_consolidados": {
                "total": riscos.get("total_riscos", 0),
                "criticos": criticos,
                "risk_score": risk_score,
                "top_riscos": [{"nome": r["nome"], "severidade": r["severidade"], "mitigacao": r["mitigacao"]} for r in riscos.get("top_riscos", [])[:5]],
            },
            "next_steps": next_steps,
            "motor": "ADK Robô Python v2 — Análise Real contra Acervo DS",
        }

    # ═══ HELPERS ═══

    def _tokenizar(self, texto: str) -> set:
        return set(re.findall(r'\b\w+\b', texto.lower()))

    def _estimar_acv(self, valores: List[str], dados: Dict) -> str:
        if dados.get("valor_estimado"):
            return dados["valor_estimado"]
        if valores:
            return f"Detectado(s): {', '.join(valores[:3])}"
        return "Não identificado"

    def _estimar_complexidade(self, chars: int, n_techs: int, escopos: Dict) -> str:
        score = 0
        if chars > 50000: score += 3
        elif chars > 20000: score += 2
        elif chars > 5000: score += 1

        score += min(3, n_techs // 3)
        score += min(2, sum(1 for v in escopos.values() if v > 0))

        if score >= 7: return "MUITO_ALTA"
        if score >= 5: return "ALTA"
        if score >= 3: return "MEDIA"
        return "BAIXA"

    def _dimensionar_perfis(self, techs: Dict) -> List[str]:
        tech_names = set(techs.keys())
        perfis = ["Tech Lead", "Scrum Master"]

        if tech_names & {"java", "spring", "spring boot", "python", "django", "flask", "fastapi", ".net", "c#", "asp.net", "node", "node.js"}:
            perfis.append("Desenvolvedor Backend Senior")
            perfis.append("Desenvolvedor Backend Pleno")
        if tech_names & {"react", "angular", "vue", "next.js", "nuxt", "typescript", "javascript"}:
            perfis.append("Desenvolvedor Frontend Senior")
        if tech_names & {"ios", "android", "flutter", "react native", "mobile"}:
            perfis.append("Desenvolvedor Mobile")
        if tech_names & {"docker", "kubernetes", "k8s", "aws", "azure", "gcp", "terraform", "devops", "ci/cd"}:
            perfis.append("Engenheiro DevOps / Cloud")
        if tech_names & {"sql", "oracle", "postgresql", "mysql", "mongodb"}:
            perfis.append("DBA / Data Engineer")
        if tech_names & {"machine learning", "ml", "ia", "ai", "inteligência artificial", "deep learning"}:
            perfis.append("Data Scientist / ML Engineer")
        if tech_names & {"sap", "salesforce", "erp", "crm"}:
            perfis.append("Consultor Funcional ERP/CRM")
        if tech_names & {"power bi", "tableau", "qlik", "bi"}:
            perfis.append("Analista BI / Data Viz")

        perfis.extend(["QA Automation", "UX/UI Designer", "Arquiteto de Soluções"])
        return perfis

    def _calcular_aderencia_ds(self, techs: Dict, kb_match: Dict) -> float:
        ds_core = {"java", "spring", "python", "react", "angular", "node", "typescript",
                    ".net", "c#", "docker", "kubernetes", "aws", "azure", "gcp",
                    "microserviço", "microservice", "api", "rest", "devops", "ci/cd",
                    "mobile", "flutter", "cloud"}
        tech_names = set(techs.keys())
        matches = len(tech_names & ds_core)
        kb_bonus = kb_match.get("cobertura_score", 0) * 0.2
        return min(10, max(1, round(2 + matches * 0.8 + kb_bonus, 1)))

    def _identificar_gaps(self, texto: str, techs: List[str]) -> List[str]:
        gaps = []
        if not any(t in techs for t in ["docker", "kubernetes", "k8s", "devops"]):
            gaps.append("DevOps/Containerização não mencionado na RFP")
        if not any(t in techs for t in ["aws", "azure", "gcp", "cloud"]):
            gaps.append("Cloud provider não especificado")
        if "teste" not in texto and "test" not in texto and "qa" not in texto:
            gaps.append("Estratégia de testes não detalhada na RFP")
        if "segurança" not in texto and "security" not in texto:
            gaps.append("Requisitos de segurança não explícitos")
        if "arquitetura" not in texto and "architecture" not in texto:
            gaps.append("Arquitetura de solução não detalhada")
        return gaps

    def _justificar_farol_ds(self, farol: Dict, dados: Dict, tecnico: Dict, riscos: Dict, kb_match: Dict, extracao: Dict) -> str:
        """Justificativas específicas para os 8 Faróis DS (spec §6.1)."""
        fid = farol["id"]
        s = farol["score"]
        nivel = farol["nivel"]
        setor = dados.get("setor", "N/A")
        total_pal = extracao.get("analise_documento", {}).get("total_palavras", 0)

        justifs = {
            "F1": (
                f"{'RFP formal com escopo detalhado' if total_pal > 3000 else 'RFP com escopo limitado'}. "
                f"Documento com {total_pal} palavras. "
                f"{'Demanda concreta com urgência identificada.' if s >= 7 else 'Urgência moderada.' if s >= 4 else 'Baixa concretude da demanda.'}"
            ),
            "F2": (
                f"{'Indicadores financeiros identificados na RFP.' if s >= 6 else 'Orçamento não explicitado na RFP.'} "
                f"Complexidade {extracao.get('complexidade_estimada', 'N/A')} "
                f"{'sugere ACV relevante.' if s >= 6 else 'requer validação de budget.'}"
            ),
            "F3": (
                f"{'Referências a sponsor/champion identificadas.' if s >= 6 else 'Champion não identificado claramente.'} "
                f"Setor {setor} {'com' if s >= 6 else 'sem'} relacionamento Minsait consolidado."
            ),
            "F4": (
                f"{'Processo decisório mapeado na RFP.' if s >= 6 else 'Decisores não claramente identificados.'} "
                f"{'Licitação formal — decisores acessíveis via processo.' if 'licitação' in str(extracao).lower() else 'Validar acesso ao comitê decisor.'}"
            ),
            "F5": (
                f"Aderência DS: {tecnico.get('aderencia_ds', 'N/A')}/10. "
                f"Setor {setor} — peso estratégico {'alto' if s >= 7 else 'médio' if s >= 4 else 'baixo'}. "
                f"{'Vertical prioritária para Minsait 2026.' if s >= 7 else 'Avaliar prioridade estratégica.'}"
            ),
            "F6": (
                f"{tecnico.get('total_tecnologias', 0)} tecnologias DS identificadas. "
                f"{'Oportunidade de cross-sell com DIC/Data&AI.' if s >= 6 else 'Escopo focado em DS puro.'} "
                f"{'Potencial de portfólio 360°.' if s >= 7 else ''}"
            ),
            "F7": (
                f"Acervo DS: {kb_match.get('docs_relevantes', kb_match.get('relevantes', 0))} docs relevantes. "
                f"{len(kb_match.get('cases', []))} cases e {len(kb_match.get('atestados', []))} atestados disponíveis. "
                f"Cobertura KB: {kb_match.get('cobertura_score', kb_match.get('cobertura', 0))}/10."
            ),
            "F8": (
                f"Posição competitiva {'forte' if nivel == 'ALTO' else 'moderada' if nivel == 'MEDIO' else 'fraca'}. "
                f"Risk score: {riscos.get('risk_score', 'N/A')}/10. "
                f"{'Alavanca: qualidade técnica + cases.' if s >= 7 else 'Atenção: diferenciação necessária.'}"
            ),
        }
        return justifs.get(fid, "")

    def _gerar_bsw_mudar(self, cliente, setor, texto_lower, extracao) -> str:
        escopo = extracao.get("escopo", {}).get("principal", "transformação digital")
        return (
            f"{cliente} necessita de {escopo} para manter competitividade no setor {setor}. "
            f"A publicação desta RFP demonstra urgência em transformar operações. "
            f"Documento com {extracao.get('analise_documento', {}).get('total_paginas_estimado', 'N/A')} páginas "
            f"e {extracao.get('analise_documento', {}).get('total_palavras', 'N/A')} palavras indica escopo bem definido."
        )

    def _gerar_bsw_agora(self, nome, dados, extracao) -> str:
        prazo = dados.get("prazo_resposta", "a definir")
        return (
            f"Janela de oportunidade aberta pela RFP '{nome}'. "
            f"Prazo de resposta: {prazo}. "
            f"Complexidade {extracao.get('complexidade_estimada', 'N/A')} exige resposta rápida "
            f"e equipe pronta para iniciar imediatamente."
        )

    def _gerar_bsw_minsait(self, setor, tecnico, cases, atestados, kb_match) -> str:
        n_perfis = len(tecnico.get("dimensionamento", {}).get("perfis_chave", []))
        cases_txt = f", incluindo: {', '.join(c.get('titulo', '')[:40] for c in cases[:3])}" if cases else ""
        atestados_txt = f" e {len(atestados)} atestados técnicos" if atestados else ""
        return (
            f"Minsait DS possui {n_perfis} perfis técnicos aderentes ao projeto. "
            f"Acervo DS contém {kb_match.get('docs_relevantes', 0)} documentos relevantes{cases_txt}{atestados_txt}. "
            f"Cobertura de base de conhecimento: {kb_match.get('cobertura_score', 0):.0f}/10."
        )

    def _gerar_bsw_confiar(self, aderencia, dim, cases, atestados) -> str:
        ftes = dim.get("ftes_estimado", "N/A")
        return (
            f"Track record Minsait em projetos DS com aderência {aderencia}/10. "
            f"Equipe dimensionada: {ftes} FTEs, {dim.get('duracao_meses', 'N/A')} meses, "
            f"{dim.get('total_sprints', 'N/A')} sprints. "
            f"{len(cases)} cases e {len(atestados)} atestados comprovam capacidade de entrega."
        )
