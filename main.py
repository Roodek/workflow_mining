import pm4py
import os
import sys
from PyQt5 import QtWidgets
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QBoxLayout, QVBoxLayout, QLabel, QPlainTextEdit, \
    QGridLayout, QLineEdit, QCheckBox, QRadioButton
import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.util import func as functools
from pm4py.visualization.process_tree import visualizer as pt_visualizer
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.discovery.alpha import algorithm as alpha_miner
from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
from pm4py.objects.conversion.process_tree import converter as pt_converter
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.heuristics_net import visualizer as hn_visualizer

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout
from enum import Enum

class MINER_TYPE(Enum):
    INDUCTIVE_MINER = 0
    ALPHA_MINER = 1
    HEURISTIC_MINER = 2
    CORRELATION_MINER=3

class Window(QWidget):

    def __init__(self):
        super().__init__()

        self.selected_file=''
        self.event_log = None
        self.filter_fields={}
        self.selected_miner=MINER_TYPE.INDUCTIVE_MINER

        main_box = QVBoxLayout()
        self.grid = QGridLayout()
        self.btn_open_file = QPushButton("Open file")
        self.btn_open_file.setGeometry(50, 50, 70, 20)
        self.btn_open_file.clicked.connect(self.btn_open_csv_file)

        self.btn_draw_bpmn = QPushButton("Draw bpmn model")
        self.btn_draw_bpmn.setGeometry(50, 50, 70, 20)
        self.btn_draw_bpmn.clicked.connect(self.show_process_bpmn)
        self.btn_draw_bpmn.setEnabled(len(self.selected_file) > 0)

        self.btn_draw_process_tree = QPushButton("Draw process tree")
        self.btn_draw_process_tree.setGeometry(50, 50, 70, 20)
        self.btn_draw_process_tree.clicked.connect(self.show_process_tree)
        self.btn_draw_process_tree.setEnabled(len(self.selected_file) > 0)

        self.btn_draw_petri_net = QPushButton("Draw petri net")
        self.btn_draw_petri_net.setGeometry(50, 50, 70, 20)
        self.btn_draw_petri_net.clicked.connect(self.show_petri_net)
        self.btn_draw_petri_net.setEnabled(len(self.selected_file) > 0)

        self.l1 = QLabel()
        self.l1.setText(self.selected_file)

        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.btn_open_file)
        hbox1.addStretch()

        self.dependency_threshold_box = QHBoxLayout()
        self.dependency_threshold_box.addWidget(QLabel("heuristic threshold value(used in heuristic miner, max value 1.00)"))
        self.dependency_threshold_input = QLineEdit()
        self.dependency_threshold_input.setInputMask('9.99')
        self.dependency_threshold_input.setText(str(0.5))
        self.dependency_threshold_box.addWidget(self.dependency_threshold_input)
        self.dependency_threshold_input.setEnabled(False)

        self.radiobtn_inductive = QRadioButton("inductive miner algorithm")
        self.radiobtn_alpha = QRadioButton("alpha miner algorithm")
        self.radiobtn_heuristic = QRadioButton("heuristic miner algorithm")
        self.radiobtn_correlation = QRadioButton("correlation miner algorithm")

        self.radiobtn_inductive.toggled.connect(self.miner_changed)
        self.radiobtn_alpha.toggled.connect(self.miner_changed)
        self.radiobtn_heuristic.toggled.connect(self.miner_changed)
        self.radiobtn_correlation.toggled.connect(self.miner_changed)

        self.radiobtn_inductive.setChecked(True)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.radiobtn_inductive)
        hbox2.addWidget(self.radiobtn_alpha)
        hbox2.addWidget(self.radiobtn_heuristic)
        hbox2.addWidget(self.radiobtn_correlation)



        main_box.addLayout(hbox1)
        main_box.addLayout(hbox2)
        main_box.addLayout(self.dependency_threshold_box)
        hbox1.addWidget(self.l1)
        main_box.addWidget(self.terminal)

        main_box.addLayout(self.grid)
        hbox = QHBoxLayout()
        main_box.addLayout(hbox)

        hbox.addWidget(self.btn_draw_bpmn)
        hbox.addWidget(self.btn_draw_process_tree)
        hbox.addWidget(self.btn_draw_petri_net)

        self.setLayout(main_box)
        self.resize(200, 100)
        self.move(500, 500)
        self.setWindowTitle('Workflow-mining')

        self.show()

    def miner_changed(self):
        radio_btn = self.sender()
        if radio_btn.isChecked():
            if radio_btn == self.radiobtn_inductive:
                self.selected_miner = MINER_TYPE.INDUCTIVE_MINER
                self.update_buttons()
            elif radio_btn == self.radiobtn_alpha:
                self.selected_miner = MINER_TYPE.ALPHA_MINER
                self.update_buttons()
            elif radio_btn == self.radiobtn_heuristic:
                self.selected_miner = MINER_TYPE.HEURISTIC_MINER
                self.update_buttons()
            elif radio_btn == self.radiobtn_correlation:
                self.selected_miner = MINER_TYPE.CORRELATION_MINER
                self.update_buttons()

    def show_process_bpmn(self):
        if self.selected_miner == MINER_TYPE.INDUCTIVE_MINER:
            self.visualize_inductive_bpmn()
        elif self.selected_miner == MINER_TYPE.ALPHA_MINER:
            pass
        elif self.selected_miner == MINER_TYPE.HEURISTIC_MINER:
            pass
        elif self.selected_miner == MINER_TYPE.CORRELATION_MINER:
            pass

    def visualize_inductive_bpmn(self):
        process_tree = pm4py.discover_process_tree_inductive(self.event_log)
        bpmn_model = pm4py.convert_to_bpmn(process_tree)
        pm4py.view_bpmn(bpmn_model)

    def show_process_tree(self):
        tree = inductive_miner.apply_tree(self.event_log)
        gviz = pt_visualizer.apply(tree)
        pt_visualizer.view(gviz)

    def show_petri_net(self):
        if self.selected_miner == MINER_TYPE.INDUCTIVE_MINER:
            self.visualize_inductive_pn()
        elif self.selected_miner == MINER_TYPE.ALPHA_MINER:
            self.visualize_alpha_pn()
        elif self.selected_miner == MINER_TYPE.HEURISTIC_MINER:
            self.visualize_heuristic_net()
        elif self.selected_miner == MINER_TYPE.CORRELATION_MINER:
            pass

    def visualize_inductive_pn(self):
        tree = inductive_miner.apply_tree(self.event_log)
        net, initial_marking, final_marking = pt_converter.apply(tree, variant=pt_converter.Variants.TO_PETRI_NET)
        gviz = pn_visualizer.apply(net, initial_marking, final_marking)
        pn_visualizer.view(gviz)

    def visualize_heuristic_net(self):
        # heu_net = heuristics_miner.apply_heu(self.event_log, parameters={
        #     heuristics_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.99})
        # gviz = hn_visualizer.apply(heu_net)
        # hn_visualizer.view(gviz)
        net, im, fm = heuristics_miner.apply(self.event_log, parameters={
            heuristics_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.5})

        gviz = pn_visualizer.apply(net, im, fm)
        pn_visualizer.view(gviz)

    def visualize_alpha_pn(self):
        net, initial_marking, final_marking = alpha_miner.apply(self.event_log)
        gviz = pn_visualizer.apply(net,initial_marking,final_marking)
        pn_visualizer.view(gviz)

    def get_csv_event_log(self, path):
        log_csv = pd.read_csv(path, sep=';')
        log_csv = pm4py.format_dataframe(log_csv, case_id='case_id', activity_key='activity', timestamp_key='timestamp',
                                         timest_format='%Y-%m-%d- %H:%M:%S%z')
        parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: 'case:concept:name'}
        self.event_log = log_converter.apply(log_csv, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)
        log_csv = log_csv.sort_values('time:timestamp')
        self.event_log = log_converter.apply(log_csv)
        self.terminal.appendPlainText('model loaded')
        self.add_column_filter_fields(log_csv)

    def add_column_filter_fields(self,csv):
        self.terminal.appendPlainText("event attributes, first 3 rows")
        self.terminal.appendPlainText(csv.head(3).to_string())
        for col in csv.columns:
            if 'index' in col:
                continue
            self.add_filter_by_attr_field(col)

    def add_filter_by_attr_field(self,attr):

        if 'timestamp' in attr:
            pass
        else:
            self.filter_fields[attr] = (QCheckBox(attr), QLineEdit())
            self.grid.addWidget(self.filter_fields[attr][0], 0, len(self.filter_fields) - 1)
            self.grid.addWidget(self.filter_fields[attr][1], 1,len(self.filter_fields)-1)

    def get_filter_attr_text_value(self,attr):
        return self.filter_fields[attr][1].text()

    def get_attributes_to_filter(self):
        fields_to_filter={}
        for i in self.filter_fields:
            if self.filter_fields[i][0].isChecked():
                fields_to_filter[i] = self.filter_fields[i][1].text()

        return fields_to_filter

    def get_xes_event_log(self, path):
        variant = xes_importer.Variants.ITERPARSE
        parameters = {variant.value.Parameters.TIMESTAMP_SORT: True}
        self.event_log = xes_importer.apply(path, variant=variant, parameters=parameters)
        self.terminal.appendPlainText(str(self.event_log))

    def filter_log(self):
        event_log_mike = pm4py.filter_log(lambda e: len(e) > 6, self.event_log)
        process_tree = pm4py.discover_process_tree_inductive(event_log_mike)
        bpmn_model = pm4py.convert_to_bpmn(process_tree)
        pm4py.view_bpmn(bpmn_model)

    def filter_by_attr(self, attr, val):
        filtered_event_log = pm4py.filter_event_attribute_values(self.event_log, attr, val, level='event')
        process_tree = pm4py.discover_process_tree_inductive(filtered_event_log)
        bpmn_model = pm4py.convert_to_bpmn(process_tree)
        pm4py.view_bpmn(bpmn_model)

    def convert_petri_net_to_bpmn(self,petri_net):
        return pm4py.objects.conversion.wf_net.variants.to_bpmn.apply(petri_net)

    def convert_petri_net_to_process_tree(self,petri_net):
        return pm4py.objects.conversion.wf_net.variants.to_process_tree.apply(petri_net)

    def btn_open_csv_file(self):
        file_name = QFileDialog.getOpenFileName()
        self.selected_file = file_name[0]
        self.get_csv_event_log(self.selected_file)
        self.l1.setText(self.selected_file)
        self.update_buttons()

    def update_buttons(self):
        if self.selected_miner == MINER_TYPE.HEURISTIC_MINER:
            self.dependency_threshold_input.setEnabled(True)
        else:
            self.dependency_threshold_input.setEnabled(False)

        if len(self.selected_file) > 0:
            if self.selected_miner == MINER_TYPE.INDUCTIVE_MINER:
                self.btn_draw_bpmn.setEnabled(True)
                self.btn_draw_process_tree.setEnabled(True)
                self.btn_draw_petri_net.setEnabled(True)
            elif self.selected_miner == MINER_TYPE.ALPHA_MINER:
                self.btn_draw_bpmn.setEnabled(False)
                self.btn_draw_process_tree.setEnabled(False)
                self.btn_draw_petri_net.setEnabled(True)
            elif self.selected_miner == MINER_TYPE.HEURISTIC_MINER:
                self.btn_draw_bpmn.setEnabled(False)
                self.btn_draw_process_tree.setEnabled(False)
                self.btn_draw_petri_net.setEnabled(True)
            elif self.selected_miner == MINER_TYPE.CORRELATION_MINER:
                pass
        else:
            self.btn_draw_bpmn.setEnabled(False)
            self.btn_draw_process_tree.setEnabled(False)
            self.btn_draw_petri_net.setEnabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Window()
    sys.exit(app.exec_())
