# -*- coding: utf-8 -*-
"""
Distribuição de status de conclusão por tarefa — experimental E controle juntos.
Cada tarefa = uma barra dividida: experimental em cima, controle embaixo.
Eixo X = NÚMERO DE PESSOAS (n=5 por grupo), não porcentagem.
Junta dificuldade_barras_empilhadas (experimental) + _controle num só.
Saída: dificuldade_barras_empilhadas_combinado.png
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

df = pd.read_csv("coleta_dados_pesquisa_v3 - tarefas_execucao.csv")
df = df.dropna(subset=['participante_id', 'tarefa_num', 'status_conclusao'])
df['tarefa_num'] = df['tarefa_num'].astype(int)
df['grupo'] = df['participante_id'].str[:3].map({'exp': 'experimental', 'con': 'controle'})

nomes_tarefas = {
    1: 'T1: Consulta CPF',
    2: 'T2: Painel de Monitoramento',
    3: 'T3: Receita Federal',
    4: 'T4: IBGE Censo',
    5: 'T5: Mapa de Empresas',
}
status_ordem = [
    'sucesso_completo',
    'sucesso_com_assistencia',
    'nao_concluida_tempo',
    'nao_concluida_barreira',
    'nao_realizada',
]
status_labels = {
    'sucesso_completo': 'Sucesso completo',
    'sucesso_com_assistencia': 'Sucesso com assistência',
    'nao_concluida_tempo': 'Não concluída (tempo)',
    'nao_concluida_barreira': 'Não concluída (barreira)',
    'nao_realizada': 'Não realizada',
}
status_cores = {
    'sucesso_completo':         '#2ca02c',
    'sucesso_com_assistencia':  '#a8d96a',
    'nao_concluida_tempo':      '#ffbb33',
    'nao_concluida_barreira':   '#d62728',
    'nao_realizada':            '#6c757d',
}


def tabela(grupo):
    """tarefa × status, em CONTAGEM (pessoas), grupo filtrado."""
    sub = df[df['grupo'] == grupo]
    return (sub.groupby(['tarefa_num', 'status_conclusao']).size()
               .unstack(fill_value=0)
               .reindex(index=[1, 2, 3, 4, 5], fill_value=0)
               .reindex(columns=status_ordem, fill_value=0))


cnt = {'experimental': tabela('experimental'), 'controle': tabela('controle')}

# Ordem fixa T1->T5 de cima para baixo (barh: y=0 embaixo, então invertido)
ordem_tarefas = [5, 4, 3, 2, 1]

# Cada tarefa ocupa uma faixa; experimental (cima) e controle (baixo) ENCOSTADOS
OFF = 0.22
BAR_H = 2 * OFF      # = altura -> as duas barras se tocam (sem espaço entre elas)
fig, ax = plt.subplots(figsize=(13, 7.5))
for i, t in enumerate(ordem_tarefas):
    for grupo, sinal, tag in (('experimental', +1, 'Experimental'),
                              ('controle', -1, 'Controle')):
        yc = i + sinal * OFF
        left = 0
        linha = cnt[grupo].loc[t]
        for status in status_ordem:
            v = int(linha[status])
            if v > 0:
                ax.barh(yc, v, left=left, height=BAR_H, color=status_cores[status],
                        edgecolor='white', linewidth=1.2, zorder=3)
                left += v
        # rótulo do grupo à direita das barras
        ax.text(5.12, yc, tag, ha='left', va='center', fontsize=10,
                fontweight='bold', color='#555')

# Linhas verticais a cada participante (1..5): dividem as barras em células = pessoas
for xline in range(1, 6):
    ax.axvline(xline, color='white', lw=1.6, alpha=0.95, zorder=4)

ax.set_yticks(range(len(ordem_tarefas)))
ax.set_yticklabels([nomes_tarefas[t] for t in ordem_tarefas], fontsize=12, fontweight='bold')
ax.set_xlim(0, 6.6)
ax.set_xticks(range(0, 6))
ax.set_xlabel('Número de pessoas (n = 5 por grupo)', size=12, fontweight='bold')
ax.set_ylim(-0.6, len(ordem_tarefas) - 0.4)
ax.set_title('Status de conclusão por tarefa — experimental (cima) vs. controle (baixo)\n'
             '(em número de pessoas; tarefas em ordem T1→T5, de cima para baixo)',
             size=15, fontweight='bold', pad=15)
ax.set_axisbelow(True)
ax.grid(axis='x', linestyle='--', alpha=0.25)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

handles = [Patch(facecolor=status_cores[s], label=status_labels[s]) for s in status_ordem]
ax.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, -0.20),
          ncol=3, frameon=False, fontsize=10)

plt.tight_layout()
plt.savefig('dificuldade_barras_empilhadas_combinado.png', dpi=300, bbox_inches='tight')
print('Salvo: dificuldade_barras_empilhadas_combinado.png')
for g in ('experimental', 'controle'):
    print(f'\n[{g}] contagem por tarefa:')
    print(cnt[g].loc[ordem_tarefas])
