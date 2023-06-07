import numpy as np
import pandas as pd
from backtester import backtest
from Helpers import Helpers

import talib

from temp import EMA, SMA, print_trades, plot_equity, calculate_metrics
from plot_ohlc import plot_ohlc


class S_rsi:
    def __init__(self, data, offset=0):
        data = pd.read_parquet(data)
        data = data[offset:]

        data.rename(
            columns={"close": "Close", "high": "High", "low": "Low", "open": "Open"},
            inplace=True,
        )
        self.data = data

    def simulation(self, mode, use_sl):
        close = self.data.Close
        size = np.full_like(close, 1)
        multiplier = 1
        size = size * multiplier
        # fees = np.full_like(prices, 2.2)

        final_value, total_pnl, equity, orders_array, trades_array = backtest(
            close.values,
            self.data.Low.values,
            self.data.Open.values,
            self.data.index.values.astype(np.int64),
            self.entries.values,
            self.exits.values,
            self.sl.values,
            size,
            initial_capital=10000,
            transaction_cost=0.0005,
            mode=mode,
            use_sl=use_sl,
        )

        return final_value, equity, orders_array, trades_array

    def get_signals(self, params):
        long, short, cutoff, atr_distance = params
        close = self.data.Close
        self.ma_long = SMA(close, long)
        self.ma_short = SMA(close, short)
        self.rsi = talib.RSI(close, timeperiod=2)
        self.atr = talib.ATR(self.data.High, self.data.Low, close, 14)

        self.entries = np.logical_and(
            close <= self.ma_short,
            np.logical_and(close >= self.ma_long, self.rsi <= cutoff),
        )
        self.exits = close > self.ma_short

        self.sl = self.data.Low - self.atr * atr_distance

    def backtest(self, params):
        self.get_signals(params)
        (final_value, equity, orders_arr, trades_arr) = self.simulation(
            mode=1, use_sl=True
        )
        self.orders_arr = orders_arr

        dd, total_return, ratio, buy_and_hold = calculate_metrics(
            equity, self.data, final_value
        )

        self.stats = pd.DataFrame(
            {
                "final_value": final_value,
                "dd": dd,
                "total_return": total_return,
                "ratio": ratio,
                "buy_and_hold": buy_and_hold,
            },
            index=[0],
        )

        self.trades_arr = trades_arr
        self.equity = equity
        # print(self.stats)

        long, short, cutoff, atr_distance = params
        return {
            "long": long,
            "short": short,
            "rsi": cutoff,
            "atr": atr_distance,
            "final_value": final_value,
            "dd": dd,
            "total_return": total_return,
            "ratio": ratio,
        }

    def print_trades(self):
        print_trades(self.trades_arr)

    def plot_equity(self):
        plot_equity(self.equity, self.data)

    def plot_ohlc(self, offset=50):
        plot_ohlc(
            self.data[offset:],
            self.equity[offset:],
            self.entries[offset:],
            self.exits[offset:],
            self.ma_long[offset:],
            self.ma_short[offset:],
            self.rsi[offset:],
            self.sl[offset:],
        )

    def save_to_csv(self):
        data = self.data.copy()
        data.reset_index(inplace=True)
        data.rename(columns={"timestamp": "Date"}, inplace=True)
        data.set_index("Date", inplace=True)

        Helpers.save_to_csv(
            data,
            self.ma_long,
            self.ma_short,
            self.rsi,
            self.atr,
            self.entries,
            self.orders_arr,
            self.equity,
            "",
        )
