# -*- coding: utf-8 -*-
"""
G1 — Conformidade automática (teórica) por portal.
Gera:
  g1_ases_aim_por_portal.png      (Q1.1 grau de conformidade: ASES e WAVE/AIM)
  g1_severidade_wave.png          (Q1.2 severidade WAVE p/ leitor de tela)
  g1_composicao_ases_secao.png    (Q1.2 composição % dos erros ASES por seção)

Fontes: ases-data.json (score 0-100, ↑melhor; errors por seção) e
        output-wave-analysis/T*/*-wave-summary.csv (aim_score 0-10 ↑melhor; sr_*).
Estilo/paleta herdados dos scripts existentes do projeto.
"""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# ------------------------------------------------------------------
# Constantes compartilhadas (mesmo padrão dos scripts já existentes)
# ------------------------------------------------------------------
nomes_tarefas = {
    1: 'T1: Consulta CPF',
    2: 'T2: Painel de Monitoramento',
    3: 'T3: Receita Federal',
    4: 'T4: IBGE Censo',
    5: 'T5: Mapa de Empresas',
}
cores_tarefa = {1: '#ff7f0e', 2: '#2ca02c', 3: '#d62728', 4: '#9467bd', 5: '#8c564b'}

wave_files = {
    1: 'output-wave-analysis/T1/cpf-wave-summary.csv',
    2: 'output-wave-analysis/T2/monitor-serv-wave-summary.csv',
    3: 'output-wave-analysis/T3/receita-federal-wave-summary.csv',
    4: 'output-wave-analysis/T4/censo-wave-summary.csv',
    5: 'output-wave-analysis/T5/mapa-emp-wave-summary.csv',
}
ases_flow_to_tarefa = {
    'ConsultarCPF': 1, 'ConsultaMonitoramentoServicos': 2,
    'BuscaUnidadesAtendimento': 3, 'ConsultaCenso': 4, 'ConsultaMapaDeEMpresas': 5,
}

with open('ases-data.json', 'r', encoding='utf-8') as f:
    ases_raw = json.load(f)
secao_labels = ases_raw['_meta']['section_labels']
secao_keys = ases_raw['_meta']['section_keys']

# ------------------------------------------------------------------
# Agregações automáticas por portal
# ------------------------------------------------------------------
ases_score = {}          # média do score por página (0-100, ↑melhor)
ases_pages = {}          # lista (score por página) p/ detalhamento
n_paginas = {}
ases_erros_secao = {}    # soma de errors por seção (todas as páginas)
for flow, paginas in ases_raw['flows'].items():
    t = ases_flow_to_tarefa[flow]
    ases_pages[t] = [float(p['score']) for p in paginas]
    ases_score[t] = float(np.mean(ases_pages[t]))
    n_paginas[t] = len(paginas)
    ases_erros_secao[t] = {
        k: sum(p['sections'][k]['errors'] for p in paginas) for k in secao_keys
    }

wave_aim = {}            # média aim_score (0-10, ↑melhor)
wave_aim_pages = {}      # lista (aim_score por página) p/ detalhamento
wave_sev = {}            # média POR PÁGINA das severidades p/ leitor de tela
sev_cols = ['sr_critical', 'sr_high', 'sr_medium', 'sr_low']
for t, path in wave_files.items():
    w = pd.read_csv(path)
    wave_aim_pages[t] = [float(v) for v in w['aim_score'].tolist()]
    wave_aim[t] = float(w['aim_score'].mean())
    wave_sev[t] = {c: float(w[c].mean()) for c in sev_cols}

tarefas = [1, 2, 3, 4, 5]
labels = [nomes_tarefas[t] for t in tarefas]
cores = [cores_tarefa[t] for t in tarefas]


# ==================================================================
# FIGURA 1 — ASES e WAVE/AIM por portal (Q1.1)
# ==================================================================
fig, (axA, axB) = plt.subplots(1, 2, figsize=(15, 6))

# -- ASES (0-100) --
vals_ases = [ases_score[t] for t in tarefas]
barsA = axA.bar(labels, vals_ases, color=cores, edgecolor='black', linewidth=0.8)
for b, v, t in zip(barsA, vals_ases, tarefas):
    axA.text(b.get_x() + b.get_width() / 2, v + 1, f'{v:.1f}',
             ha='center', va='bottom', fontsize=12, fontweight='bold')
    axA.text(b.get_x() + b.get_width() / 2, 3, f'{n_paginas[t]} pág.',
             ha='center', va='bottom', fontsize=9, color='white', fontweight='bold')
axA.axhline(100, color='gray', linestyle=':', linewidth=1)
axA.set_ylim(0, 108)
axA.set_ylabel('Score ASES (0–100)   ↑ melhor', fontsize=12, fontweight='bold')
axA.set_title('ASES — conformidade e-MAG/WCAG\n(média das páginas avaliadas)',
              fontsize=13, fontweight='bold', pad=10)
axA.grid(axis='y', linestyle='--', alpha=0.4)
axA.set_axisbelow(True)
axA.set_xticks(range(len(labels)))
axA.set_xticklabels(labels, rotation=15, ha='right', fontsize=9)

# -- WAVE/AIM (0-10) --
vals_aim = [wave_aim[t] for t in tarefas]
barsB = axB.bar(labels, vals_aim, color=cores, edgecolor='black', linewidth=0.8)
for b, v, t in zip(barsB, vals_aim, tarefas):
    axB.text(b.get_x() + b.get_width() / 2, v + 0.1, f'{v:.1f}',
             ha='center', va='bottom', fontsize=12, fontweight='bold')
    axB.text(b.get_x() + b.get_width() / 2, 0.25, f'{n_paginas[t]} pág.',
             ha='center', va='bottom', fontsize=9, color='white', fontweight='bold')
axB.axhline(10, color='gray', linestyle=':', linewidth=1)
axB.set_ylim(0, 10.8)
axB.set_ylabel('WAVE — índice AIM (0–10)   ↑ melhor', fontsize=12, fontweight='bold')
axB.set_title('WAVE — índice AIM\n(média das páginas avaliadas)',
              fontsize=13, fontweight='bold', pad=10)
axB.grid(axis='y', linestyle='--', alpha=0.4)
axB.set_axisbelow(True)
axB.set_xticks(range(len(labels)))
axB.set_xticklabels(labels, rotation=15, ha='right', fontsize=9)

fig.suptitle('G1 · Grau de conformidade automática por portal (ASES e WAVE/AIM)',
             fontsize=15, fontweight='bold', y=1.02)
fig.text(0.5, -0.02,
         'Ambas as métricas: maior = mais conforme segundo a ferramenta. '
         'Nº de páginas avaliadas difere por portal (CPF 3 · Painel 5 · Receita 5 · Censo 2 · Mapa 1) '
         '— usa-se a média por página; o Mapa (1 página) é menos estável.',
         ha='center', fontsize=9.5, color='#444', style='italic')
plt.tight_layout()
plt.savefig('g1_ases_aim_por_portal.png', dpi=300, bbox_inches='tight')
plt.close(fig)
print('Salvo: g1_ases_aim_por_portal.png')


# ==================================================================
# FIGURA 1b — Detalhe por página: barras finas + linha da média  (Q1.1)
# ==================================================================
def barras_paginas(ax, pages_por_tarefa, media_por_tarefa, ymax, ylabel, titulo, fmt):
    """Cada página = uma barra fina; média do portal = linha tracejada."""
    bw = 0.15                                   # largura fixa → barras sempre finas
    gap_t2_t3 = 0.35                            # respiro extra entre T2 e T3
    xpos = [i + (gap_t2_t3 if i >= 2 else 0) for i in range(len(tarefas))]
    for i, t in enumerate(tarefas):
        xc = xpos[i]
        vals = pages_por_tarefa[t]
        n = len(vals)
        centros = xc + (np.arange(n) - (n - 1) / 2) * bw
        ax.bar(centros, vals, width=bw * 0.88, color=cores_tarefa[t],
               edgecolor='white', linewidth=0.5, zorder=2)
        # linha da média do portal (atravessa o grupo de barras)
        meia = max(n, 1) * bw / 2 + 0.04
        ax.plot([xc - meia, xc + meia], [media_por_tarefa[t]] * 2, color='black',
                lw=1.8, linestyle='--', zorder=4)
        ax.text(xc + meia + 0.03, media_por_tarefa[t], fmt.format(media_por_tarefa[t]),
                ha='left', va='center', fontsize=12, fontweight='bold', color='black')
    ax.set_xticks(xpos)
    ax.set_xticklabels([nomes_tarefas[t] for t in tarefas], rotation=15, ha='right',
                       fontsize=10.5)
    ax.set_xlim(-0.5, xpos[-1] + 0.5)
    ax.set_ylim(0, ymax)
    ax.set_ylabel(ylabel, fontsize=12.5, fontweight='bold')
    ax.set_title(titulo, fontsize=13, fontweight='bold', pad=10)
    ax.tick_params(axis='y', labelsize=11.5)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


fig, (axA, axB) = plt.subplots(1, 2, figsize=(15, 6))
barras_paginas(axA, ases_pages, ases_score, 100,
               'Score ASES (0–100)', 'ASES — pontuação por página', '{:.1f}')
barras_paginas(axB, wave_aim_pages, wave_aim, 10,
               'WAVE — índice AIM (0–10)', 'WAVE/AIM — pontuação por página', '{:.1f}')

leg = [Patch(facecolor='#9aa0a6', edgecolor='white', label='Barra única = Página avaliada'),
       Line2D([0], [0], color='black', lw=1.8, linestyle='--', label='Média do portal')]
fig.legend(handles=leg, loc='lower center', bbox_to_anchor=(0.5, -0.02),
           ncol=2, frameon=False, fontsize=11)

fig.suptitle('Conformidade Automática por Página e Média — ASES e WAVE',
             fontsize=15, fontweight='bold', y=1.0)
plt.tight_layout(rect=(0, 0.04, 1, 1))
plt.savefig('g1_ases_aim_por_pagina.png', dpi=300, bbox_inches='tight')
plt.close(fig)
print('Salvo: g1_ases_aim_por_pagina.png')


# ==================================================================
# FIGURA 2 — Severidade WAVE p/ leitor de tela (Q1.2)
# ==================================================================
sev_labels = {'sr_critical': 'Crítico', 'sr_high': 'Alto',
              'sr_medium': 'Médio', 'sr_low': 'Baixo'}
sev_cores = {'sr_critical': '#7a0177', 'sr_high': '#d73027',
             'sr_medium': '#fc8d59', 'sr_low': '#fee08b'}

# Ordena portais pelo total de ocorrências por página (pior em cima)
totais = {t: sum(wave_sev[t].values()) for t in tarefas}
ordem = sorted(tarefas, key=lambda t: totais[t])  # menor embaixo -> maior no topo (barh)
labels_y = [nomes_tarefas[t].replace('\n', ' ') for t in ordem]

fig2, ax = plt.subplots(figsize=(12, 6))
esquerda = np.zeros(len(ordem))
for c in sev_cols:
    vals = np.array([wave_sev[t][c] for t in ordem])
    ax.barh(labels_y, vals, left=esquerda, color=sev_cores[c],
            edgecolor='white', linewidth=1, label=sev_labels[c])
    for i, v in enumerate(vals):
        if v >= 1.0:
            cor_txt = 'white' if c in ('sr_critical', 'sr_high') else '#333'
            ax.text(esquerda[i] + v / 2, i, f'{v:.1f}',
                    ha='center', va='center', fontsize=10, fontweight='bold', color=cor_txt)
    esquerda += vals

for i, t in enumerate(ordem):
    ax.text(esquerda[i] + 0.4, i, f'Σ={totais[t]:.1f}/pág · {n_paginas[t]} pág.',
            ha='left', va='center', fontsize=9.5, color='dimgray')

ax.set_xlabel('Ocorrências por página (média)   ↓ melhor',
              fontsize=12, fontweight='bold')
ax.set_xlim(0, max(totais.values()) * 1.28)
ax.set_title('G1 · Severidade dos problemas WAVE para usuários de leitor de tela\n'
             '(média por página — portais ordenados do mais ao menos problemático)',
             fontsize=14, fontweight='bold', pad=12)
ax.grid(axis='x', linestyle='--', alpha=0.4)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(title='Severidade p/ leitor de tela', loc='lower right',
          frameon=True, fontsize=10, title_fontsize=10)
fig2.text(0.5, -0.02,
          'Severidade atribuída ao impacto sobre leitor de tela (sr_critical/high/medium/low do WAVE). '
          'Usa-se média por página porque o nº de páginas difere entre portais.',
          ha='center', fontsize=9.5, color='#444', style='italic')
plt.tight_layout()
plt.savefig('g1_severidade_wave.png', dpi=300, bbox_inches='tight')
plt.close(fig2)
print('Salvo: g1_severidade_wave.png')


# ==================================================================
# FIGURA 3 — Composição % dos erros ASES por seção (Q1.2)
# ==================================================================
secao_cores = {
    'marcacao': '#4e79a7', 'comportamento': '#59a14f', 'conteudo': '#e15759',
    'apresentacao': '#f28e2b', 'multimidia': '#b07aa1', 'formularios': '#76b7b2',
}

fig3, ax = plt.subplots(figsize=(12, 6))
esquerda = np.zeros(len(tarefas))
total_erros = {t: sum(ases_erros_secao[t].values()) for t in tarefas}
labels_y3 = [nomes_tarefas[t].replace('\n', ' ') for t in tarefas]

# Só mostra na legenda seções que aparecem em algum portal
secoes_presentes = [k for k in secao_keys
                    if any(ases_erros_secao[t][k] > 0 for t in tarefas)]

for k in secoes_presentes:
    pct = np.array([100 * ases_erros_secao[t][k] / total_erros[t] if total_erros[t] else 0
                    for t in tarefas])
    ax.barh(labels_y3, pct, left=esquerda, color=secao_cores[k],
            edgecolor='white', linewidth=1, label=secao_labels[k])
    for i, v in enumerate(pct):
        if v >= 7:
            ax.text(esquerda[i] + v / 2, i, f'{v:.0f}%',
                    ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    esquerda += pct

for i, t in enumerate(tarefas):
    ax.text(101, i, f'{total_erros[t]} erros · {n_paginas[t]} pág.',
            ha='left', va='center', fontsize=9.5, color='dimgray')

ax.set_xlim(0, 122)
ax.set_xlabel('Composição dos erros ASES (% do total de erros do portal)',
              fontsize=12, fontweight='bold')
ax.set_title('G1 · Onde estão os erros de acessibilidade (ASES), por seção e-MAG\n'
             '(composição percentual — soma das páginas de cada portal)',
             fontsize=14, fontweight='bold', pad=12)
ax.grid(axis='x', linestyle='--', alpha=0.4)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.22), ncol=len(secoes_presentes),
          frameon=False, fontsize=10)
plt.tight_layout()
plt.savefig('g1_composicao_ases_secao.png', dpi=300, bbox_inches='tight')
plt.close(fig3)
print('Salvo: g1_composicao_ases_secao.png')

# Console
print('\n[G1] Resumo por portal:')
print(f"{'Portal':<26}{'ASES':>7}{'AIM':>6}{'pág':>5}{'crit/pág':>9}{'erros_sec':>11}")
for t in tarefas:
    print(f"{nomes_tarefas[t].replace(chr(10),' '):<26}{ases_score[t]:>7.1f}"
          f"{wave_aim[t]:>6.1f}{n_paginas[t]:>5}{wave_sev[t]['sr_critical']:>9.1f}"
          f"{total_erros[t]:>11}")
