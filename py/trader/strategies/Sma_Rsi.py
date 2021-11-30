import alpaca_backtrader_api
import backtrader as bt
from datetime import datetime

from py.trader.main import IS_BACKTEST, IS_LIVE,symbol,data0

class SessionFilter(object):
    def __init__(self, data):
        pass
    def __call__(self, data):
        if data.p.sessionstart <= data.datetime.time() <= data.p.sessionend:
            return False  
        data.backwards()  
        return True 
class Sma_Rsi_Cross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=5,  # period for the fast moving average
        pslow=15,   # period for the slow moving average
        rsi_per=14,
        rsi_upper=60.0,
        rsi_lower=40.0,
        rsi_out=50.0,
        warmup=35
    )

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime[0]
        dt = bt.num2date(dt)
        #print('%s, %s' % (dt.isoformat(), txt))

    def notify_trade(self, trade):
        self.log("placing trade for {}. target size: {}".format(
            trade.getdataname(),
            trade.size))

    def notify_order(self, order):
        print(f"Order notification. status{order.getstatusname()}.")
        print(f"Order info. status{order.info}.")
    def notify_store(self, msg, *args, **kwargs):
        super().notify_store(msg, *args, **kwargs)
        self.log(msg)

    def stop(self):
        print('==================================================')
        print('Starting Value - %.2f' % self.broker.startingcash)
        print('Ending   Value - %.2f' % self.broker.getvalue())
        print('==================================================')

    def __init__(self):
        self.live_bars = False
        sma1 = bt.ind.SMA(self.data0, period=self.p.pfast)
        sma2 = bt.ind.SMA(self.data0, period=self.p.pslow)
        self.crossover = bt.ind.CrossOver(sma1, sma2,plotskip=True)

        rsi = bt.indicators.RSI(period=self.p.rsi_per,
                                upperband=self.p.rsi_upper,
                                lowerband=self.p.rsi_lower,plotskip=True)

        self.crossdown = bt.ind.CrossDown(rsi, self.p.rsi_upper,plotskip=True)
        self.crossup = bt.ind.CrossUp(rsi, self.p.rsi_lower,plotskip=True)

    def notify_data(self, data, status, *args, **kwargs):
        super().notify_data(data, status, *args, **kwargs)
        #print('*' * 5, 'DATA NOTIF:', data._getstatusname(status), *args)
        if data._getstatusname(status) == "LIVE":
            self.live_bars = True

    def next(self):
        if not self.live_bars and not IS_BACKTEST:
            # only run code if we have live bars (today's bars).
            # ignore if we are backtesting
            return
        # if fast crosses slow to the upside
        if not self.positionsbyname[symbol].size:
            if self.crossover > 0 or self.crossup > 0:
                self.buy(data=data0, size=80)  # enter long

        # in the market & cross to the downside
        if self.positionsbyname[symbol].size:
            if self.crossover <= 0 or self.crossdown < 0:
                self.close(data=data0)  # close long position