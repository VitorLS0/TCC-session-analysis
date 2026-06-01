import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Carregar os dados
df_asq = pd.read_csv("coleta_dados_pesquisa_v3 - asq_nasatlx.csv")
df_tar = pd.read_csv("coleta_dados_pesquisa_v3 - tarefas_execucao.csv")

# Converter tempo_total (HH:MM:SS) para minutos
def tempo_para_minutos(t):
    if pd.isna(t) or str(t).strip() == '':
        return np.nan
    try:
        h, m, s = str(t).split(':')
        return int(h) * 60 + int(m) + int(s) / 60
    except Exception:
        return np.nan

df_tar['tempo_min'] = df_tar['tempo_total'].apply(tempo_para_minutos)

# Converter scores (CSV usa vírgula como separador decimal)
def br_to_float(x):
    if pd.isna(x):
        return np.nan
    return pd.to_numeric(str(x).replace(',', '.'), errors='coerce')

df_asq['asq_score_medio'] = df_asq['asq_score_medio'].apply(br_to_float)
df_asq['tlx_score_medio'] = df_asq['tlx_score_medio'].apply(br_to_float)
df_tar['tarefa_num'] = pd.to_numeric(df_tar['tarefa_num'], errors='coerce')

# Calcular médias por tarefa
tempo_medio = df_tar.groupby('tarefa_num')['tempo_min'].mean()
tlx_medio = df_asq.groupby('tarefa_num')['tlx_score_medio'].mean()
asq_medio = df_asq.groupby('tarefa_num')['asq_score_medio'].mean()

# Nomes das tarefas (mesmos do main.py)
nomes_tarefas = {
    1: 'T1: Consulta CPF',
    2: 'T2: Painel de\nMonitoramento',
    3: 'T3: Receita Federal',
    4: 'T4: IBGE Censo',
    5: 'T5: Mapa de Empresas'
}

# Cores para cada tarefa (mesmas do main.py)
cores = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

tarefas = [1, 2, 3, 4, 5]
labels_tarefas = [nomes_tarefas[t] for t in tarefas]

# Coletar valores na ordem das tarefas
tempos = [tempo_medio.get(t, np.nan) for t in tarefas]
tlxs = [tlx_medio.get(t, np.nan) for t in tarefas]
asqs = [asq_medio.get(t, np.nan) for t in tarefas]

# Criar figura com 3 subplots (1 linha, 3 colunas)
fig, axes = plt.subplots(1, 3, figsize=(16, 6))

metricas = [
    ('Tempo Médio de Execução', tempos, 'Minutos', axes[0]),
    ('NASA-TLX Médio', tlxs, 'Score (0-20)', axes[1]),
    ('ASQ Médio', asqs, 'Score (1-7)', axes[2]),
]

for titulo, valores, ylabel, ax in metricas:
    barras = ax.bar(labels_tarefas, valores, color=cores, edgecolor='black', linewidth=0.8)

    # Anotar valor no topo de cada barra (ou "N/D" se ausente)
    for barra, val in zip(barras, valores):
        if not np.isnan(val):
            ax.text(
                barra.get_x() + barra.get_width() / 2,
                barra.get_height(),
                f'{val:.2f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold'
            )
        else:
            ax.text(
                barra.get_x() + barra.get_width() / 2,
                0,
                'N/D',
                ha='center', va='bottom', fontsize=10,
                fontweight='bold', color='gray', style='italic'
            )

    ax.set_title(titulo, size=13, fontweight='bold', pad=12)
    ax.set_ylabel(ylabel, size=11)
    ax.tick_params(axis='x', labelsize=9, rotation=15)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.set_axisbelow(True)

    # Folga no topo para o rótulo de valor
    valores_validos = [v for v in valores if not np.isnan(v)]
    if valores_validos:
        ax.set_ylim(0, max(valores_validos) * 1.15)

plt.suptitle(
    'Métricas Médias por Tarefa: Tempo, NASA-TLX e ASQ',
    size=18, fontweight='bold', y=1.02
)
plt.tight_layout()

plt.savefig('metricas_por_tarefa.png', dpi=300, bbox_inches='tight')
print("Gráfico de métricas por tarefa gerado com sucesso!")
print("\nResumo:")
print(f"{'Tarefa':<28} {'Tempo (min)':>12} {'NASA-TLX':>10} {'ASQ':>8}")
for t in tarefas:
    nome = nomes_tarefas[t].replace('\n', ' ')
    print(f"{nome:<28} {tempo_medio.get(t, float('nan')):>12.2f} {tlx_medio.get(t, float('nan')):>10.2f} {asq_medio.get(t, float('nan')):>8.2f}")
