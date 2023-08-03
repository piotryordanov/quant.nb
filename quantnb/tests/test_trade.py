from quantnb.core.trade_module import TradeModule
from quantnb.core.data_module import DataModule
from quantnb.core.trade_create_new_trade import create_new_trade
from quantnb.indicators.random_data import random_data
from quantnb.lib.output_trades import output_trades
import pandas as pd
from quantnb.core.enums import (
    DataType,
    CommissionType,
    OrderDirection,
    Trade,
    OrderType,
)
import numpy as np


date, open, high, low, close, ohlc = random_data(2)

COMMISSION = 4
MAX_ACTIVE_TRADES = 3
SLIPPAGE = 0.4
INITIAL_CAPITAL = float(10000.0)


class TestCalculatePrice:
    trade_module = TradeModule(
        data_type=DataType.BID_ASK,
        multiplier=2,
        commission=COMMISSION,
        slippage=SLIPPAGE,
        max_active_trades=MAX_ACTIVE_TRADES,
    )
    data_module = DataModule(
        close=close,
        data_type=DataType.OHLC,
        bid=low,
        ask=high,
        date=date,
        slippage=SLIPPAGE,
        initial_capital=INITIAL_CAPITAL,
    )

    def add_trade(self, direction=OrderDirection.LONG, index=300, time_sl=np.inf):
        entry_price = self.data_module.get_entry_price(index, direction)  # index
        self.trade_module.add_trade(
            index,  # index
            direction.value,  # direction
            OrderType.MARKET,  # order_type
            date[index],  # entry_time
            entry_price,  # entry_price
            1,  # volume
            0,  # tp
            0,  # sl
            time_sl,  # time_sl
        )

    def test_add_trade(self, direction=OrderDirection.LONG):
        index = 300
        entry_price = self.data_module.get_entry_price(index, direction)  # index
        time_sl = self.data_module.date[323]
        self.add_trade(direction, index, time_sl=time_sl)
        assert self.trade_module.last_trade_index == 1
        last_trade = self.trade_module.trades[self.trade_module.last_trade_index - 1]

        assert last_trade[Trade.Index] == index
        assert last_trade[Trade.Direction] == direction.value
        assert last_trade[Trade.EntryTime] == date[index]
        assert last_trade[Trade.EntryPrice] == entry_price
        assert last_trade[Trade.Volume] == 1
        assert last_trade[Trade.ExitTime] == -1
        assert last_trade[Trade.ExitPrice] == -1
        assert last_trade[Trade.TP] == 0
        assert last_trade[Trade.SL] == 0
        assert last_trade[Trade.TIME_SL] == time_sl
        assert last_trade[Trade.PNL] == COMMISSION * -1
        assert last_trade[Trade.Commission] == COMMISSION
        assert last_trade[Trade.Active] == True
        assert last_trade[Trade.Extra] == -1

    def test_add_multiple_trades(self, direction=OrderDirection.LONG):
        idx = 0
        for index in range(300, 325):
            if index == 312:
                self.add_trade(direction, index)
            elif index == 324:
                self.add_trade(direction, index)
            self.trade_module.update_trades_pnl(self.data_module.close[index], 0, 0)
            self.trade_module.check_trades_to_close(
                self.data_module.date[index], self.data_module.close[index], 0, 0
            )
            self.data_module.update_equity(
                index, self.trade_module.closed_pnl, self.trade_module.floating_pnl
            )
            idx = index

        index = idx

        # CURRENT
        _sum = 0
        for trade in self.trade_module.active_trades:
            _sum += trade[Trade.PNL]

        current = self.data_module.close[index]
        initial_trade = self.data_module.close[300] + SLIPPAGE
        first_trade_entry = self.data_module.close[312] + SLIPPAGE
        second_trade_entry = self.data_module.close[324] + SLIPPAGE
        pnl0 = (current - initial_trade - SLIPPAGE) - COMMISSION
        pnl1 = (current - first_trade_entry - SLIPPAGE) - COMMISSION
        pnl2 = (current - second_trade_entry - SLIPPAGE) - COMMISSION

        expected_pnl = pnl0 + pnl1 + pnl2

        # print(expected_pnl)
        # print(_sum)

        expected_pnl = np.round(expected_pnl, 3)
        _sum = np.round(_sum, 3)

        assert expected_pnl == _sum

    def test_equity(self):
        expected = np.float32(
            np.round(INITIAL_CAPITAL + self.trade_module.floating_pnl, 3)
        )
        current = np.round(self.data_module.equity[324], 3)

        # trades = output_trades(self.trade_module)
        # print(trades)

        # print("==========")
        # print(current)
        # print(expected)
        # trades = output_trades(self.trade_module)
        # print(trades)
        assert expected == current

        # df = pd.DataFrame(self.data_module.equity)
        # df.plot()
        # plt.show()


# TestCalculatePrice().test_add_trade()
# TestCalculatePrice().test_add_multiple_trades()
# TestCalculatePrice().test_equity()
