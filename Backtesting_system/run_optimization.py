from backtesting.cta_backtesting import BacktestingEngine
from backtesting.optimization_setting import OptimizationSetting
from strategies.bolling_strategy import BollingStrategy
import multiprocessing
import csv
import os
import time
import json

class OptimizationEngine():
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
    end_date = "2019-09-20 00:00:00"
    check_date = "2019-10-01 00:00:00"
    check = True
    check_num = 30

    #逐个交易对进行参数优化
    for symbol in symbol_list:
        try:
            optimization_setting = OptimizationSetting()
            #设置回测周期，可设置多个周期
            optimization_setting.set_period(period_list)
            #设置参数优化目标，默认为按收益率
            optimization_setting.set_target(target_name="total_return")
            #设置各回测参数的范围和步长
            optimization_setting.add_parameter(name="n", start=50, end=500, step=10)
            optimization_setting.add_parameter(name="m", start=1, end=10, step=1)
            optimization_setting.add_parameter(name="stop_lose_pct", start=5, end=15, step=5)
            #生成回测参数列表
            settings = optimization_setting.generate_setting()
            target_name = optimization_setting.target_name

            #新建进程池
            pool = multiprocessing.Pool(multiprocessing.cpu_count()-2)
            total_num = len(settings)*len(period_list)
            print(f"{symbol}开始回测参数优化，参数组合{total_num}种")
            #初始化参数优化引擎
            optimization_engine = OptimizationEngine(
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
                            period_list
                        )
            results = []
            # 将回测参数逐个加入进程池，利用多进程进行回测
            for period in period_list:
                for setting in settings:
                    try:
                        result = (pool.apply_async(optimization_engine.optimize, (
                            setting,period
                        )))
                        results.append(result)
                    except Exception as e:
                        print(setting,e)


            #输出回测结果
            optimization_engine.output_results(results)

            #开始回测参数验证
            if check:
                print(f"{symbol[0]}开始回测验证")
                # 初始化验证引擎
                check_results = []
                check_engine = OptimizationEngine(
                    target_name,
                    BollingStrategy,
                    symbol[0],
                    "BINANCE",
                    "1m",
                    end_date,
                    check_date,
                    0.001,
                    0,
                    symbol[1],
                    symbol[2],
                    period_list
                )
                # 按优化结果排序
                result_values = [result.get() for result in results]
                result_values.sort(reverse=True, key=lambda result: result[2])
                num = 0
                for value in result_values:
                    if(value[2] !=0):
                        num += 1
                        if(num>check_num):
                            break
                        check_result = (pool.apply_async(check_engine.optimize, (
                            json.loads(value[1]), value[0])))
                        check_results.append(check_result)

                # 输出验证结果
                check_engine.output_results(check_results)
                pool.close()
                pool.join()

        except Exception as e:
            print(symbol,e)
    end_time = time.time()

    print(f"总耗时：{int((end_time-start_time)/60)}分钟")

