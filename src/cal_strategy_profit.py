import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
from backtest_gd import BackTest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StrategyMetricsCalculator:
    """策略指标计算器"""
    
    def __init__(self, lambda_0: float, mu: float, epsilon: float = 1e-6):
        self.lambda_0 = lambda_0
        self.mu = mu
        self.epsilon = epsilon
    
    def calculate_best_load(self, dayahead_price: float, realtime_load: float, 
                           realtime_price: float) -> float:
        """
        计算最优申报量
        
        Args:
            dayahead_price: 日前价格
            realtime_load: 实时负荷
            realtime_price: 实时价格
            
        Returns:
            最优申报量
        """
        if dayahead_price >= realtime_price:
            return realtime_load * (1 - self.lambda_0)
        return realtime_load * (1 + self.lambda_0)
    
    def calculate_period_profit(self, dayahead_price: float, declare_quantity: float,
                               realtime_price: float, realtime_load: float) -> Tuple[float, float, float, float]:
        """
        计算单个时段的收益
        
        Returns:
            (收益, 收入, 成本, 负荷差)
        """
        backtest = BackTest(dayahead_price, declare_quantity, realtime_price, realtime_load, 
                           self.lambda_0, self.mu)
        return backtest.get_dayahead_bid_profit()
    
    def analyze_daily_trading(self, day_profits: List[float], best_profits: List[float],
                             actual_loads: List[float]) -> Dict:
        """
        分析单日交易表现
        
        Args:
            day_profits: 各时段策略收益列表
            best_profits: 各时段理论最优收益列表
            actual_loads: 各时段实际负荷列表
            
        Returns:
            包含各项指标的字典
        """
        correct_expect_profit = 0.0  # 正确交易时段期望收益
        correct_actual_profit = 0.0  # 正确交易时段实际收益
        incorrect_actual_profit = 0.0  # 错误交易时段实际损失
        incorrect_expect_profit = 0.0  # 错误交易时段期望收益
        correct_hours = 0
        trading_correct_flags = []
        
        for profit, best_profit in zip(day_profits, best_profits):
            if profit >= 0:
                # 交易动作正确
                correct_expect_profit += best_profit
                correct_actual_profit += profit
                correct_hours += 1
                trading_correct_flags.append(1)
            else:
                # 交易动作错误
                incorrect_actual_profit += profit
                incorrect_expect_profit += best_profit
                trading_correct_flags.append(0)
        
        total_expect_profit = sum(best_profits)
        total_load = sum(actual_loads)
        
        # 计算各项指标
        success_rate = (correct_expect_profit / total_expect_profit 
                       if abs(total_expect_profit) > self.epsilon else 0.0)
        
        achievement_rate = (correct_actual_profit / correct_expect_profit 
                           if abs(correct_expect_profit) > self.epsilon else 0.0)
        
        profit_loss_rate = (abs(incorrect_actual_profit) / max(correct_actual_profit, self.epsilon))
        
        failure_loss_rate = (abs(incorrect_actual_profit) / max(incorrect_expect_profit, self.epsilon)
                            if abs(incorrect_expect_profit) > self.epsilon else 0.0)
        
        profit_per_mwh = (sum(day_profits) / (total_load * 1e3) * 1e3 
                         if total_load > 0 else 0.0)
        
        return {
            'success_rate': round(success_rate, 4),
            'achievement_rate': round(achievement_rate, 4),
            'profit_loss_rate': round(profit_loss_rate, 4),
            'failure_loss_rate': round(failure_loss_rate, 4),
            'profit_per_mwh': profit_per_mwh,
            'correct_profit': correct_actual_profit,
            'incorrect_profit': incorrect_actual_profit,
            'trading_correct_flags': trading_correct_flags,
            'total_profit': sum(day_profits),
            'best_total_profit': total_expect_profit
        }


def load_and_merge_data(strategy_file: str, actual_file: str, 
                        start_date: str, end_date: str) -> pd.DataFrame:
    """
    加载并合并策略数据和实际数据
    
    Args:
        strategy_file: 策略申报数据文件路径
        actual_file: 实际负荷和价格数据文件路径
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        合并后的DataFrame
    """
    df_strategy = pd.read_csv(strategy_file)
    df_actual = pd.read_csv(actual_file)
    
    df_merged = pd.merge(
        df_strategy, df_actual,
        on=['sale_market', 'target_day', 'period'],
        how='left'
    ).sort_values(['target_day', 'period']).reset_index(drop=True)
    
    mask = (df_merged['target_day'] >= start_date) & (df_merged['target_day'] <= end_date)
    return df_merged[mask].sort_values(['target_day', 'period']).reset_index(drop=True)


def aggregate_by_day(df: pd.DataFrame) -> pd.DataFrame:
    """
    按天聚合数据，将各列转为列表
    
    Args:
        df: 合并后的DataFrame
        
    Returns:
        按天聚合的DataFrame
    """
    cols_to_agg = [
        'actual_realtime_load', 'actual_day_ahead_price',
        'actual_realtime_price', 'price_diff_actual', 'strategy_declary_load'
    ]
    
    return (df
            .sort_values(['sale_market', 'target_day', 'period'])
            .groupby(['sale_market', 'target_day'])[cols_to_agg]
            .agg(list)
            .reset_index())


def calculate_period_metrics(calculator: StrategyMetricsCalculator,
                            dayahead_prices: List[float],
                            realtime_prices: List[float],
                            realtime_loads: List[float],
                            declare_quantities: List[float]) -> Tuple[List[float], List[float]]:
    """
    计算一天的各时段收益
    
    Returns:
        (最优收益列表, 策略收益列表)
    """
    best_profits = []
    strategy_profits = []
    
    for dah_price, rt_price, rt_load, declare_qty in zip(
        dayahead_prices, realtime_prices, realtime_loads, declare_quantities
    ):
        # 计算最优申报量及对应收益
        best_load = calculator.calculate_best_load(dah_price, rt_load, rt_price)
        best_profit, _, _, _ = calculator.calculate_period_profit(
            dah_price, best_load, rt_price, rt_load
        )
        best_profits.append(best_profit)
        
        # 计算策略实际收益
        strategy_profit, _, _, _ = calculator.calculate_period_profit(
            dah_price, declare_qty, rt_price, rt_load
        )
        strategy_profits.append(strategy_profit)
    
    return best_profits, strategy_profits


def cal_indicators(df_strategy_declary_file_path: str, 
                   df_actual_load_price_file_path: str,
                   start_date: str, end_date: str, 
                   strategy_code: str,
                   lambda_0: float, mu: float) -> None:
    """
    计算策略指标主函数
    
    Args:
        df_strategy_declary_file_path: 策略申报数据文件路径
        df_actual_load_price_file_path: 实际负荷价格数据文件路径
        start_date: 回测开始日期
        end_date: 回测结束日期
        strategy_code: 策略代码
        lambda_0: 收益回收阈值比例
        mu: 收益回收系数
    """
    # 初始化
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(os.path.dirname(base_dir), "result")
    os.makedirs(out_dir, exist_ok=True)
    
    logger.info(f"{'='*50}")
    logger.info(f"策略代码: {strategy_code}")
    logger.info(f"回测区间: {start_date} ~ {end_date}")
    logger.info(f"{'='*50}")
    
    # 加载数据
    df_merged = load_and_merge_data(
        df_strategy_declary_file_path,
        df_actual_load_price_file_path,
        start_date, end_date
    )
    logger.info(f"合并后数据:\n{df_merged}")
    
    # 按天聚合
    df_daily = aggregate_by_day(df_merged)
    
    # 提取列表数据
    declare_quantities_list = df_daily['strategy_declary_load'].tolist()
    dayahead_prices_list = df_daily['actual_day_ahead_price'].tolist()
    realtime_prices_list = df_daily['actual_realtime_price'].tolist()
    realtime_loads_list = df_daily['actual_realtime_load'].tolist()
    date_list = df_daily['target_day'].tolist()
    
    # 初始化计算器
    calculator = StrategyMetricsCalculator(lambda_0, mu)
    
    # 存储结果
    results = {
        'date_list': date_list,
        'best_profits_by_day_hour': [],
        'strategy_profits_by_day_hour': [],
        'trading_correct_flags': [],
        'metrics_by_day': []
    }
    
    # 周期累计指标
    period_correct_expect_profit = 0.0
    period_correct_actual_profit = 0.0
    period_incorrect_actual_profit = 0.0
    period_incorrect_expect_profit = 0.0
    
    # 逐天计算
    for day_idx, current_date in enumerate(date_list):
        logger.info(f"\n{'-'*30}")
        logger.info(f"当前日期: {current_date}")
        
        # 计算各时段收益
        best_profits, strategy_profits = calculate_period_metrics(
            calculator,
            dayahead_prices_list[day_idx],
            realtime_prices_list[day_idx],
            realtime_loads_list[day_idx],
            declare_quantities_list[day_idx]
        )
        
        # 分析当日交易表现
        daily_metrics = calculator.analyze_daily_trading(
            strategy_profits, best_profits, realtime_loads_list[day_idx]
        )
        
        # 保存结果
        results['best_profits_by_day_hour'].append(best_profits)
        results['strategy_profits_by_day_hour'].append(strategy_profits)
        results['trading_correct_flags'].append(daily_metrics['trading_correct_flags'])
        results['metrics_by_day'].append(daily_metrics)
        
        # 累加周期指标
        period_correct_expect_profit += sum(
            bp for bp, sp in zip(best_profits, strategy_profits) if sp >= 0
        )
        period_correct_actual_profit += daily_metrics['correct_profit']
        period_incorrect_actual_profit += daily_metrics['incorrect_profit']
        period_incorrect_expect_profit += sum(
            bp for bp, sp in zip(best_profits, strategy_profits) if sp < 0
        )
        
        # 日志输出
        logger.info(f"最优收益(时段): {best_profits}")
        logger.info(f"策略收益(时段): {strategy_profits}")
    
    # 计算周期总指标
    total_best_profit = sum(sum(p) for p in results['best_profits_by_day_hour'])
    total_strategy_profit = sum(sum(p) for p in results['strategy_profits_by_day_hour'])
    total_load = sum(sum(loads) for loads in realtime_loads_list)
    
    # 汇总指标
    summary_metrics = {
        '交易成功率': (period_correct_expect_profit / total_best_profit 
                     if total_best_profit != 0 else 0),
        '成功收益率': (period_correct_actual_profit / period_correct_expect_profit 
                     if period_correct_expect_profit != 0 else 0),
        '利润损失率': (abs(period_incorrect_actual_profit) / max(period_correct_actual_profit, calculator.epsilon)),
        '失败损失率': (abs(period_incorrect_actual_profit) / max(period_incorrect_expect_profit, calculator.epsilon)
                     if period_incorrect_expect_profit != 0 else 0),
        '度电收益(厘/kwh)': (total_strategy_profit / (total_load * 1e3) * 1e3 
                          if total_load > 0 else 0),
        '收益达成率': (total_strategy_profit / total_best_profit 
                     if total_best_profit != 0 else 0),
        '潜在累计收益': total_best_profit,
        '策略累计收益': total_strategy_profit
    }
    
    # 输出汇总结果
    logger.info(f"\n{'='*50}")
    logger.info("回测周期策略指标汇总")
    logger.info(f"{'='*50}")
    for name, value in summary_metrics.items():
        logger.info(f"{name}: {value:.6f}" if isinstance(value, float) else f"{name}: {value}")
    
    # 保存结果到DataFrame
    df_daily['best_profit_by_day_hour'] = results['best_profits_by_day_hour']
    df_daily['best_total_profit_by_day'] = [sum(p) for p in results['best_profits_by_day_hour']]
    df_daily['strategy_profit_by_day_hour'] = results['strategy_profits_by_day_hour']
    df_daily['strategy_total_profit_by_day'] = [sum(p) for p in results['strategy_profits_by_day_hour']]
    
    # 保存按天汇总结果
    df_result_by_day = df_daily[[
        'sale_market', 'target_day',
        'best_total_profit_by_day', 'strategy_total_profit_by_day'
    ]]
    df_result_by_day.to_csv(
        os.path.join(out_dir, f"{strategy_code}_profit_result_by_day.csv"),
        index=False
    )
    
    # 保存按时段详细结果
    list_cols = [
        'actual_realtime_load', 'actual_day_ahead_price', 'actual_realtime_price',
        'price_diff_actual', 'strategy_declary_load',
        'best_profit_by_day_hour', 'strategy_profit_by_day_hour'
    ]
    df_exploded = df_daily.explode(list_cols).reset_index(drop=True)
    df_exploded['period'] = df_exploded.groupby(['sale_market', 'target_day']).cumcount()
    df_exploded = df_exploded[[
        'sale_market', 'target_day', 'period', 'actual_realtime_load',
        'actual_day_ahead_price', 'actual_realtime_price', 'price_diff_actual',
        'strategy_declary_load', 'best_profit_by_day_hour', 'strategy_profit_by_day_hour'
    ]]
    df_exploded.to_csv(
        os.path.join(out_dir, f"{strategy_code}_profit_result_by_hour.csv"),
        index=False
    )
    
    # 保存指标汇总
    df_metrics = pd.DataFrame({
        'metric': list(summary_metrics.keys()),
        f'{strategy_code}_strategy': list(summary_metrics.values())
    })
    df_metrics.to_csv(
        os.path.join(out_dir, f"{strategy_code}_策略指标_{date_list[0]}_{date_list[-1]}.csv"),
        index=False
    )
    
    logger.info(f"\n结果已保存到: {out_dir}")


if __name__ == '__main__':
    # 测试用例
    base_dir = os.path.dirname(os.path.abspath(__file__))
    strategy_file = os.path.join(base_dir, '../data/baseline_strategy_data.csv')
    actual_file = os.path.join(base_dir, '../data/actual_load_price_data.csv')
    
    cal_indicators(
        strategy_file, actual_file,
        '2025-12-13', '2025-12-15',
        'baseline', 0.2, 1.0
    )
