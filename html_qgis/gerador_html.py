# gerador_html.py
from collections import defaultdict

def formatar_numero(valor, sufixo=""):
    """Formata número no padrão brasileiro: 1.234,56"""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{texto}{sufixo}"

def processar_e_gerar_html(camada, campos_agrupar, campo_area, tem_subtotal, campo_sub, prefixo_sub, tit_agrup, tit_area, tit_perc):
    """Lê os dados da camada, agrupa e retorna a string HTML formatada."""
    
    grupos = defaultdict(lambda: defaultdict(float))
    total_geral = 0.0
    
    # Identificar os índices das colunas selecionadas
    idx_agrupar = [camada.fields().indexOf(c) for c in campos_agrupar]
    idx_area = camada.fields().indexOf(campo_area)
    idx_sub = camada.fields().indexOf(campo_sub) if tem_subtotal else -1
    
    # 1. Extração e Agrupamento Matemático
    for feature in camada.getFeatures():
        valores_linha = tuple(str(feature[i]) if feature[i] else "-" for i in idx_agrupar)
        area = float(feature[idx_area] or 0)
        
        if tem_subtotal and feature[idx_sub]:
            val_sub = str(feature[idx_sub])
        else:
            val_sub = "Geral"
            
        grupos[val_sub][valores_linha] += area
        total_geral += area
        
    # 2. Construção Estrutural do HTML
    while len(tit_agrup) < len(campos_agrupar):
        tit_agrup.append("Coluna")
        
    th_agrupados = "".join(f"<th>{t}</th>" for t in tit_agrup[:len(campos_agrupar)])
    
    html = f"""<style>
  table {{ width: auto; border-collapse: collapse; font-family: 'Segoe UI', Calibri, sans-serif; font-size: 40px; letter-spacing: 0px; background-color: white; }}
  th {{ background-color: #0d2a63; color: white; padding: 10px 25px; text-align: center; border: 2px solid #000; font-weight: bold; white-space: nowrap; font-size: 45px; }}
  td {{ padding: 6px 25px; border: 2px solid #000; color: #000; white-space: nowrap; font-size: 45px; }}
  .subtotal td {{ font-weight: bold; background-color: #e6e6e6; }}
  .total td {{ font-weight: bold; background-color: #0d2a63; color: white !important; font-size: 50px; }}
  .total-label {{ text-align: left; }}
  .num {{ text-align: right; }}
  .center {{ text-align: center; }}
  body {{ margin: 0; background-color: transparent; }}
</style>
<table>
  <tr>
    {th_agrupados}
    <th>{tit_area}</th>
    <th>{tit_perc}</th>
  </tr>"""

    for val_sub in sorted(grupos.keys()):
        subtotal_area = 0.0
        linhas = sorted(grupos[val_sub].items(), key=lambda x: str(x[0]))
        
        for valores_linha, area in linhas:
            subtotal_area += area
            percentagem = (area / total_geral) * 100 if total_geral > 0 else 0
            
            tds_agrupados = "".join(f"<td>{v}</td>" for v in valores_linha)
            html += f"""
  <tr>
    {tds_agrupados}
    <td class="num">{formatar_numero(area)}</td>
    <td class="num">{formatar_numero(percentagem, "%")}</td>
  </tr>"""

        if tem_subtotal:
            perc_sub = (subtotal_area / total_geral) * 100 if total_geral > 0 else 0
            colspan = len(campos_agrupar)
            texto_label = f"{prefixo_sub} {val_sub}".strip() if prefixo_sub else val_sub
            
            html += f"""
  <tr class="subtotal">
    <td colspan="{colspan}" class="total-label">{texto_label}</td>
    <td class="num">{formatar_numero(subtotal_area)}</td>
    <td class="num">{formatar_numero(perc_sub, "%")}</td>
  </tr>"""

    colspan_total = len(campos_agrupar)
    html += f"""
  <tr class="total">
    <td colspan="{colspan_total}" class="total-label">Total Geral</td>
    <td class="num">{formatar_numero(total_geral)}</td>
    <td class="num">100,00%</td>
  </tr>
</table>"""

    return html