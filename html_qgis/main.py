import sys
import importlib
from qgis.utils import iface

# 1. Caminho absoluto da sua pasta
caminho_pasta = r'C:\Users\LINES-COLAB\Documents\teste_classif\kml'

if caminho_pasta not in sys.path:
    sys.path.insert(0, caminho_pasta)

# 2. Importa e recarrega os módulos
import gerador_html
importlib.reload(gerador_html)

import interface
importlib.reload(interface)

from interface import TabelaHtmlDialog

# A GRANDE DIFERENÇA ESTÁ AQUI:
# Declaramos a variável como 'global' ANTES de criar a janela.
# Isso impede o Python de apagar o "cérebro" do plugin da memória!
global janela_plugin

# Se já houver uma janela aberta, fechamos antes de abrir a nova
if 'janela_plugin' in globals() and janela_plugin is not None:
    janela_plugin.close()

# Cria a janela e mostra
janela_plugin = TabelaHtmlDialog(iface.mainWindow())
janela_plugin.show()
