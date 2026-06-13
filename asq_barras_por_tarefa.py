# -*- coding: utf-8 -*-
"""
ASQ por tarefa — barras agrupadas Experimental vs Controle.
Mesma grade 2x3 do radar TLX (main.py), mas para o ASQ:
  cada painel = uma tarefa; barras = Q1, Q2, Q3 e Média; cor = grupo.
ASQ recalculado das 3 questões (Q1-Q3), escala 1-7 (↑ melhor),
conforme o padrão do projeto. Q4/Q5 (só experimental) não entram.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

df = pd.read_csv("coleta_dados_pesquisa_v3 - asq_nasatlx.csv")

# Questões do ASQ que entram na média (1-7, maior = melhor)
asq_cols = ['asq_q1_facil', 'asq_q2_tempo', 'asq_q3_nao_perdido']
for c in asq_cols:
    df[c] = pd.to_numeric(df[c], errors='coerce')

# Grupo pelo prefixo de participante_id (exp / con); descarta linhas vazias
df = df[df['participante_id'].notna()].copy()
df['grupo'] = df['participante_id'].str.slice(0, 3)
# ASQ por execução = média das 3 questões (robusto a NA)
df['asq_medio'] = df[asq_cols].mean(axis=1)

nomes_tarefas = {
    1: 'T1: Consulta CPF',
    2: 'T2: Painel de Monitoramento',
    3: 'T3: Receita Federal',
    4: 'T4: IBGE Censo',
    5: 'T5: Mapa de Empresas',
}
cor_grupo = {'exp': '#d1495b', 'con': '#3a7ca5'}
nome_grupo = {'exp': 'Experimental', 'con': 'Controle'}

# Categorias no eixo x de cada painel
cats = ['Q1\nFácil', 'Q2\nTempo', 'Q3\nNão\nperdido', 'Média']
xpos = np.arange(len(cats))
width = 0.38

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for i in range(5):
    t = i + 1
    ax = axes[i]
    sub = df[df['tarefa_num'] == t]

    ns = {}
    for j, g in enumerate(['exp', 'con']):
        sg = sub[sub['grupo'] == g]
        ns[g] = int(sg['asq_medio'].notna().sum())
        vals = [sg['asq_q1_facil'].mean(), sg['asq_q2_tempo'].mean(),
                sg['asq_q3_nao_perdido'].mean(), sg['asq_medio'].mean()]
        offset = (j - 0.5) * width
        # barras ancoradas no mínimo da escala ASQ (1), não em 0
        alturas = [v - 1 if not np.isnan(v) else np.nan for v in vals]
        bars = ax.bar(xpos + offset, alturas, width, bottom=1,
                      color=cor_grupo[g], edgecolor='black', linewidth=0.6,
                      label=nome_grupo[g], zorder=3)
        for b, v in zip(bars, vals):
            if not np.isnan(v):
                ax.text(b.get_x() + b.get_width() / 2, v + 0.12, f'{v:.1f}',
                        ha='center', va='bottom', fontsize=9.5,
                        fontweight='bold', color=cor_grupo[g])

    ax.axhline(4, color='gray', linestyle=':', linewidth=1, zorder=1)  # ponto médio da escala
    ax.set_ylim(1, 7.6)
    ax.set_yticks(range(1, 8))
    ax.set_xticks(xpos)
    ax.set_xticklabels(cats, fontsize=11)
    ax.set_ylabel('ASQ (1–7)  ↑ melhor', fontsize=11)
    ax.set_title(f'{nomes_tarefas[t]}   (exp n={ns["exp"]} · con n={ns["con"]})',
                 fontsize=13, fontweight='bold', pad=8)
    ax.grid(axis='y', linestyle='--', alpha=0.35, zorder=0)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# 6º espaço: legenda
fig.delaxes(axes[5])
leg_handles = [Patch(facecolor=cor_grupo['exp'], edgecolor='black', label='Experimental (leitor de tela)'),
               Patch(facecolor=cor_grupo['con'], edgecolor='black', label='Controle'),
               plt.Line2D([0], [0], color='gray', linestyle=':', label='Ponto médio da escala (4)')]
fig.legend(handles=leg_handles, loc='center', bbox_to_anchor=(0.83, 0.27),
           fontsize=13, frameon=True)
fig.text(0.83, 0.13,
         'ASQ = média das questões Q1–Q3 (1–7, maior = melhor).\n'
         'n = execuções por grupo; T5 experimental tem n=3.',
         ha='center', fontsize=10, color='#444', style='italic')

plt.suptitle('ASQ por Tarefa — Experimental vs Controle (Q1–Q3 e média)',
             size=18, fontweight='bold', y=1.02)
plt.tight_layout()
fig.subplots_adjust(hspace=0.4)
plt.savefig('asq_barras_por_tarefa.png', dpi=300, bbox_inches='tight')
plt.close(fig)
print('Salvo: asq_barras_por_tarefa.png')

# Resumo no console
print('\n[ASQ] média por tarefa/grupo (1-7):')
for t in range(1, 6):
    sub = df[df['tarefa_num'] == t]
    e = sub[sub['grupo'] == 'exp']['asq_medio'].mean()
    c = sub[sub['grupo'] == 'con']['asq_medio'].mean()
    print(f'  {nomes_tarefas[t]:<28} exp {e:.2f} · con {c:.2f}')
