import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.legend_handler import HandlerTuple

# Carregar os dados
df = pd.read_csv("coleta_dados_pesquisa_v3 - asq_nasatlx.csv")

# Questões do ASQ (1-7, maior = melhor)
asq_cols = ['asq_q1_facil', 'asq_q2_tempo', 'asq_q3_nao_perdido']
labels = ['Q1\nFácil', 'Q2\nTempo', 'Q3\nNão perdido']

for col in asq_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Grupo derivado do prefixo de participante_id (exp = experimental, con = controle)
df = df[df['participante_id'].notna()].copy()
df['grupo'] = df['participante_id'].str.slice(0, 3)
df['tarefa_num'] = pd.to_numeric(df['tarefa_num'], errors='coerce')

nomes_tarefas = {
    1: 'T1: Consulta CPF',
    2: 'T2: Painel de Monitoramento',
    3: 'T3: Receita Federal',
    4: 'T4: IBGE Censo',
    5: 'T5: Mapa de Empresas'
}
cores = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
ASQ_MIN, ASQ_MAX = 1, 7
xs = list(range(len(labels)))            # eixos paralelos: Q1, Q2, Q3


def gerar_perfil_grupo(df_grupo, grupo_key, grupo_nome, arquivo,
                       ref_por_tarefa=None, ref_nome=None):
    """Grade 2x3 de perfis (coordenadas paralelas) ASQ para um único grupo.
    ref_por_tarefa: dict {tarefa: vetor de referência} a usar como fundo cinza
    (ex.: média do controle por tarefa). Se None, usa a média geral do grupo."""
    overall_mean = df_grupo[asq_cols].mean().values

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for i in range(5):
        tarefa_num = i + 1
        ax = axes[i]

        sub = df_grupo[df_grupo['tarefa_num'] == tarefa_num][asq_cols]
        t_mean = sub.mean().values

        if np.isnan(t_mean).all():
            ax.set_title(f'{nomes_tarefas[tarefa_num]}\n(Sem dados)', size=12)
            continue

        # Referência de fundo (cinza): controle por tarefa, ou média geral do grupo
        if ref_por_tarefa is not None:
            ref = ref_por_tarefa[tarefa_num]
            ref_label = ref_nome
        else:
            ref = overall_mean
            ref_label = f'Média geral ({grupo_nome.lower()})'
        ax.fill_between(xs, ASQ_MIN, ref, color='gray', alpha=0.18, zorder=1)
        ax.plot(xs, ref, linewidth=2.2, linestyle='solid', marker='o', markersize=7,
                color='#4d4d4d', alpha=0.85, zorder=3, label=ref_label)

        # Tarefa específica (experimental)
        ax.fill_between(xs, ASQ_MIN, t_mean, color=cores[i], alpha=0.2, zorder=2)
        ax.plot(xs, t_mean, linewidth=2, linestyle='solid', marker='o', markersize=7,
                color=cores[i], zorder=4, label='Experimental')

        ax.set_xticks(xs)
        ax.set_xticklabels(labels, size=13)
        ax.set_xlim(-0.15, len(labels) - 0.85)
        ax.set_yticks(range(1, 8))
        ax.set_ylim(ASQ_MIN, ASQ_MAX)
        ax.tick_params(axis='y', labelsize=12)
        ax.grid(axis='y', linestyle='--', alpha=0.35)
        ax.set_axisbelow(True)
        for lado in ('top', 'right'):
            ax.spines[lado].set_visible(False)
        ax.set_title(nomes_tarefas[tarefa_num], size=16, fontweight='bold', pad=10)

    # Ocultar o 6º gráfico (só 5 tarefas)
    fig.delaxes(axes[5])

    plt.suptitle(
        f'ASQ — Média por Tarefa — {grupo_nome} vs Controle',
        size=18, fontweight='bold', y=1.0)
    plt.tight_layout()
    fig.subplots_adjust(hspace=0.35)

    # Legenda no espaço vazio do 6º subplot: cores = grupo da figura; cinza = referência
    ref_label_geral = ref_nome if ref_por_tarefa is not None \
        else f'Média geral ({grupo_nome.lower()})'
    exp_handle = tuple(Line2D([0], [0], color=cores[i], lw=2.4) for i in range(5))
    ref_handle = Line2D([0], [0], color='#4d4d4d', lw=2.2)
    fig.legend([exp_handle, ref_handle],
               [f'{grupo_nome} (linhas coloridas)', ref_label_geral],
               handler_map={tuple: HandlerTuple(ndivide=None)},
               loc='center', bbox_to_anchor=(0.83, 0.27), fontsize=14)
    fig.text(0.83, 0.13,
             '\nASQ: 1–7 por questão · maior = melhor.\n\n'
             'n = 5 por grupo em todas as tarefas,\n'
             ' exceto T5 do experimental (n = 3).',
             ha='center', fontsize=15, color='#444', style='italic')

    plt.savefig(arquivo, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'Salvo: {arquivo}')


# Média do controle por tarefa (referência do perfil experimental)
df_con = df[df['grupo'] == 'con']
ref_controle = {t: df_con[df_con['tarefa_num'] == t][asq_cols].mean().values
                for t in range(1, 6)}

# Experimental: cada tarefa comparada à média do CONTROLE naquela tarefa
gerar_perfil_grupo(df[df['grupo'] == 'exp'], 'exp', 'Experimental',
                   'asq_perfil_experimental.png',
                   ref_por_tarefa=ref_controle, ref_nome='Controle')
# Controle: mantém a comparação vs. média do próprio grupo
gerar_perfil_grupo(df[df['grupo'] == 'con'], 'con', 'Controle',
                   'asq_perfil_controle.png')

print("Gráficos de perfil ASQ por grupo gerados com sucesso!")
