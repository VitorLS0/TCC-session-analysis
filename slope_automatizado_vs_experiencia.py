import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# 1) Carregar dados automatizados (WAVE + ASES) por tarefa
# ============================================================
wave_files = {
    1: 'output-wave-analysis/T1/cpf-wave-summary.csv',
    2: 'output-wave-analysis/T2/monitor-serv-wave-summary.csv',
    3: 'output-wave-analysis/T3/receita-federal-wave-summary.csv',
    4: 'output-wave-analysis/T4/censo-wave-summary.csv',
    5: 'output-wave-analysis/T5/mapa-emp-wave-summary.csv',
}

with open('ases-data.json', 'r', encoding='utf-8') as f:
    ases_raw = json.load(f)

# Mapa fluxo ASES -> tarefa_num
ases_flow_to_tarefa = {
    'ConsultarCPF': 1,
    'ConsultaMonitoramentoServicos': 2,
    'BuscaUnidadesAtendimento': 3,
    'ConsultaCenso': 4,
    'ConsultaMapaDeEMpresas': 5,
}

# Média do aim_score WAVE (0–10, maior = melhor) por tarefa
wave_aim_por_tarefa = {}
for t, path in wave_files.items():
    df_w = pd.read_csv(path)
    wave_aim_por_tarefa[t] = df_w['aim_score'].mean()

# Média do score ASES (0–100, maior = melhor) por tarefa
ases_score_por_tarefa = {}
for flow, paginas in ases_raw['flows'].items():
    t = ases_flow_to_tarefa[flow]
    ases_score_por_tarefa[t] = np.mean([p['score'] for p in paginas])

# Score automatizado composto: média de (wave/10) e (ases/100), em 0–1.
# Maior = MELHOR acessibilidade segundo as ferramentas.
auto_score = {}
for t in range(1, 6):
    w_norm = wave_aim_por_tarefa[t] / 10.0
    a_norm = ases_score_por_tarefa[t] / 100.0
    auto_score[t] = (w_norm + a_norm) / 2.0

# ============================================================
# 2) Carregar dados de experiência real por tarefa
# ============================================================
df_asq = pd.read_csv('coleta_dados_pesquisa_v3 - asq_nasatlx.csv')
df_tar = pd.read_csv('coleta_dados_pesquisa_v3 - tarefas_execucao.csv')
df_tar = df_tar.dropna(subset=['participante_id', 'tarefa_num', 'status_conclusao'])
df_tar['tarefa_num'] = df_tar['tarefa_num'].astype(int)

def br_to_float(x):
    if pd.isna(x):
        return np.nan
    return pd.to_numeric(str(x).replace(',', '.'), errors='coerce')

df_asq['asq_score_medio'] = df_asq['asq_score_medio'].apply(br_to_float)
df_asq['tlx_score_medio'] = df_asq['tlx_score_medio'].apply(br_to_float)
df_asq['tarefa_num'] = pd.to_numeric(df_asq['tarefa_num'], errors='coerce')

statuses_falha = {'nao_concluida_barreira', 'nao_concluida_tempo', 'nao_realizada'}

# Dificuldade composta: TLX/20 + (7-ASQ)/6 + taxa_falha — média em 0–1.
# Maior = PIOR experiência real.
exp_difficulty = {}
for t in range(1, 6):
    tlx_med = df_asq.loc[df_asq['tarefa_num'] == t, 'tlx_score_medio'].mean()
    asq_med = df_asq.loc[df_asq['tarefa_num'] == t, 'asq_score_medio'].mean()
    sub = df_tar[df_tar['tarefa_num'] == t]
    taxa_falha = sub['status_conclusao'].isin(statuses_falha).mean()

    tlx_norm = tlx_med / 20.0
    asq_inv = (7 - asq_med) / 6.0
    exp_difficulty[t] = np.nanmean([tlx_norm, asq_inv, taxa_falha])

# ============================================================
# 3) Ranquear (1 = pior, 5 = melhor)
# ============================================================
# Automatizado: menor auto_score = pior acessibilidade
auto_ranks = pd.Series(auto_score).rank(ascending=True, method='min').astype(int)
# Experiência: maior exp_difficulty = pior experiência
exp_ranks = pd.Series(exp_difficulty).rank(ascending=False, method='min').astype(int)

# ============================================================
# 4) Slope chart
# ============================================================
nomes_tarefas = {
    1: 'T1: Consulta CPF',
    2: 'T2: Painel de Monitoramento',
    3: 'T3: Receita Federal',
    4: 'T4: IBGE Censo',
    5: 'T5: Mapa de Empresas',
}
cores = {
    1: '#ff7f0e', 2: '#2ca02c', 3: '#d62728', 4: '#9467bd', 5: '#8c564b',
}

fig, ax = plt.subplots(figsize=(13, 7.5))

x_esq, x_dir = 0.0, 1.0
y_pior, y_melhor = 5, 1  # 1 em cima (pior)

for t in range(1, 6):
    y1 = 6 - auto_ranks[t]   # converte rank em coord y (rank 1 -> y=5 topo)
    y2 = 6 - exp_ranks[t]
    diff = abs(auto_ranks[t] - exp_ranks[t])

    # Estilo da linha indica concordância
    lw = 2.5 + diff * 1.2
    alpha = 0.55 if diff == 0 else 0.9
    ls = '-' if diff <= 1 else '--'

    ax.plot([x_esq, x_dir], [y1, y2],
            color=cores[t], linewidth=lw, alpha=alpha, linestyle=ls,
            solid_capstyle='round', zorder=2)

    # Pontos
    ax.scatter([x_esq, x_dir], [y1, y2],
               s=320, color=cores[t], edgecolors='white',
               linewidths=2.2, zorder=3)

    # Rótulo à esquerda
    ax.text(x_esq - 0.05, y1, nomes_tarefas[t],
            ha='right', va='center', fontsize=14, fontweight='bold',
            color=cores[t])
    ax.text(x_esq - 0.05, y1 - 0.27,
            f'WAVE {wave_aim_por_tarefa[t]:.1f}/10  ·  ASES {ases_score_por_tarefa[t]:.0f}/100',
            ha='right', va='center', fontsize=12, color='#222')

    # Rótulo à direita
    ax.text(x_dir + 0.05, y2, nomes_tarefas[t],
            ha='left', va='center', fontsize=14, fontweight='bold',
            color=cores[t])
    tlx_med = df_asq.loc[df_asq['tarefa_num'] == t, 'tlx_score_medio'].mean()
    asq_med = df_asq.loc[df_asq['tarefa_num'] == t, 'asq_score_medio'].mean()
    sub = df_tar[df_tar['tarefa_num'] == t]
    pct_falha = sub['status_conclusao'].isin(statuses_falha).mean() * 100
    ax.text(x_dir + 0.05, y2 - 0.27,
            f'TLX {tlx_med:.1f}  ·  ASQ {asq_med:.1f}  ·  falha {pct_falha:.0f}%',
            ha='left', va='center', fontsize=12, color='#222')

    # Marca o rank em cada ponta (dentro do círculo)
    ax.text(x_esq, y1, str(int(auto_ranks[t])),
            ha='center', va='center', fontsize=12, fontweight='bold', color='white', zorder=4)
    ax.text(x_dir, y2, str(int(exp_ranks[t])),
            ha='center', va='center', fontsize=12, fontweight='bold', color='white', zorder=4)

# Cabeçalhos das colunas
ax.text(x_esq, 5.75, 'WAVE + ASES\n(análise automatizada)',
        ha='center', va='bottom', fontsize=16, fontweight='bold', color='#111')
ax.text(x_dir, 5.75, 'NASA-TLX + ASQ + % falha\n(experiência real)',
        ha='center', va='bottom', fontsize=16, fontweight='bold', color='#111')

# Indicador de direção do ranking
ax.annotate('', xy=(-0.75, 5.0), xytext=(-0.75, 1.0),
            arrowprops=dict(arrowstyle='->', color='#444', lw=1.6))
ax.text(-0.78, 5.05, 'pior', ha='right', va='center',
        fontsize=12, color='#222', style='italic', fontweight='bold')
ax.text(-0.78, 0.95, 'melhor', ha='right', va='center',
        fontsize=12, color='#222', style='italic', fontweight='bold')

# Layout
ax.set_xlim(-0.95, 1.75)
ax.set_ylim(0.3, 6.4)
ax.axis('off')

# Legenda de leitura
legenda_txt = (
    'Espessura da linha cresce com a discrepância de ranking.\n'
    'Linha tracejada: diferença de 2+ posições entre os rankings.'
)
ax.text(0.5, -0.05, legenda_txt, transform=ax.transAxes,
        ha='center', va='top', fontsize=12, color='#222', style='italic')

plt.tight_layout()
plt.savefig('slope_automatizado_vs_experiencia.png', dpi=300, bbox_inches='tight')
print("Slope chart salvo: slope_automatizado_vs_experiencia.png\n")

# Resumo no console
print(f"{'Tarefa':<28} {'WAVE':>6} {'ASES':>6} {'Auto':>6} {'Rank':>4}   {'TLX':>5} {'ASQ':>5} {'Falha%':>7} {'Difc':>6} {'Rank':>4}   {'dRank':>3}")
print('-' * 110)
for t in range(1, 6):
    tlx_med = df_asq.loc[df_asq['tarefa_num'] == t, 'tlx_score_medio'].mean()
    asq_med = df_asq.loc[df_asq['tarefa_num'] == t, 'asq_score_medio'].mean()
    sub = df_tar[df_tar['tarefa_num'] == t]
    pct_falha = sub['status_conclusao'].isin(statuses_falha).mean() * 100
    delta = int(auto_ranks[t]) - int(exp_ranks[t])
    print(
        f'{nomes_tarefas[t]:<28} '
        f'{wave_aim_por_tarefa[t]:>6.2f} {ases_score_por_tarefa[t]:>6.1f} '
        f'{auto_score[t]:>6.3f} {int(auto_ranks[t]):>4}   '
        f'{tlx_med:>5.1f} {asq_med:>5.2f} {pct_falha:>6.0f}% '
        f'{exp_difficulty[t]:>6.3f} {int(exp_ranks[t]):>4}   '
        f'{delta:>+3d}'
    )
