import pandas as pd
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 10000)

class BollingStrategy():
    def signal(self,df, para=[100, 2, 5]):
        """
        布林线中轨：n天收盘价的移动平均线
        布林线上轨：n天收盘价的移动平均线 + m * n天收盘价的标准差
        布林线上轨：n天收盘价的移动平均线 - m * n天收盘价的标准差
        当收盘价由下向上穿过上轨的时候，做多；然后由上向下穿过下轨的时候，平仓。
        当收盘价由上向下穿过下轨的时候，做空；然后由下向上穿过上轨的时候，平仓。
        另外，当价格往亏损方向超过百分之stop_lose的时候，平仓止损。
        N：50-500
        M:1-10
        止损比例：5-15%
        """
        # ===计算指标
        n = int(para[0])
        m = int(para[1])
        stop_loss_pct = int(para[2])

        # 计算均线
        df['median'] = df['close'].rolling(n, min_periods=1).mean()

        # 计算上轨、下轨道
        df['std'] = df['close'].rolling(n, min_periods=1).std(ddof=0)  # ddof代表标准差自由度
        df['upper'] = df['median'] + m * df['std']
        df['lower'] = df['median'] - m * df['std']

        # ===找出做多信号
        condition1 = df['close'] > df['upper']  # 当前K线的收盘价 > 上轨
        condition2 = df['close'].shift(1) <= df['upper'].shift(1)  # 之前K线的收盘价 <= 上轨
        df.loc[condition1 & condition2, 'signal_long'] = 1  # 将产生做多信号的那根K线的signal设置为1，1代表做多

        # ===找出做多平仓信号
        condition1 = df['close'] < df['median']  # 当前K线的收盘价 < 中轨
        condition2 = df['close'].shift(1) >= df['median'].shift(1)  # 之前K线的收盘价 >= 中轨
        df.loc[condition1 & condition2, 'signal_long'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

        # ===找出做空信号
        condition1 = df['close'] < df['lower']  # 当前K线的收盘价 < 下轨
        condition2 = df['close'].shift(1) >= df['lower'].shift(1)  # 之前K线的收盘价 >= 下轨
        df.loc[condition1 & condition2, 'signal_short'] = -1  # 将产生做空信号的那根K线的signal设置为-1，-1代表做空

        # ===找出做空平仓信号
        condition1 = df['close'] > df['median']  # 当前K线的收盘价 > 中轨
        condition2 = df['close'].shift(1) <= df['median'].shift(1)  # 之前K线的收盘价 <= 中轨
        df.loc[condition1 & condition2, 'signal_short'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓
        # ===考察是否需要止盈止损
        info_dict = {'pre_signal': 0, 'stop_lose_price': None}  # 用于记录之前交易信号，以及止损价格
        # 逐行遍历df，考察每一行的交易信号
        for i in range(df.shape[0]):
            # 如果之前是空仓
            if info_dict['pre_signal'] == 0:
                # 当本周期有做多信号
                if df.at[i, 'signal_long'] == 1:
                    df.at[i, 'signal'] = 1  # 将真实信号设置为1
                    # 记录当前状态
                    pre_signal = 1  # 信号
                    stop_lose_price = df.at[i, 'close'] * (
                                1 - stop_loss_pct / 100)  # 以本周期的收盘价乘以一定比例作为止损价格。也可以用下周期的开盘价df.at[i+1, 'open']，但是此时需要注意i等于最后一个i时，取i+1会报错
                    info_dict = {'pre_signal': pre_signal, 'stop_lose_price': stop_lose_price}
                # 当本周期有做空信号
                elif df.at[i, 'signal_short'] == -1:
                    df.at[i, 'signal'] = -1  # 将真实信号设置为-1
                    # 记录相关信息
                    pre_signal = -1  # 信号
                    stop_lose_price = df.at[i, 'close'] * (
                                1 + stop_loss_pct / 100)  # 以本周期的收盘价乘以一定比例作为止损价格，也可以用下周期的开盘价df.at[i+1, 'open']
                    info_dict = {'pre_signal': pre_signal, 'stop_lose_price': stop_lose_price}
                # 无信号
                else:
                    # 记录相关信息
                    info_dict = {'pre_signal': 0, 'stop_lose_price': None}

            # 如果之前是多头仓位
            elif info_dict['pre_signal'] == 1:
                # 当本周期有平多仓信号，或者需要止损
                if (df.at[i, 'signal_long'] == 0) or (df.at[i, 'close'] < info_dict['stop_lose_price']):
                    df.at[i, 'signal'] = 0  # 将真实信号设置为0
                    # 记录相关信息
                    info_dict = {'pre_signal': 0, 'stop_lose_price': None}

                # 当本周期有平多仓并且还要开空仓
                if df.at[i, 'signal_short'] == -1:
                    df.at[i, 'signal'] = -1  # 将真实信号设置为-1
                    # 记录相关信息
                    pre_signal = -1  # 信号
                    stop_lose_price = df.at[i, 'close'] * (
                                1 + stop_loss_pct / 100)  # 以本周期的收盘价乘以一定比例作为止损价格，也可以用下周期的开盘价df.at[i+1, 'open']
                    info_dict = {'pre_signal': pre_signal, 'stop_lose_price': stop_lose_price}

            # 如果之前是空头仓位
            elif info_dict['pre_signal'] == -1:
                # 当本周期有平空仓信号，或者需要止损
                if (df.at[i, 'signal_short'] == 0) or (df.at[i, 'close'] > info_dict['stop_lose_price']):
                    df.at[i, 'signal'] = 0  # 将真实信号设置为0
                    # 记录相关信息
                    info_dict = {'pre_signal': 0, 'stop_lose_price': None}

                # 当本周期有平空仓并且还要开多仓
                if df.at[i, 'signal_long'] == 1:
                    df.at[i, 'signal'] = 1  # 将真实信号设置为1
                    # 记录相关信息
                    pre_signal = 1  # 信号
                    stop_lose_price = df.at[i, 'close'] * (
                                1 - stop_loss_pct / 100)  # 以本周期的收盘价乘以一定比例作为止损价格，也可以用下周期的开盘价df.at[i+1, 'open']
                    info_dict = {'pre_signal': pre_signal, 'stop_lose_price': stop_lose_price}

            # 其他情况
            else:
                raise ValueError('不可能出现其他的情况，如果出现，说明代码逻辑有误，报错')

        # 将无关的变量删除
        df.drop(['median', 'std', 'upper', 'lower', 'signal_long', 'signal_short'], axis=1, inplace=True)

        # ===由signal计算出实际的每天持有仓位
        # signal的计算运用了收盘价，是每根K线收盘之后产生的信号，到第二根开盘的时候才买入，仓位才会改变。
        df['pos'] = df['signal'].shift()
        df['pos'].fillna(method='ffill', inplace=True)
        df['pos'].fillna(value=0, inplace=True)  # 将初始行数的position补全为0

        return df