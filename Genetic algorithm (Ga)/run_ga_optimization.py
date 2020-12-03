from backtesting.cta_backtesting import BacktestingEngine
from backtesting.optimization_setting import OptimizationSetting
from strategies.bolling_strategy import BollingStrategy
import csv
import os
import time

# 遗传算法库
from gaft import GAEngine
from gaft.components import BinaryIndividual
from gaft.components import Population
from gaft.operators import TournamentSelection
from gaft.operators import UniformCrossover
from gaft.operators import FlipBitBigMutation
from gaft.analysis.fitness_store import FitnessStore
from gaft.analysis.console_output import ConsoleOutput


class GaOptimizationEngine():
    """
        参数优化引擎
    """
    def __init__(self,
        target_name: str,
        strategy_class:str,
        symbol: str,
        exchange:str,
        interval: str,
        start: str,
        end: str,
        rate: float,
        slippage: float,
        size: float,
        capital: int,
        backtest_period:list,
    ):
        """
            设置参数优化引擎参数
        :param target_name:优化指标（total_return，max_drawdown，sharpe_ratio）
        :param strategy_class:策略类名
        :param symbol:交易对
        :param exchange:交易所
        :param interval:原始数据周期
        :param start:开始日期
        :param end:结束日期
        :param rate:手续费
        :param slippage:滑点
        :param size:每次下单量
        :param capital:初始资金量
        """
        self.target_name = target_name
        self.strategy_class = strategy_class
        self.symbol = symbol
        self.exchange = exchange
        self.start = start
        self.end = end
        #初始化回测引擎
        self.engine = BacktestingEngine()
        self.engine.set_parameters(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            start=start,
            end=end,
            rate=rate,
            slippage=slippage,
            size=size,
            capital=capital,
            backtest_period=backtest_period
        )
        #载入历史数据，并转换周期
        self.engine.load_data()

    def optimize(self,
        setting: list,
        backtest_period:str,
    ):
        """
            执行策略参数优化
        :param setting: 策略参数
        :param backtest_period: 策略周期
        :return:
        """
        self.engine.init_backtesting()
        self.engine.add_strategy(self.strategy_class,backtest_period,setting)
        self.engine.run_backtesting()
        self.engine.calculate_result()
        statistics = self.engine.calculate_statistics(output=False)
        target_value = statistics[self.target_name]
        return (backtest_period,str(setting), target_value, statistics)

    def output_results(self,results):
        """
            输出参数优化结果，按优化指标排序，并将各参数结果输出到CSV文件
        :param results: 回测结果列表
        :return:
        """
        result_values = [result.get() for result in results]
        result_values.sort(reverse=True, key=lambda result: result[2])

        if(os.path.exists("../results/{strategy}"
                                  .format(strategy=self.strategy_class.__name__)) is False):
            os.makedirs("../results/{strategy}"
                        .format(strategy=self.strategy_class.__name__))

        file_name = "../results/{strategy}/{exchange}_{symbol}_{start}_{end}.csv" \
            .format(strategy=self.strategy_class.__name__,
                    exchange=self.exchange,
                    symbol=self.symbol,
                    start=self.start.split(" ")[0].replace("-",""),
                    end=self.end.split(" ")[0].replace("-",""))
        out = open(file_name, 'a', newline='')
        csv_writer = csv.writer(out, dialect='excel')
        csv_writer.writerow(['周期', '参数', '起始资金', '结束资金', '总收益率', '年化收益', '最大回撤'
                                , '百分比最大回撤', '总交易日', '盈利交易日', '亏损交易日', '总盈亏'
                                , '收益标准差', 'Sharpe Ratio', '收益回撤比'
                                , '总手续费', '总滑点', '总成交金额', '总成交笔数', '日均盈亏', '日均手续费'
                                , '日均成交金额', '日均成交笔数', '日均收益率'
                             ])

        for value in result_values:
            if(value[2] != 0):
                data = [value[0], value[1], value[3]['capital'],
                        value[3]['end_balance'], value[3]['total_return'], value[3]['annual_return'],
                        value[3]['max_drawdown'], value[3]['max_ddpercent'], value[3]['total_days'],
                        value[3]['profit_days'], value[3]['loss_days'], value[3]['total_net_pnl'],
                        value[3]['return_std'], value[3]['sharpe_ratio'], value[3]['return_drawdown_ratio'],
                        value[3]['total_commission'], value[3]['total_slippage'], value[3]['total_turnover'],
                        value[3]['total_trade_count'], value[3]['daily_net_pnl'], value[3]['daily_commission'],
                        value[3]['daily_turnover'], value[3]['daily_trade_count'], value[3]['daily_return']]

                csv_writer.writerow(data)
                msg = f"周期：{value[0]}，参数：{value[1]}, 目标：{value[2]}"
                print(msg)


if __name__ == '__main__':
    start_time = time.time()
    #回测多少代，越多效果越好，计算时间越长
    generation_num = 100
    #回测交易对列表
    symbol_list = [["BTCUSDT",1,10000],
                   #["ETHUSDT",10,10000],
                   #["EOSUSDT",200,10000],
                   #["LTCUSDT",20,10000],
                   #["ETCUSDT",200,10000]
                   ]
    #回测周期列表
    period_list = ["15T","30T","60T"]
    #回测时间，用start_date和end_date之间的数据进行回测。
    #再选取回测结果最优的10条，再验证end_date和check_date之间的结果
    start_date = "2019-09-01 00:00:00"
    end_date = "2019-10-01 00:00:00"

    #逐个交易对进行参数优化
    for symbol in symbol_list:
        optimization_setting = OptimizationSetting()
        #设置回测周期，可设置多个周期
        optimization_setting.set_period(period_list)
        #设置参数优化目标，默认为按收益率
        optimization_setting.set_target(target_name="total_return")
        target_name = optimization_setting.target_name
        #设置各回测参数的范围和步长
        param1 = (10,80)
        param2 = (1,10)
        stop_lose_pct = (5,15)
        #生成回测参数范围
        para_range = [param1,param2,stop_lose_pct]

        for period in period_list:
            # 初始化参数优化引擎
            optimizatioin_engine = GaOptimizationEngine(
                target_name,
                BollingStrategy,
                symbol[0],
                "BINANCE",
                "1m",
                start_date,
                end_date,
                0.001,
                0,
                symbol[1],
                symbol[2],
                [period]
            )

            # Define population.
            indv_template = BinaryIndividual(ranges=para_range, eps=0.001)
            population = Population(indv_template=indv_template, size=50).init()

            # Create genetic operators.
            # selection = RouletteWheelSelection()
            selection = TournamentSelection()
            crossover = UniformCrossover(pc=0.8, pe=0.5)
            mutation = FlipBitBigMutation(pm=0.1, pbm=0.55, alpha=0.6)

            # Create genetic algorithm engine.
            # Here we pass all built-in analysis to engine constructor.
            engine = GAEngine(population=population, selection=selection,
                              crossover=crossover, mutation=mutation,
                              analysis=[ConsoleOutput, FitnessStore])


            # Define fitness function.
            @engine.fitness_register
            def fitness(indv):
                para = indv.solution
                result = optimizatioin_engine.optimize(para,period)
                if (result is None):
                    return 0.01
                else:
                    return float(result[2])

            engine.run(generation_num)

    end_time = time.time()

    print(f"总耗时：{int((end_time-start_time)/60)}分钟")

