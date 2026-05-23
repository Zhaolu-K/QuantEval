我希望你作为一名使用VeighNa（vn.py）量化平台经验丰富的量化研究员，根据我描述的需求开发对应的程序代码。对于你开发的程序代码，都会提供对于程序逻辑的细节中文注释，代码中使用类型提示Type Hinting，同时代码内容需要符合PEP8代码标准要求。

使用VeighNa平台的CTA策略模板CtaTemplate（位于vnpy_ctastrategy.template子模块下），开发一套量化策略SuperComboStrategy。

具体策略逻辑可以参考该网页上的内容：https://c.mql5.com/forextsd/forum/161/super_combo_day_trading_strategy.pdf

vnpy_ctastrategy.template.py的 代码如下：
```python
from abc import ABC
from copy import copy
from typing import Any, Callable, List

from vnpy.trader.constant import Interval, Direction, Offset
from vnpy.trader.object import BarData, TickData, OrderData, TradeData
from vnpy.trader.utility import virtual

from .base import StopOrder, EngineType

class CtaTemplate(ABC):
    """"""

    author: str = ""
    parameters: list = []
    variables: list = []

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ) -> None:
        """"""
        self.cta_engine: Any = cta_engine
        self.strategy_name: str = strategy_name
        self.vt_symbol: str = vt_symbol

        self.inited: bool = False
        self.trading: bool = False
        self.pos: int = 0

        # Copy a new variables list here to avoid duplicate insert when multiple
        # strategy instances are created with the same strategy class.
        self.variables = copy(self.variables)
        self.variables.insert(0, "inited")
        self.variables.insert(1, "trading")
        self.variables.insert(2, "pos")

        self.update_setting(setting)

    def update_setting(self, setting: dict) -> None:
        """
        Update strategy parameter wtih value in setting dict.
        """
        for name in self.parameters:
            if name in setting:
                setattr(self, name, setting[name])

    @classmethod
    def get_class_parameters(cls) -> dict:
        """
        Get default parameters dict of strategy class.
        """
        class_parameters: dict = {}
        for name in cls.parameters:
            class_parameters[name] = getattr(cls, name)
        return class_parameters

    def get_parameters(self) -> dict:
        """
        Get strategy parameters dict.
        """
        strategy_parameters: dict = {}
        for name in self.parameters:
            strategy_parameters[name] = getattr(self, name)
        return strategy_parameters

    def get_variables(self) -> dict:
        """
        Get strategy variables dict.
        """
        strategy_variables: dict = {}
        for name in self.variables:
            strategy_variables[name] = getattr(self, name)
        return strategy_variables

    def get_data(self) -> dict:
        """
        Get strategy data.
        """
        strategy_data: dict = {
            "strategy_name": self.strategy_name,
            "vt_symbol": self.vt_symbol,
            "class_name": self.__class__.__name__,
            "author": self.author,
            "parameters": self.get_parameters(),
            "variables": self.get_variables(),
        }
        return strategy_data

    @virtual
    def on_init(self) -> None:
        """
        Callback when strategy is inited.
        """
        pass

    @virtual
    def on_start(self) -> None:
        """
        Callback when strategy is started.
        """
        pass

    @virtual
    def on_stop(self) -> None:
        """
        Callback when strategy is stopped.
        """
        pass

    @virtual
    def on_tick(self, tick: TickData) -> None:
        """
        Callback of new tick data update.
        """
        pass

    @virtual
    def on_bar(self, bar: BarData) -> None:
        """
        Callback of new bar data update.
        """
        pass

    @virtual
    def on_trade(self, trade: TradeData) -> None:
        """
        Callback of new trade data update.
        """
        pass

    @virtual
    def on_order(self, order: OrderData) -> None:
        """
        Callback of new order data update.
        """
        pass

    @virtual
    def on_stop_order(self, stop_order: StopOrder) -> None:
        """
        Callback of stop order update.
        """
        pass

    def buy(
        self,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        net: bool = False
    ) -> list:
        """
        Send buy order to open a long position.
        """
        return self.send_order(
            Direction.LONG,
            Offset.OPEN,
            price,
            volume,
            stop,
            lock,
            net
        )

    def sell(
        self,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        net: bool = False
    ) -> list:
        """
        Send sell order to close a long position.
        """
        return self.send_order(
            Direction.SHORT,
            Offset.CLOSE,
            price,
            volume,
            stop,
            lock,
            net
        )

    def short(
        self,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        net: bool = False
    ) -> list:
        """
        Send short order to open as short position.
        """
        return self.send_order(
            Direction.SHORT,
            Offset.OPEN,
            price,
            volume,
            stop,
            lock,
            net
        )

    def cover(
        self,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        net: bool = False
    ) -> list:
        """
        Send cover order to close a short position.
        """
        return self.send_order(
            Direction.LONG,
            Offset.CLOSE,
            price,
            volume,
            stop,
            lock,
            net
        )

    def send_order(
        self,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        net: bool = False
    ) -> list:
        """
        Send a new order.
        """
        if self.trading:
            vt_orderids: list = self.cta_engine.send_order(
                self, direction, offset, price, volume, stop, lock, net
            )
            return vt_orderids
        else:
            return []

    def cancel_order(self, vt_orderid: str) -> None:
        """
        Cancel an existing order.
        """
        if self.trading:
            self.cta_engine.cancel_order(self, vt_orderid)

    def cancel_all(self) -> None:
        """
        Cancel all orders sent by strategy.
        """
        if self.trading:
            self.cta_engine.cancel_all(self)

    def write_log(self, msg: str) -> None:
        """
        Write a log message.
        """
        self.cta_engine.write_log(msg, self)

    def get_engine_type(self) -> EngineType:
        """
        Return whether the cta_engine is backtesting or live trading.
        """
        return self.cta_engine.get_engine_type()

    def get_pricetick(self) -> float:
        """
        Return pricetick data of trading contract.
        """
        return self.cta_engine.get_pricetick(self)

    def get_size(self) -> int:
        """
        Return size data of trading contract.
        """
        return self.cta_engine.get_size(self)

    def load_bar(
        self,
        days: int,
        interval: Interval = Interval.MINUTE,
        callback: Callable = None,
        use_database: bool = False
    ) -> None:
        """
        Load historical bar data for initializing strategy.
        """
        if not callback:
            callback: Callable = self.on_bar

        bars: List[BarData] = self.cta_engine.load_bar(
            self.vt_symbol,
            days,
            interval,
            callback,
            use_database
        )

        for bar in bars:
            callback(bar)

    def load_tick(self, days: int) -> None:
        """
        Load historical tick data for initializing strategy.
        """
        ticks: List[TickData] = self.cta_engine.load_tick(self.vt_symbol, days, self.on_tick)

        for tick in ticks:
            self.on_tick(tick)

    def put_event(self) -> None:
        """
        Put an strategy data event for ui update.
        """
        if self.inited:
            self.cta_engine.put_strategy_event(self)

    def send_email(self, msg) -> None:
        """
        Send email to default receiver.
        """
        if self.inited:
            self.cta_engine.send_email(msg, self)

    def sync_data(self) -> None:
        """
        Sync strategy variables value into disk storage.
        """
        if self.trading:
            self.cta_engine.sync_strategy_data(self)
```

具体策略逻辑：

```
Inputs:
    waitPeriodMins(30),
    initTradesEndTime(1430),
    liqRevEndTime(1200),
    thrustPrcnt1(0.30),
    thrustPrcnt2(0.60),
    breakOutPrcnt(0.25),
    failedBreakOutPrcnt(0.25),
    protStopPrcnt1(0.25),
    protStopPrcnt2(0.15),
    protStopAmt(3.00),
    breakEvenPrcnt(0.50),
    avgRngLength(10),
    avgOCLength(10);

Variables:
    averageRange(0),
    averageOCRange(0),
    canTrade(0),
    buyEasierDay(FALSE),
    sellEasierDay(FALSE),
    buyBOPoint(0),
    sellBOPoint(0),
    longBreakPt(0),
    shortBreakPt(0),
    longFBOPoint(0),
    shortFBOPoint(0),
    barCount(0),
    intraHigh(0),
    intraLow(999999),
    buysToday(0),
    sellsToday(0),
    currTrdType(0),
    longLiqPoint(0),
    shortLiqPoint(0),
    yesterdayOCRRange(0),
    intraTradeHigh(0),
    intraTradeLow(999999);

{Just like we did in the pseudocode—let's start out with the daily bar calculations. If Date <> Date[1]—first bar of day}
if (Date <> Date[1]) then {save time by doing these calculations once per day}
begin
    averageRange = Average(Range, 10) of Data2; {Data 2 points to daily bars}
    yesterdayOCRRange = AbsValue(Open of Data2 - Close of Data2);
    averageOCRange = Average(AbsValue(Open of Data2 - Close of Data2), 10);
    canTrade = 0;
    if (yesterdayOCRRange < 0.85 * averageOCRange) then canTrade = 1;
    buyEasierDay = FALSE;
    sellEasierDay = FALSE;

    {See how we refer to Data2 - the daily data}
    if (Close of Data2 <= Close[1] of Data2) then buyEasierDay = TRUE;
    if (Close of Data2 > Close[1] of Data2) then sellEasierDay = TRUE;

    if (buyEasierDay) then
    begin
        buyBOPoint = Open of data1 + thrustPrcnt1 * averageRange;
        sellBOPoint = Open of data1 - thrustPrcnt2 * averageRange;
    end;

    if (sellEasierDay) then
    begin
        sellBOPoint = Open of data1 - thrustPrcnt1 * averageRange;
        buyBOPoint = Open of data1 + thrustPrcnt2 * averageRange;
    end;

    longBreakPt = High of Data2 + breakOutPrcnt * averageRange;
    shortBreakPt = Low of Data2 - breakOutPrcnt * averageRange;
    shortFBOPoint = High of Data2 - failedBreakOutPrcnt * averageRange;
    longFBOPoint = Low of Data2 + failedBreakOutPrcnt * averageRange;

    {Go ahead and initialize any variables that we may need later on in the day}
    barCount = 0;
    intraHigh = 0;
    intraLow = 999999; {Didn't know you could do this}
    buysToday = 0;
    sellsToday = 0; {You can put multiple statements on one line}
    currTrdType = 0;
end; {End of the first bar of data}

{Now let's trade and manage on 5-min bars}
if (High > intraHigh) then intraHigh = High;
if (Low < intraLow) then intraLow = Low;
barCount = barCount + 1; {count the number of bars of intraday data}

if (barCount > waitPeriodMins / BarInterval and canTrade = 1) then
{have we waited long enough—wait PeriodMin is an input variable and BarInterval is set by TradeStation. Wait PeriodMins = 30 and BarInterval = 5, so 30/5 = 6}
begin
    if (MarketPosition = 0) then
    begin
        intraTradeHigh = 0;
        intraTradeLow = 999999;
    end;

    if (MarketPosition = 1) then
    begin
        intraTradeHigh = MaxList(intraTradeHigh, High);
        buysToday = 1;
    end;

    if (MarketPosition = -1) then
    begin
        intraTradeLow = MinList(intraTradeLow, Low);
        sellsToday = 1;
    end;

    if (buysToday = 0 and Time < initTradesEndTime) then
        Buy("LBreakOut") next bar at buyBOPoint stop;

    if (sellsToday = 0 and Time < initTradesEndTime) then
        SellShort("SBreakout") next bar at sellBOPoint stop;

    if (intraHigh > longBreakPt and sellsToday = 0 and Time < initTradesEndTime) then
        SellShort("SfailedBO") next bar at shortFBOPoint stop;

    if (intraLow < shortBreakPt and buysToday = 0 and Time < initTradesEndTime) then
        Buy("BfailedBO") next bar at longFBOPoint stop;

    {The next module keeps track of positions and places protective stops}
    if (MarketPosition = 1) then
    begin
        longLiqPoint = EntryPrice - protStopPrcnt1 * averageRange;
        longLiqPoint = MinList(longLiqPoint, EntryPrice - protStopAmt);

        if (MarketPosition(1) = -1 and BarsSinceEntry = 1 and High[1] >= shortLiqPoint and shortLiqPoint < shortFBOPoint) then
            currTrdType = -2; {we just got long from a short liq reversal}

        if (currTrdType = -2) then
        begin
            longLiqPoint = EntryPrice - protStopPrcnt2 * averageRange;
            longLiqPoint = MinList(longLiqPoint, EntryPrice - protStopAmt);
        end;

        if (intraTradeHigh >= EntryPrice + breakEvenPrcnt * averageRange) then
            longLiqPoint = EntryPrice; {BreakEven trade}

        if (Time >= initTradesEndTime) then
            longLiqPoint = MaxList(longLiqPoint, Lowest(Low, 3)); {Trailing stop}

        if (Time < liqRevEndTime and sellsToday = 0 and longLiqPoint <> EntryPrice and BarsSinceEntry ≥ 4) then
        begin
            SellShort("LongLiqRev") next bar at longLiqPoint stop;
        end
        else
        begin
            Sell("LongLiq") next bar at longLiqPoint stop;
        end;
    end;

    if (MarketPosition = -1) then
    begin
        shortLiqPoint = EntryPrice + protStopPrcnt1 * averageRange;
        shortLiqPoint = MaxList(shortLiqPoint, EntryPrice + protStopAmt);

        if (MarketPosition(1) = 1 and BarsSinceEntry(0) = 1 and Low[1] <= longLiqPoint and longLiqPoint > longFBOPoint) then
            currTrdType = +2; {we just got long from a short liq reversal}

        if (currTrdType = +2) then
        begin
            shortLiqPoint = EntryPrice + protStopPrcnt2 * averageRange;
            shortLiqPoint = MaxList(shortLiqPoint, EntryPrice + protStopAmt);
        end;

        if (intraTradeLow <= EntryPrice - breakEvenPrcnt * averageRange) then
            shortLiqPoint = EntryPrice; {BreakEven trade}

        if (Time >= initTradesEndTime) then
            shortLiqPoint = MinList(shortLiqPoint, Highest(High, 3)); {Trailing stop}

        if (Time < liqRevEndTime and buysToday = 0 and shortLiqPoint <> EntryPrice and BarsSinceEntry ≥ 4) then
        begin
            Buy("ShortLiqRev") next bar at shortLiqPoint stop;
        end
        else
        begin
            BuyToCover("ShortLiq") next bar at shortLiqPoint stop;
        end;
    end;
end;

SetExitOnClose;
```

