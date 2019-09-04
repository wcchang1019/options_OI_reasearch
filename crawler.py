import requests
from bs4 import BeautifulSoup
import datetime
import pandas as pd
import numpy as np
import time
from datetime import timedelta


def get_options_price(date, contract, session, debug=True):
    """ Get options price table from the website.
    http://www.taifex.com.tw/cht/3/optDailyMarketReport
    (選擇權每日交易行情)
    Args:
        date: date in datetime.date() format
        contract: contract in string format
        session: trading session
            regular: 一般交易時段
            ah: 盤後交易時段(after hours)
    Return:
        True/False:
            True: Parse the website successfully
            False: Fail to parse the website
        target_table: an array with all the values
    """

    url = 'http://www.taifex.com.tw/cht/3/optDailyMarketReport'

    if session == 'regular':
        market_code = 0
    elif session == 'ah':
        market_code = 1
    else:
        print('Parse taifex options price: Invalid session type')
        return False, list()

    data = {'queryType': 2,
            'marketCode': market_code,
            'commodity_id': contract,
            'MarketCode': market_code,
            'commodity_idt': contract,
            'queryDate': str(date.year) + '/' + str(date.month).zfill(2) + '/' + str(date.day).zfill(2)}

    try:
        r = requests.post(url, data)
        r.encoding = 'utf8'
        soup = BeautifulSoup(r.text, 'html5lib')
        tables = soup.find_all("table")
        target_table = tables[4]
        target_table = [item.text for item in target_table.find_all('td', {'class': ['12bk', '12green']})]
        if len(target_table) == 0:
            if debug:
                print('Parse taifex options price: Target table is empty')
            return False, list()
        if len(target_table) % 19 != 0:
            target_table = target_table[:int(len(target_table)/19)*19]
        ignore_list = ['\r', '\n', '\t', ',', ' ', '▼', '▲', '%']
        for ignore in ignore_list:
            target_table = [item.replace(ignore, '') for item in target_table]

        # 部分表格為'-'
        for i, v in enumerate(target_table):
            if v == '-':
                target_table[i] = None

        return True, target_table
    except Exception as e:
        if debug:
            print('Parse taifex options price: ' + str(e))
        return False, list()


def daily_txo_reload():
    total = pd.read_csv('daily_TXO.csv', index_col=0, low_memory=False)
    all_date = np.unique(total.iloc[:, -1])
    last_date = datetime.datetime.strptime(all_date[-1], '%Y-%m-%d').date()
    last_date += datetime.timedelta(days=1)
    while last_date != datetime.datetime.now().date()+datetime.timedelta(days=1):
        print(last_date)
        flag, data = get_options_price(last_date, 'TXO', 'regular')
        if flag:
            tmp = pd.DataFrame(np.reshape(data, (int(len(data)/19), 19)))
            tmp['date'] = last_date
            tmp.columns = total.columns
            total = total.append(tmp, ignore_index=True)
        last_date += datetime.timedelta(days=1)
        time.sleep(3)
    total.to_csv('daily_TXO.csv')


def get_futures_price(date, contract, session, debug=True):
    """ Get futures price table from the website.

    http://www.taifex.com.tw/cht/3/futDailyMarketReport
    (期貨每日交易行情)

    Args:
        date: date in datetime.date() format
        contract: contract in string format
        session: trading session
            regular: 一般交易時段
            ah: 盤後交易時段(after hours)

    Return:
        True/False:
            True: Parse the website successfully
            False: Fail to parse the website
        target_table: an array with all the values
    """

    url = 'http://www.taifex.com.tw/cht/3/futDailyMarketReport'

    if session == 'regular':
        market_code = 0
    elif session == 'ah':
        market_code = 1
    else:
        print('Parse taifex futures price: Invalid session type')
        return False, list()

    data = {'queryType': 2,
            'marketCode': market_code,
            'commodity_id': contract,
            'MarketCode': market_code,
            'commodity_idt': contract,
            'queryDate': str(date.year) + '/' + str(date.month).zfill(2) + '/' + str(date.day).zfill(2)}

    try:
        r = requests.post(url, data)
        r.encoding = 'utf8'
        soup = BeautifulSoup(r.text, 'html.parser')
        tables = soup.find_all("table")
        target_table = tables[4]
        target_table = [item.text for item in target_table.find_all('td', {'class': ['12bk', '12green']})]
        if len(target_table) == 0:
            if debug:
                print('Parse taifex futures price: Target table is empty')
            return False, list()

        ignore_list = ['\r', '\n', '\t', ',', ' ', '▼', '▲', '%']
        for ignore in ignore_list:
            target_table = [item.replace(ignore, '') for item in target_table]

        # 部分表格為'-'
        for i, v in enumerate(target_table):
            if v == '-':
                target_table[i] = None

        return True, target_table
    except Exception as e:
        if debug:
            print('Parse taifex futures price: ' + str(e))
        return False, list()


def date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


def daily_txf_reload():
    df = pd.read_csv('daily_TXF.csv')
    file_end_date = list(df['date'])[-1]
    start_dt = datetime.datetime.strptime(file_end_date, "%Y/%m/%d").date() + timedelta(days=1)
    end_dt = datetime.date.today()
    all_daily_price = list()
    for dt in date_range(start_dt, end_dt):
        a, b = get_futures_price(dt, 'TX', 'regular')
        if a:
            daily_price = [dt.strftime('%Y/%m/%d')] + b[2:13]
            all_daily_price.append(daily_price)
            print(dt)
        time.sleep(2)
    col = ['date', 'open', 'high', 'low', 'close', 'up_down', 'up_down_ratio',
           'ah_v', 'r_v', 'total_v', 'final_price', 'unfilled_v']
    df2 = pd.DataFrame(all_daily_price, columns=col)
    result = pd.concat([df, df2])
    result.reset_index(drop=True, inplace=True)
    result.to_csv('daily_TXF.csv', index=False)


if __name__ == '__main__':
    daily_txo_reload()
    daily_txf_reload()
