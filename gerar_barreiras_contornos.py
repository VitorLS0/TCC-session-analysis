# -*- coding: utf-8 -*-
"""
Barreiras de acessibilidade e estratégias de contorno (grupo experimental, NVDA).
Lê o CSV consolidado (cabeçalho na 3ª linha; campos da barreira em forward-fill).
Gera:
  g_barreiras_sintese_severidade_categoria.png  (severidade × categoria × portal)
  g_eficacia_contornos.png                       (eficácia dos contornos, por severidade)
  g3_matriz_deteccao_vs_severidade.png           (barreira × detecção automática + severidade)

Avisos de validade (refletidos nas legendas):
- Severidade/criticidade INFERIDA dos relatos (escala Nielsen adaptada 0–4): julgamento qualitativo.
- Classificação de detecção automática: julgamento TÉCNICO do autor (ASES/WAVE são estáticas:
  detectam falhas no HTML/DOM, mas não executam interação, não avaliam conteúdo embarcado/
  dinâmico nem julgam o sentido de um rótulo).
- n=5 (experimental). Tudo descritivo/exploratório; sem estatística inferencial.
Contagens recalculadas do CSV (impressas no console ao final).
"""
import re
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

try:
    sys.stdout.reconfigure(encoding='utf-8')   # console Windows aceita ≤, ç, etc.
except Exception:
    pass

ARQ = "Cópia de barreiras_contornos_consolidado - Barreiras e Contornos.csv"

# ------------------------------------------------------------------
# 1) Carregar e reconstruir (forward-fill dos campos da barreira)
# ------------------------------------------------------------------
df = pd.read_csv(ARQ, skiprows=2)
df = df.rename(columns={
    'Barreira (nome / tipo)': 'barreira',
    'Criticidade (0-4 Nielsen)': 'criticidade',
    'Rótulo de severidade': 'rotulo_sev',
    'Tarefas afetadas': 'tarefas',
    'Eficácia do contorno': 'eficacia',
})
# Linhas de continuação têm ID vazio → propagar os campos da barreira
campos_barreira = ['ID', 'barreira', 'Categoria', 'criticidade', 'rotulo_sev', 'tarefas']
df[campos_barreira] = df[campos_barreira].ffill()
df = df[df['ID'].notna() & df['eficacia'].notna()].copy()
df['criticidade'] = df['criticidade'].astype(int)
df['eficacia'] = df['eficacia'].str.strip()

# Tabela por barreira (uma linha por B-ID)
barr = df.drop_duplicates('ID').set_index('ID')[
    ['barreira', 'Categoria', 'criticidade', 'rotulo_sev', 'tarefas']].copy()

# ------------------------------------------------------------------
# Constantes de apresentação (rótulos/cores no padrão do projeto)
# ------------------------------------------------------------------
cat_label = {'ROT': 'Rotulagem/semântica', 'NAV': 'Navegação', 'FORM': 'Formulário',
             'DIN': 'Conteúdo dinâmico', 'TEC': 'Técnico/comportamento'}
cat_cor = {'ROT': '#4e79a7', 'NAV': '#59a14f', 'FORM': '#f28e2b',
           'DIN': '#e15759', 'TEC': '#b07aa1'}
ef_ordem = ['Efetiva', 'Parcial', 'Não efetiva']
ef_cor = {'Efetiva': '#2ca02c', 'Parcial': '#ffbb33', 'Não efetiva': '#d62728'}
portal_nome = {1: 'CPF', 2: 'Painel', 3: 'Receita', 4: 'Censo', 5: 'Mapa'}

# Nomes curtos p/ rótulos do eixo (apresentação; não altera contagens)
nome_curto = {
    'B01': 'Cabeçalho/skip link ausente',
    'B02': 'iframe Power BI inacessível',
    'B03': 'Indicadores ocultos na árvore a11y',
    'B04': 'Keyboard trap (filtros/menus)',
    'B05': 'Timeout de sessão',
    'B06': 'Combobox autocomplete fora do ARIA',
    'B07': 'Gráficos sem alternativa textual',
    'B08': 'Listas longas sem âncoras',
    'B09': 'Rótulos obscuros ("Vire o card")',
}
# Detecção automática (julgamento técnico — ver cabeçalho)
deteccao = {
    'B01': 'Detectável', 'B02': 'Não detectável', 'B03': 'Não detectável',
    'B04': 'Não detectável', 'B05': 'Não detectável', 'B06': 'Parcial',
    'B07': 'Parcial', 'B08': 'Parcial', 'B09': 'Não detectável',
}
det_cor = {'Detectável': '#2ca02c', 'Parcial': '#ffbb33', 'Não detectável': '#b2182b'}


def portais_da_barreira(tarefas_str):
    nums = sorted(set(int(n) for n in re.findall(r'T(\d)', str(tarefas_str))))
    return ' · '.join(portal_nome[n] for n in nums)


# ==================================================================
# GRÁFICO 1 — Síntese: severidade (criticidade) × categoria × portal
# ==================================================================
ordem = barr.sort_values(['criticidade', 'ID'], ascending=[False, True]).index.tolist()
y = np.arange(len(ordem))[::-1]   # mais grave no topo

fig, ax = plt.subplots(figsize=(13, 7))
for yi, bid in zip(y, ordem):
    crit = barr.loc[bid, 'criticidade']
    cat = barr.loc[bid, 'Categoria']
    ax.barh(yi, crit, color=cat_cor[cat], edgecolor='white', linewidth=1, zorder=2)
    # rótulo de severidade dentro/na ponta da barra
    ax.text(crit - 0.08, yi, f"{barr.loc[bid, 'rotulo_sev']} ({crit})",
            ha='right', va='center', fontsize=10, fontweight='bold', color='white')
    # portais afetados à direita
    ax.text(crit + 0.06, yi, portais_da_barreira(barr.loc[bid, 'tarefas']),
            ha='left', va='center', fontsize=10.5, fontweight='bold', color='#333')

ax.set_yticks(y)
ax.set_yticklabels([f'{bid}: {nome_curto[bid]}' for bid in ordem], fontsize=11)
ax.set_xlim(0, 5.2)
ax.set_xticks(range(0, 5))
ax.set_xlabel('Criticidade (escala Nielsen adaptada 0–4 — inferida dos relatos)   ↑ mais grave',
              fontsize=12, fontweight='bold')
ax.set_title('Síntese das barreiras de acessibilidade — severidade, categoria e portal afetado\n'
             '5 das 9 barreiras são catastróficas (crit. 4) e se concentram no Censo e no Mapa',
             fontsize=13.5, fontweight='bold', pad=12)
ax.grid(axis='x', linestyle='--', alpha=0.4)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
# Legenda de categorias (só as presentes)
cats_presentes = [c for c in cat_cor if (barr['Categoria'] == c).any()]
handles = [Patch(facecolor=cat_cor[c], label=f'{c} — {cat_label[c]}') for c in cats_presentes]
ax.legend(handles=handles, title='Categoria da barreira', loc='lower right',
          fontsize=10, title_fontsize=10, framealpha=0.95)
fig.text(0.5, -0.02,
         'Texto à direita de cada barra = portal(is) afetado(s). Criticidade inferida dos relatos '
         '(julgamento qualitativo, escala Nielsen adaptada). n=5, leitura exploratória.',
         ha='center', fontsize=9, color='#444', style='italic')
plt.tight_layout()
plt.savefig('g_barreiras_sintese_severidade_categoria.png', dpi=300, bbox_inches='tight')
plt.close(fig)
print('Salvo: g_barreiras_sintese_severidade_categoria.png')


# ==================================================================
# GRÁFICO 2 — Eficácia dos contornos (segmentada por severidade)
# ==================================================================
df['grupo_sev'] = np.where(df['criticidade'] == 4,
                           'Barreiras catastróficas\n(crit. 4)',
                           'Demais barreiras\n(crit. ≤ 3)')
tab = (df.groupby(['grupo_sev', 'eficacia']).size()
         .unstack(fill_value=0).reindex(columns=ef_ordem, fill_value=0))
# ordem: catastróficas em cima
ordem_sev = ['Barreiras catastróficas\n(crit. 4)', 'Demais barreiras\n(crit. ≤ 3)']
tab = tab.reindex(ordem_sev)

fig, ax = plt.subplots(figsize=(12, 5))
esquerda = np.zeros(len(tab))
ypos = np.arange(len(tab))
for ef in ef_ordem:
    vals = tab[ef].values
    ax.barh(ypos, vals, left=esquerda, color=ef_cor[ef], edgecolor='white',
            linewidth=1.2, label=ef, zorder=2)
    for i, v in enumerate(vals):
        if v > 0:
            ax.text(esquerda[i] + v / 2, ypos[i], str(int(v)), ha='center', va='center',
                    fontsize=14, fontweight='bold', color='white')
    esquerda += vals
for i in range(len(tab)):
    ax.text(esquerda[i] + 0.15, ypos[i], f'n={int(esquerda[i])} contornos',
            ha='left', va='center', fontsize=11, color='dimgray')

ax.set_yticks(ypos)
ax.set_yticklabels(tab.index, fontsize=12, fontweight='bold')
ax.set_xlabel('Nº de estratégias de contorno relatadas', fontsize=12, fontweight='bold')
ax.set_xlim(0, esquerda.max() + 2.5)
total = int(df.shape[0])
ax.set_title('Eficácia das estratégias de contorno do usuário de leitor de tela\n'
             f'Quando a barreira é catastrófica, o contorno quase sempre falha (de {total} contornos no total)',
             fontsize=13.5, fontweight='bold', pad=12)
ax.grid(axis='x', linestyle='--', alpha=0.4)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(title='Eficácia do contorno', loc='lower right', fontsize=10.5,
          title_fontsize=10.5, framealpha=0.95)
fig.text(0.5, -0.04,
         'Eficácia: Efetiva = objetivo atingido; Parcial = dado incompleto/impreciso ou com ajuda; '
         'Não efetiva = falhou. Contagem = todas as linhas de contorno do CSV (n=5 participantes).',
         ha='center', fontsize=9, color='#444', style='italic')
plt.tight_layout()
plt.savefig('g_eficacia_contornos.png', dpi=300, bbox_inches='tight')
plt.close(fig)
print('Salvo: g_eficacia_contornos.png')


# ==================================================================
# GRÁFICO 3 — Severidade × detectabilidade (barras 100% empilhadas)
# Relação agregada: quanto mais grave a barreira, menos a ferramenta detecta.
# ==================================================================
sev_info = [(4, 'Catastrófica'), (3, 'Maior'), (2, 'Menor')]   # mais grave → menos grave
det_classes = ['Detectável', 'Parcial', 'Não detectável']

# contagem severidade × detecção (recalculada do CSV)
cont = {crit: {d: 0 for d in det_classes} for crit, _ in sev_info}
for bid in barr.index:
    cont[barr.loc[bid, 'criticidade']][deteccao[bid]] += 1
totais = {crit: sum(cont[crit].values()) for crit, _ in sev_info}

fig, ax = plt.subplots(figsize=(12, 5.6))
ypos = list(range(len(sev_info)))[::-1]          # Catastrófica no topo
for (crit, rot), yp in zip(sev_info, ypos):
    n = totais[crit]
    esquerda = 0.0
    for d in det_classes:
        c = cont[crit][d]
        pct = 100 * c / n
        ax.barh(yp, pct, left=esquerda, color=det_cor[d], edgecolor='white',
                linewidth=1.2, zorder=2, hatch='//' if n == 1 else None)
        if c > 0:
            ax.text(esquerda + pct / 2, yp, f'{c} de {n}\n{pct:.0f}%',
                    ha='center', va='center', fontsize=11.5, fontweight='bold',
                    color='white')
        esquerda += pct
    # n do nível à direita (+ ressalva p/ n=1)
    if n == 1:
        ax.text(102, yp, 'n=1  ⚠ uma única barreira — não generalizar',
                ha='left', va='center', fontsize=10.5, color='#a00000', fontweight='bold')
    else:
        ax.text(102, yp, f'n={n}', ha='left', va='center', fontsize=11, color='dimgray')

ax.set_yticks(ypos)
ax.set_yticklabels([f'{rot}\n(crit. {crit})' for crit, rot in sev_info],
                   fontsize=12, fontweight='bold')
ax.set_xlim(0, 118)
ax.set_xticks(range(0, 101, 20))
ax.set_xticklabels([f'{v}%' for v in range(0, 101, 20)])
ax.set_xlabel('Proporção das barreiras do nível detectadas pelas ferramentas (ASES/WAVE)',
              fontsize=12, fontweight='bold')
ax.set_title('Quanto mais grave a barreira, menos as ferramentas automáticas a detectam\n'
             'Severidade × detectabilidade — as ferramentas cobrem o leve e falham no grave',
             fontsize=13.5, fontweight='bold', pad=12)
ax.grid(axis='x', linestyle='--', alpha=0.4)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='y', length=0)

# Legenda com direção explícita
handles = [
    Patch(facecolor=det_cor['Detectável'], label='Detectável — a ferramenta cobre'),
    Patch(facecolor=det_cor['Parcial'], label='Parcial — cobre em parte'),
    Patch(facecolor=det_cor['Não detectável'], label='Não detectável — escapa à ferramenta'),
]
ax.legend(handles=handles, title='Detecção por ASES/WAVE', loc='lower center',
          bbox_to_anchor=(0.5, -0.30), ncol=3, frameon=False,
          fontsize=10, title_fontsize=10)
fig.text(0.5, -0.05,
         'n=9 barreiras; severidade (Nielsen adaptada) e detecção inferidas dos relatos — julgamento '
         'qualitativo/técnico, leitura descritiva. Ferramentas estáticas acham falhas no HTML/DOM, mas '
         'não executam interação, não leem conteúdo dinâmico/embarcado nem julgam o sentido de rótulos. '
         'A faixa "Maior" tem só 1 barreira (hachurada) — não generalizar.',
         ha='center', fontsize=8.8, color='#444', style='italic')
plt.tight_layout()
plt.savefig('g3_severidade_vs_detectabilidade.png', dpi=300, bbox_inches='tight')
plt.close(fig)
print('Salvo: g3_severidade_vs_detectabilidade.png')


# ==================================================================
# Contagens recalculadas do CSV (para conferência / divergências)
# ==================================================================
print('\n--- Contagens lidas do CSV ---')
print(f'Barreiras (B-IDs únicos): {barr.shape[0]}')
print('Por categoria:', barr['Categoria'].value_counts().to_dict())
print('Por criticidade:', barr['criticidade'].value_counts().sort_index(ascending=False).to_dict())
print(f'Contornos (linhas): {df.shape[0]}')
print('Eficácia (total):', df['eficacia'].value_counts().reindex(ef_ordem).to_dict())
print('Eficácia × severidade:\n', tab)
print('Detecção (por barreira):', pd.Series(deteccao).value_counts().to_dict())
