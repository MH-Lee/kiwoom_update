import os
from kiwoom import Kiwoom
from processtracker import ProcessTracker, timeit

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import os, time
import pandas as pd
import simplejson as json # simplejson for data management
import _pickle as pickle # cPickle for in-python data sorting
from datetime import datetime, timedelta
from pathlib import Path


class Update_gobble(ProcessTracker):

    @timeit
    def __init__(self):
        super().__init__() # initialize ProcessTracker
        self.starting()
        self.app = QApplication(["kiwoom.py"])
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()

    @timeit
    def step_one_kiwoom(self):
        self.step_one()
        etf = pd.read_csv('./etf_list.csv', header=None)
        etf = etf[0].tolist()
        etf = [str(e).zfill(6) for e in etf]
        for market_type in ["0", "10"]:
            pickle_name = "kospi-dict.pickle" if market_type == "0" else "kosdaq-dict.pickle"
            if market_type == "0":
                code_list = self.kiwoom.get_code_list_by_market(market_type)
                kospi_code_list = [code for code in code_list if code not in etf]
                etf_code_list = [code for code in code_list if code in etf]
                kospi_name_list = [self.kiwoom.get_master_code_name(code) for code in kospi_code_list]
                etf_name_list = [self.kiwoom.get_master_code_name(code) for code in etf_code_list]
                kospi_market_dict = dict(zip(kospi_code_list, kospi_name_list))
                pickle_out = open("./data/" + pickle_name, "wb")
                pickle.dump(kospi_market_dict, pickle_out)
                etf_market_dict = dict(zip(etf_code_list, etf_name_list))
                etf_pickle_out = open("./data/etf-dict.pickle", "wb")
                pickle.dump(etf_market_dict, etf_pickle_out)
                pickle_out.close()
            else:
                code_list = self.kiwoom.get_code_list_by_market(market_type)
                name_list = [self.kiwoom.get_master_code_name(code) for code in code_list]
                market_dict = dict(zip(code_list, name_list))
                pickle_out = open("./data/" + pickle_name, "wb")
                pickle.dump(market_dict, pickle_out)
                pickle_out.close()
        self.step_one_finish()

    def set_tasks(self, market_type=None):
        if market_type == None:
            kospi_in = open("./data/kospi-dict.pickle", "rb")
            self.kospi_task = pickle.load(kospi_in)
            kosdaq_in = open("./data/kosdaq-dict.pickle", "rb")
            self.kosdaq_task = pickle.load(kosdaq_in)
            etf_in = open("./data/etf-dict.pickle", "rb")
            self.etf_task = pickle.load(etf_in)
        elif market_type == 'kospi':
            kospi_in = open("./data/kospi-dict.pickle", "rb")
            self.kospi_task = pickle.load(kospi_in)
            self.kosdaq_task = {}
            self.etf_task = {}
        elif market_type == 'kosdaq':
            self.kospi_task = {}
            kosdaq_in = open("./data/kosdaq-dict.pickle", "rb")
            self.kosdaq_task = pickle.load(kosdaq_in)
            self.etf_task = {}
        elif market_type == 'etf':
            self.kospi_task = {}
            self.kosdaq_task = {}
            etf_in = open("./data/etf-dict.pickle", "rb")
            self.etf_task = pickle.load(etf_in)
        elif market_type == 'kospi-etf':
            kospi_in = open("./data/kospi-dict.pickle", "rb")
            self.kospi_task = pickle.load(kospi_in)
            self.kosdaq_task = {}
            etf_in = open("./data/etf-dict.pickle", "rb")
            self.etf_task = pickle.load(etf_in)

    def _get_total_stock_num(self):
        kospi_len = len(list(self.kospi_task.keys()))
        kosdaq_len = len(list(self.kosdaq_task.keys()))
        etf_len = len(list(self.etf_task.keys()))
        return kospi_len + kosdaq_len + etf_len

    def check_start_log(self):
        f =  open('./daily-log/day-check.txt', 'r')
        date = f.read()
        date_list = date.split('\n')
        f.close()
        week = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        self.last_date = datetime.strptime(date_list[-1], '%Y%m%d').date()
        w = self.last_date.weekday()
        if week[w] == 'fri':
            self.start_date = self.last_date + timedelta(days=3)
            self.start_date = self.start_date.strftime('%Y%m%d')
        elif week[w] == 'sat':
            self.start_date = self.last_date + timedelta(days=2)
            self.start_date = self.start_date.strftime('%Y%m%d')
        else:
            self.start_date = self.last_date + timedelta(days=1)
            self.start_date = self.start_date.strftime('%Y%m%d')

    def check_start_day_file(self, market, datatype):
        os.chdir('./data/stock-{}/{}-{}'.format(datatype, market, datatype))
        try:
            df = pd.read_csv('./005930.csv', sep=',')
        except UnicodeError:
            df = pd.read_csv('./005930.csv', sep=',', encoding='CP949')
        os.chdir('../../..')
        week = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        if datatype == 'short':
            last_date = datetime.strptime(str(df['date'][-1:].values[0]), '%Y%m%d').date()
        else:
            last_date = datetime.strptime(str(df['date'][0]), '%Y%m%d').date()
        w = last_date.weekday()
        if week[w] == 'fri':
            self.start_date = last_date + timedelta(days=3)
            self.start_date = self.start_date.strftime('%Y%m%d')
        elif week[w] == 'sat':
            self.start_date = last_date + timedelta(days=2)
            self.start_date = self.start_date.strftime('%Y%m%d')
        else:
            self.start_date = last_date + timedelta(days=1)
            self.start_date = start_date.strftime('%Y%m%d')

    def add_data_log(self):
        f = open('./daily-log/day-check.txt', 'a')
        today = datetime.today().strftime('%Y%m%d')
        f.write('\n' + today)
        f.close()
