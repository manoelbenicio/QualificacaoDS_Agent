"""
Gerador de Painel Executivo One-Pager — Qualificação DS Minsait
Spec: transformaca-agente-ofertas-qualificacao-ds.md §5 — Layout do Painel
Design: transformaca-agente-ofertas-qualificacao-ds.md §3 — Identidade Visual Indra Group
Cores: §3 Paleta Principal + Secundária (NUNCA opacity, NUNCA border-radius)
Ref:   skills/Painel/painel_ds_qualificacao-ofertas.pptx (layout de referência)
"""
import json, os, html as html_mod
from datetime import datetime


def _esc(v):
    if v is None:
        return 'N/A'
    return html_mod.escape(str(v))


def gerar_painel(json_path: str) -> str:
    """Gera HTML one-pager executivo conforme spec §5 + design system §3."""
    with open(json_path, 'r', encoding='utf-8') as f:
        d = json.load(f)

    parecer = d.get('parecer', {})
    oi = d.get('outputs_intermediarios', {})
    sa1 = oi.get('SA1_extracao', {})
    sa4 = oi.get('SA4_comercial', {})

    decisao = parecer.get('decisao', 'N/A')
    score = parecer.get('score_final', parecer.get('score_final_ponderado', 0))
    alto_count = parecer.get('alto_count', sa4.get('alto_count', 0))
    cliente = _esc(sa1.get('cliente', 'N/A'))
    nome_opp = _esc(sa1.get('nome_oportunidade', 'N/A'))

    farois = parecer.get('farois_consolidados', sa4.get('farois', []))
    farois_cliente = [f for f in farois if f.get('grupo', '') == 'CRITÉRIOS DO CLIENTE']
    farois_minsait = [f for f in farois if f.get('grupo', '') == 'CRITÉRIOS MINSAIT']
    if not farois_cliente and len(farois) >= 8:
        farois_cliente = farois[:4]
        farois_minsait = farois[4:]

    bsw = parecer.get('best_story_wins', sa4.get('best_story_wins', {}))
    condicoes = parecer.get('condicoes_mitigacao', [])

    # Badge decisão — spec §3: Go=Verde 3, No-Go=Laranja 3, Condicionado=Roxo 3
    if 'NO_GO' in str(decisao):
        badge_label = 'NO-GO'
        badge_bg = '#E56813'  # Laranja 3
    elif 'CONDICIONADO' in str(decisao):
        badge_label = 'GO CONDICIONADO'
        badge_bg = '#8661F5'  # Roxo 3
    else:
        badge_label = 'GO'
        badge_bg = '#44B757'  # Verde 3

    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')

    def _nivel_color(nivel):
        """Cores per spec §3: ALTO=Verde3, MEDIO=Roxo3, BAIXO=Laranja3."""
        m = {
            'ALTO': '#44B757',       # Verde 3
            'MEDIO_ALTO': '#A9E8A7', # Verde 1
            'MEDIO': '#8661F5',      # Roxo 3
            'MEDIO_BAIXO': '#FFA96E',# Laranja 1
            'BAIXO': '#E56813',      # Laranja 3
        }
        return m.get(nivel, '#8661F5')

    def _nivel_label(nivel):
        m = {
            'ALTO': 'ALTO',
            'MEDIO_ALTO': 'MÉDIO-ALTO',
            'MEDIO': 'MÉDIO',
            'MEDIO_BAIXO': 'MÉDIO-BAIXO',
            'BAIXO': 'BAIXO',
        }
        return m.get(nivel, nivel)

    def _farol_html(f):
        nome = _esc(f.get('nome', '?'))
        nivel = f.get('nivel', 'MEDIO')
        cor = _nivel_color(nivel)
        lbl = _nivel_label(nivel)
        just = _esc(f.get('justificativa', ''))
        if len(just) > 150:
            just = just[:147] + '...'
        return f'''<div class="farol">
            <div class="farol-dot" style="background:{cor}"></div>
            <div class="farol-body">
                <div class="farol-name">{nome}</div>
                <div class="farol-nivel" style="color:{cor}">{lbl}</div>
            </div>
            <div class="farol-just">{just}</div>
        </div>'''

    farois_c = ''.join(_farol_html(f) for f in farois_cliente)
    farois_m = ''.join(_farol_html(f) for f in farois_minsait)

    # BSW — spec §6.2: 4 perguntas
    bsw_cards = ''
    bsw_data = [
        ('por_que_mudar', '1. POR QUE MUDAR?', 'Qual dor justifica investir?'),
        ('por_que_agora', '2. POR QUE AGORA?', 'O que abriu a janela?'),
        ('por_que_minsait', '3. POR QUE MINSAIT?', 'Qual nosso diferencial único?'),
        ('por_que_confiar', '4. POR QUE CONFIAR?', 'Como provamos que entregamos?'),
    ]
    for key, label, sub in bsw_data:
        val = bsw.get(key, '')
        if val and len(val) > 200:
            val = val[:197] + '...'
        bsw_cards += f'''<div class="bsw-card">
            <div class="bsw-inner">
                <div class="bsw-number">PERGUNTA</div>
                <div class="bsw-question">{label}</div>
                <div class="bsw-sub">{sub}</div>
                <div class="bsw-answer">{_esc(val) if val else 'N/A'}</div>
            </div>
        </div>'''

    # Condições — spec §6.3
    cond_html = ''
    if condicoes:
        for i, c in enumerate(condicoes[:5], 1):
            texto = c.get('condicao', c) if isinstance(c, dict) else c
            cond_html += f'<div class="cond-item"><span class="cond-num">{i}.</span><span class="cond-text">{_esc(texto)}</span></div>'

    # ═══════════════════════════════════════════════════════════════
    # HTML — Design System Indra Group (spec §3)
    # Regra §3: NUNCA border-radius — usar clip-path 45°
    # Regra §3: NUNCA opacity — cores sólidas
    # Fundo padrão: Gris Cerámica #E3E2DA
    # Header/Footer: Azul Oscuro #002532
    # Títulos: Azul Amazónico #004254
    # Corpo: Gris Acero Oscuro #646459
    # ═══════════════════════════════════════════════════════════════

    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel Executivo | {nome_opp} — {cliente} | Indra Group</title>
    <style>
        @page {{ size: A4 landscape; margin: 10mm; }}
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
            --font: 'ForFuture Sans', Arial, Helvetica, sans-serif;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: var(--font);
            background: var(--gris-ceramica);
            color: var(--gris-acero-oscuro);
            line-height: 1.25;
        }}

        /* ═══ HEADER — Azul Oscuro per §3 ═══ */
        .header {{
            background: var(--azul-oscuro);
            padding: 16px 28px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header-title {{
            font-size: 20px;
            font-weight: 400;
            color: var(--branco);
        }}
        .header-sub {{
            font-size: 11px;
            color: var(--gris-acero);
            margin-top: 2px;
        }}
        .practice-badge {{
            display: inline-block;
            background: #1A73E8;
            color: var(--branco);
            padding: 2px 8px;
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 4px;
            clip-path: polygon(3px 0, calc(100% - 3px) 0, 100% 3px, 100% calc(100% - 3px), calc(100% - 3px) 100%, 3px 100%, 0 calc(100% - 3px), 0 3px);
        }}
        .header-right {{ text-align: right; }}
        .header-score {{
            font-size: 32px;
            font-weight: 300;
            color: var(--branco);
            line-height: 1;
        }}
        .header-score-label {{
            font-size: 10px;
            color: var(--gris-acero);
        }}
        .header-badge {{
            display: inline-block;
            padding: 4px 14px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            color: var(--branco);
            background: {badge_bg};
            margin-top: 4px;
            clip-path: polygon(4px 0, calc(100% - 4px) 0, 100% 4px, 100% calc(100% - 4px), calc(100% - 4px) 100%, 4px 100%, 0 calc(100% - 4px), 0 4px);
        }}

        /* ═══ CRITÉRIOS — 2 colunas sobre fundo branco per §3 ═══ */
        .criterios {{
            background: var(--branco);
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
            padding: 14px 28px 10px;
            clip-path: polygon(10px 0, calc(100% - 10px) 0, 100% 10px, 100% calc(100% - 10px), calc(100% - 10px) 100%, 10px 100%, 0 calc(100% - 10px), 0 10px);
            margin: 8px 0;
        }}
        .criterios-title {{
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--azul-amazonico);
            margin-bottom: 8px;
            padding-bottom: 6px;
            border-bottom: 2px solid var(--gris-2);
        }}
        .farol {{
            display: grid;
            grid-template-columns: 20px 130px 1fr;
            align-items: start;
            gap: 6px;
            padding: 6px 0;
            border-bottom: 1px solid var(--gris-ceramica);
        }}
        .farol-dot {{
            width: 14px; height: 14px;
            margin-top: 2px;
            clip-path: circle(50%);
        }}
        .farol-name {{
            font-size: 11px; font-weight: 700;
            text-transform: uppercase;
            color: var(--azul-amazonico);
        }}
        .farol-nivel {{
            font-size: 10px; font-weight: 700;
            margin-top: 1px;
        }}
        .farol-just {{
            font-size: 10px;
            color: var(--gris-5);
            line-height: 1.3;
        }}

        /* ═══ BSW — 4 cards escuros per spec §3 (.bsw-card) ═══ */
        .bsw-section {{
            padding: 0 0 8px;
        }}
        .bsw-title {{
            font-size: 12px; font-weight: 700;
            text-transform: uppercase;
            color: var(--azul-amazonico);
            padding: 0 28px;
            margin-bottom: 8px;
        }}
        .bsw-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            padding: 0 28px;
        }}
        .bsw-card {{
            background: var(--azul-oscuro);
            color: var(--branco);
            clip-path: polygon(8px 0, calc(100% - 8px) 0, 100% 8px, 100% calc(100% - 8px), calc(100% - 8px) 100%, 8px 100%, 0 calc(100% - 8px), 0 8px);
        }}
        .bsw-inner {{ padding: 12px 14px; }}
        .bsw-number {{
            font-size: 9px; font-weight: 700;
            color: var(--gris-acero);
            text-transform: uppercase;
            margin-bottom: 2px;
        }}
        .bsw-question {{
            font-size: 12px; font-weight: 400;
            margin-bottom: 2px;
        }}
        .bsw-sub {{
            font-size: 9px;
            color: var(--gris-acero);
            font-style: italic;
            margin-bottom: 6px;
        }}
        .bsw-answer {{
            font-size: 10px;
            line-height: 1.35;
            color: var(--gris-2);
        }}

        /* ═══ BOTTOM — Recomendação + Condições ═══ */
        .bottom {{
            display: grid;
            grid-template-columns: 220px 1fr;
            gap: 8px;
            padding: 0 28px;
            margin-top: 8px;
        }}
        .rec-box {{
            background: var(--azul-oscuro);
            color: var(--branco);
            padding: 14px 16px;
            clip-path: polygon(8px 0, calc(100% - 8px) 0, 100% 8px, 100% calc(100% - 8px), calc(100% - 8px) 100%, 8px 100%, 0 calc(100% - 8px), 0 8px);
        }}
        .rec-label {{
            font-size: 10px; font-weight: 700;
            text-transform: uppercase;
            color: var(--gris-acero);
        }}
        .rec-decisao {{
            font-size: 18px; font-weight: 700;
            margin-top: 4px;
        }}
        .rec-sub {{
            font-size: 9px;
            color: var(--gris-acero);
            margin-top: 3px;
        }}
        .cond-box {{
            background: var(--branco);
            padding: 12px 16px;
            clip-path: polygon(8px 0, calc(100% - 8px) 0, 100% 8px, 100% calc(100% - 8px), calc(100% - 8px) 100%, 8px 100%, 0 calc(100% - 8px), 0 8px);
        }}
        .cond-title {{
            font-size: 10px; font-weight: 700;
            color: var(--azul-amazonico);
            text-transform: uppercase;
            margin-bottom: 6px;
        }}
        .cond-item {{
            display: flex;
            gap: 4px;
            margin-bottom: 2px;
        }}
        .cond-num {{
            font-size: 10px; font-weight: 700;
            color: var(--laranja-risco);
            min-width: 14px;
        }}
        .cond-text {{
            font-size: 10px;
            color: var(--gris-acero-oscuro);
        }}

        /* ═══ FOOTER — Azul Oscuro per §3 ═══ */
        .footer {{
            background: var(--azul-oscuro);
            padding: 5px 28px;
            font-size: 9px;
            color: var(--gris-acero);
            margin-top: 8px;
        }}

        @media print {{
            * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; color-adjust: exact !important; }}
            body {{ background: var(--gris-ceramica); }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="header-title">Qualificação Minsait BizDev &amp; Recomendação</div>
            <div class="header-sub">Best Story Wins + Critérios Cliente × Minsait | Decisão Go/No-Go</div>
            <div class="practice-badge">DS — DESENVOLVIMENTO DE SOLUÇÕES</div>
        </div>
        <div class="header-right">
            <div class="header-score">{score}</div>
            <div class="header-score-label">/ 10 Score de Atratividade</div>
            <div class="header-badge">{badge_label}</div>
        </div>
    </div>

    <div class="criterios">
        <div>
            <div class="criterios-title">Critérios do Cliente ({cliente})</div>
            {farois_c}
        </div>
        <div>
            <div class="criterios-title">Critérios Minsait</div>
            {farois_m}
        </div>
    </div>

    <div class="bsw-section">
        <div class="bsw-title">Best Story Wins — aplicação à oportunidade {nome_opp}</div>
        <div class="bsw-grid">{bsw_cards}</div>
    </div>

    <div class="bottom">
        <div class="rec-box">
            <div class="rec-label">Recomendação</div>
            <div class="rec-decisao">{badge_label}</div>
            <div class="rec-sub">{'Prosseguir com proposta + mitigações' if 'CONDICIONADO' in str(decisao) else 'Prosseguir com proposta' if 'GO' == decisao else 'Não prosseguir'}</div>
        </div>
        <div class="cond-box">
            <div class="cond-title">{'5 condições para destravar o GO pleno (próximos 14 dias):' if cond_html else 'Observações'}</div>
            {cond_html if cond_html else '<div class="cond-text">Sem condições pendentes.</div>'}
        </div>
    </div>

    <div class="footer">
        Minsait Brasil  |  Desenvolvimento de Negócios  |  Confidencial  |  Gerado em {timestamp}  |  Prática: DS
    </div>
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
            html = gerar_painel(jf)
            html_path = jf.replace('.json', '_painel.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f'OK: {html_path} ({len(html)} bytes)')
        except Exception as e:
            import traceback
            print(f'ERRO em {jf}: {e}')
            traceback.print_exc()
