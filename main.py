import pm4py
import os
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QBoxLayout, QVBoxLayout, QLabel, QPlainTextEdit, \
    QGridLayout
import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.log.util import func as functools
from pm4py.visualization.process_tree import visualizer as pt_visualizer
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.conversion.process_tree import converter as pt_converter
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout




class Window:

    def __init__(self):
        self.selected_file=''
        self.event_log = None

        app = QApplication(sys.argv)

        w = QWidget()
        main_box = QVBoxLayout()
        self.grid = QGridLayout(

        )
        self.btn_open_file = QPushButton("Open file")
        self.btn_open_file.setGeometry(50, 50, 70, 20)
        self.btn_open_file.clicked.connect(self.btn_open_csv_file)

        self.l1 = QLabel()
        self.l1.setText(self.selected_file)

        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)

        self.btn_draw_bpmn = QPushButton("Draw bpmn model")
        self.btn_draw_bpmn.setGeometry(50, 50, 70, 20)
        self.btn_draw_bpmn.clicked.connect(self.show_process_bpmn)
        self.btn_draw_bpmn.setEnabled(len(self.selected_file)>0)

        self.btn_draw_process_tree = QPushButton("Draw process tree")
        self.btn_draw_process_tree.setGeometry(50, 50, 70, 20)
        self.btn_draw_process_tree.clicked.connect(self.show_process_tree)
        self.btn_draw_process_tree.setEnabled(len(self.selected_file) > 0)

        self.btn_draw_petri_net = QPushButton("Draw petri net")
        self.btn_draw_petri_net.setGeometry(50, 50, 70, 20)
        self.btn_draw_petri_net.clicked.connect(self.show_petri_net)
        self.btn_draw_petri_net.setEnabled(len(self.selected_file) > 0)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.btn_open_file)
        hbox1.addStretch()

        main_box.addLayout(hbox1)
        main_box.addWidget(self.l1)
        main_box.addWidget(self.terminal)


        hbox = QHBoxLayout()
        main_box.addLayout(hbox)
        hbox.addWidget(self.btn_draw_bpmn)
        hbox.addWidget(self.btn_draw_process_tree)
        hbox.addWidget(self.btn_draw_petri_net)

        w.setLayout(main_box)
        w.resize(200, 100)
        w.move(500, 500)
        w.setWindowTitle('Workflow-mining')
        w.show()

        sys.exit(app.exec_())


    def show_process_bpmn(self):
        print(str(self.event_log))
        process_tree = pm4py.discover_process_tree_inductive(self.event_log)
        bpmn_model = pm4py.convert_to_bpmn(process_tree)
        pm4py.view_bpmn(bpmn_model)


    def show_process_tree(self):
        tree = inductive_miner.apply_tree(self.event_log)
        gviz = pt_visualizer.apply(tree)
        pt_visualizer.view(gviz)


    def show_petri_net(self):
        tree = inductive_miner.apply_tree(self.event_log)
        net, initial_marking, final_marking = inductive_miner.apply(self.event_log)
        net, initial_marking, final_marking = pt_converter.apply(tree, variant=pt_converter.Variants.TO_PETRI_NET)
        gviz = pn_visualizer.apply(net, initial_marking, final_marking)
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
        self.filter_by_attr()

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

    def filter_by_attr(self):
        event_log = pm4py.filter_event_attribute_values(self.event_log,'resource','Mike', level='event')
        process_tree = pm4py.discover_process_tree_inductive(event_log)
        bpmn_model = pm4py.convert_to_bpmn(process_tree)
        pm4py.view_bpmn(bpmn_model)

    def btn_open_csv_file(self):
        file_name = QFileDialog.getOpenFileName()
        self.selected_file = file_name[0]
        self.get_csv_event_log(self.selected_file)
        self.l1.setText(self.selected_file)
        self.update_buttons()


    def update_buttons(self):
        self.btn_draw_bpmn.setEnabled(len(self.selected_file)>0)
        self.btn_draw_process_tree.setEnabled(len(self.selected_file) > 0)
        self.btn_draw_petri_net.setEnabled(len(self.selected_file) > 0)


Window()