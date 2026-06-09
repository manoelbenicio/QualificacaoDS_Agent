import json, os, glob

files = sorted(glob.glob('out/qualificacao_*.json'), key=os.path.getmtime, reverse=True)[:3]

for f in files:
    with open(f,'r',encoding='utf-8') as fh:
        d = json.load(fh)
    
    parecer = d.get('parecer',{})
    oi = d.get('outputs_intermediarios',{})
    sa1 = oi.get('SA1_extracao',{})
    sa2 = oi.get('SA2_tecnico',{})
    sa3 = oi.get('SA3_riscos',{})
    sa4 = oi.get('SA4_comercial',{})
    etapas = d.get('etapas',{})
    
    print('=' * 70)
    print('  ARQUIVO: ' + os.path.basename(f))
    print('  MOTOR:   ' + str(d.get('motor','N/A')))
    print('  DURACAO:  ' + str(d.get('duracao_segundos','N/A')) + 's')
    print('=' * 70)
    
    print('  PIPELINE DE EXECUCAO:')
    for nome, info in etapas.items():
        if isinstance(info, dict):
            status = info.get('status','?')
            tempo = info.get('tempo','?')
            print('    ' + nome.ljust(30) + ' | ' + str(status).ljust(10) + ' | ' + str(tempo))
        else:
            print('    ' + nome.ljust(30) + ' | ' + str(info))

    ad = sa1.get('analise_documento',{})
    print('  [SA1] Paginas=' + str(ad.get('total_paginas','?')) + ' Palavras=' + str(ad.get('total_palavras','?')) + ' Idioma=' + str(ad.get('idioma_detectado','?')))
    
    techs = [t.get('nome',t) if isinstance(t,dict) else t for t in sa2.get('tecnologias_identificadas',[])]
    print('  [SA2] Techs=' + str(sa2.get('total_tecnologias',0)) + ' Complexidade=' + str(sa2.get('complexidade','?')) + ' Aderencia=' + str(sa2.get('aderencia_ds','?')) + '/10')
    print('        Techs: ' + str(techs[:8]))
    dim = sa2.get('dimensionamento',{})
    print('        FTEs=' + str(dim.get('ftes_estimado','?')) + ' Sprints=' + str(dim.get('total_sprints','?')) + ' Meses=' + str(dim.get('duracao_meses','?')))
    
    print('  [SA3] Riscos=' + str(sa3.get('total_riscos',0)) + ' Criticos=' + str(sa3.get('criticos',0)) + ' Score=' + str(sa3.get('risk_score','?')))
    for r in sa3.get('top_riscos',[]):
        print('        [' + str(r.get('severidade','?')) + '] ' + str(r.get('nome','?')))

    print('  [SA4] Score=' + str(sa4.get('score_final_ponderado','?')) + '/10 Nivel=' + str(sa4.get('nivel_geral','?')))
    
    print('  [SA5] DECISAO=' + str(parecer.get('decisao','?')) + ' SCORE=' + str(parecer.get('score_final','?')) + '/10 CONFIANCA=' + str(parecer.get('confianca_pct','?')) + '%')
    just = str(parecer.get('justificativa_decisao','?'))[:150]
    print('        Justificativa: ' + just)
    
    re_exec = str(parecer.get('resumo_executivo',''))
    if re_exec:
        print('  [LLM] Resumo: ' + re_exec[:150])
    
    ns = parecer.get('next_steps',[])
    print('  [NEXT]')
    for s in ns:
        print('    -> ' + str(s))
    print()
