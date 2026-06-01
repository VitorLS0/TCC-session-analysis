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

# Calcular a média geral
overall_mean = df[tlx_cols].mean().values

# Preparar os ângulos para o radar
num_vars = len(labels)
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
angles += angles[:1]
overall_mean = np.append(overall_mean, overall_mean[0])

# Criar a figura com subplots (2 linhas, 3 colunas)
fig, axes = plt.subplots(2, 3, figsize=(15, 10), subplot_kw=dict(polar=True))
axes = axes.flatten()

# Nomes das tarefas (baseado nos dados anteriores de execução, ou genérico)
nomes_tarefas = {
    1: 'T1: Consulta CPF',
    2: 'T2: Painel de Monitoramento',
    3: 'T3: Receita Federal',
    4: 'T4: IBGE Censo',
    5: 'T5: Mapa de Empresas'
}

# Cores para cada tarefa
cores = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

# Determinar o limite máximo para o eixo Y
max_val = df[tlx_cols].max().max()

# Plotar cada tarefa
for i in range(5):
    tarefa_num = i + 1
    ax = axes[i]
    
    # Calcular média da tarefa
    t_mean = df[df['tarefa_num'] == tarefa_num][tlx_cols].mean().values
    
    # Se não houver dados, pular
    if np.isnan(t_mean).all():
        ax.set_title(f'{nomes_tarefas[tarefa_num]}\n(Sem dados)', size=12)
        continue
        
    t_mean = np.append(t_mean, t_mean[0])
    
    # Ajustar eixo
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=16)
    ax.tick_params(axis='y', labelsize=12)
    ax.set_ylim(0, max_val + 2)
    
    # Plotar média geral como referência (fundo cinza)
    ax.plot(angles, overall_mean, linewidth=1, linestyle='solid', color='gray', alpha=0.5)
    ax.fill(angles, overall_mean, color='gray', alpha=0.1, label='Média Geral')
    
    # Plotar tarefa específica
    ax.plot(angles, t_mean, linewidth=2, linestyle='solid', color=cores[i], label=f'Média da Tarefa')
    ax.fill(angles, t_mean, color=cores[i], alpha=0.2)
    
    # Título
    ax.set_title(nomes_tarefas[tarefa_num], size=17, fontweight='bold', y=1.13)

# Ocultar o 6º gráfico (já que são só 5 tarefas)
fig.delaxes(axes[5])

# Ajustar layout
plt.suptitle('Desempenho no NASA-TLX por Tarefa (vs. Média Geral)', size=18, fontweight='bold', y=1.05)
plt.tight_layout()
fig.subplots_adjust(hspace=0.45)

# Legenda global posicionada dentro do 6º espaço vazio (mais próxima dos radares)
handles, labels_leg = axes[0].get_legend_handles_labels()
fig.legend(handles, labels_leg, loc='center', bbox_to_anchor=(0.83, 0.27), fontsize=13)

# Salvar
plt.savefig('radar_individual_por_tarefa.png', dpi=300, bbox_inches='tight')
print("Gráficos de radar individuais gerados com sucesso!")