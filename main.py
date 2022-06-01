import pandas as pandas
import requests
import math
from scipy import stats
from statistics import mean

class AlgorithmicTradingMomentum:
    def __init__(self):
        self.SECRET_KEY = ""
        self.return_intervals = [
            "month1",
            "month3",
            "month6",
            "year1",
        ]

        self.stock_symbol_groups = self.getGroupsOfStockSymbols(self.getSNP500Symbols())

        self.momentum_stocks = self.batchRequest(self.stock_symbol_groups)

        self.calculatePercentile()

        self.getScorePercentile()

        print(self.momentum_stocks)


    def getStockStats(self, symbol):
        statistics_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/stats?token={self.SECRET_KEY}'
        data = requests.get(statistics_url).json()
        return data

    def getSNP500Symbols(self):
        stocks = pandas.read_csv('External Data/constituents.csv')
        return stocks["Symbol"]

    #all this grouping is to make batch API calls with a max of 100 stock per call
    #thus this function returns an array of strings of a maximum of 100 symbols delimed by a comma
    def getGroupsOfStockSymbols(self, symbols):
        max_group_size = 100
        number_groups = math.ceil(len(symbols)/max_group_size)
        symbol_groups = []
        n = 0

        for i in range(number_groups):
            symbols_string = ""
            for j in range(max_group_size):
                if(len(symbols_string)==0):
                    symbols_string = symbols[n]
                else:
                    symbols_string += ","+ symbols[n]
                n+=1
                if(n==len(symbols)):
                    if(len(symbols_string)>0):
                        symbol_groups.append(symbols_string)
                    return symbol_groups

            symbol_groups.append(symbols_string)

    def batchRequest(self, stock_symbol_groups):
        stock_dataframe = pandas.DataFrame(columns=[
            "Symbol",
            "price",
            "month1ChangePercent",
            "month1ChangePercentile",
            "month3ChangePercent",
            "month3ChangePercentile",
            "month6ChangePercent",
            "month6ChangePercentile",
            "year1ChangePercent",
            "year1ChangePercentile",
            "day50MovingAvg",
            "day200MovingAvg",
            "Score"])

        i = 0
        for symbol_group in stock_symbol_groups:
            batch_request_url = f"https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_group}&types=stats&token={self.SECRET_KEY}"
            data = requests.get(batch_request_url).json()
            symbols_list = symbol_group.split(',')
            for symbol in symbols_list:
                try:
                    new_row = pandas.DataFrame({
                        "Symbol": [symbol],
                        "price": [data[symbol]["stats"]["marketcap"]/data[symbol]["stats"]["sharesOutstanding"]],
                        "month1ChangePercent":[data[symbol]["stats"]["month1ChangePercent"]],
                        "month1ChangePercentile": "N/A",
                        "month3ChangePercent":[data[symbol]["stats"]["month3ChangePercent"]],
                        "month3ChangePercentile": "N/A",
                        "month6ChangePercent":[data[symbol]["stats"]["month6ChangePercent"]],
                        "month6ChangePercentile": "N/A",
                        "year1ChangePercent": [data[symbol]["stats"]["year1ChangePercent"]],
                        "year1ChangePercentile": "N/A",
                        "day50MovingAvg": [data[symbol]["stats"]["day50MovingAvg"]],
                        "day200MovingAvg": [data[symbol]["stats"]["day200MovingAvg"]],
                        "Score": "N/A"
                    })
                    new_row.set_index(i)
                    i+=1
                except:
                    pass


                stock_dataframe = pandas.concat([stock_dataframe, new_row], ignore_index=True)

        stock_dataframe.sort_values("year1ChangePercent", ascending = False, inplace = True)
        stock_dataframe = stock_dataframe[:50]
        pandas.set_option('display.max_columns', None)
        stock_dataframe.reset_index(inplace=True)

        return stock_dataframe

    def calculatePercentile(self):
        for stock in self.momentum_stocks.index:
            for time_interval in self.return_intervals:
                return_col = f"{time_interval}ChangePercent"
                percentile_col = f"{time_interval}ChangePercentile"

                self.momentum_stocks.loc[stock, percentile_col] = stats.percentileofscore(self.momentum_stocks[return_col], self.momentum_stocks.loc[stock, return_col])

    def getScorePercentile(self):
        for stock in self.momentum_stocks.index:
            momentum_percentiles = []
            for time_interval in self.return_intervals:
                momentum_percentiles.append(self.momentum_stocks.loc[stock, f"{time_interval}ChangePercentile"])
            self.momentum_stocks.loc[stock, "Score"] = mean(momentum_percentiles)

        self.momentum_stocks.sort_values("Score", ascending = False, inplace=True)
        self.momentum_stocks.reset_index(inplace=True)

if __name__ == '__main__':
    test = AlgorithmicTradingMomentum()
