import numpy as np
import matplotlib as mpl
import datetime
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FuncFormatter


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
