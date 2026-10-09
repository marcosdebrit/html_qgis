import sys
import importlib

# 1. Caminho absoluto da sua pasta (retirado do seu próprio print)
caminho_pasta = '/Users/marcosdebrito/Documents/html_qgis'

# 2. Adiciona o caminho ao sistema do QGIS
if caminho_pasta not in sys.path:
    sys.path.append(caminho_pasta)

# 3. Importa os seus módulos e FORÇA o recarregamento (muito importante!)
import gerador_html
importlib.reload(gerador_html)

import interface
importlib.reload(interface)

# 4. Importa a janela e o iface do QGIS
from interface import TabelaHtmlDialog
from qgis.utils import iface

def executar():
    # Cria a janela e mostra
    janela = TabelaHtmlDialog(iface.mainWindow())
    janela.show()

# No QGIS Console, podemos chamar a função diretamente
executar()