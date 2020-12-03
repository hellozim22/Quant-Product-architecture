from datetime import datetime, timedelta
import pandas as pd
from email.mime.text import MIMEText
from smtplib import SMTP
import os
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)


def transfer_to_period_data(df, rule_type='15T'):
    """
    将数据转换为其他周期的数据
    :param df:
    :param rule_type:
    :return:
    """
    # =====转换为其他分钟数据
    period_df = df.resample(rule=rule_type, on='candle_begin_time', label='left', closed='left').agg(
        {'open': 'first',
         'high': 'max',
         'low': 'min',
         'close': 'last',
         'volume': 'sum',
         })
    period_df.dropna(subset=['open'], inplace=True)  # 去除一天都没有交易的周期
    period_df = period_df[period_df['volume'] > 0]  # 去除成交量为0的交易周期
    period_df.reset_index(inplace=True)
    df = period_df[['candle_begin_time', 'open', 'high', 'low', 'close', 'volume']]

    return df

def transfer_to_period_data2(df,period_type='T',period_base=0,if_fill_empty_candle=True):
    # =====转换为其他周期
    period_df = df.resample(rule=period_type, on='candle_begin_time', label='left', base=period_base).agg(
        {'open': 'first',
         'high': 'max',
         'low': 'min',
         'close': 'last',
         'volume': 'sum',
         #'amount': 'sum',
         #'change': lambda x:(x+1.0).prod()-1.0,
         })
    #period_df = period_df[['open','high','low','close','volume','change']]
    period_df['change'] = period_df['close']/period_df['close'].shift(1) - 1
    period_df['change'].fillna(value=0)
    #将没有交易的K线数据填满
    if if_fill_empty_candle:
        period_df['change'] = period_df['change'].fillna(value=0)
        period_df['volume'] = period_df['volume'].fillna(value=0)
        period_df[['close']].fillna(method='ffill',inplace=True)
        #for i in ['open','high','low']:
        #    period_df[i].fillna(value=period_df['close'],inplace=True)
    else:
        period_df.dropna(subset=['open'],inplace=True)
        period_df = period_df[period_df['volume']>0] #去掉成交量为0的周期

    #重新设定INDEX
    period_df.reset_index(inplace=True)
    return period_df
