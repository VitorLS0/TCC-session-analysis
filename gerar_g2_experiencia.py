# -*- coding: utf-8 -*-
"""
G2 — Acessibilidade efetiva na prática (controle vs. experimental).
Gera:
  g2_conclusao_controle_vs_experimental.png   (Q2.1 conclusão pareada; lacuna=barreira)
  g2_gap_asq.png                               (Q2.2 ASQ adaptado, GAP destacado)
  g2_gap_tlx.png                               (Q2.2 NASA-TLX, GAP destacado)
  g2_tlx_perfil_dimensoes_experimental.png     (Q2.2 perfil TLX por dimensão)

Fontes:
  coleta_dados_pesquisa_v3 - asq_nasatlx.csv   (ASQ = média Q1-Q3; TLX = média 6 dim)
  coleta_dados_pesquisa_v3 - tarefas_execucao.csv (conclusão)

Definições (escalas em direções opostas — sempre rotuladas):
  ASQ adaptado 1–7  ↑ melhor      NASA-TLX 0–20  ↓ pior (maior=pior)
  Conclusão autônoma %  ↑ melhor
  - Experimental: média da taxa_conclusao_autonoma registrada por execução.
  - Controle: % de execuções com sucesso_completo (autônomo). No T5/Mapa,
    con04 e con05 concluíram COM assistência → controle autônomo = 3/5 = 60%
    (decisão registrada: medir o controle de forma honesta, não fixar 100%).
  Q4/Q5 (leitor de tela) NÃO entram no ASQ — tratados em figura à parte.
GAP = controle − experimental = barreira de acessibilidade isolada.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ------------------------------------------------------------------
nomes_tarefas = {
    1: 'T1: Consulta CPF\n(Receita)',
    2: 'T2: Painel de\nMonitoramento',
    3: 'T3: Receita Federal\n(Unidades)',
    4: 'T4: Censo\n(IBGE)',
    5: 'T5: Mapa de\nEmpresas',
}
COR_CON = '#3a7ca5'   # controle  (linha de base)
COR_EXP = '#d1495b'   # experimental (leitor de tela — grupo que enfrenta a barreira)
COR_GAP = '#555555'
tarefas = [1, 2, 3, 4, 5]


def br_to_float(x):
    if pd.isna(x):
        return np.nan
    return pd.to_numeric(str(x).replace(',', '.').replace('%', ''), errors='coerce')


# ------------------------------------------------------------------
# Carregar experiência (ASQ/TLX) e recalcular scores p/ AMBOS os grupos
# ------------------------------------------------------------------
df = pd.read_csv('coleta_dados_pesquisa_v3 - asq_nasatlx.csv')
df = df[df['participante_id'].notna()].copy()
df['grupo'] = df['participante_id'].str[:3].map({'exp': 'experimental', 'con': 'controle'})
df['tarefa_num'] = pd.to_numeric(df['tarefa_num'], errors='coerce')
asq_cols = ['asq_q1_facil', 'asq_q2_tempo', 'asq_q3_nao_perdido']
tlx_cols = ['tlx_demanda_mental', 'tlx_demanda_fisica', 'tlx_demanda_temporal',
            'tlx_desempenho', 'tlx_esforco', 'tlx_frustracao']
for c in asq_cols + tlx_cols:
    df[c] = df[c].apply(br_to_float)
df['asq_score'] = df[asq_cols].mean(axis=1, skipna=True)   # média Q1-Q3 (exclui NA)
df['tlx_score'] = df[tlx_cols].mean(axis=1, skipna=True)   # média das 6 dimensões


def por_grupo_portal(col):
    p = df.pivot_table(col, 'tarefa_num', 'grupo', aggfunc='mean')
    return ({t: p.loc[t, 'controle'] for t in tarefas},
            {t: p.loc[t, 'experimental'] for t in tarefas})


asq_con, asq_exp = por_grupo_portal('asq_score')
tlx_con, tlx_exp = por_grupo_portal('tlx_score')

# n por célula (para nota de validade — especialmente T5 experimental = 3)
n_exp = df[df.grupo == 'experimental'].dropna(subset=['asq_score']) \
          .groupby('tarefa_num').size().to_dict()

# ------------------------------------------------------------------
# Conclusão autônoma por portal
# ------------------------------------------------------------------
dt = pd.read_csv('coleta_dados_pesquisa_v3 - tarefas_execucao.csv')
dt = dt.dropna(subset=['participante_id', 'tarefa_num', 'status_conclusao'])
dt['tarefa_num'] = dt['tarefa_num'].astype(int)
dt['grupo'] = dt['participante_id'].str[:3].map({'exp': 'experimental', 'con': 'controle'})
dt['taxa_aut'] = dt['taxa_conclusao_autonoma'].apply(br_to_float)

# Experimental: média da taxa registrada (T5 com n=3, demais NA ignoradas)
concl_exp = dt[dt.grupo == 'experimental'].groupby('tarefa_num')['taxa_aut'].mean().to_dict()
n_concl_exp = dt[dt.grupo == 'experimental'].dropna(subset=['taxa_aut']) \
                .groupby('tarefa_num').size().to_dict()
# Controle: % de sucesso_completo (autônomo)
concl_con = {}
for t in tarefas:
    sub = dt[(dt.grupo == 'controle') & (dt.tarefa_num == t)]
    concl_con[t] = 100 * (sub['status_conclusao'] == 'sucesso_completo').mean()


# ==================================================================
# FIGURA 1 — Conclusão autônoma: controle vs. experimental (Q2.1)
# ==================================================================
fig, ax = plt.subplots(figsize=(13, 6.5))
x = np.arange(len(tarefas))
w = 0.38
vc = [concl_con[t] for t in tarefas]
ve = [concl_exp[t] for t in tarefas]

bc = ax.bar(x - w / 2, vc, w, color=COR_CON, edgecolor='black', linewidth=0.6,
            label='Controle (sem deficiência visual)')
be = ax.bar(x + w / 2, ve, w, color=COR_EXP, edgecolor='black', linewidth=0.6,
            label='Experimental (leitor de tela)')

for b, v in zip(bc, vc):
    ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f'{v:.0f}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold', color=COR_CON)
for b, v in zip(be, ve):
    ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f'{v:.0f}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold', color=COR_EXP)

# GAP (barreira) anotado por portal
for i, t in enumerate(tarefas):
    gap = concl_con[t] - concl_exp[t]
    ytop = max(vc[i], ve[i])
    ax.annotate('', xy=(i - w / 2, concl_con[t]), xytext=(i + w / 2, concl_exp[t]),
                arrowprops=dict(arrowstyle='<->', color=COR_GAP, lw=1.3, alpha=0.7))
    ax.text(i, ytop + 8, f'barreira\nΔ={gap:.0f} p.p.', ha='center', va='bottom',
            fontsize=9.5, fontweight='bold', color=COR_GAP)

# Destaque do T5 — barreira total
i5 = tarefas.index(5)
ax.text(i5, 4, 'barreira\ntotal', ha='center', va='bottom', fontsize=10,
        fontweight='bold', color=COR_EXP)

ax.axhline(100, color='gray', linestyle=':', linewidth=1)
ax.set_xticks(x)
ax.set_xticklabels([nomes_tarefas[t] for t in tarefas], fontsize=10)
ax.set_ylim(0, 125)
ax.set_yticks(range(0, 101, 20))
ax.set_ylabel('Conclusão autônoma (%)   ↑ melhor', fontsize=12, fontweight='bold')
ax.set_title('G2 · Conclusão autônoma por portal — controle vs. experimental\n'
             'A distância até o controle é a barreira de acessibilidade isolada',
             fontsize=14, fontweight='bold', pad=12)
ax.grid(axis='y', linestyle='--', alpha=0.4)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
fig.text(0.5, -0.04,
         'Experimental: média da taxa de conclusão autônoma dos objetivos por execução '
         f'(T5/Mapa n={n_concl_exp.get(5, 0)} — 2 execuções não realizadas). '
         'Controle: % de execuções com sucesso_completo (autônomo); no T5, 2/5 concluíram com '
         'assistência → 60%. Controle concluiu todas as tarefas (com ou sem ajuda).',
         ha='center', fontsize=9, color='#444', style='italic')
plt.tight_layout()
plt.savefig('g2_conclusao_controle_vs_experimental.png', dpi=300, bbox_inches='tight')
plt.close(fig)
print('Salvo: g2_conclusao_controle_vs_experimental.png')


# ==================================================================
# Função genérica de dumbbell (GAP destacado) para ASQ e TLX
# ==================================================================
def dumbbell(con, exp, escala_txt, xlim, titulo, arquivo, melhor_dir,
             nota=None, xticks=None):
    """melhor_dir: 'maior' (ASQ) ou 'menor' (TLX)."""
    # Ordena por magnitude do gap (maior em cima)
    ordem = sorted(tarefas, key=lambda t: abs(con[t] - exp[t]))
    y = np.arange(len(ordem))
    fig, ax = plt.subplots(figsize=(12, 6))
    for yi, t in zip(y, ordem):
        c, e = con[t], exp[t]
        ax.plot([e, c], [yi, yi], color=COR_GAP, lw=3, alpha=0.45,
                solid_capstyle='round', zorder=2)
        ax.scatter(c, yi, s=300, color=COR_CON, edgecolor='white', linewidths=2,
                   zorder=3)
        ax.scatter(e, yi, s=300, color=COR_EXP, edgecolor='white', linewidths=2,
                   zorder=3)
        ax.text(c, yi + 0.18, f'{c:.1f}', ha='center', va='bottom',
                fontsize=11, fontweight='bold', color=COR_CON)
        ax.text(e, yi + 0.18, f'{e:.1f}', ha='center', va='bottom',
                fontsize=11, fontweight='bold', color=COR_EXP)
        # Δ no meio do haltere
        gap = c - e
        ax.text((c + e) / 2, yi - 0.26, f'GAP {abs(gap):.1f}', ha='center', va='top',
                fontsize=10.5, fontweight='bold', color=COR_GAP, style='italic')
    ax.set_yticks(y)
    rotulos = []
    for t in ordem:
        lab = nomes_tarefas[t].replace('\n', ' ')
        if t == 5:
            lab += f' (n={n_exp.get(5, 0)} exp.)'
        rotulos.append(lab)
    ax.set_yticklabels(rotulos, fontsize=11)
    ax.set_xlim(*xlim)
    if xticks is not None:
        ax.set_xticks(xticks)
    ax.set_xlabel(escala_txt, fontsize=12, fontweight='bold')
    ax.set_title(titulo, fontsize=14, fontweight='bold', pad=12)
    ax.grid(axis='x', linestyle='--', alpha=0.4)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    legend_el = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=COR_CON,
               markersize=13, label='Controle (sem def. visual)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=COR_EXP,
               markersize=13, label='Experimental (leitor de tela)'),
        Line2D([0], [0], color=COR_GAP, lw=3, alpha=0.5,
               label='GAP = barreira de acessibilidade'),
    ]
    ax.legend(handles=legend_el, loc='lower center', bbox_to_anchor=(0.5, -0.24),
              ncol=3, frameon=False, fontsize=10)
    if nota:
        fig.text(0.5, -0.06, nota, ha='center', fontsize=9, color='#444', style='italic')
    plt.tight_layout()
    plt.savefig(arquivo, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'Salvo: {arquivo}')


# FIGURA 2 — ASQ adaptado (1–7, ↑ melhor)
dumbbell(
    asq_con, asq_exp,
    escala_txt='ASQ adaptado (1–7)   ↑ melhor (concorda com afirmações positivas)',
    xlim=(1, 7.4), xticks=range(1, 8),
    titulo='G2 · Facilidade percebida (ASQ adaptado) — controle vs. experimental\n'
           'GAP = quanto a barreira de acessibilidade reduz a facilidade percebida',
    arquivo='g2_gap_asq.png', melhor_dir='maior',
    nota='ASQ adaptado = média de Q1–Q3 (excluindo NA), para ambos os grupos. '
         'Q4/Q5 (leitor de tela) não entram no score. No Painel e no Mapa o próprio '
         'controle já pontua mais baixo (5,3 e 5,0): usabilidade geral frágil que a '
         'barreira amplifica.')

# FIGURA 3 — NASA-TLX (0–20, ↓ pior)
dumbbell(
    tlx_con, tlx_exp,
    escala_txt='NASA-TLX (0–20)   ↑ pior (maior = mais carga/esforço)',
    xlim=(0, 20), xticks=range(0, 21, 2),
    titulo='G2 · Carga de trabalho (NASA-TLX) — controle vs. experimental\n'
           'GAP = sobrecarga imposta pela barreira de acessibilidade',
    arquivo='g2_gap_tlx.png', melhor_dir='menor',
    nota='NASA-TLX = média das 6 dimensões (recalculada igualmente p/ os dois grupos). '
         f'T5/Mapa: experimental n={n_exp.get(5, 0)} (2 execuções não realizadas).')


# ==================================================================
# FIGURA 4 — Perfil do TLX por dimensão (experimental vs. controle)  (Q2.2)
# ==================================================================
dim_labels = ['Demanda\nMental', 'Demanda\nFísica', 'Demanda\nTemporal',
              'Desempenho', 'Esforço', 'Frustração']
exp_dim = [df.loc[df.grupo == 'experimental', c].mean() for c in tlx_cols]
con_dim = [df.loc[df.grupo == 'controle', c].mean() for c in tlx_cols]

fig, ax = plt.subplots(figsize=(12, 6.5))
x = np.arange(len(dim_labels))
w = 0.38
bc = ax.bar(x - w / 2, con_dim, w, color=COR_CON, edgecolor='black', linewidth=0.6,
            label='Controle (sem def. visual)')
be = ax.bar(x + w / 2, exp_dim, w, color=COR_EXP, edgecolor='black', linewidth=0.6,
            label='Experimental (leitor de tela)')
for bars, vals in ((bc, con_dim), (be, exp_dim)):
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.2, f'{v:.1f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

# Destaque honesto: as dimensões dominantes no experimental são cognitivo-emocionais
# (Esforço, Mental, Frustração); a física é elevada, porém menor que essas.
i_esf = 4  # Esforço (maior)
ax.annotate('maior carga: esforço,\ndemanda mental e frustração\n(cognitivo-emocional)',
            xy=(i_esf + w / 2, exp_dim[i_esf]), xytext=(2.4, 17.3),
            fontsize=9.5, fontweight='bold', color=COR_EXP, ha='center',
            arrowprops=dict(arrowstyle='->', color=COR_EXP, lw=1.6))
i_fis = 1  # Física — elevada, mas abaixo das cognitivo-emocionais
ax.annotate('demanda física também\nelevada (≈10), não desprezível',
            xy=(i_fis + w / 2, exp_dim[i_fis]), xytext=(i_fis + 0.55, 4.5),
            fontsize=9, fontweight='bold', color='#7a3b46', ha='center',
            arrowprops=dict(arrowstyle='->', color='#7a3b46', lw=1.3))

ax.set_xticks(x)
ax.set_xticklabels(dim_labels, fontsize=10.5)
ax.set_ylim(0, 20)
ax.set_yticks(range(0, 21, 4))
ax.set_ylabel('NASA-TLX por dimensão (0–20)   ↑ pior', fontsize=12, fontweight='bold')
ax.set_title('G2 · Perfil da carga de trabalho por dimensão (média de todos os portais)\n'
             'A sobrecarga do experimental é maior nas dimensões cognitivo-emocionais (esforço, mental, frustração)',
             fontsize=12.5, fontweight='bold', pad=12)
ax.grid(axis='y', linestyle='--', alpha=0.4)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
fig.text(0.5, -0.03,
         'Média sobre todas as execuções de cada grupo (experimental inclui T5 com n=3). '
         'Escala 0–20 por dimensão; maior = mais carga.',
         ha='center', fontsize=9, color='#444', style='italic')
plt.tight_layout()
plt.savefig('g2_tlx_perfil_dimensoes_experimental.png', dpi=300, bbox_inches='tight')
plt.close(fig)
print('Salvo: g2_tlx_perfil_dimensoes_experimental.png')

# Console
print('\n[G2] Conclusão autônoma (%)  | ASQ (1-7) | TLX (0-20)  [con / exp]')
for t in tarefas:
    print(f"{nomes_tarefas[t].replace(chr(10),' '):<26} "
          f"concl {concl_con[t]:>5.0f}/{concl_exp[t]:<5.0f} "
          f"asq {asq_con[t]:>4.1f}/{asq_exp[t]:<4.1f} "
          f"tlx {tlx_con[t]:>4.1f}/{tlx_exp[t]:<4.1f}")
print('TLX dim experimental:', [f'{v:.1f}' for v in exp_dim])
print('TLX dim controle    :', [f'{v:.1f}' for v in con_dim])
