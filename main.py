import base64
import hashlib
import hmac
import time
import urllib
from xlutils.copy import copy
import xlwt
import requests
import xlrd
import os
import xlwt
import xlsxwriter
import datetime
import threading
import time

from decouple import config

fnameExcel = 'Tickers.xls'


class KrakenBot:
    def __init__(self, api_key, api_secret, tickerToRequest):
        self.api_secret = api_secret
        self.Kraken_headers = {'API-Key': api_key}
        self.tickerRequest = tickerToRequest
        self.sheet = None
        self.writeBook = None
        self.readBook = None
        self.currentRow = 1
        self.sheetRead = None

    def excelStart(self):
        try:
            self.readBook = xlrd.open_workbook(fnameExcel)
            self.sheetRead = self.readBook.sheet_by_index(0)
            self.currentRow = self.readBook.sheet_by_index(0).nrows
            self.writeBook = copy(self.readBook)
            sheet = self.writeBook.get_sheet(0)
            self.sheet = sheet

        except FileNotFoundError:
            print("Pas créé")
            file = xlwt.Workbook()
            file.add_sheet('Tickers')
            file.save(fnameExcel)

            self.readBook = xlrd.open_workbook(fnameExcel)
            self.sheetRead = self.readBook.sheet_by_index(0)
            self.writeBook = copy(self.readBook)

            sheet = self.writeBook.get_sheet(0)
            sheet.write(0, 0, "Date")
            sheet.write(0, 1, "Bitcoin")
            sheet.write(0, 2, "Moyenne (10 derniers prix)")
            sheet.write(0, 3, "% (moyenne vs bitcoin actuel)")
            self.sheet = sheet
            
    def krakenOpenOrders(self):
        Kraken_nonce = str(int(time.time() * 1000))
        Kraken_POST_data = {
            'nonce': Kraken_nonce
        }

        URL_path = 'https://api.kraken.com/0/private/OpenOrders'
        URI_path = '/0/private/OpenOrders'
        url_encoded_post_data = urllib.parse.urlencode(Kraken_POST_data)

        encoded = (str(Kraken_POST_data['nonce']) + url_encoded_post_data).encode()

        msg = URI_path.encode() + hashlib.sha256(encoded).digest()

        krakenSign = hmac.new(base64.b64decode(self.api_secret), msg, hashlib.sha512)

        sign = base64.b64encode(krakenSign.digest())

        self.Kraken_headers['API-Sign'] = sign.decode()
        response = requests.post(URL_path, data=Kraken_POST_data, headers=self.Kraken_headers)
        result = response.json()
        return result

    def krakenAccountBalance(self):
        Kraken_nonce = str(int(time.time() * 1000))
        Kraken_POST_data = {
            'nonce': Kraken_nonce
        }

        URL_path = 'https://api.kraken.com/0/private/Balance'
        URI_path = '/0/private/Balance'
        url_encoded_post_data = urllib.parse.urlencode(Kraken_POST_data)

        encoded = (str(Kraken_POST_data['nonce']) + url_encoded_post_data).encode()

        msg = URI_path.encode() + hashlib.sha256(encoded).digest()

        krakenSign = hmac.new(base64.b64decode(self.api_secret), msg, hashlib.sha512)

        sign = base64.b64encode(krakenSign.digest())

        self.Kraken_headers['API-Sign'] = sign.decode()
        response = requests.post(URL_path, data=Kraken_POST_data, headers=self.Kraken_headers)
        result = response.json()
        return result

    def serverTime(self):
        response = requests.get('https://api.kraken.com/0/public/Time')
        return response.json()


    def assetsAll(self):
        response = requests.get('https://api.kraken.com/0/public/Assets')
        return response.json()

    def assetsPair(self):
        response = requests.get('https://api.kraken.com/0/public/AssetPairs')
        return response.json()

    def registerTickerDB(self):
        r = self.tickerData(self.tickerRequest)
        bot.excelStart()
        bitcoinValue = r['result']['XXBTZEUR']['c'][0]
        self.sheet.write(self.currentRow, 0, datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S:%f"))
        self.sheet.write(self.currentRow, 1, float(bitcoinValue))
        if self.currentRow > 10:
            self.createMedium(bitcoinValue)
        self.currentRow += 1

        orders = self.krakenOpenOrders()

        if len(orders['result']['open']) == 0:
            self.createOrderBuy()
        elif len(orders['result']['open']) != 1:
            print('sellfunction')
        self.writeBook.save(fnameExcel)
        return r

    def createOrderBuy(self):
        if self.checkRules():
            print('make order')
        print('no make order')
        pass
    def checkRules(self):
        if self.sheetRead.cell(self.currentRow-2, 3).value > 0.3:
            return True
        return False
    def createMedium(self, bitcoinValue):
        stockMedium = []
        medium = 0
        for i in range(self.currentRow-1, self.currentRow-11, -1):
            stockMedium.append(self.sheetRead.cell(i,1).value)

        for element in stockMedium:
            medium += element

        medium = float(medium)/10
        self.sheet.write(self.currentRow, 2, medium)
        percent = float(bitcoinValue) - medium
        percent = percent/float(medium)
        percent = percent * 100
        self.sheet.write(self.currentRow, 3, percent)

    def tickerListPair(self):
        assertRes = self.assetsPair()
        tickersPair = [ticker for ticker in assertRes["result"]]
        return tickersPair

    def tickersList(self):
        assertRes = self.assetsAll()
        tickers = [ticker for ticker in assertRes["result"]]
        return tickers

    def tickerData(self, tickerName):
        response = requests.get(f'https://api.kraken.com/0/public/Ticker?pair={tickerName}')
        return response.json()

if __name__ == '__main__':
    bot = KrakenBot(config('KEY'), config('SECRET'), config('PAIRS'))
    print('account_balance : ', bot.krakenAccountBalance())
    print('serverTime : ', bot.serverTime())
    print('assetsPair : ', bot.assetsAll())
    print('tickersList : ', bot.tickersList())
    print('tickerListPair : ', bot.tickerListPair())
    print('tickerRequested', bot.registerTickerDB())
    while True:
        print('run register')
        print('tickerRequested : ', bot.registerTickerDB())
        time.sleep(5)
