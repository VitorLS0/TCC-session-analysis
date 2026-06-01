import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

# Carregar dados
df = pd.read_csv("coleta_dados_pesquisa_v3 - tarefas_execucao.csv")
df = df.dropna(subset=['participante_id', 'tarefa_num', 'status_conclusao'])
df['tarefa_num'] = df['tarefa_num'].astype(int)

# Nomes de tarefas (mesmo padrão do main.py)
nomes_tarefas = {
    1: 'T1: Consulta CPF',
    2: 'T2: Painel de Monitoramento',
    3: 'T3: Receita Federal',
    4: 'T4: IBGE Censo',
    5: 'T5: Mapa de Empresas',
}

# Ordem dos status (do melhor ao pior) e cores semafóricas
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

# ============================================================
# GRÁFICO 1 — Barras empilhadas 100% por tarefa
# ============================================================
contagem = (
    df.groupby(['tarefa_num', 'status_conclusao'])
      .size()
      .unstack(fill_value=0)
      .reindex(columns=status_ordem, fill_value=0)
)
total_por_tarefa = contagem.sum(axis=1)
pct = contagem.div(total_por_tarefa, axis=0) * 100

# Ordenar tarefas pela taxa total de sucesso (completo + com assistência),
# usando sucesso_completo como critério de desempate. Mais difícil embaixo.
score_facilidade = pct['sucesso_completo'] + pct['sucesso_com_assistencia']
ordem_tarefas = (
    pd.DataFrame({'total': score_facilidade, 'completo': pct['sucesso_completo']})
      .sort_values(['total', 'completo'], ascending=[True, True])
      .index.tolist()
)
pct = pct.loc[ordem_tarefas]
labels_y = [nomes_tarefas[t] for t in ordem_tarefas]

fig1, ax1 = plt.subplots(figsize=(13, 6))
esquerda = np.zeros(len(ordem_tarefas))
for status in status_ordem:
    valores = pct[status].values
    ax1.barh(
        labels_y, valores, left=esquerda,
        color=status_cores[status], edgecolor='white', linewidth=1,
        label=status_labels[status],
    )
    # Rótulo dentro do segmento (só se >= 8%)
    for i, v in enumerate(valores):
        if v >= 8:
            ax1.text(
                esquerda[i] + v / 2, i, f'{v:.0f}%',
                ha='center', va='center', fontsize=14,
                fontweight='bold', color='white',
            )
    esquerda += valores

# Anotação com N à direita
for i, t in enumerate(ordem_tarefas):
    ax1.text(
        101, i, f'n={int(total_por_tarefa[t])}',
        ha='left', va='center', fontsize=12, color='dimgray',
    )

ax1.set_xlim(0, 108)
ax1.set_xlabel('% de execuções', size=11)
ax1.set_title(
    'Distribuição de status de conclusão por tarefa\n(ordenado da mais difícil à mais fácil)',
    size=15, fontweight='bold', pad=15,
)
ax1.set_axisbelow(True)
ax1.grid(axis='x', linestyle='--', alpha=0.4)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.legend(
    loc='lower center', bbox_to_anchor=(0.5, -0.22),
    ncol=3, frameon=False, fontsize=10,
)
plt.tight_layout()
plt.savefig('dificuldade_barras_empilhadas.png', dpi=300, bbox_inches='tight')
print("Gráfico 1 salvo: dificuldade_barras_empilhadas.png")

# ============================================================
# GRÁFICO 2 — Heatmap participante × tarefa colorido por status
# ============================================================
participantes = sorted(df['participante_id'].unique())
tarefas = [1, 2, 3, 4, 5]

# Mapear status para índice numérico
status_idx = {s: i for i, s in enumerate(status_ordem)}
matriz = np.full((len(participantes), len(tarefas)), np.nan)
for _, row in df.iterrows():
    i = participantes.index(row['participante_id'])
    j = tarefas.index(row['tarefa_num'])
    matriz[i, j] = status_idx[row['status_conclusao']]

cmap = ListedColormap([status_cores[s] for s in status_ordem])
norm = BoundaryNorm(np.arange(-0.5, len(status_ordem) + 0.5, 1), cmap.N)

fig2, ax2 = plt.subplots(figsize=(10, 6))
im = ax2.imshow(matriz, cmap=cmap, norm=norm, aspect='auto')

# Texto em cada célula com o status abreviado
status_abrev = {
    'sucesso_completo': 'OK',
    'sucesso_com_assistencia': 'OK*',
    'nao_concluida_tempo': 'TEMPO',
    'nao_concluida_barreira': 'BARRA.',
    'nao_realizada': '—',
}
for i in range(len(participantes)):
    for j in range(len(tarefas)):
        if not np.isnan(matriz[i, j]):
            status_nome = status_ordem[int(matriz[i, j])]
            ax2.text(
                j, i, status_abrev[status_nome],
                ha='center', va='center', fontsize=9,
                fontweight='bold', color='white',
            )

ax2.set_xticks(range(len(tarefas)))
ax2.set_xticklabels([nomes_tarefas[t].replace(': ', ':\n') for t in tarefas], fontsize=9)
ax2.set_yticks(range(len(participantes)))
ax2.set_yticklabels(participantes, fontsize=10)
ax2.set_title(
    'Status de conclusão por participante e tarefa',
    size=15, fontweight='bold', pad=15,
)

# Linhas de grade entre células
ax2.set_xticks(np.arange(-0.5, len(tarefas), 1), minor=True)
ax2.set_yticks(np.arange(-0.5, len(participantes), 1), minor=True)
ax2.grid(which='minor', color='white', linewidth=2)
ax2.tick_params(which='minor', length=0)

# Legenda manual
handles = [Patch(facecolor=status_cores[s], label=status_labels[s]) for s in status_ordem]
plt.tight_layout()
fig2.subplots_adjust(bottom=0.28)
fig2.legend(
    handles=handles, loc='lower center', bbox_to_anchor=(0.5, 0.01),
    ncol=3, frameon=False, fontsize=10,
)
plt.savefig('dificuldade_heatmap.png', dpi=300, bbox_inches='tight')
print("Gráfico 2 salvo: dificuldade_heatmap.png")
