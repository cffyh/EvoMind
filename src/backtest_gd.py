import numpy as np
import pandas as pd

class BackTest:
    def __init__(self, dayahead_price, dayahead_load, realtime_price, realtime_load, lambda_0, mu):
        # dayahead_load: 日前市场申报电量
        # dayahead_price: 日前市场价格
        # realtime_load: 实际用电量
        # realtime_price: 实时市场价格
        self.dayahead_price = dayahead_price
        self.dayahead_load = dayahead_load
        self.realtime_price = realtime_price
        self.realtime_load = realtime_load
        self.lambda_0 = lambda_0
        self.mu  = mu


    def cal_dayahead_bid_deviation_cost(self):
        """计算日前申报偏差考核"""
        # dayahead_price: 日前价格
        # dayahead_load: 日前申报电量
        # realtime_price: 实时价格
        # realtime_load: 实际用电量
        # case1: 日前价格 < 实时价格  and 日前申报电量 > (实时用电量 x (1 + lambda_0))
        if self.dayahead_load > self.realtime_load * (1 + self.lambda_0) and self.dayahead_price < self.realtime_price:
            load_diff = self.dayahead_load - (self.realtime_load * (1 + self.lambda_0))
            cost = (self.dayahead_load - (self.realtime_load * (1 + self.lambda_0))) * (self.realtime_price - self.dayahead_price) * self.mu
        # case2: 日前价格 > 实时价格  and 日前申报电量 < (实时用电量 x (1 - lambda_0))
        elif self.dayahead_load < self.realtime_load * (1 - self.lambda_0) and self.dayahead_price > self.realtime_price:
            load_diff = self.realtime_load * (1 - self.lambda_0) - self.dayahead_load
            cost = (self.realtime_load * (1 - self.lambda_0) - self.dayahead_load) * (self.dayahead_price - self.realtime_price) * self.mu
        else:
            load_diff = 0
            cost = 0
        return cost, load_diff
    
    def get_dayahead_bid_profit(self):
        # 正表示收益，负表示困损
        # 分为四种情况，
        # 1、实时价格 > 日前价格, 应该多申报, 如果申报量 > 实际, 赚了，计算为正值
        # 2、实时价格 > 日前价格, 应该多申报, 如果申报量 < 实际, 亏了，计算为负值
        # 3、实时价格 < 日前价格, 应该少申报, 如果申报量 > 实际, 亏了，计算为负值
        # 4、实时价格 < 日前价格, 应该少申报, 如果申报量 < 实际, 赚了，计算为正值
        dayahead_bid_income = (self.realtime_price - self.dayahead_price) * (self.dayahead_load - self.realtime_load)
        # 偏差收益转移, 收益回收, 日前申报偏差考核
        dayahead_bid_cost, load_diff = self.cal_dayahead_bid_deviation_cost()
        dayahead_bid_profit = dayahead_bid_income - dayahead_bid_cost
        return round(dayahead_bid_profit,3), round(dayahead_bid_income,3), round(dayahead_bid_cost,3), load_diff