import pandas as pd
import os
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def read_data(start_date, end_date, file_path):
    '''
    读取原始小时级别数据，提取真实数据保存为csv文件
    校验 start_date 前12天到 end_date 每天至少24小时数据完整
    '''
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(BASE_DIR)
    out_dir = os.path.join(parent_dir, "data")
    try:
        df_data_hour = pd.read_excel(os.path.join(out_dir, file_path))
        logging.info(f"原始数据:\n{df_data_hour}")
        col_filter = ['sale_market', 'target_day', 'time_period_name', 'actual_total_load', 'actual_day_ahead_settle_elec_price','actual_realtime_settle_elec_price']
        df_data_hour_filter = df_data_hour[col_filter].copy()
        
        # 转换 target_day 为字符串统一格式
        df_data_hour_filter['target_day'] = pd.to_datetime(df_data_hour_filter['target_day']).dt.strftime('%Y-%m-%d')
        df_data_hour_filter['period'] = pd.to_datetime(df_data_hour_filter['time_period_name'], errors='coerce').dt.hour
        
        # 校验起止日期
        required_start = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=12)).strftime('%Y-%m-%d')
        required_end = end_date
        all_required_dates = pd.date_range(start=required_start, end=required_end, freq='D').strftime('%Y-%m-%d')
        
        # 按 target_day 统计每天数据条数
        day_counts = df_data_hour_filter.groupby('target_day').size()
        
        missing_dates = []
        incomplete_dates = []
        for d in all_required_dates:
            count = day_counts.get(d, 0)
            if count == 0:
                missing_dates.append(d)
            elif count != 24:
                incomplete_dates.append((d, count))
        
        if missing_dates or incomplete_dates:
            if missing_dates:
                logging.error(f"缺失数据的日期: {missing_dates}")
            if incomplete_dates:
                logging.error(f"小时数不足的日期(期望24小时): {incomplete_dates}")
            raise ValueError("数据完整性校验失败")
        
        # 过滤到需要的日期范围（前12天到end_date）
        df_data_hour_filter = df_data_hour_filter[
            (df_data_hour_filter['target_day'] >= required_start) & 
            (df_data_hour_filter['target_day'] <= required_end)
        ]
        
        if(df_data_hour_filter.isnull().values.any()):
            logging.error(f"回测时间内存在真实数据不存在的情况")
            raise ValueError("回测时间内存在真实数据不存在的情况")
        
        df_data_hour_filter = df_data_hour_filter.rename(columns={'actual_total_load': 'actual_realtime_load', 'actual_day_ahead_settle_elec_price':'actual_day_ahead_price', 'actual_realtime_settle_elec_price':'actual_realtime_price'})
        df_data_hour_filter['price_diff_actual'] = (df_data_hour_filter['actual_day_ahead_price'] - df_data_hour_filter['actual_realtime_price']).round(3)
        df_data_hour_filter = df_data_hour_filter[['sale_market', 'target_day', 'period', 'actual_realtime_load', 'actual_day_ahead_price','actual_realtime_price', 'price_diff_actual']].sort_values(by=['sale_market', 'target_day', 'period']).reset_index(drop=True)
        logging.info(f"过滤后的数据列:\n{df_data_hour_filter.head()}")
        df_data_hour_filter.to_csv(os.path.join(out_dir,f"actual_load_price_data.csv"),index=False)
        logging.info("成功提取真实负荷和价差数据")
    except Exception as e:
        logging.error(f"提取真实负荷和价差数据失败:{e}")
        raise

if __name__ == "__main__":
    start_date = '2025-01-13'
    end_date = '2026-03-31'
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(BASE_DIR)
    out_dir = os.path.join(parent_dir, "data")
    file_path = '小时级广东市场负荷、电价与气象数据.xlsx'
    read_data(start_date, end_date, file_path)
