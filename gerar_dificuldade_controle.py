# -*- coding: utf-8 -*-
"""
Distribuição de status de conclusão por tarefa — GRUPO CONTROLE.
Mesmo formato de dificuldade_barras_empilhadas.png, filtrado ao controle (con01-con05).
Serve de linha de base: o controle conclui tudo; só no Mapa (T5) 2/5 precisaram de
assistência. Saída: dificuldade_barras_empilhadas_controle.png
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Carregar dados — apenas o grupo controle
df = pd.read_csv("coleta_dados_pesquisa_v3 - tarefas_execucao.csv")
df = df.dropna(subset=['participante_id', 'tarefa_num', 'status_conclusao'])
df['tarefa_num'] = df['tarefa_num'].astype(int)
df['grupo'] = df['participante_id'].str[:3].map({'exp': 'experimental', 'con': 'controle'})
df = df[df['grupo'] == 'controle']

# Nomes de tarefas (mesmo padrão do projeto)
nomes_tarefas = {
    1: 'T1: Consulta CPF',
    2: 'T2: Painel de Monitoramento',
    3: 'T3: Receita Federal',
    4: 'T4: IBGE Censo',
    5: 'T5: Mapa de Empresas',
}

# Ordem dos status (do melhor ao pior) e cores semafóricas (idênticas ao original)
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
    'sucesso_completo':         '#2ca02c',  # verde
    'sucesso_com_assistencia':  '#a8d96a',  # verde-claro
    'nao_concluida_tempo':      '#ffbb33',  # âmbar
    'nao_concluida_barreira':   '#d62728',  # vermelho
    'nao_realizada':            '#6c757d',  # cinza
}

# Barras empilhadas 100% por tarefa
contagem = (
    df.groupby(['tarefa_num', 'status_conclusao'])
      .size()
      .unstack(fill_value=0)
      .reindex(columns=status_ordem, fill_value=0)
)
total_por_tarefa = contagem.sum(axis=1)
pct = contagem.div(total_por_tarefa, axis=0) * 100

# Ordenar tarefas pela taxa total de sucesso (completo + com assistência),
# desempate por sucesso_completo. Mais difícil embaixo.
score_facilidade = pct['sucesso_completo'] + pct['sucesso_com_assistencia']
ordem_tarefas = (
    pd.DataFrame({'total': score_facilidade, 'completo': pct['sucesso_completo']})
      .sort_values(['total', 'completo'], ascending=[True, True])
      .index.tolist()
)
pct = pct.loc[ordem_tarefas]
labels_y = [nomes_tarefas[t] for t in ordem_tarefas]

fig, ax = plt.subplots(figsize=(13, 6))
esquerda = np.zeros(len(ordem_tarefas))
for status in status_ordem:
    valores = pct[status].values
    ax.barh(
        labels_y, valores, left=esquerda,
        color=status_cores[status], edgecolor='white', linewidth=1,
        label=status_labels[status],
    )
    for i, v in enumerate(valores):
        if v >= 8:
            ax.text(
                esquerda[i] + v / 2, i, f'{v:.0f}%',
                ha='center', va='center', fontsize=14,
                fontweight='bold', color='white',
            )
    esquerda += valores

# Anotação com N à direita
for i, t in enumerate(ordem_tarefas):
    ax.text(
        101, i, f'n={int(total_por_tarefa[t])}',
        ha='left', va='center', fontsize=12, color='dimgray',
    )

ax.set_xlim(0, 108)
ax.set_xlabel('% de execuções', size=11)
ax.set_title(
    'Distribuição de status de conclusão por tarefa — grupo controle\n'
    '(linha de base: concluiu todas as tarefas; só o Mapa exigiu assistência)',
    size=15, fontweight='bold', pad=15,
)
ax.set_axisbelow(True)
ax.grid(axis='x', linestyle='--', alpha=0.4)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(
    loc='lower center', bbox_to_anchor=(0.5, -0.22),
    ncol=3, frameon=False, fontsize=10,
)
plt.tight_layout()
plt.savefig('dificuldade_barras_empilhadas_controle.png', dpi=300, bbox_inches='tight')
print("Salvo: dificuldade_barras_empilhadas_controle.png")
print("\nComposição (%) por tarefa (controle):")
print(pct.round(0).astype(int))
