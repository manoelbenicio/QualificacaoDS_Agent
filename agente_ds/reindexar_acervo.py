# -*- coding: utf-8 -*-
"""
REINDEXADOR COMPLETO DO ACERVO DS
Varre TODA a árvore Materiais_DS e gera catalog.json com TODOS os documentos.
"""
import os
import json
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.resolve()  # Materiais_DS
print(f"Root: {ROOT}")

# Pastas a IGNORAR (não são acervo)
IGNORAR = {
    "agente_ds", "__pycache__", ".git", "node_modules",
    ".venv", "template_UI_UX",
}

# Mapeamento de pasta → categoria
CATEGORIA_MAP = {
    "A_Atestados": {"cat": "A", "desc": "Atestados Técnicos", "prioridade": 1},
    "B_Cases": {"cat": "B", "desc": "Cases de Sucesso", "prioridade": 2},
    "C_Capacidades_Portfolio": {"cat": "C", "desc": "Capacidades e Portfolio", "prioridade": 3},
    "D_Defesas_Tecnicas": {"cat": "D", "desc": "Defesas Técnicas", "prioridade": 4},
    "I_Institucional": {"cat": "I", "desc": "Institucional", "prioridade": 5},
    "M_Metodologias": {"cat": "M", "desc": "Metodologias", "prioridade": 6},
    "O_Outros": {"cat": "O", "desc": "Outros", "prioridade": 10},
    "P_Planejamento_OpTech": {"cat": "P", "desc": "Planejamento OpTech", "prioridade": 7},
    "PT_Propostas_Tecnicas": {"cat": "PT", "desc": "Propostas Técnicas", "prioridade": 3},
    "S_Solucoes_Verticais": {"cat": "S", "desc": "Soluções Verticais", "prioridade": 4},
    "T_Templates_Proposta": {"cat": "T", "desc": "Templates de Proposta", "prioridade": 5},
    "Z_Normativo": {"cat": "Z", "desc": "Normativo / Regulatório", "prioridade": 8},
    "_ofertas_ativas": {"cat": "OA", "desc": "Ofertas Ativas (Projetos em andamento)", "prioridade": 2},
    "_operacional": {"cat": "OP", "desc": "Operacional (rates, jurídico, contratos)", "prioridade": 6},
    "_modelos_rfp_respondidas": {"cat": "RFP", "desc": "Modelos de RFP Respondidas", "prioridade": 3},
    "_cases_horizontais": {"cat": "CH", "desc": "Cases Horizontais", "prioridade": 2},
    "_archive": {"cat": "ARQ", "desc": "Arquivo", "prioridade": 10},
}

# Extensões relevantes (documentos de negócio)
EXTENSOES_DOC = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xlsm", ".xlsb", ".xls",
    ".pptx", ".ppt", ".txt", ".md", ".csv", ".html", ".htm",
    ".eml", ".msg", ".xml", ".json", ".zip",
}

# Tecnologias para tags
TECH_TAGS = [
    "java", "spring", "python", "django", "flask", ".net", "c#",
    "react", "angular", "vue", "node", "typescript", "javascript",
    "docker", "kubernetes", "aws", "azure", "gcp", "cloud",
    "microserviço", "microservice", "api", "rest", "devops",
    "sap", "salesforce", "power bi", "tableau",
    "machine learning", "ia", "mobile", "flutter",
    "sql", "oracle", "postgresql", "mongodb",
    "outsourcing", "sustentação", "ams", "body shop",
    "fábrica de software", "squad",
]

# Mercados/Verticais para tags
MERCADOS = [
    "energia", "utilities", "financeiro", "banco", "seguros",
    "governo", "público", "telecom", "saúde", "indústria",
    "manufatura", "varejo", "transporte", "logística",
    "óleo", "gás", "mineração", "agro", "educação",
]

# Clientes para tags
CLIENTES = [
    "volkswagen", "vw", "cpfl", "santander", "bradesco", "itaú",
    "motiva", "energisa", "enel", "light", "cemig", "copel",
    "sabesp", "comgás", "equatorial", "neoenergia", "petrobras",
    "vale", "gerdau", "ambev", "natura", "magazine luiza",
    "mercado livre", "nubank", "inter", "porto seguro",
]


def extrair_tags(nome_arquivo: str, path_rel: str) -> list:
    """Extrai tags de busca do nome do arquivo e path."""
    texto = f"{nome_arquivo} {path_rel}".lower()
    tags = set()

    # Tecnologias
    for tech in TECH_TAGS:
        if tech in texto:
            tags.add(tech)

    # Mercados
    for mercado in MERCADOS:
        if mercado in texto:
            tags.add(mercado)

    # Clientes
    for cliente in CLIENTES:
        if cliente in texto:
            tags.add(cliente)

    # Palavras significativas do nome do arquivo
    nome_clean = re.sub(r'[_\-\.]', ' ', Path(nome_arquivo).stem).lower()
    palavras = [p for p in nome_clean.split() if len(p) > 3 and p not in {'para', 'com', 'que', 'das', 'dos', 'uma', 'este'}]
    tags.update(palavras[:10])

    return sorted(tags)


def determinar_praticas(nome: str, path: str) -> list:
    """Determina práticas associadas ao documento."""
    texto = f"{nome} {path}".lower()
    praticas = []

    if any(kw in texto for kw in ["desenvolvimento", "software", "dev", "squad", "fábrica", "factory"]):
        praticas.append("Desenvolvimento de Soluções")
    if any(kw in texto for kw in ["sustentação", "ams", "manutenção", "suporte"]):
        praticas.append("Sustentação / AMS")
    if any(kw in texto for kw in ["outsourcing", "body shop", "alocação"]):
        praticas.append("Outsourcing")
    if any(kw in texto for kw in ["consultoria", "assessment", "diagnóstico"]):
        praticas.append("Consultoria")
    if any(kw in texto for kw in ["data", "analytics", "bi", "dados", "ia", "machine learning"]):
        praticas.append("Data & Analytics")
    if any(kw in texto for kw in ["cloud", "infra", "devops", "migração"]):
        praticas.append("Cloud & Infra")

    if not praticas:
        praticas.append("Desenvolvimento de Soluções")  # Default DS

    return praticas


def determinar_mercado(nome: str, path: str) -> str:
    """Determina mercado/vertical do documento."""
    texto = f"{nome} {path}".lower()

    mapa = {
        "Energia & Utilities": ["energia", "utilities", "cpfl", "cemig", "enel", "light", "copel", "energisa", "equatorial", "neoenergia", "comgás", "sabesp"],
        "Financeiro & Seguros": ["financeiro", "banco", "seguros", "santander", "bradesco", "itaú", "nubank", "inter", "porto seguro"],
        "Indústria & Manufatura": ["indústria", "manufatura", "volkswagen", "vw", "gerdau", "vale", "ambev"],
        "Telecom & Mídia": ["telecom", "telecomunicação", "mídia"],
        "Governo & Setor Público": ["governo", "público", "licitação"],
        "Saúde": ["saúde", "hospital", "farmacêutic"],
        "Varejo": ["varejo", "retail", "magazine", "mercado livre"],
        "Transporte & Logística": ["transporte", "logística"],
        "Óleo & Gás": ["óleo", "gás", "petrobras"],
        "Mineração": ["mineração"],
    }

    for mercado, keywords in mapa.items():
        if any(kw in texto for kw in keywords):
            return mercado

    return "Multi-setor"


def indexar():
    """Indexa TODOS os arquivos relevantes do Materiais_DS."""
    documentos = []
    total_scanned = 0
    total_indexed = 0

    for dirpath, dirnames, filenames in os.walk(ROOT):
        # Filtrar pastas ignoradas
        dirnames[:] = [d for d in dirnames if d not in IGNORAR]

        for filename in filenames:
            total_scanned += 1
            fpath = Path(dirpath) / filename
            ext = fpath.suffix.lower()

            # Só documentos de negócio
            if ext not in EXTENSOES_DOC:
                continue

            # Ignorar arquivos temporários
            if filename.startswith("~") or filename.startswith("."):
                continue

            rel = fpath.relative_to(ROOT)
            parts = str(rel).split(os.sep)
            pasta_raiz = parts[0] if len(parts) > 1 else "/"

            # Categoria
            cat_info = CATEGORIA_MAP.get(pasta_raiz, {"cat": "?", "desc": pasta_raiz, "prioridade": 9})

            # Subpasta (se existir) = contexto adicional
            subpasta = parts[1] if len(parts) > 2 else ""

            # Tags
            tags = extrair_tags(filename, str(rel))

            # Práticas
            praticas = determinar_praticas(filename, str(rel))

            # Mercado
            mercado = determinar_mercado(filename, str(rel))

            # Tamanho
            try:
                size_bytes = fpath.stat().st_size
            except:
                size_bytes = 0

            doc = {
                "titulo": Path(filename).stem.replace("_", " ").replace("-", " "),
                "arquivo": filename,
                "path": str(rel),
                "categoria": cat_info["cat"],
                "categoria_descricao": cat_info["desc"],
                "prioridade": cat_info["prioridade"],
                "subpasta": subpasta,
                "extensao": ext,
                "tamanho_bytes": size_bytes,
                "mercado": mercado,
                "praticas": praticas,
                "tags_busca": tags,
                "relevancia_agentes": {
                    "A1_qualificacao": "alto" if cat_info["cat"] in ("A", "B", "C", "PT", "OA", "RFP", "CH") else "medio",
                },
            }

            documentos.append(doc)
            total_indexed += 1

    return documentos, total_scanned, total_indexed


# ═══ EXECUTAR ═══
print(f"Indexando Materiais_DS...")
print(f"Timestamp: {datetime.now().isoformat()}")
print()

docs, scanned, indexed = indexar()

# Estatísticas
por_cat = {}
for d in docs:
    cat = d["categoria"]
    por_cat[cat] = por_cat.get(cat, 0) + 1

print(f"Scanned: {scanned} arquivos")
print(f"Indexed: {indexed} documentos de negócio")
print()
print("Por categoria:")
for cat, count in sorted(por_cat.items(), key=lambda x: -x[1]):
    desc = next((d["categoria_descricao"] for d in docs if d["categoria"] == cat), cat)
    print(f"  [{cat:>3}] {desc}: {count}")

# Salvar
catalog = {
    "versao": "2.0",
    "gerado_em": datetime.now().isoformat(),
    "total_documentos": len(docs),
    "por_categoria": por_cat,
    "documentos": docs,
}

out_path = ROOT / "catalog.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)

print(f"\nSalvo em: {out_path}")
print(f"Tamanho: {out_path.stat().st_size:,} bytes")
print(f"\n✅ CATALOG COMPLETO: {indexed} documentos indexados")
