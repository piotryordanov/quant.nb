from numba import njit
from quantnb.lib.plotting import plotting
from quantnb.lib.time_manip import time_manip
from quantnb.lib import np, timeit, pd, find_files
from quantnb.lib.calculate_stats import calculate_stats
from quantnb.lib.output_trades import output_trades
from quantnb.core.enums import CommissionType, DataType
from quantnb.lib import pd, find_files, np, optimize

import quantnb as qnb

# import talib
import pandas_ta as ta

from quantnb.strategies.S_base import S_base
from quantnb.core.backtester import Backtester
from quantnb.strategies.S_bid_ask import S_bid_ask
from quantnb.core.place_orders_on_ohlc import place_orders_on_ohlc
import matplotlib

import quantnb.indicators as ind

# ==================================================================== #
#                                                                      #
# ==================================================================== #
ohlc = pd.read_parquet("./data/binance-BTCUSDT-1h.parquet")
ohlc = pd.read_parquet("./data/binance-ETHUSDT-1h.parquet")
ohlc.reset_index(inplace=True)

"""
Uncomment this if you want to see how it would look like on arbitrum equivalent data, which start in Dec 2022
"""
# ohlc = ohlc[-6000:]

INITIAL_CAPITAL = 10000
ohlc

# ohlc = ohlc[0:210]

# ohlc = ohlc[3120:4600]
ohlc = ohlc[3120:]
ohlc


# |%%--%%| <bKsjcb3XDl|QgQzeXd36C>

import os
from quantnb.lib import np, timeit, pd, find_files

def strategy(ohlc, params, plot=False):
    def get_signals(params):
        # long, short, cutoff, atr_distance = params
        long, short, cutoff = params
        close = ohlc.close
        # ma_long = ind.talib_SMA(ohlc.close, long)
        # ma_short = ind.talib_SMA(close, short)
        # rsi = talib.RSI(close, timeperiod=2)
        # atr = talib.ATR(ohlc.high, ohlc.low, close, 14)

        ma_long = ta.sma(ohlc.close, length=long)
        ma_short = ta.sma(ohlc.close, length=short)
        rsi = ta.rsi(ohlc.close, length=2)
        atr = ta.atr(ohlc.high, ohlc.low, close, 14)
        #
        entries = np.logical_and(
            close <= ma_short,
            np.logical_and(close >= ma_long, rsi <= cutoff),
        ).values
        exits = ind.cross_above(close, ma_short)

        # sl = ohlc.low - atr * atr_distance

        return entries, exits, ma_long, ma_short, rsi

    entries, exits, ma_long, ma_short, rsi = get_signals(params)
    backtester = qnb.core.backtester.Backtester(
        close=ohlc.close.to_numpy(dtype=np.float32),
        data_type=DataType.OHLC,
        date=time_manip.convert_datetime_to_ms(ohlc["Date"]).values,
        initial_capital=INITIAL_CAPITAL,
        commission=0.0005,
        commission_type=CommissionType.PERCENTAGE,
    )

    # Shift the array one position to the left
    def shift(arr, index=1):
        return np.concatenate((arr[index:], arr[:index]))

    backtester.from_signals(
        long_entries=entries,
        long_exits=exits,
        short_entries=exits,
        short_exits=entries,
        short_entry_price=shift(ohlc.open),
        long_entry_price=shift(ohlc.open),
        # short_entry_price=ohlc.close.to_numpy(dtype=np.float32),
        # long_entry_price=ohlc.close.to_numpy(dtype=np.float32),
        default_size=0.99
    )
    trades, closed_trades, active_trades = output_trades(backtester.bt)
    stats = calculate_stats(
        ohlc,
        trades,
        closed_trades,
        backtester.data_module.equity,
        INITIAL_CAPITAL,
        display=False,
        index=[(params)],
    )
    print(stats)
    if plot:
        plotting.plot_equity(backtester, ohlc, "close")
    return stats


strategy(ohlc, (112, 6, 8), plot=True)
# strategy(ohlc, (526, 6, 10), plot=True)
# for i in range(0, 1):
#     for long in range(100 + i * 50, 150 + i * 50, 1):
#         for short in range(5, 55, 1):
#             for rsi in range(3, 15, 1):
#                 stats = strategy(ohlc, (long, short, rsi))

# |%%--%%| <QgQzeXd36C|B71b17sxwt>


assets = find_files("./data/", "binance-BTC")
assets

step = 50
for asset in assets:
    sym = asset.split("/")[-1].split(".")[0]
    data = pd.read_parquet(asset)
    print(asset)
    print(data)
    for i in range(0, 9):
        print(i)
        out = f"./optimisation/{sym}-RSI-{i}.parquet"
        if not os.path.exists(out):
            optimisation = optimize(
                ohlc,
                strategy,
                # long=range(100, 101, 1),
                # short=range(5, 55, 1),
                # rsi=range(3, 15, 1),
                long=range(100 + i * step, 150 + i * step, 1),
                short=range(5, 55, 1),
                rsi=range(3, 15, 1),
                # atr_distance=np.arange(0.5, 10.5, 0.5),
            )
            print(optimisation)
            # optimisation = optimisation.sort_values("ratio", ascending=False)
            optimisation.to_parquet(f"./optimisation/{sym}-RSI-{i}.parquet")
# print(optimisation)
# optimisation.sort_values("ratio", ascending=False)
# |%%--%%| <B71b17sxwt|wKaYjtFVdf>


newdf = pd.DataFrame()

opti = find_files("./optimisation/", "RSI")
for opt in opti:
    df = pd.read_parquet(opt)
    newdf = pd.concat([newdf, df])

# newdf.sort_values("RIO: (%)", ascending=False)
newdf.sort_values("ratio", ascending=False)
newdf.sort_values("End Value", ascending=False)
