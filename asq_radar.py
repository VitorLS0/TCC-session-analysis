import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.legend_handler import HandlerTuple

# Carregar os dados
df = pd.read_csv("coleta_dados_pesquisa_v3 - asq_nasatlx.csv")

# Questões do ASQ que entram no radar (1-7, maior = melhor)
asq_cols = ['asq_q1_facil', 'asq_q2_tempo', 'asq_q3_nao_perdido']

# Rótulos para o gráfico
labels = ['Q1\nFácil', 'Q2\nTempo', 'Q3\nNão perdido']

# Garantir que os dados são numéricos
for col in asq_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Grupo derivado do prefixo de participante_id (exp = experimental, con = controle)
df = df[df['participante_id'].notna()].copy()
df['grupo'] = df['participante_id'].str.slice(0, 3)
df['tarefa_num'] = pd.to_numeric(df['tarefa_num'], errors='coerce')

# Nomes das tarefas
nomes_tarefas = {
    1: 'T1: Consulta CPF',
    2: 'T2: Painel de Monitoramento',
    3: 'T3: Receita Federal',
    4: 'T4: IBGE Censo',
    5: 'T5: Mapa de Empresas'
}

# Cores por tarefa (identidade de cada subplot)
cores = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

# Escala fixa para o ASQ (1-7, maior = melhor) -> as duas figuras ficam comparáveis
ASQ_MIN, ASQ_MAX = 1, 7

# Ângulos do radar
num_vars = len(labels)
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
angles += angles[:1]


def gerar_radar_grupo(df_grupo, grupo_key, grupo_nome, arquivo,
                      ref_por_tarefa=None, ref_nome=None):
    """Gera a grade 2x3 de radares ASQ para um único grupo.
    ref_por_tarefa: dict {tarefa: vetor de referência} a usar como fundo cinza
    (ex.: média do controle por tarefa). Se None, usa a média geral do grupo."""
    # Média geral do grupo (referência de fundo padrão)
    overall_mean = df_grupo[asq_cols].mean().values
    overall_mean = np.append(overall_mean, overall_mean[0])

    fig, axes = plt.subplots(2, 3, figsize=(15, 10), subplot_kw=dict(polar=True))
    axes = axes.flatten()

    for i in range(5):
        tarefa_num = i + 1
        ax = axes[i]

        sub = df_grupo[df_grupo['tarefa_num'] == tarefa_num][asq_cols]
        t_mean = sub.mean().values

        if np.isnan(t_mean).all():
            ax.set_title(f'{nomes_tarefas[tarefa_num]}\n(Sem dados)', size=12)
            continue

        t_mean = np.append(t_mean, t_mean[0])

        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=15)
        ax.set_yticks([1, 3, 5, 7])
        ax.tick_params(axis='y', labelsize=11)
        ax.set_ylim(ASQ_MIN, ASQ_MAX)

        # Referência de fundo (cinza): controle por tarefa, ou média geral do grupo
        if ref_por_tarefa is not None:
            ref = ref_por_tarefa[tarefa_num]
            ref_label = ref_nome
        else:
            ref = overall_mean
            ref_label = f'Média geral ({grupo_nome.lower()})'
        ax.plot(angles, ref, linewidth=2.2, linestyle='solid',
                color='#4d4d4d', alpha=0.85, zorder=3)
        ax.fill(angles, ref, color='gray', alpha=0.18, label=ref_label, zorder=1)

        # Tarefa específica
        ax.plot(angles, t_mean, linewidth=2, linestyle='solid',
                color=cores[i], label='Experimental')
        ax.fill(angles, t_mean, color=cores[i], alpha=0.2)

        ax.set_title(nomes_tarefas[tarefa_num],
                     size=16, fontweight='bold', y=1.13)

    # Ocultar o 6º gráfico (só 5 tarefas)
    fig.delaxes(axes[5])

    plt.suptitle(
        f'ASQ Média por Tarefa — {grupo_nome} vs Controle',
        size=18, fontweight='bold', y=1.05)
    plt.tight_layout()
    fig.subplots_adjust(hspace=0.45)

    # Legenda no espaço vazio do 6º subplot: cores = grupo da figura; cinza = referência
    ref_label_geral = ref_nome if ref_por_tarefa is not None \
        else f'Média geral ({grupo_nome.lower()})'
    exp_handle = tuple(Line2D([0], [0], color=cores[i], lw=2.4) for i in range(5))
    ref_handle = Line2D([0], [0], color='#4d4d4d', lw=2.2)
    fig.legend([exp_handle, ref_handle],
               [f'{grupo_nome} (linhas coloridas)', ref_label_geral],
               handler_map={tuple: HandlerTuple(ndivide=None)},
               loc='center', bbox_to_anchor=(0.83, 0.27), fontsize=12)
    fig.text(0.83, 0.13,
             'ASQ: 1–7 por questão · maior = melhor (concorda com a afirmação).\n'
             'n = 5 por grupo em todas as tarefas, exceto T5 do experimental (n = 3).',
             ha='center', fontsize=10.5, color='#444', style='italic')

    plt.savefig(arquivo, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'Salvo: {arquivo}')


# Média do controle por tarefa (referência do radar experimental)
df_con = df[df['grupo'] == 'con']
ref_controle = {}
for t in range(1, 6):
    m = df_con[df_con['tarefa_num'] == t][asq_cols].mean().values
    ref_controle[t] = np.append(m, m[0])

# Experimental: cada tarefa comparada à média do CONTROLE naquela tarefa
gerar_radar_grupo(df[df['grupo'] == 'exp'], 'exp', 'Experimental',
                  'asq_radar_experimental.png',
                  ref_por_tarefa=ref_controle, ref_nome='Controle')
# Controle: mantém a comparação vs. média do próprio grupo
gerar_radar_grupo(df[df['grupo'] == 'con'], 'con', 'Controle',
                  'asq_radar_controle.png')

print("Gráficos de radar ASQ por grupo gerados com sucesso!")
