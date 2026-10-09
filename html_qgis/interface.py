# interface.py
from qgis.PyQt.QtWidgets import (QApplication, QDialog, QVBoxLayout, QFormLayout, 
                                 QLineEdit, QPushButton, QHBoxLayout,
                                 QListWidget, QListWidgetItem, QAbstractItemView,
                                 QDialogButtonBox, QMessageBox, QCheckBox)
from qgis.PyQt.QtCore import Qt
from qgis.gui import QgsMapLayerComboBox, QgsFieldComboBox
from qgis.core import QgsMapLayerProxyModel

# Importar o nosso motor HTML
from gerador_html import processar_e_gerar_html

class DialogoSelecaoCampos(QDialog):
    def __init__(self, camada, campos_atuais, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dissolver campo(s)")
        self.resize(300, 400)
        
        layout = QVBoxLayout(self)
        self.lista_campos = QListWidget(self)
        self.lista_campos.setSelectionMode(QAbstractItemView.NoSelection)
        
        for campo in camada.fields():
            item = QListWidgetItem(campo.name())
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if campo.name() in campos_atuais else Qt.Unchecked)
            self.lista_campos.addItem(item)
            
        layout.addWidget(self.lista_campos)
        
        btn_layout = QHBoxLayout()
        btn_todos = QPushButton("Selecionar todos")
        btn_limpar = QPushButton("Remover Seleção")
        btn_todos.clicked.connect(self.selecionar_todos)
        btn_limpar.clicked.connect(self.remover_selecao)
        btn_layout.addWidget(btn_todos)
        btn_layout.addWidget(btn_limpar)
        layout.addLayout(btn_layout)
        
        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)
        
    def selecionar_todos(self):
        for i in range(self.lista_campos.count()):
            self.lista_campos.item(i).setCheckState(Qt.Checked)
            
    def remover_selecao(self):
        for i in range(self.lista_campos.count()):
            self.lista_campos.item(i).setCheckState(Qt.Unchecked)
            
    def get_campos_selecionados(self):
        return [self.lista_campos.item(i).text() for i in range(self.lista_campos.count()) 
                if self.lista_campos.item(i).checkState() == Qt.Checked]


class TabelaHtmlDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerador de Tabela HTML - Lines Brasil")
        self.resize(550, 420)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.cb_camada = QgsMapLayerComboBox(self)
        self.cb_camada.setFilters(QgsMapLayerProxyModel.VectorLayer)
        form_layout.addRow("Camada de Entrada:", self.cb_camada)
        
        box_agrupar = QHBoxLayout()
        self.txt_campos_agrupar = QLineEdit(self)
        self.txt_campos_agrupar.setReadOnly(True)
        self.btn_selecionar = QPushButton("...", self)
        self.btn_selecionar.setFixedWidth(40)
        self.btn_selecionar.clicked.connect(self.abrir_janela_campos)
        box_agrupar.addWidget(self.txt_campos_agrupar)
        box_agrupar.addWidget(self.btn_selecionar)
        form_layout.addRow("Dissolver campo(s):", box_agrupar)
        
        box_subtotal = QHBoxLayout()
        self.chk_subtotal = QCheckBox("Agrupar/Subtotal por:")
        self.cb_campo_subtotal = QgsFieldComboBox(self)
        self.cb_campo_subtotal.setEnabled(False)
        box_subtotal.addWidget(self.chk_subtotal)
        box_subtotal.addWidget(self.cb_campo_subtotal)
        form_layout.addRow("", box_subtotal)
        
        self.txt_prefixo_sub = QLineEdit("Subtotal", self)
        self.txt_prefixo_sub.setEnabled(False)
        self.txt_prefixo_sub.setPlaceholderText("Ex: Subtotal (ou deixe vazio)")
        form_layout.addRow("Prefixo da linha:", self.txt_prefixo_sub)
        
        self.chk_subtotal.toggled.connect(self.cb_campo_subtotal.setEnabled)
        self.chk_subtotal.toggled.connect(self.txt_prefixo_sub.setEnabled)
        
        self.cb_campo_area = QgsFieldComboBox(self)
        form_layout.addRow("Campo de Área (Soma):", self.cb_campo_area)
        
        self.txt_titulo_agrupar = QLineEdit("Retiro, Nº Piquete, Nome Piquete", self)
        self.txt_titulo_area = QLineEdit("Área Cercada (ha)", self)
        self.txt_titulo_perc = QLineEdit("Área (%)", self)
        form_layout.addRow("Títulos Iniciais (Separe por ,):", self.txt_titulo_agrupar)
        form_layout.addRow("Título Coluna de Área:", self.txt_titulo_area)
        form_layout.addRow("Título Coluna Percentual:", self.txt_titulo_perc)
        
        layout.addLayout(form_layout)
        
        self.cb_camada.layerChanged.connect(self.ao_mudar_camada)
        
        btn_layout = QHBoxLayout()
        self.btn_gerar = QPushButton("Gerar HTML e Copiar", self)
        self.btn_cancelar = QPushButton("Cancelar", self)
        self.btn_gerar.clicked.connect(self.executar_geracao)
        self.btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_gerar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)
        
        self.ao_mudar_camada()

    def ao_mudar_camada(self):
        camada = self.cb_camada.currentLayer()
        self.cb_campo_area.setLayer(camada)
        self.cb_campo_subtotal.setLayer(camada)
        self.txt_campos_agrupar.clear()

    def abrir_janela_campos(self):
        camada = self.cb_camada.currentLayer()
        if not camada: return
        texto_atual = self.txt_campos_agrupar.text()
        campos_atuais = [c.strip() for c in texto_atual.split(",") if c.strip()]
        dialogo = DialogoSelecaoCampos(camada, campos_atuais, self)
        if dialogo.exec_():
            self.txt_campos_agrupar.setText(", ".join(dialogo.get_campos_selecionados()))

    def executar_geracao(self):
        """Coleta as informações da janela e envia para o Motor no outro ficheiro"""
        camada = self.cb_camada.currentLayer()
        campo_area = self.cb_campo_area.currentField()
        campos_agrupar = [c.strip() for c in self.txt_campos_agrupar.text().split(",") if c.strip()]
        
        tem_subtotal = self.chk_subtotal.isChecked()
        campo_sub = self.cb_campo_subtotal.currentField()
        prefixo_sub = self.txt_prefixo_sub.text().strip()
        
        if not camada or not campos_agrupar or not campo_area:
            QMessageBox.warning(self, "Aviso", "Por favor, preencha as camadas e campos a dissolver!")
            return
            
        tit_agrup = [t.strip() for t in self.txt_titulo_agrupar.text().split(",")]
        tit_area = self.txt_titulo_area.text()
        tit_perc = self.txt_titulo_perc.text()

        # Chama a função isolada que está no gerador_html.py
        html_final = processar_e_gerar_html(
            camada, campos_agrupar, campo_area, tem_subtotal, 
            campo_sub, prefixo_sub, tit_agrup, tit_area, tit_perc
        )

        QApplication.clipboard().setText(html_final)
        QMessageBox.information(self, "Sucesso!", "HTML gerado e copiado!\nPode colar (Ctrl+V) no seu Quadro HTML do QGIS.")
        self.accept()