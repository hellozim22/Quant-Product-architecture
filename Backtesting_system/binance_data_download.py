from datetime import datetime, timedelta
import time
import csv
import ccxt

#设定数据开始时间和结束时间,从2017-08-20开始
binance = ccxt.binance()
start_date='2017-09-01 00:00:00'
end_date = '2019-10-09 00:00:00'
symbol = 'BTC/USDT'
period = '1m'
limit = 720


#生成CSV文件
out_put_file = '../historical_data/BINANCE_' + symbol.replace('/','') + '_' + period.upper() + '.csv'
out = open(out_put_file, 'a', newline='')
csv_writer = csv.writer(out, dialect='excel')

date_list = []
begin_date = datetime.strptime(str(start_date),'%Y-%m-%d %H:%M:%S')
end_date = datetime.strptime(str(end_date),'%Y-%m-%d %H:%M:%S')
while begin_date <= end_date:
    date_list.append(begin_date)
    begin_date += timedelta(hours=12)

size = 0

#遍历所有日期段，每次取720条K线(半天)
for date in date_list:
    while True:
        try:
            since = int(time.mktime(date.timetuple())*1000)

            datas = binance.fetch_ohlcv(symbol=symbol,timeframe=period,since=since,limit=720)
            print(date,len(datas))
            print(datas)
            for data in datas:
                timeStamp = data[0]/1000
                timeArray = time.localtime(timeStamp)
                time_str = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
                newdata = [time_str, data[1], data[2], data[3], data[4], data[5]]
                #print(newdata)
                #csv_writer.writerow(newdata)
                size += 1
            break
        except Exception as e:
            print(symbol + ' error!' + str(e))
            time.sleep(5)
    time.sleep(2)

print('总数:' + str(size))














