import os
import pandas as pd
import time
from datetime import datetime, timedelta
import numpy as np
from datetime import datetime, timedelta
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def baseline_strategy(df_actual_load_price_file_path, start_date, end_date, lambda_0, strategy_code):
    df_actual_data = pd.read_csv(f"{df_actual_load_price_file_path}")
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(BASE_DIR)
    out_dir = os.path.join(parent_dir, "data")
    os.makedirs(out_dir, exist_ok=True)

    # 真实结算价信息披露时间：D-6; D为运行日;
    info_get_days_gap = 6
    # 设置统计时间
    statistic_window_size = 7
    df_actual_data = df_actual_data.sort_values(['sale_market', 'target_day', 'period']).reset_index(drop=True)
    cols_to_agg = ['actual_realtime_load', 'actual_day_ahead_price', 'actual_realtime_price', 'price_diff_actual']
    df_actual_data_merge = (
        df_actual_data
        .sort_values(['sale_market', 'target_day', 'period'])  # 保证24小时顺序
        .groupby(['sale_market', 'target_day'])[cols_to_agg]
        .agg(list)
        .reset_index()
    )
    df_actual_data_merge_ = df_actual_data_merge[(df_actual_data_merge['target_day']>=start_date) & (df_actual_data_merge['target_day']<=end_date)].sort_values(['sale_market', 'target_day']).reset_index(drop=True)
    date_list = df_actual_data_merge_['target_day'].to_list()
    logging.info(f"df_actual_data_merge:\n{df_actual_data_merge}")
    logging.info(f"date_list:{date_list}")

    similate_avg_price_diff_target_day_dict = {}
    similate_avg_load_target_day_dict = {}
    similate_strategy_declary_load_target_day_dict = {}
    for current_target_day in date_list:
        logging.info(f"current_target_day:{current_target_day}")
        # 获取历史样本最早时间
        start_cal_day = (datetime.strptime(current_target_day, "%Y-%m-%d") - timedelta(days=info_get_days_gap+statistic_window_size-1)).strftime("%Y-%m-%d")
        end_cal_day = (datetime.strptime(current_target_day, "%Y-%m-%d") - timedelta(days=info_get_days_gap)).strftime("%Y-%m-%d")
        logging.info(f"start_cal_day, end_cal_day:{start_cal_day, end_cal_day}")
        # 获取对应时间窗内的数据
        df_cal_temp = df_actual_data_merge[(df_actual_data_merge['target_day'] >= start_cal_day)&(df_actual_data_merge['target_day'] <= end_cal_day)].sort_values(['sale_market', 'target_day']).reset_index(drop=True)
        # 计算均值的时间信息
        cal_date_list = df_cal_temp['target_day'].to_list()
        logging.info(f"cal_date_list:{cal_date_list}")
        if(len(cal_date_list) < statistic_window_size):
            logging.error(f"--------历史真实数据不足{statistic_window_size}天-------------")
            df_cal_temp = df_actual_data_merge[df_actual_data_merge['target_day'] <= end_cal_day].sort_values(['sale_market', 'target_day']).reset_index(drop=True).tail(statistic_window_size)
            date_list = df_cal_temp['target_day'].to_list()
            logging.info(f"--------历史真实数据不足{statistic_window_size}天，使用{date_list}数据-------------")
        # 获取统计时间内内每天24小时的实际价差
        actual_price_diff_lists = df_cal_temp['price_diff_actual'].to_list()
        actual_load_lists = df_cal_temp['actual_realtime_load'].to_list()

        # 计算平均价差
        avg_price_diff_list = np.array(actual_price_diff_lists).mean(axis=0).tolist()
        similate_avg_price_diff_target_day_dict[current_target_day] = avg_price_diff_list
        logging.info(f"avg_price_diff_list:{avg_price_diff_list}")
        # 计算平均负荷
        avg_load_list = np.array(actual_load_lists).mean(axis=0).tolist()
        similate_avg_load_target_day_dict[current_target_day] = avg_load_list
        logging.info(f"avg_load_list:{avg_load_list}")

        # 计算策略申报量
        strategy_declary_load_list = [avg_load*(1+lambda_0) if avg_price_diff < 0 else avg_load*(1-lambda_0) if avg_price_diff > 0 else avg_load for avg_price_diff, avg_load in zip(avg_price_diff_list, avg_load_list)]
        similate_strategy_declary_load_target_day_dict[current_target_day] = strategy_declary_load_list
        logging.info(f"strategy_declary_load_list:{strategy_declary_load_list}")
    
    # 将策略申报数据保存
    df_strategy_data = pd.DataFrame({'target_day': list(similate_strategy_declary_load_target_day_dict.keys()), 
                                    'strategy_declary_load': list(similate_strategy_declary_load_target_day_dict.values())})
    sale_market = df_actual_data_merge_['sale_market'].unique()[0]
    df_strategy_data['sale_market'] = sale_market
    logging.info(f"df_strategy_data:\n{df_strategy_data}")
    list_cols = ['strategy_declary_load']
    df_result_exploded = df_strategy_data.explode(list_cols).reset_index(drop=True)
    df_result_exploded['period'] = df_result_exploded.groupby(['sale_market', 'target_day']).cumcount()
    df_result_exploded = df_result_exploded[['sale_market', 'target_day', 'period', 'strategy_declary_load']]
    logging.info(f"df_result_exploded:\n{df_result_exploded}")

    df_result_exploded.to_csv(os.path.join(out_dir,f"{strategy_code}_strategy_data.csv"), index=False)



    

if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    df_actual_load_price_file_path = os.path.join(BASE_DIR, '../data/actual_load_price_data.csv')
   
    start_date = '2025-12-13'
    end_date = '2025-12-15'
    lambda_0 = 0.2
    strategy_code = 'baseline'
    baseline_strategy(df_actual_load_price_file_path, start_date, end_date, lambda_0, strategy_code)

