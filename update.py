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
from pathlib import Path
from datetime import datetime, timedelta
from pathlib import Path

TR_REQ_TIME_INTERVAL = 3.8

class UpdateGobble(ProcessTracker):
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
                pickle_out = open("./update_data/" + pickle_name, "wb")
                pickle.dump(kospi_market_dict, pickle_out)
                etf_market_dict = dict(zip(etf_code_list, etf_name_list))
                etf_pickle_out = open("./update_data/etf-dict.pickle", "wb")
                pickle.dump(etf_market_dict, etf_pickle_out)
                pickle_out.close()
            else:
                code_list = self.kiwoom.get_code_list_by_market(market_type)
                name_list = [self.kiwoom.get_master_code_name(code) for code in code_list]
                market_dict = dict(zip(code_list, name_list))
                pickle_out = open("./update_data/" + pickle_name, "wb")
                pickle.dump(market_dict, pickle_out)
                pickle_out.close()
        self.step_one_finish()

    def set_tasks(self, market_type=None):
        if market_type == None:
            kospi_in = open("./update_data/kospi-dict.pickle", "rb")
            self.kospi_task = pickle.load(kospi_in)
            kosdaq_in = open("./update_data/kosdaq-dict.pickle", "rb")
            self.kosdaq_task = pickle.load(kosdaq_in)
            etf_in = open("./update_data/etf-dict.pickle", "rb")
            self.etf_task = pickle.load(etf_in)
        elif market_type == 'kospi':
            kospi_in = open("./update_data/kospi-dict.pickle", "rb")
            self.kospi_task = pickle.load(kospi_in)
            self.kosdaq_task = {}
            self.etf_task = {}
        elif market_type == 'kosdaq':
            self.kospi_task = {}
            kosdaq_in = open("./update_data/kosdaq-dict.pickle", "rb")
            self.kosdaq_task = pickle.load(kosdaq_in)
            self.etf_task = {}
        elif market_type == 'etf':
            self.kospi_task = {}
            self.kosdaq_task = {}
            etf_in = open("./update_data/etf-dict.pickle", "rb")
            self.etf_task = pickle.load(etf_in)
        elif market_type == 'kospi-etf':
            kospi_in = open("./update_data/kospi-dict.pickle", "rb")
            self.kospi_task = pickle.load(kospi_in)
            self.kosdaq_task = {}
            etf_in = open("./update_data/etf-dict.pickle", "rb")
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

    def check_start_day_file(self, datatype):
        os.chdir('./data/stock-{}/kospi-{}'.format(datatype, datatype))
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
            self.start_date = self.start_date.strftime('%Y%m%d')
        return self.start_date

    def add_data_log(self):
        f = open('./daily-log/day-check.txt', 'a')
        today = datetime.today().strftime('%Y%m%d')
        f.write('\n' + today)
        f.close()

    def _ohlcv_skip_codes(self):
        os.chdir("./update_data/stock-ohlcv/kospi-ohlcv")
        kospi_list = [json.split(".")[0] for json in os.listdir()]
        os.chdir("../../../")
        os.chdir("./update_data/stock-ohlcv/kosdaq-ohlcv")
        kosdaq_list = [json.split(".")[0] for json in os.listdir()]
        os.chdir("../../../")
        os.chdir("./update_data/stock-ohlcv/etf-ohlcv")
        etf_list = [json.split(".")[0] for json in os.listdir()]
        os.chdir("../../../")
        return kospi_list + kosdaq_list + etf_list

    def _buysell_skip_codes(self):
        os.chdir("./update_data/stock-net/kospi-net")
        kospi_list = [json.split(".")[0] for json in os.listdir()]
        os.chdir("../../../")
        os.chdir("./update_data/stock-net/kosdaq-net")
        kosdaq_list = [json.split(".")[0] for json in os.listdir()]
        os.chdir("../../../")
        os.chdir("./update_data/stock-net/etf-net")
        etf_list = [json.split(".")[0] for json in os.listdir()]
        os.chdir("../../../")
        return kospi_list + kosdaq_list + etf_list

    def _short_skip_codes(self):
        os.chdir("./update_data/stock-short/kospi-short")
        kospi_list = [json.split(".")[0] for json in os.listdir()]
        os.chdir("../../../")
        os.chdir("./update_data/stock-short/kosdaq-short")
        kosdaq_list = [json.split(".")[0] for json in os.listdir()]
        os.chdir("../../../")
        os.chdir("./update_data/stock-short/etf-short")
        etf_list = [json.split(".")[0] for json in os.listdir()]
        os.chdir("../../../")
        return kospi_list + kosdaq_list + etf_list

    def req_ohlcv(self):
        done_list = self._ohlcv_skip_codes()
        total_stock_num = self._get_total_stock_num() - len(done_list)
        start = self.check_start_day_file('ohlcv')
        code_looped = 0
        total_time = 0

        for market_type in [0, 10, 2]:
            if market_type == 0:
                market = "kospi"
                task = self.kospi_task
            elif market_type == 10:
                market = "kosdaq"
                task = self.kosdaq_task
            else:
                market = "etf"
                task = self.etf_task

            for code, name in task.items():
                if code in done_list:
                    continue
                ts = time.time()
                try:
                    self._initialize_ohlcv_data(code, market, start)
                except:
                    print(code + ", " + name + " ohlcv save skipped due to error")
                te = time.time()
                time_took = te - ts
                total_time += time_took
                code_looped += 1
                avg_time_took = total_time/code_looped
                stocks_left = total_stock_num - code_looped
                time_left = avg_time_took * stocks_left
                print(str(stocks_left) + " stocks left to save")
                print(str(time_left) + " seconds left to finish whole request")
                print("---------------------------------------------------")

    def _initialize_ohlcv_data(self, code, market, start):
        global TR_REQ_TIME_INTERVAL

        kiwoom = self.kiwoom
        name = kiwoom.get_master_code_name(code)
        time.sleep(TR_REQ_TIME_INTERVAL)
        print(code + ": " + name + " ohlcv data initializing")
        kiwoom.prepare_data()
        print("update data dict created")

        # opt10059 TR 요청
        kiwoom.set_input_value("기준일자", time.strftime('%Y%m%d'))
        kiwoom.set_input_value("종목코드", code)
        kiwoom.set_input_value("수정주가구분 ", 1)
        kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")
        time.sleep(TR_REQ_TIME_INTERVAL)
        print("first request sent in successfully")

        while kiwoom.remained_data == True:
            kiwoom.set_input_value("기준일자", time.strftime('%Y%m%d'))
            kiwoom.set_input_value("종목코드", code)
            kiwoom.set_input_value("수정주가구분 ", 1)
            kiwoom.comm_rq_data("opt10081_req", "opt10081", 2, "0101")
            print("requesting...")
            current_date = kiwoom.get_date()
            print("date loop is on: ", str(current_date))
            if current_date <= int(start):
                print("loop breaking b/c " + str(current_date) + " lower than " + str(start))
                break
            time.sleep(TR_REQ_TIME_INTERVAL)
        print("OHLCV data saved, ready for DB")
        length = kiwoom.data.shape[0]
        code_list = [code]*length
        name_list = [name]*length
        kiwoom.data['code'] = code_list
        kiwoom.data['name'] = name_list
        cols = ["date", "code", "name", "open_price", "high_price", "low_price", "close_price", "volume"]
        kiwoom.data = kiwoom.data[cols]
        path= ".\\update_data\\stock-ohlcv\\" + market + "-ohlcv\\"
        file_name = code + ".csv"
        Update_ohlcv = kiwoom.data[kiwoom.data['date']>=int(start)]
        Update_ohlcv.to_csv(os.path.join(path,file_name), index = False)
        print(code + ": " + name + " ohlcv data successfully saved")

    def req_buysell(self):
        done_list = self._buysell_skip_codes()
        total_stock_num = self._get_total_stock_num() - len(done_list)
        start = self.check_start_day_file('buy')
        code_looped = 0
        total_time = 0

        # get code list (0: KOSPI, 10: KOSDAQ)
        for market_type in [0, 10, 2]:
            if market_type == 0:
                market = "kospi"
                task = self.kospi_task
            elif market_type == 10:
                market = "kosdaq"
                task = self.kosdaq_task
            else:
                market = "etf"
                task = self.etf_task

            for code, name in task.items():
                if code in done_list:
                    continue
                ts = time.time()
                try:
                    self._initialize_buysell_data(code, market, start)
                except:
                    print(code + ", " + name + " buysell save skipped due to error")
                te = time.time()
                time_took = te - ts
                total_time += time_took
                code_looped += 1
                avg_time_took = total_time/code_looped
                stocks_left = total_stock_num - code_looped
                time_left = avg_time_took * stocks_left
                print(str(stocks_left) + " stocks left to save")
                print(str(time_left) + " seconds left to finish whole request")
                print("---------------------------------------------------")

    def _initialize_buysell_data(self, code, market, start):
        global TR_REQ_TIME_INTERVAL

        kiwoom = self.kiwoom
        name = kiwoom.get_master_code_name(code)
        time.sleep(TR_REQ_TIME_INTERVAL)
        print(code + ": " + name + " buysell data initializing")
        kiwoom.prepare_data()
        print("update data dict created")

        for buysell in [1, 2]:
            if buysell == 1:
                kiwoom.set_buysell_state("buy")
            elif buysell == 2:
                kiwoom.set_buysell_state("sell")

            # opt10059 TR 요청
            kiwoom.set_input_value("일자", time.strftime('%Y%m%d'))
            kiwoom.set_input_value("종목코드", code)
            kiwoom.set_input_value("금액수량구분", 2)
            kiwoom.set_input_value("매매구분", buysell)
            kiwoom.set_input_value("단위구분", 1)
            kiwoom.comm_rq_data("opt10059_req", "opt10059", 0, "0101")
            time.sleep(TR_REQ_TIME_INTERVAL)
            print("first request sent in successfully")

            while kiwoom.remained_data == True:
                kiwoom.set_input_value("일자", time.strftime('%Y%m%d'))
                kiwoom.set_input_value("종목코드", code)
                kiwoom.set_input_value("금액수량구분", 2)
                kiwoom.set_input_value("매매구분", buysell)
                kiwoom.set_input_value("단위구분", 1)
                kiwoom.comm_rq_data("opt10059_req", "opt10059", 2, "0101")
                print("requesting...")
                current_date = kiwoom.get_date()
                print("date loop is on: ", str(current_date))
                if current_date <= int(start):
                    print("loop breaking b/c " + str(current_date) + " lower than " + str(start))
                    break
                time.sleep(TR_REQ_TIME_INTERVAL)
            if buysell == 1:
                print("BUY data saved, ready for DB")
            elif buysell == 2:
                print("SELL data saved, ready for DB")

        length = kiwoom.data.shape[0]
        code_list = [code]*length
        name_list = [name]*length
        kiwoom.data['code'] = code_list
        kiwoom.data['name'] = name_list
        cols  = ["date", "code", "name","close_price", "individual", "foreign_retail", "institution", "financial", "insurance", "trust",
                "etc_finance", "bank", "pension", "private", "nation", "etc_corporate", "foreign", "buysell"]
        kiwoom.data = kiwoom.data[cols]
        path_buy= ".\\update_data\\stock-buy\\{}-buy\\".format(market)
        path_sell = ".\\update_data\\stock-sell\\{}-sell\\".format(market)
        # path_net = ".\\update_data\\stock-net\\{}-net\\".format(market)
        file_name = code + ".csv"
        tmp_buy = kiwoom.data[kiwoom.data['buysell'] == 'buy']
        tmp_sell = kiwoom.data[kiwoom.data['buysell'] == 'sell']
        tmp_buy = tmp_buy[tmp_buy['date']>=int(start)]
        tmp_sell = tmp_sell[tmp_sell['date']>=int(start)]
        del tmp_buy['buysell']
        del tmp_sell['buysell']
        # cols2  = ["date", "code", "name", "close_price", "individual", "foreign_retail", "institution", "financial", "insurance", "trust",
        #         "etc_finance", "bank", "pension", "private", "nation", "etc_corporate", "foreign"]
        # tmp_net = tmp_buy.loc[:,["individual", "foreign_retail", "institution", "financial", "insurance", "trust",
        #             "etc_finance", "bank", "pension", "private", "nation", "etc_corporate", "foreign"]] + tmp_sell.loc[:,["individual", "foreign_retail", "institution", "financial", "insurance", "trust",
        #             "etc_finance", "bank", "pension", "private", "nation", "etc_corporate", "foreign"]]
        # tmp_net['date'] = tmp_buy['date']
        # tmp_net['name'] = tmp_buy['name']
        # tmp_net['code'] = tmp_buy['code']
        # tmp_net['close_price'] = tmp_buy['close_price']
        # tmp_net = tmp_net[cols2]
        tmp_buy.to_csv(os.path.join(path_buy ,file_name), index=False, sep=',')
        tmp_sell.to_csv(os.path.join(path_sell,file_name), index=False, sep=',')
        # tmp_net.to_csv(os.path.join(path_net,file_name), index=False, sep=',')
        print(code + ": " + name + " buysell data successfully saved")

    def req_short(self):
        done_list = self._short_skip_codes()
        total_stock_num = self._get_total_stock_num() - len(done_list)
        start = self.check_start_day_file('short')
        code_looped = 0
        total_time = 0

        for market_type in [0, 10, 2]:
            if market_type == 0:
                market = "kospi"
                task = self.kospi_task
            elif market_type == 10:
                market = "kosdaq"
                task = self.kosdaq_task
            else:
                market = "etf"
                task = self.etf_task

            for code, name in task.items():
                if code in done_list:
                    continue
                ts = time.time()
                try:
                    self._initialize_short_data(code, market, start)
                except:
                    print(code + ", " + name + " short save skipped due to error")
                te = time.time()
                time_took = te - ts
                total_time += time_took
                code_looped += 1
                avg_time_took = total_time/code_looped
                stocks_left = total_stock_num - code_looped
                time_left = avg_time_took * stocks_left
                print(str(stocks_left) + " stocks left to save")
                print(str(time_left) + " seconds left to finish whole request")
                print("---------------------------------------------------")

    def _initialize_short_data(self, code, market, start):
        global TR_REQ_TIME_INTERVAL

        kiwoom = self.kiwoom
        name = kiwoom.get_master_code_name(code)
        time.sleep(TR_REQ_TIME_INTERVAL)
        print(code + ": " + name + " short data initializing")
        kiwoom.prepare_data()
        print("update data dict created")

        # opt10059 TR 요청
        kiwoom.set_input_value("종목코드", code)
        kiwoom.set_input_value("시간구분 ", 0)
        kiwoom.set_input_value("시작일자", time.strftime('%Y%m%d'))
        kiwoom.set_input_value("종료일자", time.strftime('%Y%m%d'))
        kiwoom.comm_rq_data("opt10014_req", "opt10014", 0, "0101")
        time.sleep(TR_REQ_TIME_INTERVAL)
        print("first request sent in successfully")

        while kiwoom.remained_data == True:
            kiwoom.set_input_value("종목코드", code)
            kiwoom.set_input_value("시간구분 ", 0)
            kiwoom.set_input_value("시작일자", time.strftime('%Y%m%d'))
            kiwoom.set_input_value("종료일자", time.strftime('%Y%m%d'))
            kiwoom.comm_rq_data("opt10014_req", "opt10014", 2, "0101")
            print("requesting...")
            current_date = kiwoom.get_date()
            print("date loop is on: ", str(current_date))
            if current_date <= int(start):
                print("loop breaking b/c " + str(current_date) + " lower than " + str(start))
                break
            time.sleep(TR_REQ_TIME_INTERVAL)
        print("short data saved, ready for DB")
        length = kiwoom.data.shape[0]
        code_list = [code]*length
        name_list = [name]*length
        kiwoom.data['code'] = code_list
        kiwoom.data['name'] = name_list
        cols = ["date", "code", "name", "short", "short_proportion", "short_total_price", "short_average_price"]
        kiwoom.data = kiwoom.data[cols]
        update_short = kiwoom.data[kiwoom.data['date']>=int(start)]
        path= ".\\update_data\\stock-short\\" + market + "-short\\"
        file_name = code + ".csv"
        update_short.to_csv(os.path.join(path,file_name), index = False)
        print(code + ": " + name + " short data successfully saved")
