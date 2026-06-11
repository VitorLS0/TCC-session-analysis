# -*- coding: utf-8 -*-
"""
G3 — Correspondência teoria × prática (os gráficos mais importantes).
Gera:
  g3_conformidade_vs_experiencia.png  (Q3.1)

Cruza a conformidade automática (ASES + WAVE/AIM) com a acessibilidade real do
usuário de leitor de tela, por portal, evidenciando onde alta conformidade
coexiste com baixa acessibilidade prática.

Duas medidas de experiência são mostradas porque uma sozinha pode mascarar a
barreira: no Painel, o experimental completa 77% dos OBJETIVOS de forma autônoma,
mas 0% das TAREFAS chegam ao fim (todos esbarram numa barreira). Mostrar as duas
é mais honesto.

n pequeno (5/grupo; T5 experimental n=3): leitura descritiva/exploratória.
SEM teste de significância, SEM correlação, SEM linha de regressão.
"""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ------------------------------------------------------------------
nomes_curto = {1: 'T1: CPF\n(Receita)', 2: 'T2: Painel de\nMonitoramento',
               3: 'T3: Receita Fed.\n(Unidades)', 4: 'T4: Censo\n(IBGE)',
               5: 'T5: Mapa de\nEmpresas'}
COR_CON = '#3a7ca5'
COR_EXP = '#d1495b'
COR_CONF = '#8d99ae'   # ferramenta (conformidade)
COR_AIM = '#41597a'


def br_to_float(x):
    if pd.isna(x):
        return np.nan
    return pd.to_numeric(str(x).replace(',', '.').replace('%', ''), errors='coerce')


# ---------- Conformidade automática ----------
with open('ases-data.json', encoding='utf-8') as f:
    ases_raw = json.load(f)
flow_t = {'ConsultarCPF': 1, 'ConsultaMonitoramentoServicos': 2,
          'BuscaUnidadesAtendimento': 3, 'ConsultaCenso': 4, 'ConsultaMapaDeEMpresas': 5}
ases_score = {flow_t[fl]: float(np.mean([p['score'] for p in pg]))
              for fl, pg in ases_raw['flows'].items()}
n_pag = {flow_t[fl]: len(pg) for fl, pg in ases_raw['flows'].items()}

wave_files = {1: 'output-wave-analysis/T1/cpf-wave-summary.csv',
              2: 'output-wave-analysis/T2/monitor-serv-wave-summary.csv',
              3: 'output-wave-analysis/T3/receita-federal-wave-summary.csv',
              4: 'output-wave-analysis/T4/censo-wave-summary.csv',
              5: 'output-wave-analysis/T5/mapa-emp-wave-summary.csv'}
aim = {t: float(pd.read_csv(p)['aim_score'].mean()) for t, p in wave_files.items()}

# ---------- Experiência real (experimental) ----------
dt = pd.read_csv('coleta_dados_pesquisa_v3 - tarefas_execucao.csv')
dt = dt.dropna(subset=['participante_id', 'tarefa_num', 'status_conclusao'])
dt['tarefa_num'] = dt['tarefa_num'].astype(int)
dt['grupo'] = dt['participante_id'].str[:3].map({'exp': 'experimental', 'con': 'controle'})
dt['taxa_aut'] = dt['taxa_conclusao_autonoma'].apply(br_to_float)
de = dt[dt.grupo == 'experimental']

concl_aut = de.groupby('tarefa_num')['taxa_aut'].mean().to_dict()       # % objetivos autônomos
n_aut = de.dropna(subset=['taxa_aut']).groupby('tarefa_num').size().to_dict()
tarefa_ok = {t: 100 * (de[de.tarefa_num == t]['status_conclusao'] == 'sucesso_completo').mean()
             for t in range(1, 6)}                                       # % tarefas concluídas

# Controle: conclusão autônoma (% sucesso_completo) — linha de base
concl_con = {t: 100 * (dt[(dt.grupo == 'controle') & (dt.tarefa_num == t)]['status_conclusao']
                       == 'sucesso_completo').mean() for t in range(1, 6)}

# Ordena por conformidade (ASES) decrescente — esquerda = "mais conforme"
ordem = sorted(range(1, 6), key=lambda t: -ases_score[t])
x = np.arange(len(ordem))

# ==================================================================
fig, (axA, axB) = plt.subplots(2, 1, figsize=(13, 10.5), sharex=True,
                               gridspec_kw={'height_ratios': [1, 1.25], 'hspace': 0.12})

# ---------- Painel A: conformidade automática ----------
vals_ases = [ases_score[t] for t in ordem]
vals_aim10 = [aim[t] * 10 for t in ordem]
b = axA.bar(x, vals_ases, 0.5, color=COR_CONF, edgecolor='black', linewidth=0.6,
            label='ASES (0–100)')
for xi, t in zip(x, ordem):
    axA.text(xi, ases_score[t] + 1.5, f'{ases_score[t]:.0f}', ha='center', va='bottom',
             fontsize=11, fontweight='bold', color='#3a3f47')
axA.scatter(x, vals_aim10, s=200, marker='D', color=COR_AIM, edgecolor='white',
            linewidths=1.5, zorder=3, label='WAVE/AIM (0–10, ×10)')
for xi, t in zip(x, ordem):
    axA.text(xi, aim[t] * 10 - 7, f'AIM {aim[t]:.1f}', ha='center', va='top',
             fontsize=9.5, fontweight='bold', color=COR_AIM)
axA.axhspan(80, 100, color='#2ca02c', alpha=0.06, zorder=0)
axA.text(len(ordem) - 0.5, 99, 'faixa de "boa conformidade"', ha='right', va='top',
         fontsize=9, color='#2ca02c', style='italic')
axA.set_ylim(0, 108)
axA.set_yticks(range(0, 101, 20))
axA.set_ylabel('Conformidade automática   ↑ melhor', fontsize=12, fontweight='bold')
axA.set_title('As ferramentas automáticas indicam conformidade ALTA em todos os portais',
              fontsize=13, fontweight='bold', pad=10, color='#3a3f47')
axA.grid(axis='y', linestyle='--', alpha=0.4)
axA.set_axisbelow(True)
axA.legend(loc='lower left', fontsize=10, framealpha=0.9)
axA.spines['top'].set_visible(False)
axA.spines['right'].set_visible(False)

# ---------- Painel B: acessibilidade real (usuário de leitor de tela) ----------
w = 0.36
v_obj = [concl_aut[t] for t in ordem]
v_tar = [tarefa_ok[t] for t in ordem]
b1 = axB.bar(x - w / 2, v_obj, w, color=COR_EXP, edgecolor='black', linewidth=0.6,
             label='Objetivos concluídos de forma autônoma (%)')
b2 = axB.bar(x + w / 2, v_tar, w, color='#7a2233', edgecolor='black', linewidth=0.6,
             hatch='//', label='Tarefas concluídas com êxito (sucesso completo, %)')
for xi, t in zip(x, ordem):
    axB.text(xi - w / 2, concl_aut[t] + 1.5, f'{concl_aut[t]:.0f}', ha='center', va='bottom',
             fontsize=10.5, fontweight='bold', color=COR_EXP)
    axB.text(xi + w / 2, tarefa_ok[t] + 1.5, f'{tarefa_ok[t]:.0f}', ha='center', va='bottom',
             fontsize=10.5, fontweight='bold', color='#7a2233')

# Linha de base do controle (concluiu todas as tarefas)
axB.axhline(100, color=COR_CON, linestyle='--', linewidth=1.6, alpha=0.9)
axB.text(len(ordem) - 0.5, 101.5, 'controle: concluiu todas as tarefas (linha de base)',
         ha='right', va='bottom', fontsize=9.5, color=COR_CON, style='italic', fontweight='bold')

axB.set_ylim(0, 115)
axB.set_yticks(range(0, 101, 20))
axB.set_ylabel('Acessibilidade real (experimental)   ↑ melhor', fontsize=12, fontweight='bold')
axB.set_title('…mas, para o usuário de leitor de tela, a acessibilidade real desaba',
              fontsize=13, fontweight='bold', pad=10, color=COR_EXP)
axB.set_xticks(x)
axB.set_xticklabels([nomes_curto[t] for t in ordem], fontsize=10.5)
axB.grid(axis='y', linestyle='--', alpha=0.4)
axB.set_axisbelow(True)
axB.legend(loc='upper center', fontsize=9.5, framealpha=0.95)
axB.spines['top'].set_visible(False)
axB.spines['right'].set_visible(False)

# n no experimental (T5 = 3) — acima do grupo de barras p/ não colidir com o eixo
for xi, t in zip(x, ordem):
    nn = int(n_aut.get(t, 0))
    if nn < 5:
        axB.text(xi, 9, f'n={nn}', ha='center', va='bottom', fontsize=9,
                 color='#444', fontweight='bold')

# ---------- Callouts da narrativa (falsos negativos vs. lacuna menor) ----------
pos = {t: xi for xi, t in zip(x, ordem)}
# Painel e Mapa: alta conformidade, experiência péssima (tarefa = 0%)
for t in (2, 5):
    axB.annotate('conformidade ~96,\ntarefa 0% concluída',
                 xy=(pos[t] + w / 2, tarefa_ok[t]), xytext=(pos[t], 52),
                 ha='center', fontsize=9, fontweight='bold', color='#7a0177',
                 bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#7a0177', alpha=0.85),
                 arrowprops=dict(arrowstyle='->', color='#7a0177', lw=1.5))
# Censo: menor conformidade, mas barreira menor que a do Mapa
axB.annotate('menor conformidade (86),\nmas 60% das tarefas\nconcluídas: barreira\nmenor que a do Mapa',
             xy=(pos[4] + w / 2, tarefa_ok[4]), xytext=(pos[4] - 0.05, 84),
             ha='center', fontsize=8.6, fontweight='bold', color='#1f5e1f',
             bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#1f5e1f', alpha=0.85),
             arrowprops=dict(arrowstyle='->', color='#1f5e1f', lw=1.5))

fig.suptitle('G3 · Conformidade automática × acessibilidade real, por portal\n'
             'Onde a teoria (ferramentas) e a prática (usuário de leitor de tela) discordam',
             fontsize=15, fontweight='bold', y=0.98)
fig.text(0.5, 0.055,
         'Portais ordenados pela conformidade ASES (decrescente). Conformidade alta convive com '
         'acessibilidade real baixa — sobretudo no Painel e no Mapa (conformidade ~96, 0% de tarefas '
         'concluídas pelo leitor de tela). No Painel, 77% dos objetivos são alcançados, mas a tarefa '
         'não chega ao fim: uma única métrica pode mascarar a barreira.',
         ha='center', fontsize=9.5, color='#444', style='italic', wrap=True)
fig.text(0.5, 0.02,
         'n=5 por grupo (T5 experimental n=3). Leitura descritiva/exploratória — sem testes de '
         'significância, correlação ou regressão.',
         ha='center', fontsize=9, color='#666', style='italic')
plt.savefig('g3_conformidade_vs_experiencia.png', dpi=300, bbox_inches='tight')
plt.close(fig)
print('Salvo: g3_conformidade_vs_experiencia.png')

print('\n[G3] ordem por ASES desc:', [nomes_curto[t].split(chr(10))[0] for t in ordem])
print(f"{'Portal':<14}{'ASES':>6}{'AIM':>6}{'objAut%':>9}{'tarefaOK%':>10}{'ctrlOK%':>9}")
for t in ordem:
    print(f"{nomes_curto[t].split(chr(10))[0]:<14}{ases_score[t]:>6.1f}{aim[t]:>6.1f}"
          f"{concl_aut[t]:>9.0f}{tarefa_ok[t]:>10.0f}{concl_con[t]:>9.0f}")
