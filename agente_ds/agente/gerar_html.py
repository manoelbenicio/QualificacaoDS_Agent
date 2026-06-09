"""
Gerador de Relatório HTML — Qualificação DS Minsait
Spec: 07_AGENTE_1_QUALIFICACAO_DS.md §4.1.2 — 10 seções DS
      transformaca-agente-ofertas-qualificacao-ds.md §3 — Identidade Visual
      transformaca-agente-ofertas-qualificacao-ds.md §4 — Template HTML
Produz HTML autocontido com design Indra Group.
"""
import json, os, html as html_mod
from datetime import datetime


def _esc(v):
    """Escape HTML."""
    if v is None:
        return 'N/A'
    return html_mod.escape(str(v))


def gerar_html(json_path: str) -> str:
    with open(json_path, 'r', encoding='utf-8') as f:
        d = json.load(f)

    parecer = d.get('parecer', {})
    oi = d.get('outputs_intermediarios', {})
    sa1 = oi.get('SA1_extracao', {})
    sa2 = oi.get('SA2_tecnico', {})
    sa3 = oi.get('SA3_riscos', {})
    sa4 = oi.get('SA4_comercial', {})
    kb = d.get('kb_match', {})

    # ── Dados gerais ──
    decisao = parecer.get('decisao', 'N/A')
    score = parecer.get('score_final', parecer.get('score_final_ponderado', 0))
    confianca = parecer.get('confianca_pct', 0)
    justificativa = parecer.get('justificativa_decisao', '')
    motor = parecer.get('motor', d.get('motor', 'N/A'))
    cenario = d.get('cenario', 'N/A')
    duracao = d.get('duracao_segundos', 0)
    trace_id = d.get('trace_id', 'N/A')
    alto_count = parecer.get('alto_count', sa4.get('alto_count', 0))

    # ── SA1 ──
    ad = sa1.get('analise_documento', {})
    cliente = _esc(sa1.get('cliente', 'N/A'))
    nome_opp = _esc(sa1.get('nome_oportunidade', 'N/A'))
    setor = _esc(sa1.get('setor_informado', 'N/A'))
    tipo = _esc(sa1.get('tipo_servico', 'N/A'))
    escopo = sa1.get('escopo', {})
    escopo_principal = _esc(escopo.get('principal', 'N/A'))
    total_pag = ad.get('total_paginas_estimado', ad.get('total_paginas', '?'))
    total_pal = ad.get('total_palavras', '?')
    docs_processados = sa1.get('documentos_processados', [])

    # ── SA2 ──
    techs = sa2.get('tecnologias_identificadas', [])
    tech_names = [t.get('nome', t) if isinstance(t, dict) else t for t in techs]
    complexidade = sa2.get('complexidade', 'N/A')
    aderencia = sa2.get('aderencia_ds', 0)
    dim = parecer.get('dimensionamento_final', sa2.get('dimensionamento', {}))
    perfis = dim.get('perfis_chave', [])
    gaps = sa2.get('gaps_tecnicos', [])
    cross_pratica = sa2.get('cross_pratica', [])
    oportunidades = sa2.get('oportunidades_diferenciacao', [])
    restricoes = sa2.get('restricoes', [])

    # ── SA3 ──
    top_riscos = parecer.get('riscos_consolidados', {}).get('top_riscos', sa3.get('top_riscos', []))
    total_riscos = sa3.get('total_riscos', parecer.get('riscos_consolidados', {}).get('total', 0))
    criticos = sa3.get('criticos', parecer.get('riscos_consolidados', {}).get('criticos', 0))
    medios = sa3.get('medios', 0)
    baixos = sa3.get('baixos', 0)
    risk_score = sa3.get('risk_score', parecer.get('riscos_consolidados', {}).get('risk_score', 0))
    mitigacoes = sa3.get('mitigacoes_chave', [])

    # ── SA4: 8 FARÓIS ──
    farois = parecer.get('farois_consolidados', sa4.get('farois', []))
    bsw = parecer.get('best_story_wins', sa4.get('best_story_wins', {}))
    score_ponderado = sa4.get('score_final_ponderado', score)

    # ── SA5 ──
    next_steps = parecer.get('next_steps', [])
    condicoes = parecer.get('condicoes_mitigacao', [])

    # Badge decisão
    if 'NO_GO' in str(decisao):
        badge_cls = 'badge-nogo'
        badge_label = 'NO-GO'
    elif 'CONDICIONADO' in str(decisao):
        badge_cls = 'badge-condicionado'
        badge_label = 'GO CONDICIONADO'
    else:
        badge_cls = 'badge-go'
        badge_label = 'GO'

    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')

    # ══════ Separar faróis em 2 grupos ══════
    farois_cliente = [f for f in farois if f.get('grupo', '') == 'CRITÉRIOS DO CLIENTE']
    farois_minsait = [f for f in farois if f.get('grupo', '') == 'CRITÉRIOS MINSAIT']
    # Fallback: se não tiver grupo, dividir 4+4
    if not farois_cliente and len(farois) >= 8:
        farois_cliente = farois[:4]
        farois_minsait = farois[4:]

    def _badge_nivel(nivel):
        m = {
            'ALTO': ('badge-go', 'ALTO'),
            'MEDIO_ALTO': ('badge-medio-alto', 'MÉDIO-ALTO'),
            'MEDIO': ('badge-condicionado', 'MÉDIO'),
            'MEDIO_BAIXO': ('badge-medio-baixo', 'MÉDIO-BAIXO'),
            'BAIXO': ('badge-nogo', 'BAIXO'),
        }
        cls, lbl = m.get(nivel, ('badge-condicionado', nivel))
        return f'<span class="badge {cls}">{lbl}</span>'

    def _farol_card(f):
        s = f.get('score', 0)
        nome = _esc(f.get('nome', '?'))
        fid = f.get('id', '')
        nivel = f.get('nivel', 'MEDIO')
        just = _esc(f.get('justificativa', ''))
        desc = _esc(f.get('descricao', ''))
        bar_pct = int(s * 10)
        cor = f.get('cor', '#8661F5')
        return f'''
            <div class="farol-card">
                <div class="farol-header">
                    <span class="farol-id">{fid}</span>
                    <span class="farol-name">{nome}</span>
                    {_badge_nivel(nivel)}
                </div>
                <div class="farol-score-row">
                    <span class="farol-score">{s}/10</span>
                    <div class="farol-bar">
                        <div class="farol-bar-fill" style="width:{bar_pct}%;background:{cor}"></div>
                    </div>
                </div>
                <p class="farol-just">{just}</p>
            </div>'''

    farois_cliente_html = ''.join(_farol_card(f) for f in farois_cliente)
    farois_minsait_html = ''.join(_farol_card(f) for f in farois_minsait)

    # ── Documentos processados ──
    docs_rows = ''
    if docs_processados:
        for doc in docs_processados:
            if isinstance(doc, dict):
                docs_rows += f'<tr><td>{_esc(doc.get("nome", "?"))}</td><td>{_esc(doc.get("tipo", "?"))}</td><td>{_esc(doc.get("tamanho", "?"))}</td></tr>'
            else:
                docs_rows += f'<tr><td colspan="3">{_esc(doc)}</td></tr>'
    if not docs_rows:
        docs_rows = f'<tr><td colspan="3">Documento principal: {total_pag} páginas, {total_pal} palavras</td></tr>'

    # ── Tech badges ──
    techs_html = ''.join(f'<span class="tech-badge">{_esc(t)}</span>' for t in tech_names[:25])

    # ── Riscos ──
    riscos_html = ''
    for r in top_riscos:
        sev = r.get('severidade', 'MEDIO')
        badge_r = 'badge-nogo' if sev in ('ALTO', 'CRITICO') else ('badge-condicionado' if sev == 'MEDIO' else 'badge-go')
        riscos_html += f'''
            <div class="risk-item">
                <span class="badge {badge_r}">{_esc(sev)}</span>
                <div class="risk-content">
                    <strong>{_esc(r.get("nome", "?"))}</strong>
                    <p><strong>Mitigação:</strong> {_esc(r.get("mitigacao", "N/A"))}</p>
                </div>
            </div>'''

    # ── BSW ──
    bsw_html = ''
    for key, label, sub in [
        ('por_que_mudar', 'POR QUE MUDAR?', 'Qual dor justifica investir em desenvolvimento?'),
        ('por_que_agora', 'POR QUE AGORA?', 'O que abriu a janela de oportunidade?'),
        ('por_que_minsait', 'POR QUE MINSAIT?', 'Qual nosso diferencial único para DS?'),
        ('por_que_confiar', 'POR QUE CONFIAR?', 'Como provamos que entregamos?'),
    ]:
        val = bsw.get(key, '')
        if val:
            bsw_html += f'''
                <div class="bsw-card">
                    <div class="bsw-number">PERGUNTA {["1","2","3","4"][["por_que_mudar","por_que_agora","por_que_minsait","por_que_confiar"].index(key)]}</div>
                    <div class="bsw-question">{label}</div>
                    <div class="bsw-sub">{sub}</div>
                    <div class="bsw-answer">{_esc(val)}</div>
                </div>'''

    # ── Oportunidades ──
    oport_html = ''
    if oportunidades:
        for o in oportunidades:
            if isinstance(o, dict):
                oport_html += f'<div class="auto-item"><h4>{_esc(o.get("nome", "?"))}</h4><p>{_esc(o.get("descricao", ""))}</p></div>'
            else:
                oport_html += f'<div class="auto-item"><p>{_esc(o)}</p></div>'
    else:
        oport_html = '<p>IA assistida no desenvolvimento, CI/CD avançado, testes automatizados, Design System, DevSecOps — avaliar aplicabilidade.</p>'

    # ── Restrições ──
    restr_html = ''
    if restricoes:
        for r in restricoes:
            if isinstance(r, dict):
                restr_html += f'<div class="auto-item"><h4>{_esc(r.get("nome", "?"))}</h4><p>{_esc(r.get("descricao", ""))}</p></div>'
            else:
                restr_html += f'<div class="auto-item"><p>{_esc(r)}</p></div>'
    else:
        restr_html = '<p>Verificar: exigências de stack específico, presencialidade, PI, certificações obrigatórias.</p>'

    # ── Condições GO CONDICIONADO ──
    cond_html = ''
    if condicoes:
        for i, c in enumerate(condicoes, 1):
            if isinstance(c, dict):
                cond_html += f'<tr><td>{i}</td><td>{_esc(c.get("condicao", "?"))}</td><td>{c.get("prazo_dias", 14)} dias</td><td>{_esc(c.get("responsavel", "N/A"))}</td></tr>'
            else:
                cond_html += f'<tr><td>{i}</td><td colspan="3">{_esc(c)}</td></tr>'

    # ── Next Steps ──
    ns_html = ''.join(f'<li>{_esc(s)}</li>' for s in next_steps)

    # ── KB ──
    kb_docs = kb.get('total_docs', kb.get('total_docs_analisados', 0))
    kb_rel = kb.get('relevantes', kb.get('docs_relevantes', 0))
    kb_cob = kb.get('cobertura', kb.get('cobertura_score', 0))

    # ══════════════════════════════════════════════════════════════════
    # HTML COMPLETO — 10 SEÇÕES CONFORME SPEC §4.1.2
    # ══════════════════════════════════════════════════════════════════

    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qualificação de Oferta DS | {nome_opp} — {cliente} | Indra Group</title>
    <style>
        :root {{
            --azul-oscuro: #002532;
            --gris-ceramica: #E3E2DA;
            --azul-amazonico: #004254;
            --gris-acero: #AAAA9F;
            --branco: #FFFFFF;
            --gris-acero-oscuro: #646459;
            --verde-go: #44B757;
            --verde-claro: #A9E8A7;
            --verde-escuro: #0A382A;
            --laranja-risco: #E56813;
            --laranja-claro: #FFA96E;
            --laranja-escuro: #84270B;
            --roxo-metrica: #8661F5;
            --roxo-claro: #C0B3F8;
            --roxo-escuro: #0F0F6B;
            --gris-2: #BCBBB5;
            --gris-4: #74746D;
            --gris-5: #565652;
            --azul-tech: #1A73E8;
            --azul-tech-bg: #E8F0FE;
            --font-primary: 'ForFuture Sans', Arial, Helvetica, sans-serif;
            --font-code: 'Fira Code', 'JetBrains Mono', monospace;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: var(--font-primary); background: var(--gris-ceramica); color: var(--gris-acero-oscuro); line-height: 1.25; }}
        html {{ scroll-behavior: smooth; }}

        /* Sidebar */
        .sidebar {{
            position: fixed; left: 0; top: 0; width: 280px; height: 100vh;
            background: var(--azul-oscuro); padding: 30px 20px; overflow-y: auto; z-index: 100;
        }}
        .sidebar .logo {{ color: var(--branco); font-size: 18px; font-weight: 400; margin-bottom: 10px; }}
        .sidebar .practice-badge {{
            display: inline-block; background: var(--azul-tech); color: var(--branco);
            padding: 3px 10px; font-size: 10px; font-weight: 700; text-transform: uppercase;
            letter-spacing: 0.08em; margin-bottom: 16px;
            clip-path: polygon(4px 0, calc(100% - 4px) 0, 100% 4px, 100% calc(100% - 4px), calc(100% - 4px) 100%, 4px 100%, 0 calc(100% - 4px), 0 4px);
        }}
        .sidebar .subtitle {{
            color: var(--gris-acero); font-size: 11px; font-weight: 700;
            text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 30px;
        }}
        .sidebar nav a {{
            display: block; color: var(--gris-acero); text-decoration: none;
            padding: 10px 15px; margin-bottom: 4px; font-size: 13px; transition: all 0.2s;
            clip-path: polygon(6px 0, calc(100% - 6px) 0, 100% 6px, 100% calc(100% - 6px), calc(100% - 6px) 100%, 6px 100%, 0 calc(100% - 6px), 0 6px);
        }}
        .sidebar nav a:hover, .sidebar nav a.active {{ background: var(--azul-amazonico); color: var(--branco); }}

        /* Main */
        .main-content {{ margin-left: 280px; padding: 40px; }}

        /* Sections — clip-path 45° */
        .section {{
            background: var(--branco); padding: 40px; margin-bottom: 30px;
            clip-path: polygon(12px 0, calc(100% - 12px) 0, 100% 12px, 100% calc(100% - 12px), calc(100% - 12px) 100%, 12px 100%, 0 calc(100% - 12px), 0 12px);
        }}
        .section-title {{ color: var(--azul-amazonico); font-size: 28px; font-weight: 400; line-height: 1.0; margin-bottom: 20px; }}
        .section-subtitle {{ color: var(--azul-amazonico); font-size: 20px; font-weight: 400; margin-top: 24px; margin-bottom: 12px; }}

        /* Cards — clip-path 45° */
        .card {{
            background: var(--gris-ceramica); padding: 24px; margin-bottom: 16px;
            clip-path: polygon(10px 0, calc(100% - 10px) 0, 100% 10px, 100% calc(100% - 10px), calc(100% - 10px) 100%, 10px 100%, 0 calc(100% - 10px), 0 10px);
        }}
        .card-dark {{
            background: var(--azul-oscuro); color: var(--branco); padding: 24px; margin-bottom: 16px;
            clip-path: polygon(10px 0, calc(100% - 10px) 0, 100% 10px, 100% calc(100% - 10px), calc(100% - 10px) 100%, 10px 100%, 0 calc(100% - 10px), 0 10px);
        }}

        /* Badges */
        .badge {{
            display: inline-block; padding: 4px 12px; font-size: 11px; font-weight: 700;
            text-transform: uppercase; letter-spacing: 0.05em;
            clip-path: polygon(4px 0, calc(100% - 4px) 0, 100% 4px, 100% calc(100% - 4px), calc(100% - 4px) 100%, 4px 100%, 0 calc(100% - 4px), 0 4px);
        }}
        .badge-go {{ background: var(--verde-go); color: var(--branco); }}
        .badge-medio-alto {{ background: var(--verde-claro); color: var(--verde-escuro); }}
        .badge-condicionado {{ background: var(--roxo-metrica); color: var(--branco); }}
        .badge-medio-baixo {{ background: var(--laranja-claro); color: var(--laranja-escuro); }}
        .badge-nogo {{ background: var(--laranja-risco); color: var(--branco); }}

        /* Tables */
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
        th {{ background: var(--azul-oscuro); color: var(--branco); padding: 12px 16px; text-align: left; font-size: 12px; font-weight: 700; text-transform: uppercase; }}
        td {{ padding: 10px 16px; border-bottom: 1px solid var(--gris-2); font-size: 13px; }}
        tr:nth-child(even) {{ background: var(--gris-ceramica); }}

        /* Metrics */
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 20px 0; }}
        .metric-card {{
            background: var(--azul-oscuro); color: var(--branco); padding: 20px; text-align: center;
            clip-path: polygon(8px 0, calc(100% - 8px) 0, 100% 8px, 100% calc(100% - 8px), calc(100% - 8px) 100%, 8px 100%, 0 calc(100% - 8px), 0 8px);
        }}
        .metric-value {{ font-size: 28px; font-weight: 300; margin-bottom: 4px; }}
        .metric-label {{ font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--gris-acero); }}

        /* Tech badges */
        .tech-stack {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }}
        .tech-badge {{
            display: inline-flex; align-items: center; padding: 6px 14px; font-size: 12px;
            font-weight: 700; font-family: var(--font-code); background: var(--azul-tech-bg); color: var(--azul-tech);
            clip-path: polygon(4px 0, calc(100% - 4px) 0, 100% 4px, 100% calc(100% - 4px), calc(100% - 4px) 100%, 4px 100%, 0 calc(100% - 4px), 0 4px);
        }}

        /* Faróis — 2 colunas (Cliente × Minsait) */
        .farois-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
        .farois-col-title {{
            font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;
            color: var(--azul-amazonico); margin-bottom: 12px; padding-bottom: 8px;
            border-bottom: 2px solid var(--gris-2);
        }}
        .farol-card {{
            padding: 16px; margin-bottom: 12px; background: var(--gris-ceramica);
            clip-path: polygon(8px 0, calc(100% - 8px) 0, 100% 8px, 100% calc(100% - 8px), calc(100% - 8px) 100%, 8px 100%, 0 calc(100% - 8px), 0 8px);
        }}
        .farol-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }}
        .farol-id {{ font-size: 11px; font-weight: 700; color: var(--gris-4); }}
        .farol-name {{ font-size: 13px; font-weight: 700; text-transform: uppercase; color: var(--azul-amazonico); flex: 1; }}
        .farol-score-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }}
        .farol-score {{ font-size: 14px; font-weight: 700; color: var(--azul-amazonico); min-width: 40px; }}
        .farol-bar {{ flex: 1; height: 8px; background: rgba(0,0,0,0.15); }}
        .farol-bar-fill {{ height: 100%; transition: width 0.3s; }}
        .farol-just {{ font-size: 12px; line-height: 1.4; color: var(--gris-5); }}

        /* BSW */
        .bsw-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 20px 0; }}
        .bsw-card {{
            padding: 20px; background: var(--azul-oscuro); color: var(--branco);
            clip-path: polygon(10px 0, calc(100% - 10px) 0, 100% 10px, 100% calc(100% - 10px), calc(100% - 10px) 100%, 10px 100%, 0 calc(100% - 10px), 0 10px);
        }}
        .bsw-number {{ font-size: 11px; font-weight: 700; color: var(--gris-acero); text-transform: uppercase; margin-bottom: 4px; }}
        .bsw-question {{ font-size: 15px; font-weight: 400; margin-bottom: 4px; }}
        .bsw-sub {{ font-size: 11px; color: var(--gris-acero); font-style: italic; margin-bottom: 10px; }}
        .bsw-answer {{ font-size: 13px; line-height: 1.4; color: var(--gris-2); }}

        /* Risk */
        .risk-item {{
            display: flex; align-items: flex-start; gap: 12px; margin-bottom: 12px; padding: 12px;
            background: var(--gris-ceramica);
            clip-path: polygon(8px 0, calc(100% - 8px) 0, 100% 8px, 100% calc(100% - 8px), calc(100% - 8px) 100%, 8px 100%, 0 calc(100% - 8px), 0 8px);
        }}
        .risk-item .badge {{ flex-shrink: 0; margin-top: 2px; }}
        .risk-content {{ flex: 1; }}
        .risk-content strong {{ display: block; margin-bottom: 4px; color: var(--azul-amazonico); }}
        .risk-content p {{ font-size: 13px; line-height: 1.4; }}

        /* Oportunidades/Restrições */
        .auto-item {{
            padding: 16px; margin-bottom: 12px; background: var(--gris-ceramica);
            clip-path: polygon(8px 0, calc(100% - 8px) 0, 100% 8px, 100% calc(100% - 8px), calc(100% - 8px) 100%, 8px 100%, 0 calc(100% - 8px), 0 8px);
        }}
        .auto-item h4 {{ color: var(--azul-amazonico); margin-bottom: 6px; font-size: 14px; }}
        .auto-item p {{ font-size: 13px; line-height: 1.4; }}

        /* Parecer */
        .parecer-box {{
            background: var(--azul-oscuro); color: var(--branco); padding: 40px; text-align: center;
            clip-path: polygon(12px 0, calc(100% - 12px) 0, 100% 12px, 100% calc(100% - 12px), calc(100% - 12px) 100%, 12px 100%, 0 calc(100% - 12px), 0 12px);
            margin-bottom: 20px;
        }}
        .parecer-box .badge {{ font-size: 16px; padding: 8px 24px; }}
        .score-container {{ display: flex; align-items: center; gap: 16px; margin: 20px 0; justify-content: center; }}
        .score-number {{ font-size: 72px; font-weight: 300; color: var(--branco); line-height: 1.0; }}
        .score-label {{ font-size: 14px; color: var(--gris-acero); text-align: left; }}

        .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        ul {{ margin-left: 20px; margin-bottom: 12px; }}
        li {{ font-size: 13px; line-height: 1.6; }}
        p {{ margin-bottom: 8px; font-size: 14px; line-height: 1.5; }}
        .gen-date {{ text-align: right; font-size: 11px; color: var(--gris-4); margin-bottom: 20px; }}

        .btn-export {{
            position: fixed; bottom: 30px; right: 30px;
            background: var(--azul-amazonico); color: var(--branco); border: none;
            padding: 14px 24px; font-size: 13px; font-weight: 700;
            text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer;
            z-index: 200; font-family: var(--font-primary); transition: background 0.2s;
            clip-path: polygon(8px 0, calc(100% - 8px) 0, 100% 8px, 100% calc(100% - 8px), calc(100% - 8px) 100%, 8px 100%, 0 calc(100% - 8px), 0 8px);
        }}
        .btn-export:hover {{ background: var(--azul-oscuro); }}

        @media print {{
            * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; color-adjust: exact !important; }}
            .sidebar {{ display: none; }}
            .main-content {{ margin-left: 0; padding: 20px; }}
            .section {{ break-inside: avoid; }}
            .btn-export {{ display: none !important; }}
        }}
        @media (max-width: 900px) {{
            .sidebar {{ display: none; }}
            .main-content {{ margin-left: 0; }}
            .farois-grid, .bsw-grid, .two-col {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <aside class="sidebar">
        <div class="logo">Indra Group</div>
        <div class="practice-badge">DS — DESENVOLVIMENTO DE SOLUÇÕES</div>
        <div class="subtitle">QUALIFICAÇÃO DE OFERTA<br>{nome_opp}</div>
        <nav>
            <a href="#resumo" class="active">1. Resumo Executivo</a>
            <a href="#documentos">2. Documentos Analisados</a>
            <a href="#escopo">3. Escopo do Projeto</a>
            <a href="#stack">4. Stack Tecnológico</a>
            <a href="#dimensionamento">5. Dimensionamento de Equipe</a>
            <a href="#riscos">6. Riscos Técnicos e Contratuais</a>
            <a href="#oportunidades">7. Oportunidades de Diferenciação</a>
            <a href="#restricoes">8. Restrições e Limitações</a>
            <a href="#parecer">9. Parecer Go/No-Go</a>
            <a href="#anexos">10. Anexos e Observações</a>
        </nav>
    </aside>

    <main class="main-content">
        <div class="gen-date">Relatório gerado em: {timestamp} | Motor: {_esc(motor)} | Cenário: {_esc(cenario)}</div>

        <!-- SEÇÃO 1 — RESUMO EXECUTIVO -->
        <section class="section" id="resumo">
            <h2 class="section-title">resumo executivo</h2>
            <div class="card-dark">
                <p style="font-size:15px; line-height:1.5;">
                    <strong>{cliente}</strong> — RFP para <strong>{escopo_principal}</strong> no setor
                    <strong>{setor}</strong>. Tipo de serviço: <strong>{tipo}</strong>.
                    Documento com {total_pag} páginas e {total_pal} palavras analisado pelo motor
                    multi-agente Minsait DS (5 sub-agentes especializados).
                </p>
            </div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{score}/10</div>
                    <div class="metric-label">Score Final</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value"><span class="{badge_cls}" style="font-size:16px;padding:4px 12px">{badge_label}</span></div>
                    <div class="metric-label">Decisão</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{alto_count}/8</div>
                    <div class="metric-label">Faróis Alto/Médio-Alto</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{len(tech_names)}</div>
                    <div class="metric-label">Tecnologias</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{total_riscos}</div>
                    <div class="metric-label">Riscos ({criticos} Críticos)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{dim.get('ftes_estimado', dim.get('total_ftes', 'N/A'))}</div>
                    <div class="metric-label">FTEs Estimados</div>
                </div>
            </div>
            <p><strong>Justificativa:</strong> {_esc(justificativa)}</p>
        </section>

        <!-- SEÇÃO 2 — DOCUMENTOS ANALISADOS -->
        <section class="section" id="documentos">
            <h2 class="section-title">documentos analisados</h2>
            <table>
                <thead><tr><th>Documento</th><th>Tipo</th><th>Tamanho</th></tr></thead>
                <tbody>{docs_rows}</tbody>
            </table>
        </section>

        <!-- SEÇÃO 3 — ESCOPO DO PROJETO -->
        <section class="section" id="escopo">
            <h2 class="section-title">escopo do projeto</h2>
            <div class="card">
                <p><strong>Objeto da Contratação:</strong> {escopo_principal}</p>
                <p><strong>Tipo de Engajamento:</strong> {tipo}</p>
                <p><strong>Setor:</strong> {setor}</p>
                <p><strong>Complexidade:</strong> {_esc(complexidade)}</p>
                <p><strong>Aderência DS:</strong> {aderencia}/10</p>
            </div>
        </section>

        <!-- SEÇÃO 4 — STACK TECNOLÓGICO -->
        <section class="section" id="stack">
            <h2 class="section-title">stack tecnológico</h2>
            <div class="tech-stack">{techs_html}</div>
            {'<h3 class="section-subtitle">Gaps Tecnológicos</h3><div class="card"><ul>' + "".join(f"<li>{_esc(g)}</li>" for g in gaps) + '</ul></div>' if gaps else ''}
        </section>

        <!-- SEÇÃO 5 — DIMENSIONAMENTO DE EQUIPE -->
        <section class="section" id="dimensionamento">
            <h2 class="section-title">dimensionamento de equipe</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{dim.get('ftes_estimado', dim.get('total_ftes', 'N/A'))}</div>
                    <div class="metric-label">FTEs</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{dim.get('duracao_meses', '?')}</div>
                    <div class="metric-label">Meses</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{dim.get('total_sprints', '?')}</div>
                    <div class="metric-label">Sprints</div>
                </div>
            </div>
            {'<h3 class="section-subtitle">Perfis Técnicos</h3><div class="card"><ul>' + "".join(f"<li>{_esc(p)}</li>" for p in perfis[:15]) + '</ul></div>' if perfis else ''}
        </section>

        <!-- SEÇÃO 6 — RISCOS TÉCNICOS E CONTRATUAIS -->
        <section class="section" id="riscos">
            <h2 class="section-title">riscos técnicos e contratuais</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{total_riscos}</div>
                    <div class="metric-label">Total Riscos</div>
                </div>
                <div class="metric-card" style="{'background:var(--laranja-risco)' if criticos > 0 else ''}">
                    <div class="metric-value">{criticos}</div>
                    <div class="metric-label">Críticos</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{medios}</div>
                    <div class="metric-label">Médios</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{risk_score}/10</div>
                    <div class="metric-label">Risk Score</div>
                </div>
            </div>
            {riscos_html if riscos_html else '<p>Nenhum risco crítico identificado.</p>'}
        </section>

        <!-- SEÇÃO 7 — OPORTUNIDADES DE DIFERENCIAÇÃO -->
        <section class="section" id="oportunidades">
            <h2 class="section-title">oportunidades de diferenciação</h2>
            {oport_html}
        </section>

        <!-- SEÇÃO 8 — RESTRIÇÕES E LIMITAÇÕES -->
        <section class="section" id="restricoes">
            <h2 class="section-title">restrições e limitações</h2>
            {restr_html}
        </section>

        <!-- SEÇÃO 9 — PARECER GO/NO-GO (8 Faróis + BSW) -->
        <section class="section" id="parecer">
            <h2 class="section-title">parecer de qualificação (Go/No-Go)</h2>

            <!-- Parecer Box -->
            <div class="parecer-box">
                <p style="font-size:11px;text-transform:uppercase;letter-spacing:0.1em;color:var(--gris-acero);margin-bottom:10px;">
                    Qualificação Minsait BizDev &amp; Recomendação | Prática: DS
                </p>
                <span class="badge {badge_cls}" style="font-size:18px;padding:10px 28px;">{badge_label}</span>
                <div class="score-container">
                    <div class="score-number">{score}</div>
                    <div class="score-label">/ 10<br>Score de<br>Atratividade</div>
                </div>
                <p style="font-size:13px;color:var(--gris-acero);">{alto_count} de 8 faróis ALTO/MÉDIO-ALTO | Confiança: {confianca}%</p>
            </div>

            <!-- 8 Faróis — 2 colunas -->
            <h3 class="section-subtitle">8 Critérios Faróis Ponderados</h3>
            <div class="farois-grid">
                <div>
                    <div class="farois-col-title">Critérios do Cliente</div>
                    {farois_cliente_html}
                </div>
                <div>
                    <div class="farois-col-title">Critérios Minsait</div>
                    {farois_minsait_html}
                </div>
            </div>

            <!-- Best Story Wins -->
            <h3 class="section-subtitle">Best Story Wins</h3>
            <div class="bsw-grid">
                {bsw_html if bsw_html else '<p>Não disponível.</p>'}
            </div>

            <!-- Condições GO CONDICIONADO -->
            {'<h3 class="section-subtitle">Condições para Destravar o GO Pleno (14 dias)</h3><table><thead><tr><th>#</th><th>Condição</th><th>Prazo</th><th>Responsável</th></tr></thead><tbody>' + cond_html + '</tbody></table>' if cond_html else ''}

            <div class="card">
                <p><strong>Justificativa:</strong> {_esc(justificativa)}</p>
            </div>
        </section>

        <!-- SEÇÃO 10 — ANEXOS E OBSERVAÇÕES -->
        <section class="section" id="anexos">
            <h2 class="section-title">anexos e observações</h2>
            <div class="two-col">
                <div class="card">
                    <h3 class="section-subtitle">Acervo DS Consultado</h3>
                    <p><strong>Docs analisados:</strong> {kb_docs}</p>
                    <p><strong>Relevantes:</strong> {kb_rel}</p>
                    <p><strong>Cobertura KB:</strong> {kb_cob}/10</p>
                </div>
                <div class="card">
                    <h3 class="section-subtitle">Metadados</h3>
                    <p><strong>Motor:</strong> {_esc(motor)}</p>
                    <p><strong>Cenário:</strong> {_esc(cenario)}</p>
                    <p><strong>Duração:</strong> {duracao:.1f}s</p>
                    <p><strong>Trace ID:</strong> {_esc(trace_id)}</p>
                </div>
            </div>
            {'<h3 class="section-subtitle">Próximos Passos</h3><div class="card"><ul>' + ns_html + '</ul></div>' if ns_html else ''}
        </section>
    </main>

    <button class="btn-export" onclick="window.print()">⬇ Exportar PDF</button>

    <script>
        const sections = document.querySelectorAll('.section');
        const navLinks = document.querySelectorAll('.sidebar nav a');
        window.addEventListener('scroll', () => {{
            let current = '';
            sections.forEach(section => {{
                const sectionTop = section.offsetTop - 100;
                if (window.scrollY >= sectionTop) current = section.getAttribute('id');
            }});
            navLinks.forEach(link => {{
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + current) link.classList.add('active');
            }});
        }});
    </script>
</body>
</html>'''
    return html


if __name__ == '__main__':
    import glob
    files = sorted(glob.glob('out/qualificacao_*.json'), key=os.path.getmtime, reverse=True)
    for jf in files[:5]:
        try:
            with open(jf, 'r', encoding='utf-8') as f:
                d = json.load(f)
            if not d.get('parecer'):
                continue
            html = gerar_html(jf)
            html_path = jf.replace('.json', '.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f'OK: {html_path} ({len(html)} bytes)')
        except Exception as e:
            import traceback
            print(f'ERRO em {jf}: {e}')
            traceback.print_exc()
