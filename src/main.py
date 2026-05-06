import os
import logging
import argparse
import pandas as pd
from datetime import datetime, timedelta
from cal_strategy_profit import cal_indicators
from baseline_strategy import baseline_strategy
from data_process import read_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def check_data_availability(file_path, start_date, end_date):
    """
    校验 actual_load_price_data.csv 中是否包含从 start_date 到 end_date 的所有日期数据
    
    Args:
        file_path: 实际数据文件路径
        start_date: 开始日期，格式 'YYYY-MM-DD'
        end_date: 结束日期，格式 'YYYY-MM-DD'
    
    Returns:
        (bool, list): (是否完整, 缺失日期列表)
    """
    # 读取数据文件
    df = pd.read_csv(file_path)
    
    # 获取数据中所有唯一的日期
    available_dates = set(df['target_day'].unique())
    
    # 生成从 start_date 到 end_date 的所有日期
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    required_dates = []
    current = start
    while current <= end:
        required_dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    # 找出缺失的日期
    missing_dates = [d for d in required_dates if d not in available_dates]
    
    return len(missing_dates) == 0, missing_dates


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_date", type=str, required=True, help="开始时间")
    parser.add_argument("--end_date", type=str, required=True, help="结束时间")
    parser.add_argument("--strategy_code", type=str, required=True, help="策略名称")
    args = parser.parse_args()
    start_date = args.start_date
    end_date = args.end_date
    strategy_code = args.strategy_code

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    df_strategy_declary_file_path = os.path.join(BASE_DIR, f'../data/{strategy_code}_strategy_data.csv')
    # 收益回收阈值比例
    lambda_0 = 0.2
    # 收益回收系数
    mu = 1.0
    # 处理数据：将原始csv数据处理为用于计算指标的格式数据：actual_load_price_data.csv:主要包含日前结算价、实时结算价、价差、实时负荷；TODO
    raw_data_file_path = 'GD_power_spot_hourly_data.xlsx'
    read_data(start_date=start_date, end_date=end_date, file_path=raw_data_file_path)
    # 校验真实数据是否完整
    df_actual_load_price_file_path = os.path.join(BASE_DIR, '../data/actual_load_price_data.csv')
    is_complete, missing_dates = check_data_availability(df_actual_load_price_file_path, start_date, end_date)
    if not is_complete:
        for missing_date in missing_dates:
            logging.error(f"缺失 {missing_date} 的真实数据")
        logging.error("数据校验失败，程序退出")
        exit(1)
    logging.info("数据校验通过：所有日期的真实数据均已存在")

    # 开始构建策略：基线策略
    baseline_strategy(df_actual_load_price_file_path, start_date, end_date, lambda_0, strategy_code)

    # 计算策略指标
    cal_indicators(df_strategy_declary_file_path, df_actual_load_price_file_path, start_date, end_date, strategy_code, lambda_0, mu)