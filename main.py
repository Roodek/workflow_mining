import pm4py
import os
import sys
from PyQt5 import QtWidgets
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QBoxLayout, QVBoxLayout, QLabel, QPlainTextEdit, \
    QGridLayout, QLineEdit, QCheckBox, QRadioButton, QMessageBox
import pandas as pd
from PyQt5.QtCore import *
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.conversion.wf_net.variants.to_process_tree import Parameters
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
import re


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
        self.original_dataframe = None
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

        self.btn_draw_heuristic_net = QPushButton("Draw heuristic net")
        self.btn_draw_heuristic_net.setGeometry(50, 50, 70, 20)
        self.btn_draw_heuristic_net.clicked.connect(self.show_heuristic_net)
        self.btn_draw_heuristic_net.setEnabled(len(self.selected_file) > 0)
        self.btn_draw_heuristic_net.setHidden(True)

        self.l1 = QLabel()
        self.l1.setText(self.selected_file)

        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.btn_open_file)
        hbox1.addWidget(self.l1)
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

        main_box.addWidget(self.terminal)

        main_box.addLayout(self.grid)
        hbox = QHBoxLayout()
        main_box.addLayout(hbox)
        main_box.addWidget(self.btn_draw_heuristic_net)

        hbox.addWidget(self.btn_draw_bpmn)
        hbox.addWidget(self.btn_draw_process_tree)
        hbox.addWidget(self.btn_draw_petri_net)

        self.setLayout(main_box)
        self.resize(250, 180)
        self.move(500, 500)
        self.setWindowTitle('Workflow-mining')

        self.show()

    def get_threshold_level(self):
        threshold_value = float(self.dependency_threshold_input.text())
        if threshold_value>1.0:
            threshold_value=1.0
            self.dependency_threshold_input.setText(str(1.0))
        return threshold_value

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
        dataframe = self.apply_attr_filter_on_df()
        self.event_log = self.df_events_to_event_log(dataframe)
        if self.selected_miner == MINER_TYPE.INDUCTIVE_MINER:
            self.visualize_inductive_bpmn()
        elif self.selected_miner == MINER_TYPE.ALPHA_MINER:
            self.visualize_alpha_bpmn()
        elif self.selected_miner == MINER_TYPE.HEURISTIC_MINER:
            self.visualize_heuristics_bpmn()
        elif self.selected_miner == MINER_TYPE.CORRELATION_MINER:
            pass

    def visualize_inductive_bpmn(self):
        process_tree = pm4py.discover_process_tree_inductive(self.event_log)
        bpmn_model = pm4py.convert_to_bpmn(process_tree)
        pm4py.view_bpmn(bpmn_model)

    def visualize_alpha_bpmn(self):
        petri_net = alpha_miner.apply(self.event_log)
        bpmn_model = self.convert_petri_net_to_bpmn(petri_net)
        pm4py.view_bpmn(bpmn_model)

    def visualize_heuristics_bpmn(self):
        petri_net = heuristics_miner.apply(self.event_log, parameters={
            heuristics_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: self.get_threshold_level()})
        bpmn_model = self.convert_petri_net_to_bpmn(petri_net)
        pm4py.view_bpmn(bpmn_model)

    def show_process_tree(self):
        dataframe = self.apply_attr_filter_on_df()
        self.event_log = self.df_events_to_event_log(dataframe)
        if self.selected_miner == MINER_TYPE.INDUCTIVE_MINER:
            self.show_process_tree_inductive()
        elif self.selected_miner == MINER_TYPE.ALPHA_MINER:
            self.show_process_tree_alpha()
        elif self.selected_miner == MINER_TYPE.HEURISTIC_MINER:
            self.show_process_tree_heuristic()
        elif self.selected_miner == MINER_TYPE.CORRELATION_MINER:
            pass

    def show_process_tree_inductive(self):
        tree = inductive_miner.apply_tree(self.event_log)
        gviz = pt_visualizer.apply(tree)
        pt_visualizer.view(gviz)

    def show_process_tree_alpha(self):
        petri_net = alpha_miner.apply(self.event_log)
        tree = self.convert_petri_net_to_process_tree(petri_net)
        gviz = pt_visualizer.apply(tree)
        pt_visualizer.view(gviz)

    def show_process_tree_heuristic(self):
        petri_net = heuristics_miner.apply(self.event_log, parameters={
            heuristics_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: self.get_threshold_level()})
        tree = self.convert_petri_net_to_process_tree(petri_net)
        if tree is not None:
            gviz = pt_visualizer.apply(tree)
            pt_visualizer.view(gviz)

    def show_petri_net(self):
        dataframe = self.apply_attr_filter_on_df()
        self.event_log = self.df_events_to_event_log(dataframe)
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
        net, im, fm = heuristics_miner.apply(self.event_log, parameters={
            heuristics_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: self.get_threshold_level()})

        gviz = pn_visualizer.apply(net, im, fm)
        pn_visualizer.view(gviz)

    def show_heuristic_net(self):
        dataframe = self.apply_attr_filter_on_df()
        self.event_log = self.df_events_to_event_log(dataframe)
        heu_net = heuristics_miner.apply_heu(self.event_log, parameters={
            heuristics_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: self.get_threshold_level()})
        gviz = hn_visualizer.apply(heu_net)
        hn_visualizer.view(gviz)

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
        self.original_dataframe=log_csv
        self.terminal.appendPlainText('model loaded')
        self.add_column_filter_fields(log_csv)

    def df_events_to_event_log(self,df):
        return log_converter.apply(df)

    def add_column_filter_fields(self,csv):
        self.terminal.appendPlainText("event attributes, first 3 rows")
        self.terminal.appendPlainText(csv.head(3).to_string())
        self.grid.addWidget(QLabel("use regex expression for filtering attributes"),0,0)
        for col in csv.columns:
            if 'index' in col:
                continue
            self.add_filter_by_attr_field(col)

    def add_filter_by_attr_field(self,attr):
        if 'timestamp' in attr:
            pass
        else:
            self.filter_fields[attr] = (QCheckBox(attr), QLineEdit())
            self.grid.addWidget(self.filter_fields[attr][0], 1, len(self.filter_fields) - 1)
            self.grid.addWidget(self.filter_fields[attr][1], 2,len(self.filter_fields)-1)

    def apply_attr_filter_on_df(self):
        filtered_dataframe = self.original_dataframe
        filter_fields =self.get_attributes_to_filter()
        for attr in filter_fields:
            regex = filter_fields[attr]
            filtered_dataframe = filtered_dataframe[filtered_dataframe[attr].str.match(regex)]
        return filtered_dataframe

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
        return pm4py.objects.conversion.wf_net.variants.to_bpmn.apply(petri_net[0],petri_net[1],petri_net[2])

    def convert_petri_net_to_process_tree(self,petri_net):
        if pm4py.objects.petri_net.utils.check_soundness.check_wfnet(petri_net[0]):
            try:
                tree = pm4py.objects.conversion.wf_net.variants.to_process_tree.apply(petri_net[0],petri_net[1],petri_net[2])#parameters={Parameters.DEBUG:True}
                return tree
            except:
                self.showdialog("Petri net is not sound for generating process tree")
        else:
            return None

    def btn_open_csv_file(self):
        file_name = QFileDialog.getOpenFileName()
        self.selected_file = file_name[0]
        self.get_csv_event_log(self.selected_file)
        self.l1.setText(self.selected_file)
        self.update_buttons()

    def update_buttons(self):
        if self.selected_miner == MINER_TYPE.HEURISTIC_MINER:
            self.dependency_threshold_input.setEnabled(True)
            self.btn_draw_heuristic_net.setHidden(False)
        else:
            self.dependency_threshold_input.setEnabled(False)
            self.btn_draw_heuristic_net.setEnabled(False)
            self.btn_draw_heuristic_net.setHidden(True)

        if len(self.selected_file) > 0:
            if self.selected_miner == MINER_TYPE.INDUCTIVE_MINER:
                self.btn_draw_bpmn.setEnabled(True)
                self.btn_draw_process_tree.setEnabled(True)
                self.btn_draw_petri_net.setEnabled(True)
            elif self.selected_miner == MINER_TYPE.ALPHA_MINER:
                self.btn_draw_bpmn.setEnabled(True)
                self.btn_draw_process_tree.setEnabled(True)
                self.btn_draw_petri_net.setEnabled(True)
            elif self.selected_miner == MINER_TYPE.HEURISTIC_MINER:
                self.btn_draw_bpmn.setEnabled(True)
                self.btn_draw_process_tree.setEnabled(True)
                self.btn_draw_petri_net.setEnabled(True)
                self.btn_draw_heuristic_net.setEnabled(True)
                self.btn_draw_heuristic_net.setHidden(False)
            elif self.selected_miner == MINER_TYPE.CORRELATION_MINER:
                pass
        else:
            self.btn_draw_bpmn.setEnabled(False)
            self.btn_draw_process_tree.setEnabled(False)
            self.btn_draw_petri_net.setEnabled(False)

    def showdialog(self,text):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText(text)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        retval = msg.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Window()
    sys.exit(app.exec_())
