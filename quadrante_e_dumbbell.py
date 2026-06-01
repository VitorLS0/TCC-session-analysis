import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# ============================================================
# 1) Carregar dados (mesma lógica dos gráficos anteriores)
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
    'ConsultarCPF': 1, 'ConsultaMonitoramentoServicos': 2,
    'BuscaUnidadesAtendimento': 3, 'ConsultaCenso': 4,
    'ConsultaMapaDeEMpresas': 5,
}

# Score automatizado por tarefa (0–100, maior = MELHOR segundo as ferramentas)
auto_qualidade = {}
for t, path in wave_files.items():
    wave_aim = pd.read_csv(path)['aim_score'].mean() * 10  # 0–100
    ases_score = np.mean([
        p['score'] for flow, pgs in ases_raw['flows'].items()
        for p in pgs if ases_flow_to_tarefa[flow] == t
    ])
    auto_qualidade[t] = (wave_aim + ases_score) / 2

# Experiência: dificuldade composta (0–100, maior = PIOR experiência)
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

exp_dificuldade = {}
exp_qualidade = {}
for t in range(1, 6):
    tlx = df_asq.loc[df_asq['tarefa_num'] == t, 'tlx_score_medio'].mean()
    asq = df_asq.loc[df_asq['tarefa_num'] == t, 'asq_score_medio'].mean()
    pct_falha = df_tar[df_tar['tarefa_num'] == t]['status_conclusao']\
                    .isin(statuses_falha).mean() * 100
    # componentes na escala 0–100, maior = pior
    componentes = [
        (tlx / 20) * 100,
        ((7 - asq) / 6) * 100,
        pct_falha,
    ]
    exp_dificuldade[t] = float(np.nanmean(componentes))
    exp_qualidade[t]   = 100 - exp_dificuldade[t]

# Cores e nomes (mesmo padrão do main.py)
nomes_tarefas = {
    1: 'T1: Consulta CPF',
    2: 'T2: Painel de\nMonitoramento',
    3: 'T3: Receita Federal',
    4: 'T4: IBGE Censo',
    5: 'T5: Mapa de Empresas',
}
cores = {1: '#ff7f0e', 2: '#2ca02c', 3: '#d62728', 4: '#9467bd', 5: '#8c564b'}

# ============================================================
# GRÁFICO 1 — Quadrant plot
# ============================================================
fig1, ax1 = plt.subplots(figsize=(11, 9))

# Backgrounds dos quadrantes com leitura semântica
# Eixos: X = qualidade automatizada (0–100), Y = dificuldade real (0–100)
# Split nos midpoints (50, 50)
ax1.add_patch(Rectangle((50, 50), 50, 50, facecolor='#ffcccc', alpha=0.55, zorder=0))  # top-right
ax1.add_patch(Rectangle((0, 50),  50, 50, facecolor='#fff2cc', alpha=0.55, zorder=0))  # top-left
ax1.add_patch(Rectangle((0, 0),   50, 50, facecolor='#fff2cc', alpha=0.35, zorder=0))  # bottom-left
ax1.add_patch(Rectangle((50, 0),  50, 50, facecolor='#d6f0d6', alpha=0.55, zorder=0))  # bottom-right

# Diagonal de concordância perfeita: (0, 100) -> (100, 0)
ax1.plot([0, 100], [100, 0], linestyle='--', color='gray',
         linewidth=1.5, alpha=0.7, zorder=1, label='Concordância perfeita')

# Linhas de midpoint
ax1.axhline(50, color='white', linewidth=2, zorder=1)
ax1.axvline(50, color='white', linewidth=2, zorder=1)

# Pontos das tarefas
for t in range(1, 6):
    x = auto_qualidade[t]
    y = exp_dificuldade[t]
    ax1.scatter(x, y, s=420, color=cores[t], edgecolor='white',
                linewidths=2.5, zorder=3)
    # Rótulos deslocados manualmente para evitar sobreposições
    offsets = {
        1: ( 2.8, -3.0, 'left',  'top'),     # CPF — abaixo-direita
        2: (-3.0,  0.0, 'right', 'center'),
        3: (-3.0,  3.0, 'right', 'bottom'),  # Receita — acima-esquerda (longe de T1)
        4: ( 2.5,  2.5, 'left',  'bottom'),
        5: ( 2.5, -2.5, 'left',  'top'),
    }
    dx, dy, ha, va = offsets[t]
    ax1.text(x + dx, y + dy, nomes_tarefas[t],
             ha=ha, va=va, fontsize=11.5, fontweight='bold', color=cores[t])

# Rótulos dos quadrantes (cantos)
ax1.text(75, 65, 'FALSOS NEGATIVOS\nferramentas dizem "ok",\nusuários sofrem',
         ha='center', va='center', fontsize=11, color='#8b0000',
         fontweight='bold', alpha=0.85)
ax1.text(25, 75, 'CONCORDÂNCIA RUIM\nambos detectam\ndificuldade',
         ha='center', va='center', fontsize=11, color='#7a5c00',
         fontweight='bold', alpha=0.85)
ax1.text(25, 25, 'FALSOS POSITIVOS\nferramentas alertam,\nusuários não notam',
         ha='center', va='center', fontsize=11, color='#7a5c00',
         fontweight='bold', alpha=0.85)
ax1.text(75, 12, 'CONCORDÂNCIA BOA\nambos consideram\nacessível',
         ha='center', va='center', fontsize=11, color='#1f5e1f',
         fontweight='bold', alpha=0.85)

ax1.set_xlabel('Qualidade automatizada (WAVE + ASES)  →  maior é melhor',
               fontsize=12, fontweight='bold')
ax1.set_ylabel('Dificuldade real (TLX + ASQ⁻¹ + % falha)  →  maior é pior',
               fontsize=12, fontweight='bold')
ax1.set_xlim(0, 100)
ax1.set_ylim(0, 100)
ax1.set_xticks(range(0, 101, 10))
ax1.set_yticks(range(0, 101, 10))
ax1.grid(True, linestyle=':', alpha=0.3, zorder=0)
ax1.set_axisbelow(True)
ax1.legend(loc='center left', bbox_to_anchor=(0.0, 0.5), framealpha=0.9, fontsize=10)
ax1.set_title(
    'Quadrante: ferramentas automatizadas vs. experiência real\n'
    'Distância da diagonal indica o quanto a análise automatizada erra',
    fontsize=14, fontweight='bold', pad=15,
)

plt.tight_layout()
plt.savefig('quadrante_auto_vs_experiencia.png', dpi=300, bbox_inches='tight')
print('Gráfico 1 salvo: quadrante_auto_vs_experiencia.png')

# ============================================================
# GRÁFICO 2 — Dumbbell chart
# ============================================================
# Para o dumbbell, ambos no mesmo eixo "qualidade" (maior = melhor)
linhas = []
for t in range(1, 6):
    discrepancia = auto_qualidade[t] - exp_qualidade[t]
    linhas.append((t, auto_qualidade[t], exp_qualidade[t], discrepancia))

# Ordenar pela MAGNITUDE da discrepância (maior em cima)
linhas.sort(key=lambda r: -abs(r[3]))

fig2, ax2 = plt.subplots(figsize=(13, 6))

y_pos = list(range(len(linhas)))[::-1]  # invertido pra maior discrepância no topo
labels_y = []

for idx, (t, qa, qe, disc) in enumerate(linhas):
    y = y_pos[idx]
    labels_y.append(nomes_tarefas[t].replace('\n', ' '))

    # Linha de conexão
    ax2.plot([qe, qa], [y, y], color=cores[t], linewidth=4, alpha=0.45,
             solid_capstyle='round', zorder=2)

    # Marker da experiência real (círculo cheio)
    ax2.scatter(qe, y, s=320, color=cores[t], edgecolor='white',
                linewidths=2.2, zorder=3, marker='o')
    # Marker da análise automatizada (losango)
    ax2.scatter(qa, y, s=300, facecolor='white', edgecolor=cores[t],
                linewidths=3, zorder=3, marker='D')

    # Valor sobre cada marker
    ax2.text(qe, y + 0.30, f'{qe:.0f}', ha='center', va='bottom',
             fontsize=13, fontweight='bold', color=cores[t])
    ax2.text(qa, y + 0.30, f'{qa:.0f}', ha='center', va='bottom',
             fontsize=13, fontweight='bold', color=cores[t])

    # Anotação da discrepância à direita do haltere (uniforme em todas as linhas)
    sinal = '+' if disc > 0 else ''
    rotulo = f'Δ = {sinal}{disc:.0f}'
    x_max = max(qa, qe)
    ax2.text(x_max + 3, y, rotulo, ha='left', va='center',
             fontsize=13, color='#222', fontweight='bold', style='italic')

ax2.set_yticks(y_pos)
ax2.set_yticklabels(labels_y, fontsize=14, fontweight='bold')
ax2.set_xlim(-5, 115)
ax2.set_xlabel('Score de qualidade (0–100)  —  maior é melhor',
               fontsize=14, fontweight='bold', color='#111')
ax2.set_xticks(range(0, 101, 10))
ax2.tick_params(axis='x', labelsize=12)
ax2.grid(axis='x', linestyle=':', alpha=0.4)
ax2.set_axisbelow(True)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

# Legenda dos marcadores
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='D', color='w', markerfacecolor='white',
           markeredgecolor='#222', markersize=14, markeredgewidth=2.8,
           label='Análise automatizada (WAVE + ASES)'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#222',
           markersize=16, label='Experiência real (TLX + ASQ + sucesso)'),
]
ax2.legend(handles=legend_elements, loc='upper center',
           bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False, fontsize=13)

plt.tight_layout()
plt.savefig('dumbbell_auto_vs_experiencia.png', dpi=300, bbox_inches='tight')
print('Gráfico 2 salvo: dumbbell_auto_vs_experiencia.png')

print('\nResumo dos scores (0–100, maior = melhor):')
print(f"{'Tarefa':<28} {'Auto (W+A)':>10} {'Exp':>6} {'discrep':>9}")
for t, qa, qe, disc in linhas:
    print(f'{nomes_tarefas[t].replace(chr(10), " "):<28} {qa:>10.1f} {qe:>6.1f} {disc:>+9.1f}')
