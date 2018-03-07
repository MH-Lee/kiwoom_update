### Run on Python 3.4 ###
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import pandas as pd
import sys

TR_REQ_TIME_INTERVAL = 3.8

class Kiwoom(QAxWidget):
    """Kiwoom class: connects to Kiwoom OpenAPI
       requests OHLCV, Buy, Sell data"""

    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

    def prepare_data(self):
        self.data_list = []

    def _set_date(self, date):
        self.date_list = date

    def get_date(self):
        return self.date_list

    def set_buysell_state(self, buysell):
        self.buysell_state = buysell

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("Connected to Kiwoom server")
        else:
            print("Disconnected from Kiwoom server")

        self.login_event_loop.exit()

    def get_code_list_by_market(self, market):
        # 0: kospi, 10: kosdaq, 8: etf
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)
        elif rqname == "opt10059_req":
            self._opt10059(rqname, trcode)
        elif rqname == "opt10014_req":
            self._opt10014(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open_price = self._comm_get_data(trcode, "", rqname, i, "시가")
            high_price = self._comm_get_data(trcode, "", rqname, i, "고가")
            low_price = self._comm_get_data(trcode, "", rqname, i, "저가")
            close_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            update_data = [int(date), int(open_price), int(high_price), int(low_price), int(close_price), int(volume)]
            self.data_list.append(update_data)
            self._set_date(update_data[0])
        Labels1 = ["date", "open_price", "high_price", "low_price","close_price", "volume"]
        self.data = pd.DataFrame(self.data_list, columns=Labels1)
        return self.data

    def _opt10059(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            close_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            individual = self._comm_get_data(trcode, "", rqname, i, "개인투자자")
            for_retail = self._comm_get_data(trcode, "", rqname, i, "외국인투자자")
            institution = self._comm_get_data(trcode, "", rqname, i, "기관계")
            financial = self._comm_get_data(trcode, "", rqname, i, "금융투자")
            insurance = self._comm_get_data(trcode, "", rqname, i, "보험")
            trust = self._comm_get_data(trcode, "", rqname, i, "투신")
            etc_finance = self._comm_get_data(trcode, "", rqname, i, "기타금융")
            bank = self._comm_get_data(trcode, "", rqname, i, "은행")
            pension = self._comm_get_data(trcode, "", rqname, i, "연기금등")
            private = self._comm_get_data(trcode, "", rqname, i, "사모펀드")
            nation = self._comm_get_data(trcode, "", rqname, i, "국가")
            etc_corporate = self._comm_get_data(trcode, "", rqname, i, "기타법인")
            foreign = self._comm_get_data(trcode, "", rqname, i, "내외국인")

            update_data = [int(date), abs(int(close_price)), int(individual), int(for_retail), int(institution), int(financial),
                            int(insurance), int(trust), int(etc_finance), int(bank), int(pension), int(private), int(nation),
                            int(etc_corporate), int(foreign), self.buysell_state]
            self.data_list.append(update_data)
            # for label in Labels:
            self._set_date(update_data[0])
        Labels2 = ["date", "close_price", "individual", "foreign_retail", "institution", "financial", "insurance", "trust",  "etc_finance", "bank", "pension", "private", "nation", "etc_corporate", "foreign", "buysell"]
        self.data = pd.DataFrame(self.data_list, columns=Labels2)
        return self.data

    def _opt10014(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            short = self._comm_get_data(trcode, "", rqname, i, "공매도량")
            short_proportion = self._comm_get_data(trcode, "", rqname, i, "매매비중")
            short_total_price = self._comm_get_data(trcode, "", rqname, i, "공매도거래대금")
            short_average_price = self._comm_get_data(trcode, "", rqname, i, "공매도평균가")
            update_data = [int(date), int(short), float(short_proportion), int(short_total_price), float(short_average_price)]
            self.data_list.append(update_data)
            # for label in Labels:
            self._set_date(update_data[0])
        cols = ["date", "short", "short_proportion", "short_total_price", "short_average_price"]
        self.data = pd.DataFrame(self.data_list, columns=cols)
        return self.data
