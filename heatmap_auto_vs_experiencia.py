import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

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

ases_flow_to_tarefa = {
    'ConsultarCPF': 1,
    'ConsultaMonitoramentoServicos': 2,
    'BuscaUnidadesAtendimento': 3,
    'ConsultaCenso': 4,
    'ConsultaMapaDeEMpresas': 5,
}

# Agregar WAVE por tarefa
wave_agg = {}
for t, path in wave_files.items():
    df_w = pd.read_csv(path)
    wave_agg[t] = {
        'aim_deficit': 10 - df_w['aim_score'].mean(),  # 0-10 (maior = pior)
        'errors_total': int(df_w['errors'].sum()),
        'alerts_total': int(df_w['alerts'].sum()),
        'criticos_total': int(df_w['sr_critical'].sum()),
    }

# Agregar ASES por tarefa
ases_agg = {}
for flow, paginas in ases_raw['flows'].items():
    t = ases_flow_to_tarefa[flow]
    scores = [p['score'] for p in paginas]
    erros_secao = sum(
        sec['errors'] for p in paginas for sec in p['sections'].values()
    )
    ases_agg[t] = {
        'score_deficit': 100 - np.mean(scores),  # 0-100 (maior = pior)
        'erros_secao_total': erros_secao,
    }

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
df_tar['num_barreiras_observadas'] = pd.to_numeric(
    df_tar['num_barreiras_observadas'], errors='coerce'
)

statuses_falha = {'nao_concluida_barreira', 'nao_concluida_tempo', 'nao_realizada'}

exp_agg = {}
for t in range(1, 6):
    sub_asq = df_asq[df_asq['tarefa_num'] == t]
    sub_tar = df_tar[df_tar['tarefa_num'] == t]
    exp_agg[t] = {
        'tlx': sub_asq['tlx_score_medio'].mean(),
        'asq_inv': 7 - sub_asq['asq_score_medio'].mean(),     # 1-6 (maior = pior)
        'pct_falha': sub_tar['status_conclusao'].isin(statuses_falha).mean() * 100,
        'barreiras_media': sub_tar['num_barreiras_observadas'].mean(),
    }

# ============================================================
# 3) Montar a matriz
# ============================================================
nomes_tarefas = {
    1: 'T1: Consulta CPF',
    2: 'T2: Painel de Monitoramento',
    3: 'T3: Receita Federal',
    4: 'T4: IBGE Censo',
    5: 'T5: Mapa de Empresas',
}

cols_auto = [
    ('WAVE\naim deficit\n(0–10)',     'aim_deficit',     wave_agg, '{:.1f}'),
    ('WAVE errors\n(soma páginas)',   'errors_total',    wave_agg, '{:d}'),
    ('WAVE críticos\n(soma páginas)', 'criticos_total',  wave_agg, '{:d}'),
    ('ASES\nscore deficit\n(0–100)',  'score_deficit',   ases_agg, '{:.1f}'),
]
cols_exp = [
    ('NASA-TLX\n(0–20)',          'tlx',             exp_agg, '{:.1f}'),
    ('ASQ inverso\n(0–6, alto=pior)', 'asq_inv',     exp_agg, '{:.1f}'),
    ('% falha de\nconclusão',     'pct_falha',       exp_agg, '{:.0f}%'),
    ('Barreiras\nobservadas\n(média)', 'barreiras_media', exp_agg, '{:.1f}'),
]

# Ordenar tarefas por dificuldade real (pior em cima)
ordem = sorted(
    range(1, 6), key=lambda t: -exp_agg[t]['pct_falha'] - exp_agg[t]['tlx'] / 20
)

def montar_bloco(cols, ordem):
    raw = np.zeros((len(ordem), len(cols)))
    fmt = [[''] * len(cols) for _ in ordem]
    for j, (label, chave, fonte, formato) in enumerate(cols):
        for i, t in enumerate(ordem):
            val = fonte[t][chave]
            raw[i, j] = val
            fmt[i][j] = formato.format(val) if not pd.isna(val) else 'N/D'
    # Normalização min-max por coluna (0-1, maior = pior)
    norm = np.zeros_like(raw)
    for j in range(raw.shape[1]):
        col = raw[:, j]
        mn, mx = np.nanmin(col), np.nanmax(col)
        if mx > mn:
            norm[:, j] = (col - mn) / (mx - mn)
        else:
            norm[:, j] = 0.0
    return raw, norm, fmt

raw_a, norm_a, fmt_a = montar_bloco(cols_auto, ordem)
raw_e, norm_e, fmt_e = montar_bloco(cols_exp, ordem)

# ============================================================
# 4) Plot — dois blocos lado a lado
# ============================================================
cmap = LinearSegmentedColormap.from_list(
    'badness', ['#f7f7f7', '#fee08b', '#fc8d59', '#d73027', '#7a0177']
)

fig, (axA, axE) = plt.subplots(
    1, 2, figsize=(15, 6.2),
    gridspec_kw={'width_ratios': [len(cols_auto), len(cols_exp)], 'wspace': 0.18},
)

def plot_bloco(ax, norm, fmt, cols, mostrar_yticks):
    im = ax.imshow(norm, cmap=cmap, vmin=0, vmax=1, aspect='auto')
    for i in range(norm.shape[0]):
        for j in range(norm.shape[1]):
            cor_texto = 'white' if norm[i, j] > 0.55 else 'black'
            ax.text(j, i, fmt[i][j],
                    ha='center', va='center', fontsize=11,
                    fontweight='bold', color=cor_texto)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([c[0] for c in cols], fontsize=9)
    if mostrar_yticks:
        ax.set_yticks(range(len(ordem)))
        ax.set_yticklabels([nomes_tarefas[t] for t in ordem], fontsize=11)
    else:
        ax.set_yticks([])
    # Grade
    ax.set_xticks(np.arange(-0.5, len(cols), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(ordem), 1), minor=True)
    ax.grid(which='minor', color='white', linewidth=2)
    ax.tick_params(which='minor', length=0)
    ax.tick_params(axis='x', length=0)
    ax.tick_params(axis='y', length=0)
    return im

plot_bloco(axA, norm_a, fmt_a, cols_auto, mostrar_yticks=True)
im = plot_bloco(axE, norm_e, fmt_e, cols_exp, mostrar_yticks=False)

axA.set_title('Análise automatizada (WAVE + ASES)',
              size=13, fontweight='bold', pad=12, color='#444')
axE.set_title('Experiência real (usuários)',
              size=13, fontweight='bold', pad=12, color='#444')

# Barra de cor compartilhada
cbar = fig.colorbar(im, ax=[axA, axE], shrink=0.7, pad=0.02,
                    ticks=[0, 0.5, 1.0])
cbar.ax.set_yticklabels(['melhor', 'meio', 'pior'])
cbar.set_label('Intensidade dentro de cada coluna\n(normalizado min-max)', size=10)

fig.suptitle(
    'Heatmap: análise automatizada vs. experiência real, por tarefa\n'
    '(escuro = pior dentro da coluna; tarefas ordenadas da mais difícil à mais fácil)',
    size=14, fontweight='bold', y=1.02,
)

plt.savefig('heatmap_auto_vs_experiencia.png', dpi=300, bbox_inches='tight')
print('Heatmap salvo: heatmap_auto_vs_experiencia.png\n')

# Tabela auxiliar no console
print('Valores brutos (ordem do gráfico — pior em cima):')
print(f"{'Tarefa':<28} | {' '.join(c[0].replace(chr(10), ' ') for c in cols_auto)} | {' '.join(c[0].replace(chr(10), ' ') for c in cols_exp)}")
for i, t in enumerate(ordem):
    vals_a = ' '.join(fmt_a[i])
    vals_e = ' '.join(fmt_e[i])
    print(f'{nomes_tarefas[t]:<28} | {vals_a} | {vals_e}')
