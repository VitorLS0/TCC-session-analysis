import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Carregar os dados
df = pd.read_csv("coleta_dados_pesquisa_v3 - asq_nasatlx.csv")

# Selecionar as colunas do NASA-TLX
tlx_cols = [
    'tlx_demanda_mental', 'tlx_demanda_fisica',
    'tlx_demanda_temporal', 'tlx_desempenho',
    'tlx_esforco', 'tlx_frustracao'
]

# Rótulos para o gráfico
labels = [
    'Demanda\nMental', 'Demanda\nFísica', 'Demanda\nTemporal',
    'Desempenho', 'Esforço', 'Frustração'
]

# Garantir que os dados são numéricos
for col in tlx_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Grupo derivado do prefixo de participante_id (exp = experimental, con = controle)
df = df[df['participante_id'].notna()].copy()
df['grupo'] = df['participante_id'].str.slice(0, 3)

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

# Escala fixa para o TLX (0-20, maior = pior) -> as duas figuras ficam comparáveis
TLX_MAX = 20

# Ângulos do radar
num_vars = len(labels)
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
angles += angles[:1]


def gerar_radar_grupo(df_grupo, grupo_key, grupo_nome, arquivo):
    """Gera a grade 2x3 de radares NASA-TLX para um único grupo."""
    # Média geral do grupo (referência de fundo)
    overall_mean = df_grupo[tlx_cols].mean().values
    overall_mean = np.append(overall_mean, overall_mean[0])

    fig, axes = plt.subplots(2, 3, figsize=(15, 10), subplot_kw=dict(polar=True))
    axes = axes.flatten()

    for i in range(5):
        tarefa_num = i + 1
        ax = axes[i]

        sub = df_grupo[df_grupo['tarefa_num'] == tarefa_num][tlx_cols]
        n = int(sub.notna().any(axis=1).sum())
        t_mean = sub.mean().values

        if np.isnan(t_mean).all():
            ax.set_title(f'{nomes_tarefas[tarefa_num]}\n(Sem dados)', size=12)
            continue

        t_mean = np.append(t_mean, t_mean[0])

        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=16)
        ax.tick_params(axis='y', labelsize=12)
        ax.set_ylim(0, TLX_MAX)

        # Média geral do grupo como referência (fundo cinza)
        ax.plot(angles, overall_mean, linewidth=1, linestyle='solid',
                color='gray', alpha=0.5)
        ax.fill(angles, overall_mean, color='gray', alpha=0.1,
                label=f'Média geral ({grupo_nome.lower()})')

        # Tarefa específica
        ax.plot(angles, t_mean, linewidth=2, linestyle='solid',
                color=cores[i], label='Média da tarefa')
        ax.fill(angles, t_mean, color=cores[i], alpha=0.2)

        ax.set_title(f'{nomes_tarefas[tarefa_num]}  (n={n})',
                     size=16, fontweight='bold', y=1.13)

    # Ocultar o 6º gráfico (só 5 tarefas)
    fig.delaxes(axes[5])

    plt.suptitle(
        f'NASA-TLX por Tarefa — Grupo {grupo_nome} (vs. média do grupo)',
        size=18, fontweight='bold', y=1.05)
    plt.tight_layout()
    fig.subplots_adjust(hspace=0.45)

    # Legenda no espaço vazio do 6º subplot
    handles, labels_leg = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels_leg, loc='center',
               bbox_to_anchor=(0.83, 0.27), fontsize=13)
    fig.text(0.83, 0.13,
             'NASA-TLX: 0–20 por dimensão · maior = mais carga',
             ha='center', fontsize=10.5, color='#444', style='italic')

    plt.savefig(arquivo, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'Salvo: {arquivo}')


# Uma figura por grupo
gerar_radar_grupo(df[df['grupo'] == 'exp'], 'exp', 'Experimental',
                  'radar_tlx_experimental.png')
gerar_radar_grupo(df[df['grupo'] == 'con'], 'con', 'Controle',
                  'radar_tlx_controle.png')

print("Gráficos de radar por grupo gerados com sucesso!")
