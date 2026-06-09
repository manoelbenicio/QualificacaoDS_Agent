# Prompt de Contexto (PROMPT_CONTEXTO_AGENTES.md) — Base de Conhecimento Materiais_DS

> **Como usar:** Copie o bloco abaixo (entre os marcadores `===`) e cole no system prompt ou contexto de qualquer agente que precise consumir o acervo intelectual Indra Minsait.
> **Versão:** 2.0 — 08/06/2026 (pós-classificação completa dos 2.047 arquivos)

---

## ••• INÍCIO DO PROMPT — COPIAR DAQUI •••

```
Você tem acesso à base de conhecimento "Materiais_DS" da Indra Minsait Brasil.
Esta base contém 2.047 arquivos classificados por mercado e prática:
  • 195 documentos catalogados (IDs estáveis ACV-{CAT}-{NNN})
  • 1.687 arquivos de ofertas ativas (42 projetos em 8 clientes)
  • 81 RFPs respondidas históricas (7 ofertas)
  • 178 arquivos operacionais (atestados, rates, certificados, jurídico)
  • 7 cases horizontais cross-mercado

═══════════════════════════════════════
 ARQUIVOS DE CONTROLE (carregue SEMPRE)
═══════════════════════════════════════

1. Materiais_DS/README.md
   → Documento mestre. Explica toda a estrutura, convenções, uso por agente, FAQ.
   → CARREGUE PRIMEIRO — é o entry point.

2. Materiais_DS/taxonomy.json
   → Definições canônicas para classificação:
     • 8 Mercados (DNs): energia_e_utilities, telco, industria_e_consumo, sge,
       administracao_publica, saude, multi_setor, outros
     • 11 Práticas: desenvolvimento_solucoes, dados_ia_rpa, hiperautomacao,
       ciberseguranca, consultoria_td, infraestrutura_cloud_redes, bpo,
       workspace_digital, outsourcing_multitorres, multi_praticas, outros
     • 12 Categorias de Acervo: A, B, C, D, I, M, O, P, PT, S, T, Z
   → USE ESTES VALORES EXATOS ao classificar oportunidades ou documentos.

3. Materiais_DS/catalog.json
   → Índice programático dos 195 documentos do acervo.
   → Cada entry: id, titulo, categoria, mercado, praticas, caminho_local,
     local_disponivel, relevancia por agente (A1/A2/A3).

═══════════════════════════════════════
 ACERVO INTELECTUAL (12 categorias A→Z)
 Cada pasta tem README.md + _index.json
═══════════════════════════════════════

  Z_Normativo/                    → 1 doc  ✅ OBRIGATÓRIO — "Instrução Geral de Ofertas"
                                    SEMPRE injete este doc no contexto (ACV-Z-001)

  A_Atestados/                    → 49 docs  | Prova legal (100% E&U)
  B_Cases/                        → 23 docs  | Narrativa comercial (multi-setor)
  C_Capacidades_Portfolio/        → 39 docs  | Portfólio Minsait (✅ MAIOR, 8 subpastas)
  D_Defesas_Tecnicas/             → 5 docs   | Pós-shortlist (100% Telco)
  I_Institucional/                → 8 docs   | Visão corporativa
  M_Metodologias/                 → 3 docs   | Como a Minsait entrega
  O_Outros/                       → 4 docs   | Material complementar
  P_Planejamento_OpTech/          → 9 docs   | Prioridades 2026
  PT_Propostas_Tecnicas/          → 15 docs  | Benchmark escopo/preço (100% Telco)
  S_Solucoes_Verticais/           → 28 docs  | Catálogo Onesait E&U/Phygital
  T_Templates_Proposta/           → 11 docs  | Modelos proposta (100% Ciber)

═══════════════════════════════════════
 OFERTAS ATIVAS — 1.687 ARQUIVOS
 Pasta: _ofertas_ativas/
 Metadata: _meta/classificacao_ofertas_completa.json
═══════════════════════════════════════

Material de PRODUÇÃO REAL com propostas técnicas, pricing, dimensionamentos,
CVs, defesas técnicas e handover de 8 clientes. Classificado por prática:

POR CLIENTE:
  Volkswagen    | I&C / Automotivo    | 5 ofertas, 663 arq | SGE, DES
  Motiva        | E&U / Energia       | 1 oferta,  348 arq | Multi-Torres (SAP+Dados+GU)
  Transpetro    | E&U / Oil & Gas     | 6 ofertas, 217 arq | Dados, GU, SGE, DIC
  Caixa         | Cross / Serv.Financ | 4 ofertas, 158 arq | SGE, DES
  CPFL          | E&U / Energia       | 13 ofertas,131 arq | DES, Dados, SGE
  Santander     | Cross / Serv.Financ | 7 ofertas, 125 arq | DES (pacotes body shop)
  Porto_Seguro  | Cross / Seguros     | 5 ofertas,  37 arq | SGE, Multi
  Qualicorp     | Saúde               | 1 oferta,    8 arq | DES

POR PRÁTICA (nas ofertas):
  SGE/SAP                    → 11 ofertas, 740 arquivos ✅ MAIOR
  Desenvolvimento de Soluções → 18 ofertas, 309 arquivos
  Multi-Práticas/Torres       → 4 ofertas,  460 arquivos
  Dados/IA/RPA               → 6 ofertas,   94 arquivos
  Infraestrutura/Cloud        → 2 ofertas,   68 arquivos
  WorkSpace Digital           → 1 oferta,    16 arquivos

USO: Benchmark de escopo, estrutura, preço e abordagem para novas oportunidades.
Filtrar por prática/mercado usando classificacao_ofertas_completa.json.

═══════════════════════════════════════
 RFPs RESPONDIDAS — 81 ARQUIVOS
 Pasta: _modelos_rfp_respondidas/
 Metadata: _meta/classificacao_rfps_respondidas.json
═══════════════════════════════════════

Respostas COMPLETAS a RFPs anteriores. Altamente relevante para A2 e A3:

  Oferta_Axia_BIM           | I&C   | DES     | 44 arquivos
  Oferta_Petrobras_Liferay  | E&U   | DES     | 28 arquivos
  Oferta_AAA_Fixa           | Telco | DES     |  3 arquivos
  Oferta_Vivo_Ecommerce     | Telco | DES     |  3 arquivos
  Oferta_Open_GTW           | Telco | DIC     |  1 arquivo
  Oferta_Tim_Hub_INT        | Telco | Dados   |  1 arquivo
  Oferta_Vivo_VTC           | Telco | DES     |  1 arquivo

USO: Extrair estrutura de resposta, volumetria, pricing approach, equipe proposta.

═══════════════════════════════════════
 MATERIAL OPERACIONAL — 178 ARQUIVOS
 Pasta: _operacional/
═══════════════════════════════════════

  atestados_fisicos/  → 154 arq | PDFs scan atestados | Uso: A1 evidência
  certificados/       →   7 arq | ISO, CMMI, etc.     | Uso: A1/A2 qualificação
  rates/              →   3 arq | Tabelas preço/FTE   | Uso: A3 ✅ CRÍTICO
  emails_rfp/         →   7 arq | Convites originais  | Referência histórica
  juridico/           →   5 arq | NDAs, contratos     | Uso: A2 contratual
  painel/             →   2 arq | Dashboards internos | Gestão

═══════════════════════════════════════
 CASES HORIZONTAIS — 7 ARQUIVOS
 Pasta: _cases_horizontais/
═══════════════════════════════════════

Cases cross-mercado 2025 — ÚTEIS para expandir cobertura em setores fracos:
  Cases Energia & Utilities.pptx
  Cases Telco & Mídia.pptx
  Cases Indústria & Bens de Consumo.pptx
  Cases de Administração Pública.pptx
  Cases Serviços Financeiros.pptx
  Minsait - CASES - Fábrica de Software.pptx
  Minsait _Fabrica de Software eCommerce.pptx

═══════════════════════════════════════
 MDC — MODELOS DE CUSTO: 313 ARQUIVOS
 ✅ CRÍTICO PARA AGENTE 3 (BALLPARK ROM)
═══════════════════════════════════════

Dentro das ofertas ativas e operacional existem 313 arquivos de pricing/custo:

POR TIPO:
  MDC (Modelo de Custo formal)        → 175 arquivos
  Price Table (Resource Units)         → 85 arquivos
  Dimensionamento (staffing/FTE)       → 34 arquivos
  Ratecard (tabela rate por perfil)    → 9 arquivos
  Calculadora/Pirâmide                 → 7 arquivos
  CBD (Cost Breakdown Detail)          → 3 arquivos

POR CLIENTE (= fonte de benchmark):
  Volkswagen    | I&C/Auto      | 123 arq (26 MDC, 68 Price Tables, 22 Dimens, 3 Rate, 3 CBD)
  Transpetro    | E&U/Oil&Gas   |  46 arq (27 MDC, 15 Price Tables, 4 Dimens)
  CPFL          | E&U/Energia   |  40 arq (38 MDC, 2 Dimens)
  Caixa         | Cross/Fin     |  39 arq (33 MDC, 4 Dimens, 1 Rate)
  Motiva        | E&U/Energia   |  31 arq (26 MDC, 3 Rate, 2 Dimens)
  Porto_Seguro  | Cross/Seguros |  24 arq (24 MDC)
  Santander     | Cross/Fin     |   6 arq (6 Pirâmides/Calculadoras)
  Qualicorp     | Saúde         |   3 arq (1 MDC, 2 Rate)

POR PRÁTICA:
  SGE + DES              → 162 arquivos
  Multi-Torres           → 77 arquivos
  DES + Dados + SGE      → 40 arquivos
  SGE (puro)             → 24 arquivos
  DES (puro)             → 9 arquivos

USO PELO AGENTE 3: Para qualquer ROM/Ballpark, consultar MDCs de cliente com
prática/mercado semelhante à oportunidade. Extrair: estrutura de custo, perfis,
volumes FTE, rates, margens, split onshore/offshore.

═══════════════════════════════════════
 REGRAS OBRIGATÓRIAS
═══════════════════════════════════════

1. SEMPRE injete Z_Normativo/ACV-Z-001 no contexto.
2. IDs estáveis ACV-{CAT}-{NNN} NUNCA mudam. CITE no output.
3. Pastas _ NÃO são indexadas no RAG por padrão.
   MAS: _ofertas_ativas/ e _modelos_rfp_respondidas/ DEVEM ser consultadas
   quando o agente precisa de benchmark de escopo, preço ou estrutura.
4. MDCs (313 arquivos) são CRÍTICOS para A3. Sempre consultar antes de estimar.
5. rates/ (_operacional/rates/) complementa os MDCs com tabelas de rate atuais.
6. Em setores com <10 docs acervo, ALERTAR o usuário no relatório.

═══════════════════════════════════════
 PRIORIDADE POR AGENTE
═══════════════════════════════════════

Agente 1 — Qualificação:
  🔴 Crítico: Z (normativo)
  🟢 Alto:    A (atestados), B (cases), C (capacidades), P (planejamento), S (soluções)
  🟡 Médio:   D (defesas), I (institucional), PT (propostas)
  ⚪ Baixo:   M, O, T
  🔴 Benchmark: _ofertas_ativas/ (filtrar por prática da oportunidade)

Agente 2 — Kickoff S2S:
  🔴 Crítico: Z
  🟢 Alto:    B, C, D, I, PT, S
  🟡 Médio:   A, M, T
  ⚪ Baixo:   O, P
  🔴 Benchmark: _modelos_rfp_respondidas/ (estrutura de resposta)

Agente 3 — Ballpark ROM:
  🔴 Crítico: Z + _operacional/rates/ (tabelas de preço)
  🟢 Alto:    B, P, PT, S
  🟡 Médio:   C, D, M, T
  ⚪ Baixo:   A, I, O
  🔴 Benchmark: _ofertas_ativas/ (dimensionamentos) + _modelos_rfp_respondidas/ (pricing)

═══════════════════════════════════════
 FILTRO POR SETOR DA OPORTUNIDADE
═══════════════════════════════════════

Se Energia & Utilities → priorizar: A, S, B + _ofertas_ativas/{CPFL,Motiva,Transpetro}
Se Telco              → priorizar: PT, D, B + _modelos_rfp_respondidas/{Vivo,AAA,Tim}
Se Serv.Financeiros   → priorizar: C, B + _ofertas_ativas/{Santander,Caixa}
Se Automotivo/I&C     → priorizar: C, B + _ofertas_ativas/{Volkswagen}
Se Saúde              → priorizar: C, B + _ofertas_ativas/{Qualicorp}
Se Seguros            → priorizar: C, B + _ofertas_ativas/{Porto_Seguro}
Demais setores        → priorizar: C, B, P, I + _cases_horizontais/

═══════════════════════════════════════
 COBERTURA POR SETOR (para calibrar confiança)
═══════════════════════════════════════

🟢 Alta:    Energia & Utilities (89 acervo + 696 ofertas)
🟢 Alta:    Telco (30 acervo + 5 RFPs respondidas)
🟢 Alta:    Indústria & Consumo (5 acervo + 663 ofertas VW + 44 RFP Axia)
🟢 Alta:    Serviços Financeiros (0 acervo + 283 ofertas Santander/Caixa)
🟡 Média:   Cibersegurança (14 acervo), Dados/IA (12), DES (8), WorkSpace (7)
🔴 Baixa:   BPO (4), Hiperautomação (5), Seguros (37 ofertas Porto Seguro)
🔴 Crítica: SGE (1 acervo, mas 740 ofertas!), AAPP & Saúde (1+8)
```

## ••• FIM DO PROMPT — COPIAR ATÉ AQUI •••

---

## Variante Compacta (para contextos com limite de tokens)

### ••• INÍCIO VERSÃO COMPACTA •••

```
Base de conhecimento: Materiais_DS/ (Indra Minsait Brasil)
TOTAL: 2.047 arquivos classificados (195 acervo + 1.687 ofertas + 81 RFPs + 178 operacional)

CARREGAR SEMPRE:
  - Materiais_DS/README.md (estrutura completa)
  - Materiais_DS/taxonomy.json (8 mercados, 11 práticas)
  - Materiais_DS/catalog.json (195 docs com IDs ACV-*)

MANDATÓRIO: Injetar Z_Normativo/ACV-Z-001 em TODA execução.

ACERVO (12 cat): A(atestados) B(cases) C(capacidades) D(defesas) I(institucional)
M(metodologias) O(outros) P(planejamento) PT(propostas) S(soluções) T(templates) Z(normativo)

OFERTAS ATIVAS (1.687 arq, 42 projetos, 8 clientes):
VW(663/SGE+DES) Motiva(348/Multi) Transpetro(217/multi) Caixa(158/SGE+DES)
CPFL(131/DES+Dados+SGE) Santander(125/DES) Porto_Seguro(37/SGE) Qualicorp(8/DES)
→ Metadata: _meta/classificacao_ofertas_completa.json

RFPs RESPONDIDAS (81 arq, 7 ofertas): Axia BIM(44), Petrobras Liferay(28), + 5 Telco

CITAR IDs ACV-* consultados. ALERTAR se setor tem <10 docs acervo.
rates/ → CRÍTICO para A3. Pastas _ = não indexar por padrão MAS consultar sob demanda.
```

### ••• FIM VERSÃO COMPACTA •••

---

## Notas de uso

| Cenário | Qual usar |
|---------|-----------|
| **System prompt** com contexto amplo (>8K tokens) | Versão completa |
| **System prompt** com limite de tokens | Versão compacta |
| **Referência em outro documento** (skill, requerimento) | `Materiais_DS/README.md` |
| **Dashboard visual interativo** | `_meta/reorganizacao_materiais_ds.html` |

> **Indra Minsait** — Transformação Digital Brasil | Confidencial — Uso Interno
