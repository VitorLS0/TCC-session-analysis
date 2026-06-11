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
from matplotlib.patches import Patch, Rectangle

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
# GRÁFICO 3 — Matriz: barreira × detecção automática (+ severidade)
# ==================================================================
ordem3 = barr.sort_values(['criticidade', 'ID'], ascending=[False, True]).index.tolist()
y3 = np.arange(len(ordem3))[::-1]
# escala de cor da criticidade (mais escuro = mais grave)
crit_cor = {2: '#fee08b', 3: '#fc8d59', 4: '#b30000'}

fig, ax = plt.subplots(figsize=(12, 7))
x_sev, x_det = 0.0, 1.05
cw = 0.92
for yi, bid in zip(y3, ordem3):
    crit = barr.loc[bid, 'criticidade']
    det = deteccao[bid]
    # célula severidade
    ax.add_patch(Rectangle((x_sev - cw / 2, yi - 0.42), cw, 0.84,
                           facecolor=crit_cor[crit], edgecolor='white', lw=2, zorder=2))
    ax.text(x_sev, yi, f'{barr.loc[bid, "rotulo_sev"]}\n({crit})', ha='center', va='center',
            fontsize=9.5, fontweight='bold', color='white' if crit == 4 else '#333')
    # célula detecção
    ax.add_patch(Rectangle((x_det - cw / 2, yi - 0.42), cw, 0.84,
                           facecolor=det_cor[det], edgecolor='white', lw=2, zorder=2))
    ax.text(x_det, yi, det, ha='center', va='center', fontsize=10,
            fontweight='bold', color='white')

ax.set_xlim(-0.7, 1.75)
ax.set_ylim(-0.7, len(ordem3) - 0.3)
ax.set_yticks(y3)
ax.set_yticklabels([f'{bid}: {nome_curto[bid]}' for bid in ordem3], fontsize=11)
ax.set_xticks([x_sev, x_det])
ax.set_xticklabels(['Severidade\n(criticidade)', 'Detecção por\nASES / WAVE'],
                   fontsize=12, fontweight='bold')
ax.xaxis.set_ticks_position('top')
ax.tick_params(axis='x', length=0)
ax.tick_params(axis='y', length=0)
for spine in ax.spines.values():
    spine.set_visible(False)

# Destaque da mensagem central
n_cat = int((barr['criticidade'] == 4).sum())
n_cat_nd = sum(1 for b in ordem3 if barr.loc[b, 'criticidade'] == 4 and deteccao[b] == 'Não detectável')
n_cat_p = sum(1 for b in ordem3 if barr.loc[b, 'criticidade'] == 4 and deteccao[b] == 'Parcial')
ax.set_title('As barreiras mais graves escapam das ferramentas automáticas\n'
             f'Das {n_cat} barreiras catastróficas, NENHUMA é plenamente detectável '
             f'({n_cat_nd} não detectáveis, {n_cat_p} parciais)',
             fontsize=13.5, fontweight='bold', pad=18)
# Legenda de detecção
handles = [Patch(facecolor=det_cor[k], label=k) for k in ['Detectável', 'Parcial', 'Não detectável']]
ax.legend(handles=handles, title='Detecção automática', loc='center left',
          bbox_to_anchor=(1.0, 0.5), fontsize=10, title_fontsize=10, framealpha=0.95)
fig.text(0.5, 0.005,
         'Classificação de detecção = julgamento técnico do autor: ferramentas estáticas (ASES/WAVE) '
         'acham falhas no HTML/DOM, mas não executam interação, não leem conteúdo dinâmico/embarcado '
         'nem julgam o sentido de rótulos. Linhas ordenadas da mais à menos grave.',
         ha='center', fontsize=9, color='#444', style='italic')
plt.tight_layout()
plt.savefig('g3_matriz_deteccao_vs_severidade.png', dpi=300, bbox_inches='tight')
plt.close(fig)
print('Salvo: g3_matriz_deteccao_vs_severidade.png')


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
