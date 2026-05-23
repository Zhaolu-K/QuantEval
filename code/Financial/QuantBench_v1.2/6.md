我希望你作为一名使用VeighNa（vn.py）量化平台经验丰富的量化研究员，根据我描述的需求开发对应的程序代码。对于你开发的程序代码，都会提供对于程序逻辑的细节中文注释，代码中使用类型提示Type Hinting，同时代码内容需要符合PEP8代码标准要求。

使用VeighNa平台的CTA策略模板CtaTemplate（位于vnpy_ctastrategy.template子模块下），开发一套量化策略TurtleStrategy。

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

具体策略逻辑可以参考该网页上的内容：

```著名的商品投机家理查德·丹尼斯想弄清楚伟大的交易员是天生造就的还是后天培养的。为此，在1983年他招募了13个人，教授给他们期货交易的基本概念，以及他自己的交易方法和原则。

“学员们被称为‘海龟’（丹尼斯先生说这项计划开始时他刚刚从亚洲回来，他解释了自己向别人说过的话，‘我们正在成长为交易员，就象在新加坡他们正在成长为海龟一样’）。”—-斯坦利.W.安格瑞斯特，《华尔街期刊》，1989年9月5日。

海龟成为交易史上最著名的实验，因为在随后的四年中海龟们取得了年均复利80%的收益。

丹尼斯证明用一套简单的系统和法则，可以使仅有很少或根本没有交易经验的人成为优秀的交易员。

当时，海龟们认为应对理查德·丹尼斯负责，商定甚至在他们议定的10年保密协定于1993年终止后也不泄露这些法则。但是，有个别海龟在网站上出售海龟交易法则而谋取钱财。两个原版海龟科蒂斯·费思和阿瑟·马多克，为了阻止个别海龟对知识产权的偷窃和出售海龟交易法则而赚钱的行为，决定在网站上将海龟交易法则免费公之于众。

我们现在能看到的海龟交易法则，既是由此所得。

这就是海龟交易法则的由来——稍微有点曲折。

大多数成功的交易员都使用机械交易系统。这并非偶然。

一个良好的机械交易系统可以自动运行整个交易程序。对于交易员在交易中必须制定的每项决策，系统都会给出答案。该系统使交易员更容易进行一致性的交易，因为有一套明确说明应该做什么的法则。交易的机械化就是不留给交易员自己进行判断。

自信、一致性以及由彻底检测过的机械交易系统所保证的纪律，是大多数能够赢利的交易员成功的关键。

海龟交易系统是一个完整的交易系统。其法则覆盖了交易的各个方面，并且不给交易员留下一点主观想象决策的余地。它具备一个完整的交易系统的所有成分。

一个完整的交易系统包含了成功的交易所需的每项决策：

·市场—-买卖什么

·头寸规模—-买卖多少

·入市—-何时买卖

·止损—-何时退出亏损的头寸

·离市—-何时退出赢利的头寸

·策略—-如何买卖

·市场—-买卖什么

海龟交易的是在美国芝加哥和纽约交易所交易的具有流动性的期货。

流动性海龟们用于确定能够参与交易的期货品种的主要标准就是构成市场基础的流动性。

一般，海龟在除谷物和肉类以外美国所有具有流动性的市场进行交易。

·头寸规模—-买卖多少

买卖多少既影响多样化，又影响资金管理。

多样化就是努力在诸多投资工具上分散风险，并且通过增加抓住成功交易的机会而增加赢利的机会。正确的多样化要求在多种不同的投资工具上进行类似的（如果不是同样的话）下注。（概率问题：顺势组合比单一品种容易分散风险提高成功率。）

大多数交易新手在单项交易中冒太大的风险，即使他们拥有其他方面有效的交易风格，这也大大增加了他们破产的机会。

·入市—-何时买卖

海龟用两个相关的系统入市，这两个系统都以唐奇安的通道突破系统（Donchian’schannelbreakoutsystem）为基础。突破，定义为价格超过特定天数内的最高价或最低价。

系统一—-以20日突破为基础的偏短线系统（价格超过前20天的最高价或最低价）

系统二—-以50日突破为基础的较简单的长线系统（价格超过前50天的最高价或最低价）

·止损—-何时退出亏损的头寸

长期来看，不会止住亏损的交易员不会取得成功。

关于止损，最重要的是在你建立头寸之前，你已经预先确定退出的点位。如果市场的波动触及你的价位，你就必须每一次都毫无例外地退出。在这一立场上摇摆不定最终会导致灾难。

海龟以头寸风险为基础设置止损。任何一笔交易都不能出现2%以上的风险。

·离市—-何时退出赢利的头寸

海龟的离市：

系统一离市对于多头头寸为10日最低价，对于空头头寸为10日最高价。如果价格波动与头寸背离至10日突破，头寸中的所有单位都会退出。

系统二离市对于多头头寸为20日最低价，对于空头头寸为20日最高价。如果价格波动与头寸背离至20日突破，头寸中的所有单位都会退出。

海龟在入市时一般不会设置离市止损指令，但会在日间盯着价格，一旦交易价格穿过离市突破价，就开始打电话下离市指令。

何时退出赢利头寸的问题对于系统的收益性是至关重要的。任何不说明赢利头寸的离市的交易系统都不是一个完整的交易系统。

有一个古老的说法：“落袋为安，你永远不会破产。”海龟不会同意这种说法。过早地退出赢利头寸，即过早地“落袋为安”，是采用趋势跟随系统交易时最为常见的错误之一。

价格从来不会直来直去；因此，如果你想赶上一段趋势就有必要让价格背离你运动。在趋势的早期，这通常可能意味着眼看着10%到30%可观的利润逐渐成为小幅亏损。在趋势的中期，这可能意味着眼看着80%到100%的利润下降30%到40%。减轻仓位“锁定利润”的诱惑可能会非常巨大。

对于大多数的交易员，海龟系统离市或许是海龟系统法则中唯一最难的部分。等待10日或20日新低出现通常可能意味着眼睁睁地瞅着20%、40%甚至100%的可观利润化为泡影。

人们具有一种想要早点离市的强烈倾向。你需要极强的纪律性才能为了继续持有头寸直到真正的大幅波动到来而眼看着你的利润化为泡影。在大幅赢利的交易中，遵守纪律和坚持原则的能力是成功老道的交易员的特征。

·策略—-如何买卖

入市指令：

理查德.丹尼斯和威廉姆斯.埃克哈特建议海龟在下指令时不要使用止损。他们建议我们观察市场，并且在价格触及止损价位时下指令。（盘中止损而非收盘价定止损）

我们还被告知，一般比较好的做法是设置限价指令而不是市价指令。

买强卖弱：

如果信号突然出现，我们总是在最强的市场买入，在最弱的市场成批地卖空。

同时，我们也会只在一个市场上建立一个单位的头寸。例如，我们会挑选最强的具有足够的成交量和流动性的合约月份，而不是同时买入二月份、三月份和四月份的原油。

这是非常重要的！在相关的一组中，最佳的多头头寸是最强的市场（该市场在同一组中几乎总是要胜过较弱的市场）。相反，空头方面最大的赢利交易来自于相关一组中最弱的市场。

重要的是持有在最强的市场（或合约）上多头头寸，在最弱的市场（或合约）上持有空头头寸。

知道这些法则并不足以使你致富。你必须能遵循这些法则。

记住理查德.丹尼斯说过的话：“我总是说你们可以在报纸上发表我的交易法则，没有人会遵循它们。关键在于连续性和纪律。几乎任何人都能够罗列一张交易法则的清单，其中的80%与我们教授给我们的学员的一样。他们所不能做的是带给他们自信，甚至在情况恶化时仍坚持那些法则。”—-摘自《华尔街点金人》，约翰.施瓦格。

遵循海龟法则是非常困难的，因为海龟法则依赖于捕捉相对罕见的大级别趋势。结果是，两次赢利之间可能会经过许多个月份，有时甚至要经过一两年。在这期间，很容易找到理由来怀疑这套系统，进而停止遵循法则。

学会成为好的交易员（甚至出色的交易员）是有可能的，但是，你需要付出大量艰苦的工作并具有一种健康的怀疑主义精神。对于我们这些选择了这条道路的人，这段旅程永远没有尽头。那些继续保持成功的人将永远不会达到目的地，但是，他们将在旅程中学会找到乐趣。
```