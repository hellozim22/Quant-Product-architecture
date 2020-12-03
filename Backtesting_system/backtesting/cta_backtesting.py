from datetime import datetime
from collections import defaultdict
import pandas as pd
import numpy as np
import csv
import os
import time
from pandas import DataFrame
from backtesting.constants import Direction, Offset
from backtesting.object import TradeData
import matplotlib.pyplot as plt
import mpl_finance as mpf
import matplotlib.dates as mdates
from matplotlib.pylab import date2num
from util.Functions import transfer_to_period_data
from backtesting.daily_result import DailyResult


class BacktestingEngine:
    """
        基于VNPY回测引擎修改
    """
    def __init__(self):
        self.symbol = ""
        self.exchange = None
        self.interval = None
        self.start = None
        self.end = None
        self.rate = 0
        self.slippage = 0
        self.size = 1
        self.capital = 10000
        self.backtest_period = []
        self.strategy_list = []

        self.strategy = None
        self.strategy_class = None
        self.strategy_para = []

        self.history_data = None
        self.backtest_data = {}

        self.days = 0
        self.pre_pos = 0
        self.trade_count = 0
        self.trades = {}
        self.daily_results = {}
        self.daily_df = None
        self.total_results = []

    def set_parameters(
        self,
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
            设置回测引擎参数
        :param symbol: 交易对
        :param exchange: 交易所
        :param interval: 数据周期
        :param start: 开始日期
        :param end: 结束日期
        :param rate: 手续费率
        :param slippage: 滑点
        :param size: 每次下单数量
        :param capital: 初始资金
        :param backtest_period: 回测周期列表["5T","15T","30T"....]
        :return:
        """
        self.symbol = symbol
        self.interval = interval
        self.rate = rate
        self.slippage = slippage
        self.size = size
        self.start = start
        self.end = end
        self.exchange = exchange
        self.capital = capital
        self.backtest_period = backtest_period


    def add_strategy(self, strategy_class: type,period:str,strategy_para=[]):
        """
            添加回测策略
        :param strategy_class: 策略的类名
        :param period: 回测周期
        :param strategy_para: 回测参数
        :return:
        """
        self.strategy_class = strategy_class
        self.strategy_para = strategy_para
        self.strategy = strategy_class()
        self.period = period
        self.strategy_list.append({
            'strategy_class':strategy_class,
            'strategy_para':strategy_para,
            'strategy':strategy_class(),
            'period':period
        })

    def load_data(self, path = ""):
        """
            加载本地的CSV数据，并且根据回测周期，生成各周期的数据
        :return:
        """
        if not self.end:
            self.end = datetime.now()

        if self.start >= self.end:
            return
        if len(path) == 0:
            path = '../historical_data/{exchange}_{symbol}_{period}.csv'\
                .format(exchange=self.exchange,symbol=self.symbol,period=self.interval)
        # 读取全量数据
        all_data = pd.read_csv(path, parse_dates=['candle_begin_time'])
        # 选取时间段
        all_data = all_data[all_data['candle_begin_time'] >= pd.to_datetime(self.start)]
        all_data = all_data[all_data['candle_begin_time'] <= pd.to_datetime(self.end)]
        all_data.reset_index(inplace=True, drop=True)
        self.history_data = all_data
        print(f"历史数据加载完成，数据量：{len(self.history_data)}")

        for period in self.backtest_period:
            datas = transfer_to_period_data(self.history_data.copy(), period)
            self.backtest_data[period] = datas
            #print(f"{period}周期历史数据转换完成，数据量：{len(datas)}")

    def init_backtesting(self):
        """
            初始化清零回测参数
        :return:
        """
        self.strategy_para = []
        self.days = 0
        self.pre_pos = 0
        self.trade_count = 0
        self.trades = {}
        self.daily_results = {}
        self.daily_df = None
        self.period = ""


    def run_backtesting(self):
        """
            执行回测程序，先调用策略的信号接口生成交易信号，再根据交易信号生成成交明细
        :return:
        """
        try:
            for strategy_item in self.strategy_list:
                strategy = strategy_item['strategy']
                strategy_para = strategy_item['strategy_para']
                period = strategy_item['period']

                df = strategy.signal(self.backtest_data[period].copy(),strategy_para)
                print(f"**********开始回测{self.symbol}：回测周期{period},回测参数{strategy_para}***********")
                #逐笔回放每一条K线数据
                for index, data_row in df.iterrows():
                    signal = data_row['signal']
                    price = data_row['close']
                    trade_time = datetime.strptime(str(data_row['candle_begin_time']), '%Y-%m-%d %H:%M:%S')
                    #更新每日收盘价
                    self.update_daily_close(trade_time,price)
                    #如果有交易信号，则生成交易明细
                    if(pd.isna(signal) is False):
                        #print(trade_time,signal,self.pre_pos)
                        if(signal >=0 and self.pre_pos >= 0):
                            diff_pos = signal - self.pre_pos
                            if(diff_pos >0):
                                self.trade_count += 1
                                self.trades["TRADE_NO_" + str(self.trade_count)] = TradeData(
                                    self.symbol,Direction.LONG,Offset.OPEN,price,abs(diff_pos),trade_time)
                            else:
                                self.trade_count += 1
                                self.trades["TRADE_NO_" + str(self.trade_count)] = TradeData(
                                    self.symbol, Direction.SHORT, Offset.CLOSE, price, abs(diff_pos), trade_time)
                        elif(signal <=0 and self.pre_pos <= 0):
                            diff_pos = signal - self.pre_pos
                            if(diff_pos <0):
                                self.trade_count += 1
                                self.trades["TRADE_NO_" + str(self.trade_count)] = TradeData(
                                    self.symbol, Direction.SHORT, Offset.OPEN, price, abs(diff_pos), trade_time)
                            else:
                                self.trade_count += 1
                                self.trades["TRADE_NO_" + str(self.trade_count)] = TradeData(
                                    self.symbol, Direction.LONG, Offset.CLOSE, price, abs(diff_pos), trade_time)
                        elif ((signal <= 0 and self.pre_pos >= 0) or
                                (signal >= 0 and self.pre_pos <= 0)):
                            if(signal >0):
                                self.trade_count += 1
                                self.trades["TRADE_NO_" + str(self.trade_count)] = TradeData(
                                    self.symbol, Direction.LONG, Offset.CLOSE, price, abs(self.pre_pos), trade_time)
                                self.trade_count += 1
                                self.trades["TRADE_NO_" + str(self.trade_count)] = TradeData(
                                    self.symbol, Direction.LONG, Offset.OPEN, price, abs(signal), trade_time)
                            else:
                                self.trade_count += 1
                                self.trades["TRADE_NO_" + str(self.trade_count)] = TradeData(
                                    self.symbol, Direction.SHORT, Offset.CLOSE, price, abs(self.pre_pos), trade_time)
                                self.trade_count += 1
                                self.trades["TRADE_NO_" + str(self.trade_count)] = TradeData(
                                    self.symbol, Direction.SHORT, Offset.OPEN, price, abs(signal), trade_time)
                        self.pre_pos = signal
        except Exception as e:
            print(f"回测出错：周期{self.period},回测参数{strategy_para}",e)

    def calculate_result(self):
        """
            根据交易明细记录，计算逐日盈亏
        :return:
        """
        if not self.trades:
            return

        #将交易记录加入每日交易记录的列表
        for trade in self.trades.values():
            d = trade.time.date()
            daily_result = self.daily_results[d]
            daily_result.add_trade(trade)

        #计算每日的交易盈亏
        pre_close = 0
        start_pos = 0

        for daily_result in self.daily_results.values():
            daily_result.calculate_pnl(
                pre_close, start_pos, self.size, self.rate, self.slippage
            )

            pre_close = daily_result.close_price
            start_pos = daily_result.end_pos

        results = defaultdict(list)

        for daily_result in self.daily_results.values():
            for key, value in daily_result.__dict__.items():
                results[key].append(value)

        self.daily_df = DataFrame.from_dict(results).set_index("date")

        return self.daily_df


    def calculate_statistics(self, df: DataFrame = None, output=True):
        """
            计算策略的各项统计指标
        :param df:
        :param output:
        :return:
        """

        if df is None:
            df = self.daily_df

        if df is None:
            start_date = ""
            end_date = ""
            total_days = 0
            profit_days = 0
            loss_days = 0
            end_balance = 0
            max_drawdown = 0
            max_ddpercent = 0
            total_net_pnl = 0
            daily_net_pnl = 0
            total_commission = 0
            daily_commission = 0
            total_slippage = 0
            daily_slippage = 0
            total_turnover = 0
            daily_turnover = 0
            total_trade_count = 0
            daily_trade_count = 0
            total_return = 0
            annual_return = 0
            daily_return = 0
            return_std = 0
            sharpe_ratio = 0
            return_drawdown_ratio = 0
        else:
            try:
                df["balance"] = df["net_pnl"].cumsum() + self.capital
                df["return"] = np.log(df["balance"] / df["balance"].shift(1)).fillna(0)
                df["highlevel"] = (
                    df["balance"].rolling(
                        min_periods=1, window=len(df), center=False).max()
                )
                df["drawdown"] = df["balance"] - df["highlevel"]
                df["ddpercent"] = df["drawdown"] / df["highlevel"] * 100

                start_date = df.index[0]
                end_date = df.index[-1]

                total_days = len(df)
                profit_days = len(df[df["net_pnl"] > 0])
                loss_days = len(df[df["net_pnl"] < 0])

                end_balance = df["balance"].iloc[-1]
                max_drawdown = df["drawdown"].min()
                max_ddpercent = df["ddpercent"].min()

                total_net_pnl = df["net_pnl"].sum()
                daily_net_pnl = total_net_pnl / total_days

                total_commission = df["commission"].sum()
                daily_commission = total_commission / total_days

                total_slippage = df["slippage"].sum()
                daily_slippage = total_slippage / total_days

                total_turnover = df["turnover"].sum()
                daily_turnover = total_turnover / total_days

                total_trade_count = df["trade_count"].sum()
                daily_trade_count = total_trade_count / total_days

                total_return = (end_balance / self.capital - 1) * 100
                annual_return = total_return / total_days * 365
                daily_return = df["return"].mean() * 100
                return_std = df["return"].std() * 100

                if return_std:
                    sharpe_ratio = daily_return / return_std * np.sqrt(365)
                else:
                    sharpe_ratio = 0

                return_drawdown_ratio = -total_return / max_ddpercent
            except Exception as e:
                pass

        if output:
            print("-" * 30)
            print(f"首个交易日：\t{start_date}")
            print(f"最后交易日：\t{end_date}")

            print(f"总交易日：\t{total_days}")
            print(f"盈利交易日：\t{profit_days}")
            print(f"亏损交易日：\t{loss_days}")

            print(f"起始资金：\t{self.capital:,.2f}")
            print(f"结束资金：\t{end_balance:,.2f}")

            print(f"总收益率：\t{total_return:,.2f}%")
            print(f"年化收益：\t{annual_return:,.2f}%")
            print(f"最大回撤: \t{max_drawdown:,.2f}")
            print(f"百分比最大回撤: {max_ddpercent:,.2f}%")

            print(f"总盈亏：\t{total_net_pnl:,.2f}")
            print(f"总手续费：\t{total_commission:,.2f}")
            print(f"总滑点：\t{total_slippage:,.2f}")
            print(f"总成交金额：\t{total_turnover:,.2f}")
            print(f"总成交笔数：\t{total_trade_count}")

            print(f"日均盈亏：\t{daily_net_pnl:,.2f}")
            print(f"日均手续费：\t{daily_commission:,.2f}")
            print(f"日均滑点：\t{daily_slippage:,.2f}")
            print(f"日均成交金额：\t{daily_turnover:,.2f}")
            print(f"日均成交笔数：\t{daily_trade_count}")

            print(f"日均收益率：\t{daily_return:,.2f}%")
            print(f"收益标准差：\t{return_std:,.2f}%")
            print(f"Sharpe Ratio：\t{sharpe_ratio:,.2f}")
            print(f"收益回撤比：\t{return_drawdown_ratio:,.2f}")

        statistics = {
            "period":self.period,
            "strategy_parameters":self.strategy_para,
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "profit_days": profit_days,
            "loss_days": loss_days,
            "capital": self.capital,
            "end_balance": end_balance,
            "max_drawdown": max_drawdown,
            "max_ddpercent": max_ddpercent,
            "total_net_pnl": total_net_pnl,
            "daily_net_pnl": daily_net_pnl,
            "total_commission": total_commission,
            "daily_commission": daily_commission,
            "total_slippage": total_slippage,
            "daily_slippage": daily_slippage,
            "total_turnover": total_turnover,
            "daily_turnover": daily_turnover,
            "total_trade_count": total_trade_count,
            "daily_trade_count": daily_trade_count,
            "total_return": total_return,
            "annual_return": annual_return,
            "daily_return": daily_return,
            "return_std": return_std,
            "sharpe_ratio": sharpe_ratio,
            "return_drawdown_ratio": return_drawdown_ratio,
        }
        self.total_results.append(statistics)
        return statistics


    def update_daily_close(self,date_time, price: float):
        """
            更新每日收盘价
        :param date_time:
        :param price:
        :return:
        """
        d = date_time.date()

        daily_result = self.daily_results.get(d, None)
        if daily_result:
            daily_result.close_price = price
        else:
            self.daily_results[d] = DailyResult(d, price)


    def show_chart(self,df: DataFrame = None):
        """
            展现图表
        :param df:
        :return:
        """
        if df is None:
            df = self.daily_df

        if df is None:
            return

        plt.figure(figsize=(10, 16))
        plt.rcParams["savefig.dpi"] = 300
        plt.rcParams["figure.dpi"] = 300
        balance_plot = plt.subplot(4, 1, 1)
        balance_plot.set_title("Balance")
        df["balance"].plot(legend=True)

        drawdown_plot = plt.subplot(4, 1, 2)
        drawdown_plot.set_title("Drawdown")
        drawdown_plot.fill_between(range(len(df)), df["drawdown"].values)

        pnl_plot = plt.subplot(4, 1, 3)
        pnl_plot.set_title("Daily Pnl")
        df["net_pnl"].plot(kind="bar", legend=False, grid=False, xticks=[])

        distribution_plot = plt.subplot(4, 1, 4)
        distribution_plot.set_title("Daily Pnl Distribution")
        df["net_pnl"].hist(bins=50)

        # 保存回测图形
        root_path = os.path.abspath('.')
        if (os.path.exists(root_path + "/details/{strategy}"
                .format(strategy=self.strategy_class.__name__)) is False):
            os.makedirs(root_path + "/details/{strategy}"
                        .format(strategy=self.strategy_class.__name__))

        file_name = root_path + "/details/{strategy}/{exchange}_{symbol}_{start}_{end}_{period}_{para}.png" \
            .format(strategy=self.strategy_class.__name__,
                    exchange=self.exchange,
                    symbol=self.symbol,
                    start=self.start.split(" ")[0].replace("-", ""),
                    end=self.end.split(" ")[0].replace("-", ""),
                    period=self.period,
                    para=self.strategy_para
                    )
        plt.savefig(file_name)

        plt.show()


    def output_trades(self):
        """
            记录每笔交易明细到CSV
        :return:
        """
        root_path = os.path.abspath('.')
        if (os.path.exists(root_path + "/details/{strategy}"
                .format(strategy=self.strategy_class.__name__)) is False):
            os.makedirs(root_path + "/details/{strategy}"
                        .format(strategy=self.strategy_class.__name__))

        file_name = root_path + "/details/{strategy}/{exchange}_{symbol}_{start}_{end}_{period}_{para}_trades.csv"\
            .format(strategy=self.strategy_class.__name__,
                    exchange=self.exchange,
                    symbol=self.symbol,
                    start=self.start.split(" ")[0].replace("-",""),
                    end=self.end.split(" ")[0].replace("-",""),
                    period=self.period,
                    para=self.strategy_para
                    )
        out = open(file_name, 'w', newline='')
        csv_writer = csv.writer(out, dialect='excel')
        csv_writer.writerow(['交易时间', '买卖方向', '开平仓', '交易价格', '交易数量'])
        count = 0
        for trade in self.trades.values():
            data = [trade.time,trade.direction.value,trade.offset.value,trade.price,trade.volume]
            csv_writer.writerow(data)
            count = count + trade.price*trade.volume
        print("交易明细保存完成")


    def show_bar_chart(self):
        df = self.backtest_data[self.period].copy()
        bar_datas = []
        # 逐笔回放每一条K线数据
        for index in range(0, df.shape[0]):
            bar_time = date2num(datetime.strptime(str(df.iloc[index]['candle_begin_time']), '%Y-%m-%d %H:%M:%S'))
            open = float(df.iloc[index]['open'])
            high = float(df.iloc[index]['high'])
            low = float(df.iloc[index]['low'])
            close = float(df.iloc[index]['close'])
            data = (bar_time,open,high,low,close)
            bar_datas.append(data)

        plt.figure(figsize=(20, 12))
        plt.rcParams["savefig.dpi"] = 300
        plt.rcParams["figure.dpi"]=300
        fig, ax = plt.subplots(facecolor=("white"))
        fig.subplots_adjust(bottom=0.1)
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
        ax.autoscale_view()
        plt.xticks(rotation=45)
        plt.title(self.symbol)
        plt.xlabel("time")
        plt.ylabel("price")
        mpf.candlestick_ohlc(ax,bar_datas,width=0.001,colorup="r",colordown="green",alpha=1)
        plt.subplots_adjust(left=0.1, right=0.9, top=0.859, bottom=0.15)
        plt.grid(True)


        # 保存回测图形
        root_path = os.path.abspath('.')
        if (os.path.exists(root_path + "/details/{strategy}"
                .format(strategy=self.strategy_class.__name__)) is False):
            os.makedirs(root_path + "/details/{strategy}"
                        .format(strategy=self.strategy_class.__name__))

        file_name = root_path + "/details/{strategy}/{exchange}_{symbol}_{start}_{end}_{period}_{para}_bar.png" \
            .format(strategy=self.strategy_class.__name__,
                    exchange=self.exchange,
                    symbol=self.symbol,
                    start=self.start.split(" ")[0].replace("-", ""),
                    end=self.end.split(" ")[0].replace("-", ""),
                    period=self.period,
                    para=self.strategy_para
                    )
        plt.savefig(file_name)

        #plt.show()
