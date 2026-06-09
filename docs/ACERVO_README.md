# Materiais_DS — Base de Conhecimento para Agentes de IA

> **Projeto:** BPO Agentificação — Indra Minsait Brasil
> **Versão:** 2.0 — 08/06/2026 (pós-reorganização)
> **Solução aplicada:** Solução 3 — Híbrida (Categorias Semânticas + Catálogo JSON)
> **Maintainers:** Filipe Barreira, Manoel Benicio
> **Confidencialidade:** Uso interno Indra Minsait — Não distribuir externamente

---

## 0. Instrução rápida para agentes de IA

```
1. Carregue ESTE ARQUIVO (README.md) para entender a estrutura completa.
2. Carregue taxonomy.json para classificação (Mercado, Prática, Categoria).
3. Consulte catalog.json para buscar documentos por ID (ACV-*), título, setor ou práticas.
4. Cada pasta de categoria (A→Z) tem um _index.json com instruções específicas.
5. IGNORE pastas com prefixo _ (não fazem parte do acervo indexável).
6. O documento Z_Normativo/ é OBRIGATÓRIO — sempre injete no contexto.
```

---

## 1. Visão geral

Este diretório contém o **Acervo Intelectual** da Indra Minsait Brasil, organizado para consumo programático por **3 agentes de IA** e navegação humana.

| Dimensão | Valor |
|----------|-------|
| **Documentos catalogados** | 195 (IDs estáveis `ACV-{CAT}-{NNN}`) |
| **Documentos locais** | 51 (presentes no filesystem) |
| **Documentos SharePoint** | 144 (referenciados no catalog.json) |
| **Categorias de acervo** | 12 (A, B, C, D, I, M, O, P, PT, S, T, Z) |
| **Pastas auxiliares** | 6 (prefixo `_`, excluídas do RAG) |
| **Arquivos de controle** | 3 (README.md, catalog.json, taxonomy.json) |
| **Mercados (DNs)** | 8 (definidos em taxonomy.json) |
| **Práticas** | 11 (definidas em taxonomy.json) |
| **Agentes consumidores** | A1 (Qualificação), A2 (Kickoff S2S), A3 (Ballpark ROM) |

---

## 2. Árvore completa de diretórios

```
Materiais_DS/                                     ← VOCÊ ESTÁ AQUI
│
├── README.md                                     ← ESTE ARQUIVO (entry point)
├── catalog.json                                  ← Índice programático dos 195 docs
├── taxonomy.json                                 ← Definições canônicas (Mercado/Prática/Categoria)
│
│   ════════════════════════════════════════════
│   ACERVO INTELECTUAL — 12 categorias (A→Z)
│   Cada pasta tem: README.md + _index.json
│   ════════════════════════════════════════════
│
├── A_Atestados/                                  ← 49 docs | 100% SharePoint | 100% E&U
│   └── energia_e_utilities/                      ← subpastas por cliente (CEEE, CEMIG, EDP, ENEL, ...)
│
├── B_Cases/                                      ← 23 docs | 4 local + 19 SharePoint
│   ├── dados_ia_rpa/                             ← cases de Dados/IA/RPA
│   ├── energia_e_utilities/                      ← cases de E&U
│   ├── hiperautomacao/                           ← cases de Hiperautomação
│   ├── industria_e_consumo/                      ← cases de I&C
│   └── telco/                                    ← cases de Telco
│
├── C_Capacidades_Portfolio/                      ← 39 docs | 33 local + 6 SharePoint ★ MAIOR
│   ├── bpo/                                      ← 3 docs (portfólio BPO, storytelling, governança)
│   ├── ciberseguranca/                           ← 3 docs (catálogo full, deck Brasil, visão global)
│   ├── dados_ia_rpa/                             ← 8 docs (propostas IA, defesa técnica, Aegea, Petrobras)
│   ├── desenvolvimento_solucoes/                 ← 8 docs (Phygital, QA, WebPortals, Outsystems, Appian, Power Platform)
│   ├── hiperautomacao/                           ← 3 docs (Accor RPA, Lactalis RPA&IA, Motiva RPA)
│   ├── infraestrutura_cloud/                     ← 6 docs (Cloud Computing, Data Center, SmartITO, Observabilidade)
│   ├── sge/                                      ← 1 doc (SGE geral)
│   └── workspace_digital/                        ← 7 docs (Salas Reunião, Gestão Ativos, IT Corner, Smart Locker, DEX)
│
├── D_Defesas_Tecnicas/                           ← 5 docs | 100% SharePoint | 100% Telco
│   └── telco/                                    ← defesas pós-shortlist (RCA IA, CDR-Gateway, LIRG, VTC)
│
├── I_Institucional/                              ← 8 docs | 100% SharePoint
│                                                    (IndraGroup, Organização Brasil, Account Planning)
│
├── M_Metodologias/                               ← 3 docs | 100% local
│   ├── bpo/                                      ← Metodologia de Atuação e Governança
│   ├── dados_ia_rpa/                             ← Metodologias Dados
│   └── hiperautomacao/                           ← METODOLOGIA_RPA_IA_Agentes
│
├── O_Outros/                                     ← 4 docs | 100% SharePoint
│                                                    (material complementar não categorizado)
│
├── P_Planejamento_OpTech/                        ← 9 docs | 100% SharePoint
│   ├── mercados/                                 ← OpTech por mercado (AAPP&Saúde, E&U)
│   ├── praticas/                                 ← OpTech por prática (BPO, Ciber, DIC, GU)
│   └── hyperscalers/                             ← Business Partnership (Microsoft)
│
├── PT_Propostas_Tecnicas/                        ← 15 docs | 100% SharePoint | 100% Telco
│   └── telco/                                    ← propostas técnicas históricas (SBC, AAA, CDR, LIRG, VTC, ...)
│
├── S_Solucoes_Verticais/                         ← 28 docs | 100% SharePoint | 100% E&U
│   ├── phygital_utilities/                       ← Phygital Utilities (Facilities, Onesait Grid, Platform)
│   ├── asset_management/                         ← EAM, SEC, Mobile, Asset Health
│   ├── iot_edge/                                 ← IoT & Edge Computing
│   ├── sustentabilidade/                         ← Prosumers, Oblysis, Saneamento
│   ├── geo_gis/                                  ← GIS, SEC & GIS Mobile, Geoespacial
│   ├── intelligence/                             ← Onesait Intelligence, Utility Intelligence
│   ├── otimizacao/                               ← Monitorização da Distribuição, Otimizador de Rotas
│   ├── cloud_native_eu/                          ← iQoS Cloud, Modernização IQOS
│   └── inovacao_aerea/                           ← Inspeção com Drones
│
├── T_Templates_Proposta/                         ← 11 docs | 100% local | 100% Ciber
│   └── ciberseguranca/
│       ├── mss_it_ot/                            ← 2 templates (Neoenergia, Minsait genérico)
│       ├── simoc/                                ← 3 templates (SIMOC Treinamento, Proposta Técnica, GCC)
│       ├── soc_mss/                              ← 2 templates (VLI SOC&MSS, Konica Minolta)
│       └── pentest/                              ← 4 templates (GWM, IBM, Braspine, Minsait genérico)
│
├── Z_Normativo/                                  ← 1 doc | ★ CRÍTICO
│                                                    ACV-Z-001: "Instrução Geral - Ofertas"
│                                                    "Constituição" do processo de ofertas Indra
│                                                    MANDATÓRIO para TODOS os agentes (🔴 A1, 🔴 A2, 🔴 A3)
│
│   ════════════════════════════════════════════
│   PASTAS AUXILIARES — prefixo _ = NÃO INDEXAR
│   Excluídas do RAG por padrão
│   ════════════════════════════════════════════
│
├── _ofertas_ativas/                              ← 1.686 arquivos · 8 clientes
│   ├── Caixa/
│   ├── CPFL/
│   ├── Motiva/
│   ├── Porto_Seguro/
│   ├── Qualicorp/
│   ├── Santander/
│   ├── Transpetro/
│   └── Volkswagen/
│
├── _operacional/                                 ← 178 arquivos · 6 subpastas
│   ├── atestados_fisicos/                        ← PDFs originais de atestados
│   ├── certificados/                             ← Certificações da empresa
│   ├── emails_rfp/                               ← Emails de convites RFP
│   ├── juridico/                                 ← Documentação jurídica
│   ├── painel/                                   ← Painéis e dashboards internos
│   └── rates/                                    ← Tabelas de rates/preços
│
├── _cases_horizontais/                           ← 7 arquivos PPTX
│                                                    Cases cross-mercado 2025 (não categorizáveis)
│
├── _modelos_rfp_respondidas/                     ← 81 arquivos · 7 ofertas
│   ├── Oferta_AAA_Fixa/
│   ├── Oferta_Axia_BIM/
│   ├── Oferta_Open_GTW/
│   ├── Oferta_Petrobras_Liferay/
│   ├── Oferta_Tim_Hub_INT/
│   ├── Oferta_Vivo_Ecommerce/
│   └── Oferta_Vivo_VTC/
│
├── _meta/                                        ← Meta-documentação
│   ├── requerimentos/                            ← 8 documentos de engenharia (00→07)
│   │   ├── 00_VISAO_GERAL.md
│   │   ├── 01_AGENTE_1_QUALIFICACAO.md
│   │   ├── 02_AGENTE_2_KICKOFF_S2S.md
│   │   ├── 03_AGENTE_3_BALLPARK_ROM.md
│   │   ├── 04_MAPEAMENTO_KB_ACERVO.md
│   │   ├── 05_PATHS_E_FONTES_DE_DADOS.md        ← Contrato de paths (v2.0)
│   │   ├── 06_ARQUITETURA_REFERENCIA.md
│   │   └── 07_AGENTE_1_QUALIFICACAO_DS.md
│   ├── agente_draft/                             ← Rascunhos de definição de agentes
│   ├── skills_draft/                             ← Rascunhos de skills
│   ├── output_detalhado/                         ← Outputs gerados por agentes
│   └── reorganizacao_materiais_ds.html           ← Dashboard visual da reorganização
│
└── _archive/                                     ← ~5GB (material depreciado)
    ├── OneDrive.zip
    └── Volkswagen.zip
```

---

## 3. Arquivos de controle (fonte de verdade)

### 3.1 `catalog.json` — Índice programático

Contém os metadados de todos os 195 documentos catalogados. Estrutura de cada entry:

```json
{
  "id": "ACV-C-015",
  "categoria": "C",
  "titulo": "Phygital - 2024",
  "tipo": "pptx",
  "mercado": "Desenvolvimento de soluções",
  "praticas": ["desenvolvimento_solucoes"],
  "caminho_acervo": "2.Praticas DNs/Pratica DN Desv. Sol/Phygital - 2024.pptx",
  "caminho_local": "C_Capacidades_Portfolio/desenvolvimento_solucoes/Phygital - 2024.pptx",
  "local_disponivel": true,
  "owner": "Filipe Barreira",
  "relevancia": { "A1": "🟢", "A2": "🟡", "A3": "🟡" },
  "tags": ["phygital", "IoT", "desenvolvimento"]
}
```

**Campos-chave:**
| Campo | Descrição |
|-------|-----------|
| `id` | ID estável `ACV-{CAT}-{NNN}` — NUNCA muda |
| `categoria` | Código da categoria (A, B, C, ..., Z) |
| `caminho_acervo` | Path original no SharePoint (imutável) |
| `caminho_local` | Path no filesystem local `Materiais_DS/` (pós-reorganização) |
| `local_disponivel` | `true` se o arquivo está fisicamente no filesystem local |
| `relevancia` | Prioridade por agente: 🔴 Crítico · 🟢 Alto · 🟡 Médio · ⚪ Baixo |

### 3.2 `taxonomy.json` — Definições canônicas

Contém os valores oficiais de classificação. **Usar estes valores — e somente estes — ao classificar documentos ou oportunidades.**

#### Mercados (8 DNs)

| Slug (chave JSON) | Código DN | Label | Descrição |
|-------------------|:---------:|-------|-----------|
| `energia_e_utilities` | E&U | Energia e Utilities | Distribuidoras, geradoras, utilities, oil & gas |
| `telco` | T&M | Telco | Operadoras, ISPs, broadcasters |
| `industria_e_consumo` | I&C | Indústria e Consumo | Manufatura, varejo, travel |
| `sge` | SAP | SGE | ERP, CRM, plataformas enterprise |
| `administracao_publica` | AAPP | Administração Pública | Gov federal, estadual, municipal |
| `saude` | Sanidad | Saúde | Hospitais, operadoras de saúde, healthtech |
| `multi_setor` | Cross | Multi-setor | Oportunidades cross-DN |
| `outros` | — | Outros | Não categorizados |

#### Práticas (11)

| Slug (chave JSON) | Código | Label | Descrição |
|-------------------|:------:|-------|-----------|
| `desenvolvimento_solucoes` | DES | Desenvolvimento de Soluções | Fábricas de software, low-code, portais, QA |
| `dados_ia_rpa` | Dados | Dados/IA/RPA | Analytics, BI, ML, RPA, agentes IA |
| `hiperautomacao` | Hiper | Hiperautomação | RPA avançado, process mining |
| `ciberseguranca` | Ciber | Cibersegurança | SOC, MSS, pentest, SIMOC |
| `consultoria_td` | CTD | Consultoria & Transformação Digital | Roadmaps, estratégia |
| `infraestrutura_cloud_redes` | DIC | Infraestrutura/Cloud/Redes | ITO, cloud, FinOps, data center |
| `bpo` | BPO | BPO | Business process outsourcing, service desk |
| `workspace_digital` | GU | WorkSpace / Digital Workplace | Gestão de ativos, smart workplace, DEX |
| `outsourcing_multitorres` | EMB | Outsourcing Multi-torres | Múltiplas torres integradas |
| `multi_praticas` | Multi | Multi-Práticas | Combinação em uma mesma oportunidade |
| `outros` | — | Outros | Não categorizadas |

### 3.3 `_index.json` — Por pasta de categoria

Cada pasta de categoria contém um `_index.json` com metadata local:

```json
{
  "categoria": "C",
  "nome": "Capacidades por Prática (Portfólio)",
  "total_docs": 39,
  "mercados_cobertos": ["bpo", "ciberseguranca", "dados_ia_rpa", "..."],
  "praticas_cobertas": ["bpo", "ciberseguranca", "dados_ia_rpa", "..."],
  "instrucao_agente": "Use estes documentos para avaliar aderência ao portfólio Minsait."
}
```

---

## 4. Uso por agente

### 4.1 Agente 1 — Qualificação de Oportunidade

| Prioridade | Categorias | O que buscar |
|:----------:|:----------:|--------------|
| 🔴 Crítico | Z | Instrução Geral de Ofertas — sempre injetar |
| 🟢 Alto | A, B, C, P, S | Atestados, cases, capacidades, planejamento, soluções |
| 🟡 Médio | D, I, PT | Defesas, institucional, propostas técnicas |
| ⚪ Baixo | M, O, T | Metodologias, outros, templates |

**Filtro por setor:**
- Se oportunidade é **E&U**: priorizar A, S, B (filtro setor `energia_e_utilities`)
- Se oportunidade é **Telco**: priorizar PT, D, B (filtro setor `telco`)
- Demais setores: priorizar C, B, P, I

### 4.2 Agente 2 — Kickoff S2S

| Prioridade | Categorias | O que buscar |
|:----------:|:----------:|--------------|
| 🔴 Crítico | Z | Instrução Geral de Ofertas |
| 🟢 Alto | B, C, D, I, PT, S | Cases, capacidades, defesas, institucional, propostas, soluções |
| 🟡 Médio | A, M, T | Atestados, metodologias, templates |
| ⚪ Baixo | O, P | Outros, planejamento |

### 4.3 Agente 3 — Ballpark ROM

| Prioridade | Categorias | O que buscar |
|:----------:|:----------:|--------------|
| 🔴 Crítico | Z | Instrução Geral de Ofertas |
| 🟢 Alto | B, P, PT, S | Cases, planejamento, propostas técnicas (benchmark de preço), soluções |
| 🟡 Médio | C, D, M, T | Capacidades, defesas, metodologias, templates |
| ⚪ Baixo | A, I, O | Atestados, institucional, outros |

---

## 5. Cobertura por setor

| Setor | Docs | Cobertura | Comportamento esperado do agente |
|-------|:----:|:---------:|----------------------------------|
| Energia & Utilities | 89 | 🟢 Alta | Análise rica — maior base de conhecimento |
| Telco | 30 | 🟢 Alta | Análise rica — forte em propostas técnicas |
| Cibersegurança | 14 | 🟡 Média | Sólida — foco em templates e SOC/MSS |
| Dados/IA/RPA | 12 | 🟡 Média | Sólida |
| Desenvolvimento de Soluções | 8 | 🟡 Média | Aceitável — offerings bem documentados |
| WorkSpace | 7 | 🟡 Média | Aceitável |
| ITO-CLOUD | 6 | 🟡 Média | Aceitável |
| Indústria e Consumo | 5 | 🔴 Baixa | **Alertar usuário** — poucas referências |
| Hiperautomação | 5 | 🔴 Baixa | **Alertar usuário** |
| BPO | 4 | 🔴 Baixa | **Alertar usuário** |
| SGE | 1 | 🔴 Crítica | **Alerta forte** — quase sem material |
| AAPP & Saúde | 1 | 🔴 Crítica | **Alerta forte** — quase sem material |

> Em setores de baixa cobertura, o agente deve incluir avisão explícito no relatório e considerar acionar cases globais do Indra Group (EMEA).

---

## 6. Convenções e regras de governança

### 6.1 Nomenclatura

| Elemento | Padrão | Exemplo |
|----------|--------|---------|
| **IDs de documento** | `ACV-{CAT}-{NNN}` | `ACV-C-015`, `ACV-Z-001` |
| **Pastas de categoria** | `{LETRA}_{Nome_Pascal}` | `C_Capacidades_Portfolio` |
| **Subpastas** | `snake_case` (sem acentos) | `dados_ia_rpa`, `energia_e_utilities` |
| **Pastas auxiliares** | Prefixo `_` | `_ofertas_ativas`, `_meta` |

### 6.2 IDs estáveis — regras de imutabilidade

- Um ID atribuído **NUNCA é reciclado** — removidos ficam `DEPRECATED`
- Se um doc muda de categoria → ID antigo vira `DEPRECATED` + novo ID na nova categoria
- Docs novos recebem o **próximo número disponível** — nunca preenchem buracos

### 6.3 Prefixo `_` = excluir do RAG

Pastas com underscore prefix **NÃO devem ser indexadas** no RAG por padrão:
- `_ofertas_ativas/` — ofertas comerciais em andamento (dados sensíveis por cliente)
- `_operacional/` — atestados físicos, certificados, jurídico, rates, emails
- `_cases_horizontais/` — cases cross-mercado (sem categorização semântica)
- `_modelos_rfp_respondidas/` — benchmark de respostas a RFP
- `_meta/` — requerimentos dos agentes, drafts, dashboards, este HTML
- `_archive/` — material compactado e depreciado (~5GB)

### 6.4 Política de mudança de paths

Qualquer alteração de path requer **ADR** (Architecture Decision Record):
- Template e fluxo completo em `_meta/requerimentos/05_PATHS_E_FONTES_DE_DADOS.md` §3
- Owners temporários: Filipe Barreira, Manoel Benicio
- Mudanças 🔴/🟢 disparam smoke test e re-indexação obrigatórios

---

## 7. FAQ para agentes

**P: Onde encontro o documento normativo obrigatório?**
R: `Z_Normativo/` — ID `ACV-Z-001`. Sempre injete no system prompt.

**P: Um doc está listado no catalog.json mas não existe localmente. O que fazer?**
R: Verifique o campo `local_disponivel`. Se `false`, o doc está apenas no SharePoint. Use o `caminho_acervo` para solicitar ao usuário.

**P: Como filtrar docs por setor/prática?**
R: Use os campos `mercado` e `praticas` no `catalog.json`. Os valores válidos estão em `taxonomy.json`.

**P: Posso usar material das pastas `_`?**
R: Apenas se o usuário solicitar explicitamente. Não indexe por padrão.

**P: Como sei a relevância de um doc para meu agente?**
R: Campo `relevancia` no `catalog.json`: `{ "A1": "🔴", "A2": "🟢", "A3": "🟡" }`.

---

## 8. Referências cruzadas

| Documento | Path | Função |
|-----------|------|--------|
| Contrato de paths (v2.0) | `_meta/requerimentos/05_PATHS_E_FONTES_DE_DADOS.md` | Governança + tabela mestre dos 195 docs |
| Mapeamento KB | `_meta/requerimentos/04_MAPEAMENTO_KB_ACERVO.md` | Análise detalhada do acervo |
| Visão geral | `_meta/requerimentos/00_VISAO_GERAL.md` | Contexto executivo do projeto |
| Agente 1 spec | `_meta/requerimentos/01_AGENTE_1_QUALIFICACAO.md` | Especificação do Agente de Qualificação |
| Agente 2 spec | `_meta/requerimentos/02_AGENTE_2_KICKOFF_S2S.md` | Especificação do Agente de Kickoff |
| Agente 3 spec | `_meta/requerimentos/03_AGENTE_3_BALLPARK_ROM.md` | Especificação do Agente Ballpark ROM |
| Dashboard visual | `_meta/reorganizacao_materiais_ds.html` | Visualização interativa da reorganização |

---

## 9. Histórico

| Versão | Data | Mudanças |
|--------|------|----------|
| 1.0 | 2026-06-08 | Versão inicial pós-reorganização. Estrutura básica. |
| 2.0 | 2026-06-08 | **Reescrita completa.** Documentação exaustiva de toda a estrutura de diretórios, subpastas, taxonomia completa (8 mercados, 11 práticas), uso detalhado por agente, cobertura por setor, convenções de governança, FAQ, referências cruzadas. |

---

> **Indra Minsait** — Transformação Digital Brasil | Confidencial — Uso Interno | Não distribuir externamente

---

## Dados Completos para Agentes

> **Total: 2.047 arquivos classificados** (195 acervo + 1.687 ofertas ativas + 81 RFPs + 178 operacional + 313 MDCs).
> Para o prompt completo com ofertas por cliente, MDCs por tipo e cobertura por setor:
> Carregue `PROMPT_CONTEXTO_AGENTES.md` (este diretório).
