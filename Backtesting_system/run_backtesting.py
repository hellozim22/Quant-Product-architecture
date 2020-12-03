from backtesting.cta_backtesting import BacktestingEngine
from strategies.bolling_strategy import BollingStrategy
import os
# 获取当前程序的地址
current_file = __file__
# 程序根目录地址
root_path = os.path.abspath(os.path.join(current_file, os.pardir, os.pardir))


engine = BacktestingEngine()
#设置回测参数
engine.set_parameters(
    symbol="ETHUSD",
    exchange="okex",
    interval="5m",
    start= "2019-01-01 00:00:00",
    end= "2020-01-01 00:00:00",
    rate=0.002,
    slippage=0,
    size=100/5,
    capital=10000,
    backtest_period = ["15T","30T","1H","2H","4H"]
)
path = root_path + '/backtesting/historical_data/okswap_eth_usd_td_5min_data1.csv'
#载入回测数据
engine.load_data(path = path)
#初始化回测参数
engine.init_backtesting()
#添加回测策略和参数
# engine.add_strategy(BollingStrategy,"15T",strategy_para=[400, 2.2, 10])
# engine.add_strategy(BollingStrategy,"30T",strategy_para=[400, 2.2, 10])
# engine.add_strategy(BollingStrategy,"1H",strategy_para=[400, 2.2, 10])
# engine.add_strategy(BollingStrategy,"2H",strategy_para=[400, 2.2, 10])
engine.add_strategy(BollingStrategy,"4H",strategy_para=[200, 2, 2])
#执行回测程序
engine.run_backtesting()
#计算每日收益
engine.calculate_result()
#计算策略统计数据
engine.calculate_statistics()
#展示并保存图形
engine.show_chart()
#输出交易明细
engine.output_trades()
#输出K线图
engine.show_bar_chart()






