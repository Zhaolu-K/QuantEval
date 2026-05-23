
from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)


class DualThrustStrategy(CtaTemplate):
    """
    Dual Thrust策略是一种趋势跟踪系统，属于日内交易策略。
    该策略由Michael Chalek 在20世纪80年代开发，曾被Future Thruth杂志评为最赚钱的策略之一。
    """

    author = "用Python的交易员"

    # 策略参数
    n_days: int = 5  # N日周期
    k1: float = 0.5  # 上轨系数
    k2: float = 0.5  # 下轨系数

    # 策略变量
    buy_line: float = 0.0  # 上轨
    sell_line: float = 0.0  # 下轨
    range_value: float = 0.0  # 震荡区间大小

    parameters = ["n_days", "k1", "k2"]
    variables = ["buy_line", "sell_line", "range_value"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """
        初始化策略。
        """
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)  # 用于生成分钟K线
        self.am = ArrayManager()  # 用于计算技术指标

    def on_init(self):
        """
        策略初始化回调函数。
        """
        self.write_log("策略初始化")
        self.load_bar(self.n_days)  # 加载历史数据

    def on_start(self):
        """
        策略启动回调函数。
        """
        self.write_log("策略启动")
        self.put_event()

    def on_stop(self):
        """
        策略停止回调函数。
        """
        self.write_log("策略停止")
        self.put_event()

    def on_tick(self, tick: TickData):
        """
        新Tick数据回调函数。
        """
        self.bg.update_tick(tick)  # 将Tick数据更新到BarGenerator

    def on_bar(self, bar: BarData):
        """
        新Bar数据回调函数。
        """
        self.cancel_all()  # 撤销所有未成交订单

        am = self.am
        am.update_bar(bar)  # 更新Bar数据到ArrayManager
        if not am.inited:
            return

        # 计算N日High的最高价HH, N日Close的最低价LC
        # N日Close的最高价HC，N日Low的最低价LL
        HH = am.high[-self.n_days:].max()
        LC = am.close[-self.n_days:].min()
        HC = am.close[-self.n_days:].max()
        LL = am.low[-self.n_days:].min()

        # 计算震荡区间大小
        self.range_value = max(HH - LC, HC - LL)

        # 计算上轨和下轨
        self.buy_line = bar.open_price + self.k1 * self.range_value
        self.sell_line = bar.open_price - self.k2 * self.range_value

        # 交易逻辑
        if bar.close_price > self.buy_line:  # 价格突破上轨
            if self.pos < 0:  # 如果持有空仓
                self.cover(bar.close_price, 1)  # 先平空仓
            if self.pos == 0:  # 如果没有仓位
                self.buy(bar.close_price, 1)  # 开多仓

        elif bar.close_price < self.sell_line:  # 价格突破下轨
            if self.pos > 0:  # 如果持有多仓
                self.sell(bar.close_price, 1)  # 先平多仓
            if self.pos == 0:  # 如果没有仓位
                self.short(bar.close_price, 1)  # 开空仓

        self.put_event()  # 更新策略状态

    def on_order(self, order: OrderData):
        """
        订单状态更新回调函数。
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        成交状态更新回调函数。
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        停止单状态更新回调函数。
        """
        pass