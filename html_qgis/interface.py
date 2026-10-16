# interface.py
from qgis.PyQt.QtWidgets import (QApplication, QDialog, QVBoxLayout, QFormLayout, 
                                 QLineEdit, QPushButton, QHBoxLayout,
                                 QListWidget, QListWidgetItem, QAbstractItemView,
                                 QDialogButtonBox, QMessageBox, QCheckBox, QLabel)
from qgis.PyQt.QtCore import Qt
from qgis.gui import QgsMapLayerComboBox, QgsFieldComboBox
from qgis.core import QgsMapLayerProxyModel, QgsProject

# Importar o nosso motor HTML
from gerador_html import processar_e_gerar_html

class DialogoSelecaoCampos(QDialog):
    def __init__(self, camada, campos_atuais, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar e Ordenar Campos")
        self.resize(350, 450)
        
        layout = QVBoxLayout(self)
        
        lbl_instrucao = QLabel("Marque os campos desejados.\nArraste os itens para cima ou para baixo para\ndefinir a ordem das colunas na tabela.")
        layout.addWidget(lbl_instrucao)
        
        self.lista_campos = QListWidget(self)
        self.lista_campos.setDragDropMode(QAbstractItemView.InternalMove)
        
        campos_restantes = [f.name() for f in camada.fields() if f.name() not in campos_atuais]
        
        for nome_campo in campos_atuais:
            if camada.fields().indexOf(nome_campo) != -1:
                item = QListWidgetItem(nome_campo)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                self.lista_campos.addItem(item)
                
        for nome_campo in campos_restantes:
            item = QListWidgetItem(nome_campo)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
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
        self.resize(550, 520)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.cb_camada = QgsMapLayerComboBox(self)
        self.cb_camada.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.cb_camada.setProject(QgsProject.instance())
        form_layout.addRow("Camada de Entrada:", self.cb_camada)
        
        box_agrupar = QHBoxLayout()
        self.txt_campos_agrupar = QLineEdit(self)
        self.txt_campos_agrupar.setPlaceholderText("Deixe vazio ou escolha os campos...")
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
        
        box_area = QHBoxLayout()
        self.txt_campos_area = QLineEdit(self)
        self.txt_campos_area.setPlaceholderText("Ex: AREA_PIQUE, AREA_USO_P")
        self.btn_selecionar_area = QPushButton("...", self)
        self.btn_selecionar_area.setFixedWidth(40)
        self.btn_selecionar_area.clicked.connect(self.abrir_janela_campos_area)
        box_area.addWidget(self.txt_campos_area)
        box_area.addWidget(self.btn_selecionar_area)
        form_layout.addRow("Campo(s) de Área (Soma):", box_area)
        
        # NOVA OPÇÃO DE DEDUPLICAÇÃO
        self.chk_deduplicar = QCheckBox("1º Campo de Área é Fixo/Total (Remover duplicadas)")
        self.chk_deduplicar.setChecked(True) # Ligado por padrão, ótimo para área de piquetes!
        self.chk_deduplicar.setToolTip("Marque isto quando usar interseção. Evita que a área do polígono original seja somada várias vezes.")
        form_layout.addRow("", self.chk_deduplicar)
        
        self.chk_perc = QCheckBox("Gerar coluna de Área (%)")
        self.chk_perc.setChecked(False)
        form_layout.addRow("", self.chk_perc)
        
        # Titulos Iniciais (Opcionais)
        self.txt_titulo_agrupar = QLineEdit(self)
        self.txt_titulo_agrupar.setPlaceholderText("Deixe vazio para usar o nome da coluna")
        
        self.txt_titulo_area = QLineEdit(self)
        self.txt_titulo_area.setPlaceholderText("Deixe vazio para usar o nome da coluna")
        
        self.txt_titulo_perc = QLineEdit("Área (%)", self)
        self.txt_titulo_perc.setEnabled(False)
        
        form_layout.addRow("Títulos Iniciais (Separe por ,):", self.txt_titulo_agrupar)
        form_layout.addRow("Título(s) de Área (Separe por ,):", self.txt_titulo_area)
        form_layout.addRow("Título Coluna Percentual:", self.txt_titulo_perc)
        
        self.chk_perc.toggled.connect(self.txt_titulo_perc.setEnabled)
        
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
        if camada:
            self.cb_campo_subtotal.setLayer(camada)
        self.txt_campos_agrupar.clear()
        self.txt_campos_area.clear()

    def abrir_janela_campos(self):
        camada = self.cb_camada.currentLayer()
        if not camada: return
        texto_atual = self.txt_campos_agrupar.text()
        campos_atuais = [c.strip() for c in texto_atual.split(",") if c.strip()]
        dialogo = DialogoSelecaoCampos(camada, campos_atuais, self)
        if dialogo.exec_():
            self.txt_campos_agrupar.setText(", ".join(dialogo.get_campos_selecionados()))

    def abrir_janela_campos_area(self):
        camada = self.cb_camada.currentLayer()
        if not camada: return
        texto_atual = self.txt_campos_area.text()
        campos_atuais = [c.strip() for c in texto_atual.split(",") if c.strip()]
        dialogo = DialogoSelecaoCampos(camada, campos_atuais, self)
        dialogo.setWindowTitle("Selecionar Campos Numéricos (Soma)")
        if dialogo.exec_():
            self.txt_campos_area.setText(", ".join(dialogo.get_campos_selecionados()))

    def executar_geracao(self):
        camada = self.cb_camada.currentLayer()
        campos_agrupar = [c.strip() for c in self.txt_campos_agrupar.text().split(",") if c.strip()]
        campos_area = [c.strip() for c in self.txt_campos_area.text().split(",") if c.strip()]
        
        tem_subtotal = self.chk_subtotal.isChecked()
        gerar_perc = self.chk_perc.isChecked()
        deduplicar_primeiro = self.chk_deduplicar.isChecked() # Captura a nova opção
        campo_sub = self.cb_campo_subtotal.currentField()
        prefixo_sub = self.txt_prefixo_sub.text().strip()
        
        if not camada:
            QMessageBox.warning(self, "Aviso", "Nenhuma camada selecionada na 'Camada de Entrada'!")
            return
            
        if not campos_agrupar:
            QMessageBox.warning(self, "Aviso", "Por favor, defina os campos a dissolver!")
            return
            
        if not campos_area:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione os 'Campos de Área (Soma)'!")
            return
            
        tit_agrup = [t.strip() for t in self.txt_titulo_agrupar.text().split(",") if t.strip()]
        tit_areas = [t.strip() for t in self.txt_titulo_area.text().split(",") if t.strip()]
        tit_perc = self.txt_titulo_perc.text().strip() or "Área (%)"

        # Passa a nova variável para a função principal
        html_final = processar_e_gerar_html(
            camada, campos_agrupar, campos_area, tem_subtotal, 
            campo_sub, prefixo_sub, tit_agrup, tit_areas, gerar_perc, tit_perc, deduplicar_primeiro
        )

        QApplication.clipboard().setText(html_final)
        QMessageBox.information(self, "Sucesso!", "HTML gerado e copiado!\nPode colar (Ctrl+V) no seu Quadro HTML do QGIS.")
        self.accept()
