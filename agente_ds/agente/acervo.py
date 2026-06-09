# -*- coding: utf-8 -*-
"""
Acervo DS — Busca no Catálogo de Materiais_DS
Consulta catalog.json e taxonomy.json para fornecer contexto RAG ao agente.
Baseado em: 07_AGENTE_1_QUALIFICACAO_DS.md §2.3, 04_MAPEAMENTO_KB_ACERVO.md
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional


class AcervoDS:
    """
    Gerencia o acervo documental DS usando catalog.json como índice.
    Gerencia o acervo documental DS com busca por relevância.
    """

    # Categorias prioritárias para DS (§2.3)
    CATEGORIAS_PRIORIDADE = ["C", "B", "PT", "P", "I"]

    # Filtros específicos da prática DS
    FILTRO_PRATICA = ["Desenvolvimento de Soluções", "DES", "DS"]
    FILTRO_TECNOLOGIAS = [
        "Java", ".NET", "React", "Angular", "Mobile", "Cloud",
        "Python", "TypeScript", "Flutter", "Vue.js", "Next.js",
        "Node.js", "Spring", "Microservices", "Kubernetes",
        "DevOps", "CI/CD", "Terraform", "AWS", "Azure", "GCP",
    ]

    def __init__(self, acervo_root: str = None, catalog_path: str = None, taxonomy_path: str = None):
        """
        Args:
            acervo_root: Raiz do Materiais_DS (contém as pastas A-Z)
            catalog_path: Caminho para catalog.json
            taxonomy_path: Caminho para taxonomy.json
        """
        base = Path(acervo_root or os.getenv("ACERVO_ROOT", ".."))
        if not base.is_absolute():
            base = Path(__file__).parent.parent / base

        self.acervo_root = base.resolve()
        self.catalog_path = Path(catalog_path or os.getenv("CATALOG_PATH", str(self.acervo_root / "catalog.json")))
        self.taxonomy_path = Path(taxonomy_path or os.getenv("TAXONOMY_PATH", str(self.acervo_root / "taxonomy.json")))

        if not self.catalog_path.is_absolute():
            self.catalog_path = (Path(__file__).parent.parent / self.catalog_path).resolve()
        if not self.taxonomy_path.is_absolute():
            self.taxonomy_path = (Path(__file__).parent.parent / self.taxonomy_path).resolve()

        self._catalog = None
        self._taxonomy = None

    @property
    def catalog(self) -> List[Dict]:
        if self._catalog is None:
            raw = self._carregar_json(self.catalog_path, [])
            if isinstance(raw, dict):
                self._catalog = raw.get("documentos", [])
            elif isinstance(raw, list):
                self._catalog = raw
            else:
                self._catalog = []
        return self._catalog

    @property
    def taxonomy(self) -> Dict:
        if self._taxonomy is None:
            self._taxonomy = self._carregar_json(self.taxonomy_path, {})
        return self._taxonomy

    def buscar_relevantes(self, texto_rfp: str, top_k: int = 15) -> List[Dict]:
        """
        Busca os top_k documentos mais relevantes do acervo para a RFP.
        Estratégia: keyword matching + peso por categoria prioritária.
        """
        if not self.catalog:
            return []

        # Tokenizar texto da RFP
        tokens_rfp = set(texto_rfp.lower().split())

        scores = []
        for doc in self.catalog:
            score = self._calcular_relevancia(doc, tokens_rfp)
            if score > 0:
                scores.append((score, doc))

        # Ordenar por score desc e retornar top_k
        scores.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scores[:top_k]]

    def _calcular_relevancia(self, doc: Dict, tokens_rfp: set) -> float:
        """Calcula score de relevância de um documento para a RFP."""
        score = 0.0

        # 1. Categoria prioritária (+2 por match)
        categoria = doc.get("categoria", "")
        if categoria in self.CATEGORIAS_PRIORIDADE:
            idx = self.CATEGORIAS_PRIORIDADE.index(categoria)
            score += (len(self.CATEGORIAS_PRIORIDADE) - idx) * 0.5

        # 2. Match de prática DS (+3)
        praticas = doc.get("praticas", [])
        if isinstance(praticas, str):
            praticas = [praticas]
        for p in praticas:
            if any(fp.lower() in p.lower() for fp in self.FILTRO_PRATICA):
                score += 3.0
                break

        # 3. Match de tecnologias (+1 por tech)
        tags = doc.get("tags_busca", doc.get("tags", []))
        titulo = doc.get("titulo", "").lower()
        desc = doc.get("categoria_descricao", doc.get("descricao", "")).lower()
        conteudo = f"{titulo} {desc} {' '.join(str(t).lower() for t in tags)}"

        for tech in self.FILTRO_TECNOLOGIAS:
            if tech.lower() in conteudo:
                score += 1.0

        # 4. Overlap de palavras com RFP (+0.1 por word match)
        doc_tokens = set(conteudo.split())
        overlap = tokens_rfp & doc_tokens
        score += len(overlap) * 0.1

        # 5. Relevância por agente (se alto = +1)
        relevancia = doc.get("relevancia_agentes", {})
        if isinstance(relevancia, dict):
            for agent_key in ["A1_qualificacao", "A1", "agente_1", "qualificacao"]:
                val = relevancia.get(agent_key, "")
                if isinstance(val, str) and "alto" in val.lower():
                    score += 1.0
                    break

        return score

    def get_contexto_rag(self, texto_rfp: str, top_k: int = 15) -> str:
        """
        Retorna string formatada com os documentos relevantes do acervo
        para inclusão no prompt do agente.
        """
        docs = self.buscar_relevantes(texto_rfp, top_k)

        if not docs:
            return "[ACERVO] Nenhum documento relevante encontrado no acervo DS."

        linhas = [f"[ACERVO DS — {len(docs)} documentos relevantes encontrados]\n"]

        for i, doc in enumerate(docs, 1):
            titulo = doc.get("titulo", "Sem título")
            categoria = doc.get("categoria", "?")
            mercado = doc.get("mercado", "N/A")
            praticas = doc.get("praticas", [])
            if isinstance(praticas, list):
                praticas = ", ".join(praticas)
            desc = doc.get("categoria_descricao", doc.get("descricao", ""))
            path = doc.get("path", "")

            linhas.append(
                f"  [{i}] {titulo}\n"
                f"      Categoria: {categoria} | Mercado: {mercado} | Práticas: {praticas}\n"
                f"      Descrição: {desc[:200]}\n"
                f"      Path: {path}\n"
            )

        return "\n".join(linhas)

    def get_taxonomia_resumo(self) -> str:
        """Retorna resumo da taxonomia para o prompt."""
        tax = self.taxonomy
        if not tax:
            return "[TAXONOMIA] Não carregada."

        mercados = tax.get("mercados", tax.get("markets", []))
        praticas = tax.get("praticas", tax.get("practices", []))

        linhas = ["[TAXONOMIA DS]"]
        if mercados:
            linhas.append(f"  Mercados ({len(mercados)}): {', '.join(str(m.get('nome', m.get('name', m))) for m in mercados if isinstance(m, dict))}")
        if praticas:
            linhas.append(f"  Práticas ({len(praticas)}): {', '.join(str(p.get('nome', p.get('name', p))) for p in praticas if isinstance(p, dict))}")

        return "\n".join(linhas)

    def get_stats(self) -> Dict:
        """Estatísticas do acervo."""
        total = len(self.catalog)
        por_categoria = {}
        for doc in self.catalog:
            cat = doc.get("categoria", "?")
            por_categoria[cat] = por_categoria.get(cat, 0) + 1

        return {
            "total_documentos": total,
            "por_categoria": por_categoria,
            "categorias_prioridade_ds": self.CATEGORIAS_PRIORIDADE,
            "catalog_path": str(self.catalog_path),
            "taxonomy_path": str(self.taxonomy_path),
            "acervo_root": str(self.acervo_root),
        }

    def _carregar_json(self, path: Path, default):
        """Carrega JSON com fallback."""
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8-sig") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[AcervoDS] Erro ao carregar {path}: {e}")
        return default
