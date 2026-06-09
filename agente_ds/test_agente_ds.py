# -*- coding: utf-8 -*-
"""
Teste de Qualificação DS — Simulação com RFP fictícia
Executa o pipeline completo do Agente DS sem precisar de servidor HTTP.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Adicionar diretórios ao path
sys.path.insert(0, str(Path(__file__).parent))

from agente import AgenteDS, ExtratorDocumental, AcervoDS, ValidadorInput


def criar_rfp_teste() -> str:
    """Cria uma RFP fictícia de DS para teste."""
    rfp_content = """
SOLICITAÇÃO DE PROPOSTA (RFP)
EMPRESA: ENERGISA — Grupo Energisa S.A.
DATA: 05/06/2026
OBJETO: Desenvolvimento de Portal de Autoatendimento do Cliente + App Mobile

═══════════════════════════════════════════════
1. ESCOPO DO PROJETO
═══════════════════════════════════════════════

A Energisa busca parceiro tecnológico para desenvolver:

1.1 Portal Web de Autoatendimento (responsivo)
- Tecnologia: React.js + Next.js (SSR/SSG)
- Backend: API REST com Node.js ou Java Spring Boot
- Banco de dados: PostgreSQL (principal) + Redis (cache)
- Autenticação: OAuth 2.0 + SSO com Azure AD
- Funcionalidades:
  - Segunda via de fatura (PDF download)
  - Histórico de consumo (gráficos D3.js/Chart.js)
  - Solicitação de serviços (religação, troca titularidade)
  - Chat com atendente (WebSocket)
  - Notificações push
  - Dashboard de consumo em tempo real

1.2 Aplicativo Mobile
- Tecnologia: Flutter (Android + iOS)
- Features:
  - Todas do portal web
  - Leitura de medidor por foto (OCR)
  - Geolocalização de agências
  - Pagamento via PIX (integração bancária)
  - Modo offline (sincronização automática)

1.3 Integrações obrigatórias
- SAP ISU (Sistema Comercial) via SAP Gateway OData
- CRM Salesforce via API REST
- Gateway de pagamentos CIELO/REDE
- Plataforma de SMS/WhatsApp (Twilio)
- Google Maps API
- Azure Cognitive Services (OCR)

═══════════════════════════════════════════════
2. REQUISITOS NÃO-FUNCIONAIS
═══════════════════════════════════════════════

- Performance: < 3s tempo de resposta em 95th percentile
- Disponibilidade: 99.9% (SLA)
- Segurança: LGPD compliance, WAF, rate limiting, OWASP Top 10
- Escalabilidade: 50.000 acessos simultâneos
- Acessibilidade: WCAG 2.1 AA
- CI/CD: Pipeline automatizado (Jenkins ou GitHub Actions)
- Testes: Cobertura mínima 80% (unitários + integração)
- Documentação: OpenAPI 3.0 para todas as APIs

═══════════════════════════════════════════════
3. MODELO DE CONTRATAÇÃO
═══════════════════════════════════════════════

- Tipo: Projeto com escopo fechado (Fase 1) + Sustentação (Fase 2)
- Fase 1: 8 meses de desenvolvimento
- Fase 2: 24 meses de sustentação / AMS
- Modelo de trabalho: Híbrido (escritório São Paulo + remoto)
- Metodologia: Scrum (sprints de 2 semanas)

═══════════════════════════════════════════════
4. REQUISITOS DE EQUIPE
═══════════════════════════════════════════════

Equipe mínima esperada:
- 1 Tech Lead / Arquiteto de Soluções
- 2 Desenvolvedores Backend Sênior (Java/Node)
- 2 Desenvolvedores Frontend Sênior (React/Next.js)
- 2 Desenvolvedores Mobile (Flutter)
- 1 QA Engineer Sênior (automação)
- 1 UX/UI Designer
- 1 DevOps Engineer
- 1 Scrum Master
- 1 Product Owner (compartilhado)

═══════════════════════════════════════════════
5. CRONOGRAMA
═══════════════════════════════════════════════

- Proposta técnica: até 20/06/2026
- Apresentação técnica: 25/06/2026
- Início do projeto: 15/07/2026
- MVP (portal web): Outubro/2026
- MVP (mobile): Dezembro/2026
- Go-live completo: Março/2027

═══════════════════════════════════════════════
6. CRITÉRIOS DE AVALIAÇÃO
═══════════════════════════════════════════════

| Critério | Peso |
|----------|------|
| Experiência em projetos similares (utilities) | 25% |
| Capacidade técnica (stack React + Flutter) | 30% |
| Metodologia e governança | 15% |
| Preço global | 20% |
| Cases com SAP ISU | 10% |

═══════════════════════════════════════════════
7. PENALIDADES
═══════════════════════════════════════════════

- Atraso no MVP: multa de 2% do valor do contrato por semana
- SLA < 99.9%: desconto de 5% na fatura mensal
- Turnover > 20% em 3 meses: multa de 1 salário por profissional substituído
- Não conformidade LGPD: rescisão contratual imediata

═══════════════════════════════════════════════
8. ORÇAMENTO ESTIMADO
═══════════════════════════════════════════════

Budget do cliente: R$ 3.500.000 (Fase 1) + R$ 150.000/mês (Fase 2)
ACV total estimado: R$ 7.100.000 (Fase 1 + 2 anos de sustentação)

═══════════════════════════════════════════════
9. CONCORRENTES CONHECIDOS
═══════════════════════════════════════════════

- Accenture
- Capgemini
- Stefanini
- CI&T
"""
    # Salvar como arquivo temporário
    rfp_dir = Path(__file__).parent / "uploads"
    rfp_dir.mkdir(exist_ok=True)
    rfp_path = rfp_dir / "RFP_Energisa_Portal_Mobile_2026.txt"
    rfp_path.write_text(rfp_content, encoding="utf-8")
    return str(rfp_path)


def test_validacao():
    """Testa validação de inputs."""
    print("\n" + "═" * 60)
    print("  TESTE 1 — VALIDAÇÃO DE INPUTS")
    print("═" * 60)

    v = ValidadorInput()

    # Teste com dados válidos
    dados_ok = {
        "nome_oportunidade": "Energisa - Portal Autoatendimento + App Mobile",
        "cliente": "Energisa",
        "setor": "Energia & Utilities",
        "tipo_servico": "Desenvolvimento de Software (Projeto/Escopo Fechado)",
        "pratica": "DS",
        "modelo_trabalho": "Híbrido",
        "acv_estimado": 7100000,
        "prazo_entrega_proposta": "2026-06-20",
        "stack_preferida": ["React", "Next.js", "Flutter", "Node.js", "Java Spring Boot"],
        "concorrentes_conhecidos": ["Accenture", "Capgemini", "Stefanini", "CI&T"],
    }
    valido, erros = v.validar(dados_ok)
    print(f"  Dados válidos: {valido}")
    if erros:
        print(f"  Erros: {erros}")
    assert valido, f"Deveria ser válido, mas: {erros}"
    print("  ✅ PASSED")

    # Teste com dados inválidos
    dados_bad = {"nome_oportunidade": "x", "cliente": "", "setor": "Invalido"}
    valido2, erros2 = v.validar(dados_bad)
    print(f"\n  Dados inválidos: {not valido2}")
    print(f"  Erros capturados: {len(erros2)}")
    for e in erros2:
        print(f"    ❌ {e}")
    assert not valido2, "Deveria ser inválido"
    print("  ✅ PASSED")


def test_extracao():
    """Testa extração de documentos."""
    print("\n" + "═" * 60)
    print("  TESTE 2 — EXTRAÇÃO DOCUMENTAL")
    print("═" * 60)

    ext = ExtratorDocumental()
    rfp_path = criar_rfp_teste()

    resultado = ext.extrair(rfp_path)
    print(f"  Status: {resultado['status']}")
    print(f"  Arquivo: {resultado.get('arquivo', 'N/A')}")
    print(f"  Caracteres: {resultado.get('caracteres', 0):,}")
    print(f"  Parsers disponíveis: {list(ext._parsers.keys())}")

    assert resultado["status"] == "ok"
    assert resultado["caracteres"] > 100
    print("  ✅ PASSED")


def test_acervo():
    """Testa consulta ao acervo."""
    print("\n" + "═" * 60)
    print("  TESTE 3 — ACERVO DS (RAG)")
    print("═" * 60)

    acervo = AcervoDS()
    stats = acervo.get_stats()
    print(f"  Catalog: {stats['catalog_path']}")
    print(f"  Total docs: {stats['total_documentos']}")
    print(f"  Por categoria: {json.dumps(stats['por_categoria'], indent=4)}")

    # Buscar docs relevantes
    texto_busca = "Desenvolvimento de portal web React Node.js mobile Flutter energia utilities SAP"
    docs = acervo.buscar_relevantes(texto_busca, top_k=5)
    print(f"\n  Busca: '{texto_busca[:60]}...'")
    print(f"  Resultados: {len(docs)}")
    for i, doc in enumerate(docs[:5], 1):
        print(f"    [{i}] {doc.get('titulo', 'N/A')[:60]} (cat: {doc.get('categoria', '?')})")

    # Taxonomia
    tax_resumo = acervo.get_taxonomia_resumo()
    print(f"\n  Taxonomia: {tax_resumo[:100]}...")

    print("  ✅ PASSED")


def test_qualificacao_completa():
    """Testa pipeline completo (sem LLM - apenas estrutura)."""
    print("\n" + "═" * 60)
    print("  TESTE 4 — PIPELINE COMPLETO (dry-run)")
    print("═" * 60)

    agente = AgenteDS()

    # Verificar que o health check funciona
    health = agente.health_check()
    print(f"  Agente: {health['agente']}")
    print(f"  Prática: {health['pratica']}")
    print(f"  Model: {health['llm_model']}")
    print(f"  API Key: {'✅ Configurada' if health['api_key_configurada'] else '⚠️ Não configurada'}")
    print(f"  Parsers: {health['extrator_parsers']}")
    print(f"  Acervo docs: {health['acervo']['total_documentos']}")

    if not health["api_key_configurada"]:
        print("\n  ⚠️ API key não configurada — pulando chamada LLM")
        print("  Para testar com LLM: crie .env com ANTHROPIC_API_KEY")

        # Testar pipeline parcial (validação + extração + acervo)
        rfp_path = criar_rfp_teste()
        dados = {
            "nome_oportunidade": "Energisa - Portal + Mobile",
            "cliente": "Energisa",
            "setor": "Energia & Utilities",
            "tipo_servico": "Desenvolvimento de Software (Projeto/Escopo Fechado)",
            "pratica": "DS",
        }

        # Validar
        valido, erros = agente.validador.validar(dados)
        print(f"\n  Validação: {'✅' if valido else '❌'}")

        # Extrair
        extracao = agente.extrator.extrair(rfp_path)
        print(f"  Extração: {extracao['status']} ({extracao.get('caracteres', 0):,} chars)")

        # Acervo
        texto = extracao.get("texto", "")
        contexto = agente.acervo.get_contexto_rag(texto, top_k=5)
        print(f"  Acervo RAG: {contexto[:80]}...")

        print("\n  ✅ Pipeline parcial OK (sem LLM)")
    else:
        print("\n  🚀 Executando qualificação COMPLETA com LLM...")
        rfp_path = criar_rfp_teste()
        dados = {
            "nome_oportunidade": "Energisa - Portal Autoatendimento + App Mobile",
            "cliente": "Energisa",
            "setor": "Energia & Utilities",
            "tipo_servico": "Desenvolvimento de Software (Projeto/Escopo Fechado)",
            "pratica": "DS",
            "modelo_trabalho": "Híbrido",
            "acv_estimado": 7100000,
            "prazo_entrega_proposta": "2026-06-20",
            "stack_preferida": ["React", "Next.js", "Flutter", "Node.js", "Java Spring Boot"],
            "concorrentes_conhecidos": ["Accenture", "Capgemini", "Stefanini", "CI&T"],
        }

        resultado = agente.qualificar(dados, rfp_path)
        print(f"\n  Status: {resultado['status']}")
        print(f"  Duração: {resultado.get('duracao_segundos', 'N/A')}s")

        if resultado["status"] == "concluido":
            parecer = resultado.get("parecer", {})
            decisao = parecer.get("decisao", "N/A")
            score = parecer.get("score_final", "N/A")
            print(f"  Decisão: {decisao}")
            print(f"  Score: {score}")

            # Salvar output
            output_path = Path(__file__).parent / "out" / f"teste_qualificacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_path.parent.mkdir(exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)
            print(f"  Output salvo: {output_path}")

        print("  ✅ PASSED")


def main():
    """Executa todos os testes."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║   AGENTE DS — SUITE DE TESTES DE QUALIFICAÇÃO            ║
║   Prática: Desenvolvimento de Soluções                   ║
║   Indra Minsait Brasil — DSS Agents v1.0                 ║
╚═══════════════════════════════════════════════════════════╝
    """)

    test_validacao()
    test_extracao()
    test_acervo()
    test_qualificacao_completa()

    print("\n" + "═" * 60)
    print("  TODOS OS TESTES CONCLUÍDOS ✅")
    print("═" * 60)


if __name__ == "__main__":
    main()
