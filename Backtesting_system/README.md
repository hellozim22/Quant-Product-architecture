# backtesting
# # # #
Back test framework modified based on VNPY optimization:
Function:
1. Support single parameter backtest: transaction details and graphs can be output
2. Support violent exhaustive parameter optimization
3. Support genetic algorithm parameter optimization
4. Support BITMEX and BINANCE historical data downloads
5. Support multi-strategy, multi-cycle and multi-parameter combined backtest
   
Instructions for use

1. Run_backtesting. Py: Supports multi-policy, multi-parameter and multi-cycle backtesting.
Detailed backtest results, backtest transaction details, graphs, and K lines will be output
Back test steps:
(1) Initialize the backtest engine
(2) Engine. set_parameters sets the basic parameters of backtest:
This includes the trading pair, the exchanges, the time period of the data file (1M is downloaded), the start time, the end time,
Handling fee, quantity of each order, initial amount, and time cycle of back test
(3) Load_data () loads the original data file under historical_data and automatically converts it according to the backtest period set
(4) InIT_backtesting () initializes the backtest engine
(5) Add_strategy () Add the backtest strategy class and parameters.
The writing method of strategy class can refer to xxxSignal writing method in the big course of punishment, which can be directly used.
It also supports the writing of position allocation in position management courses
(6) Run_backtesting () start backtesting
(7) Calculate_result () calculates the profit and loss and revenue of the strategy on a daily basis
(8) Calculate_STATISTICS () Statistics the indicators of the strategy:
Including final amount, final return, annualized return, maximum retracement, winning rate, Sharpe ratio, etc
(9) Show_chart () draw the yield curve and other graphs
(10) Output_trades () output each transaction detail
(11) Show_bar_chart () outputs the k-chart chart and marks each transaction (not finished yet, the graph is not very nice and is being adjusted)
Note: All output including transaction details and graphics will be saved in the Details directory

2. Run_optimization. Py: Parameter optimization selection using brute force optimization method
According to the parameter range and time range set, the optimal parameters are selected and verified in the subsequent time period.
Back test steps:
(1) Initialize the backtest engine
(2) Set the list of backtest trading pairs (multiple trading pairs can be added in batch and backtest one by one)
(3) Set the list of cycles to be backtested, such as 15T, 30T and 60T
(4) Set the backtest period and validation period, and the period between start_date-end_date is the backtest period.
After the backtest, select the N parameters with the best backtest results (N=check_num)
Verify the result between end_date-check_date again
(5) Initialize OptimizationSetting parameter combination
Set the callback period and the optimization target set_target (generally the optimization target is total_RETURN total return rate, but others can also be set)
Set the range and step size of each optimization parameter. The larger the range of this setting, the longer the optimization combination and the longer the time
(6) Create a new process pool and use multiple processes to test back to improve efficiency (the number of process pools is CPU core number -2). If the process pool is full, it is easy to kill the machine
(7) Initialize the backtest engine and start backtesting one by one (similar to run_backtesting).
(8) At the end of the backtest for each transaction, two files will be output, one is the backtest result, the other is the verification result, both of which will be output under the Results folder

3. Run_ga_optimization. Py: Use genetic algorithm for parameter optimization selection
The GAFT genetic algorithm library is used to carry out continuous genetic optimization according to the set parameter range and genetic algebra, and finally the optimal parameter combination is selected
Compared with brute force exhaustive method, it saves a lot of time (some parameter combinations with poor results are omitted, and the backtest will not be repeated).
Back test steps:
(1) Set the number of generations, the more the better, the longer the time required
(2) Set the list of backtest trading pairs (multiple trading pairs can be added in batch and backtest one by one)
(3) Set the list of cycles to be backtested, such as 15T, 30T and 60T
(4) Set the back test period
(5) Initialize OptimizationSetting parameter combination
Set the callback period and the optimization target set_target (generally the optimization target is total_RETURN total return rate, but others can also be set)
Set the range and step size of each optimization parameter
(7) Initialize the backtest engine, start backtest by generation, and finally select the optimal parameter


