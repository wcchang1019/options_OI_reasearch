import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator, FuncFormatter
import matplotlib as mpl
import datetime
import matplotlib.font_manager as fm
import sys
# plt.rcParams['axes.unicode_minus'] = False
font_path = r'C:\Users\white\Anaconda3\Lib\site-packages\matplotlib\mpl-data\fonts\ttf\NotoSansMonoCJKtc-Regular.otf'
chinese_font = fm.FontProperties(fname=font_path, size=20)


def plot_performance(per_profit, dates, model_name):
    ans = per_profit
    trades_count = len(ans)
    win_count = len([x for x in ans if x > 0])
    total = list(np.cumsum(ans))
    dd = []
    for x in ans:
        if len(dd) == 0:
            if x > 0:
                dd.append(0)
            else:
                dd.append(x)
        elif dd[-1] + x > 0:
            dd.append(0)
        else:
            dd.append(dd[-1] + x)
    try:
        xs = [datetime.datetime.strptime(d, '%Y-%m-%d').date() for d in dates]
    except:
        xs = dates
    highest_x = []
    highest_dt = []
    for i in range(len(total)):
        if total[i] == max(total[:i+1]) and total[i] > 0:
            highest_x.append(total[i])
            highest_dt.append(i)
    mpl.style.use('seaborn')
    f, axarr = plt.subplots(2, sharex=True, figsize=(20, 12), gridspec_kw={'height_ratios': [3, 1]})
    axarr[0].plot(np.arange(len(xs)), total, color='b', zorder=1)
    axarr[0].scatter(highest_dt, highest_x, color='lime', marker='o', s=40, zorder=2)
    axarr[0].set_title(str(model_name) + ' Equity Curve', fontsize=20, fontproperties=chinese_font)
    axarr[1].bar(np.arange(len(xs)), dd, color='red')
    date_tickers = dates
    def format_date(x,pos=None):
        if x < 0 or x > len(date_tickers)-1:
            return ''
        return date_tickers[int(x)]
    axarr[0].xaxis.set_major_locator(MultipleLocator(80))
    axarr[0].xaxis.set_major_formatter(FuncFormatter(format_date))
    axarr[0].grid(True)
    shift = (max(total)-min(total))/20
    text_loc = max(total)-shift
    axarr[0].text(np.arange(len(xs))[5], text_loc, 'Total trades: %d' % trades_count, fontsize=15)
    axarr[0].text(np.arange(len(xs))[5], text_loc-shift, 'Win ratio: %.2f' % (win_count/trades_count), fontsize=15)
    axarr[0].text(np.arange(len(xs))[5], text_loc-shift*2, 'Total profit points: %d' % total[-1], fontsize=15)
    axarr[0].text(np.arange(len(xs))[5], text_loc-shift*3, 'Average profit points: %.2f' % (total[-1]/trades_count), fontsize=15)
    axarr[0].text(np.arange(len(xs))[5], text_loc-shift*4, 'Max drawdown: %d' % min(dd), fontsize=15)
    plt.savefig(model_name + '.jpg')
    plt.show()


def options_hold_strategy(bs_type, options_df, futures_df, order, amp_range, cp_type=None):
    all_dt = np.unique(options_df['date'])
    all_dt.sort()
    if not cp_type:
        open_day_df = options_df[(options_df['date'] == all_dt[0])]
    else:
        open_day_df = options_df[(options_df['date'] == all_dt[0]) & (options_df['CP'] == cp_type)]
    sorted_volume = list(open_day_df.loc[:, 'OI'])
    sorted_volume.sort()
    open_exercise_price = open_day_df[open_day_df['OI'] == sorted_volume[order]]
    exercise_price = open_exercise_price['exercise_price'].iloc[0]
    cp = open_exercise_price['CP'].iloc[0]
    x = (open_exercise_price['close'].iloc[0] - open_exercise_price['open'].iloc[0])/open_exercise_price['open'].iloc[0]
    if -amp_range < x < amp_range:
        print('No trade', end=' ')
        return None, None
    print(exercise_price, cp, end=' ')
    try:
        next_day_df = options_df[options_df['date'] == all_dt[1]]
    except:
        print('Not enough day error', end=' ')
        return None, None
    open_price = next_day_df[(next_day_df['exercise_price'] == exercise_price)
                             & (next_day_df['CP'] == cp)]['open'].iloc[0]
    if np.isnan(open_price):
        print('open price nan error', end=' ')
        sys.exit()
    close_day_df = options_df[options_df['date'] == all_dt[-1]]
    close_price = close_day_df[(close_day_df['exercise_price'] == exercise_price)
                               & (close_day_df['CP'] == cp)]['close'].iloc[0]
    if np.isnan(close_price):
        final_price = futures_df[futures_df['date'] == all_dt[-1]]['close'].iloc[0]
        if cp_type == 'Call' or cp == 'Call':
            final_value = final_price - exercise_price
            if final_value > 0:
                close_price = final_price
            else:
                close_price = 0
        elif cp_type == 'Put' or cp == 'Put':
            final_value = exercise_price - final_price
            if final_value > 0:
                close_price = final_price
            else:
                close_price = 0
    if bs_type == 'buy':
        return all_dt[-1], close_price-open_price
    elif bs_type == 'sell':
        return all_dt[-1], open_price-close_price


def hold_strategy_performance():
    df = pd.read_csv('daily_TXO.csv', index_col=0, low_memory=False).iloc[:, [1, 2, 3, 4, 5, 6, 7, 13, 14, 19]]
    df.columns = ['settlement', 'exercise_price', 'CP', 'open', 'high', 'low', 'close', 'volume', 'OI', 'date']
    week_contracts = np.unique(df.iloc[:, 0].astype(str))
    week_contracts = week_contracts[['W' in i for i in week_contracts]]
    print(week_contracts)
    num = -3
    amp = 0.16
    profit = []
    all_dt = []
    for wc in week_contracts:
        print(wc, end=' ')
        dt, tmp = options_hold_strategy('sell', df[df['settlement'] == wc], num, amp)
        if dt and tmp:
            profit.append(tmp)
            all_dt.append(dt)
    print(profit, all_dt)
    name = '裸賣第%d大未平倉量+振幅%.2f~%.2f不做交易' % (num*-1, -amp, amp)
    plot_performance(profit, all_dt, name)


if __name__ == '__main__':
    txo = pd.read_csv('daily_TXO.csv', index_col=0, low_memory=False).iloc[:, [1, 2, 3, 4, 5, 6, 7, 13, 14, 19]]
    txo.columns = ['settlement', 'exercise_price', 'CP', 'open', 'high', 'low', 'close', 'volume', 'OI', 'date']
    txo['date'] = [datetime.datetime.strptime(dt, '%Y-%m-%d') for dt in txo['date']]
    txf = pd.read_csv('daily_TXF.csv').loc[:, ['date', 'close']]
    txf['date'] = [datetime.datetime.strptime(dt, '%Y/%m/%d') for dt in txf['date']]

    week_contracts = np.unique(txo.iloc[:, 0].astype(str))
    week_contracts = week_contracts[['W' in i for i in week_contracts]]
    print(week_contracts)
    num = -3
    amp = 0
    x = -3
    y = -4
    profit = []
    all_dt = []
    for wc in week_contracts:
        print(wc, end=' ')
        dt, tmp = options_hold_strategy('sell', txo[txo['settlement'] == wc], txf, x, 0.16, None)
        dt2, tmp2 = options_hold_strategy('buy', txo[txo['settlement'] == wc], txf, y, 0.3, None)
        print()
        # print(tmp, tmp2)
        ans = 0
        if tmp:
            ans += tmp
        if tmp2:
            ans += tmp2
        if dt:
            profit.append(ans)
            all_dt.append(dt)
        elif dt2:
            profit.append(ans)
            all_dt.append(dt2)
    # print(profit, all_dt)
    name = 'Sell-' + str(x) + ' Buy-' + str(y) + 'Amp-' + str(0.16) + 'Amp2-' + str(0.3)
    plot_performance(profit, all_dt, name)
