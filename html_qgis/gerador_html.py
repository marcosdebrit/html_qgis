# gerador_html.py
from collections import defaultdict

def formatar_numero(valor, sufixo=""):
    """Formata número no padrão brasileiro: 1.234,56"""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{texto}{sufixo}"

def processar_e_gerar_html(camada, campos_agrupar, campos_area, tem_subtotal, campo_sub, prefixo_sub, tit_agrup, tit_areas, gerar_perc, tit_perc, deduplicar_primeiro):
    """Lê os dados da camada, agrupa e retorna a string HTML formatada."""
    
    # Se os títulos estiverem vazios, puxa automaticamente o nome das colunas da camada
    if not tit_agrup:
        tit_agrup = campos_agrupar.copy()
    if not tit_areas:
        tit_areas = campos_area.copy()
        
    # Garante que não faltam títulos
    while len(tit_agrup) < len(campos_agrupar):
        tit_agrup.append("Coluna")
    while len(tit_areas) < len(campos_area):
        tit_areas.append("Área")

    grupos = defaultdict(lambda: defaultdict(lambda: [0.0] * len(campos_area)))
    
    idx_agrupar = [camada.fields().indexOf(c) for c in campos_agrupar]
    idx_areas = [camada.fields().indexOf(c) for c in campos_area]
    idx_sub = camada.fields().indexOf(campo_sub) if tem_subtotal else -1
    
    # 1. Extração e Agrupamento Matemático
    for feature in camada.getFeatures():
        valores_linha = tuple(str(feature[i]) if feature[i] else "-" for i in idx_agrupar)
        
        if tem_subtotal and feature[idx_sub]:
            val_sub = str(feature[idx_sub])
        else:
            val_sub = "Geral"
            
        for j, idx in enumerate(idx_areas):
            try:
                valor_cru = str(feature[idx] or 0).replace(',', '.')
                area = float(valor_cru)
            except ValueError:
                area = 0.0
                
            # LÓGICA DE DEDUPLICAÇÃO (Para resolver o problema da Interseção GIS)
            if j == 0 and deduplicar_primeiro:
                # Se for a área total do polígono, pegamos apenas o valor único/maior
                # Em vez de somar os fragmentos duplicados
                if area > grupos[val_sub][valores_linha][j]:
                    grupos[val_sub][valores_linha][j] = area
            else:
                # Para as áreas de uso (fragmentos), somamos normalmente
                grupos[val_sub][valores_linha][j] += area
                
    # Recalcular o Total Geral com base nas linhas JÁ deduplicadas e corrigidas
    total_geral = [0.0] * len(campos_area)
    for val_sub in grupos.keys():
        for valores_linha, areas in grupos[val_sub].items():
            for j in range(len(campos_area)):
                total_geral[j] += areas[j]
            
    # 2. Construção Estrutural do HTML
    th_agrupados = "".join(f"<th>{t}</th>" for t in tit_agrup[:len(campos_agrupar)])
    th_areas = "".join(f"<th>{t}</th>" for t in tit_areas[:len(campos_area)])
    th_perc = f"<th>{tit_perc}</th>" if gerar_perc else ""

    # NOTA: AS CHAVES {} DO CSS DEVEM ESTAR DUPLICADAS {{ }} PARA FUNCIONAR NO PYTHON!
    html = f"""<style>
  table {{ 
      width: auto; /* Ajusta a largura ao conteúdo, não à caixa */
      border-collapse: collapse; 
      font-family: 'Segoe UI', Calibri, sans-serif; 
      font-size: 30px; 
      letter-spacing: 0px; 
      background-color: white; /* Garante fundo branco nas células */
  }}
  th {{ background-color: #0d2a63; color: white; padding: 10px 25px; text-align: center; border: 2px solid #000; font-weight: bold; white-space: nowrap; font-size: 30px; }}
  td {{ padding: 6px 25px; border: 2px solid #000; color: #000; white-space: nowrap; font-size: 30px; }}
  .subtotal td {{ font-weight: bold; background-color: #e6e6e6; }}
  .total td {{ font-weight: bold; background-color: #0d2a63; color: white !important; font-size: 40px; }}
  .total-label {{ text-align: left; }}
  .num {{ text-align: right; }}
  .center {{ text-align: center; }}
  body {{ margin: 0; background-color: transparent; }}
</style>
<table>
  <tr>
    {th_agrupados}
    {th_areas}
    {th_perc}
  </tr>"""

    for val_sub in sorted(grupos.keys()):
        subtotal_area = [0.0] * len(campos_area)
        linhas = sorted(grupos[val_sub].items(), key=lambda x: str(x[0]))
        
        for valores_linha, areas in linhas:
            for j in range(len(campos_area)):
                subtotal_area[j] += areas[j]
            
            tds_agrupados = "".join(f"<td>{v}</td>" for v in valores_linha)
            tds_areas = "".join(f'<td class="num">{formatar_numero(a)}</td>' for a in areas)
            
            td_perc = ""
            if gerar_perc:
                perc = (areas[0] / total_geral[0]) * 100 if total_geral[0] > 0 else 0
                td_perc = f'<td class="num">{formatar_numero(perc, "%")}</td>'
                
            html += f"""
  <tr>
    {tds_agrupados}
    {tds_areas}
    {td_perc}
  </tr>"""

        if tem_subtotal:
            colspan = len(campos_agrupar)
            texto_label = f"{prefixo_sub} {val_sub}".strip() if prefixo_sub else val_sub
            
            tds_sub_areas = "".join(f'<td class="num">{formatar_numero(a)}</td>' for a in subtotal_area)
            td_sub_perc = ""
            if gerar_perc:
                perc_sub = (subtotal_area[0] / total_geral[0]) * 100 if total_geral[0] > 0 else 0
                td_sub_perc = f'<td class="num">{formatar_numero(perc_sub, "%")}</td>'
                
            html += f"""
  <tr class="subtotal">
    <td colspan="{colspan}" class="total-label">{texto_label}</td>
    {tds_sub_areas}
    {td_sub_perc}
  </tr>"""

    colspan_total = len(campos_agrupar)
    tds_tot_areas = "".join(f'<td class="num">{formatar_numero(a)}</td>' for a in total_geral)
    td_tot_perc = f'<td class="num">100,00%</td>' if gerar_perc else ""
    
    html += f"""
  <tr class="total">
    <td colspan="{colspan_total}" class="total-label">Total Geral</td>
    {tds_tot_areas}
    {td_tot_perc}
  </tr>
</table>"""

    return html
