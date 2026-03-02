"""
Strategy F 净值监控程序 V1.1
"""
import time
import pandas as pd
from datetime import datetime, timedelta
import os


# ===重试机制
def retry_wrapper(func, params={}, func_name='', retry_times=5, sleep_seconds=5):
    """
    需要在出错时不断重试的函数，例如和交易所交互，可以使用本函数调用。
    :param func:            需要重试的函数名
    :param params:          参数
    :param func_name:       方法名称
    :param retry_times:     重试次数
    :param sleep_seconds:   报错后的sleep时间
    :return:
    """
    for _ in range(retry_times):
        try:
            result = func(params=params)
            return result
        except Exception as e:
            print(func_name, '报错，报错内容：', str(e), '程序暂停(秒)：', sleep_seconds)
            time.sleep(sleep_seconds)
    else:
        raise ValueError(func_name, '报错重试次数超过上限，程序退出。')


# ===下次运行时间
def next_run_time(time_interval, ahead_seconds=5, cheat_seconds=100):
    """
    根据time_interval，计算下次运行的时间。
    PS：目前只支持分钟和小时。
    :param time_interval: 运行的周期，15m，1h
    :param ahead_seconds: 预留的目标时间和当前时间之间计算的间隙
    :param cheat_seconds: 相对于下个周期时间，提前或延后多长时间， 100： 提前100秒； -50：延后50秒
    :return: 下次运行的时间

    案例：
    15m  当前时间为：12:50:51  返回时间为：13:00:00
    15m  当前时间为：12:39:51  返回时间为：12:45:00

    10m  当前时间为：12:38:51  返回时间为：12:40:00
    10m  当前时间为：12:11:01  返回时间为：12:20:00

    5m  当前时间为：12:33:51  返回时间为：12:35:00
    5m  当前时间为：12:34:51  返回时间为：12:40:00

    30m  当前时间为：21日的23:33:51  返回时间为：22日的00:00:00
    30m  当前时间为：14:37:51  返回时间为：14:56:00

    1h  当前时间为：14:37:51  返回时间为：15:00:00
    """

    # 将 time_interval 转换成 时间类型
    ti = pd.to_timedelta(time_interval)
    # 获取当前时间
    now_time = datetime.now()
    # 计算当日时间的 00：00：00
    this_midnight = now_time.replace(hour=0, minute=0, second=0, microsecond=0)
    # 每次计算时间最小时间单位1分钟
    min_step = timedelta(minutes=1)
    # 目标时间：设置成默认时间，并将 秒，毫秒 置零
    target_time = now_time.replace(second=0, microsecond=0)

    while True:
        # 增加一个最小时间单位
        target_time = target_time + min_step
        # 获取目标时间已经从当日 00:00:00 走了多少时间
        delta = target_time - this_midnight
        # delta 时间可以整除 time_interval，表明时间是 time_interval 的倍数，是一个 整时整分的时间
        # 目标时间 与 当前时间的 间隙超过 ahead_seconds，说明 目标时间 比当前时间大，是最靠近的一个周期时间
        if delta.seconds % ti.seconds == 0 and (target_time - now_time).seconds >= ahead_seconds:
            break

    # # 配置 cheat_seconds ，对目标时间进行 提前 或者 延后
    # if cheat_seconds != 0:
    #     target_time = target_time - timedelta(seconds=cheat_seconds)

    print('程序下次运行的时间：', target_time, '\n')
    return target_time


# ===依据时间间隔, 自动计算并休眠到指定时间
def sleep_until_run_time(time_interval='1h', ahead_time=1, if_sleep=True, cheat_seconds=0):
    """
    根据next_run_time()函数计算出下次程序运行的时候，然后sleep至该时间
    In Mr.Xing's version, target_time and run_time were the same, both with cheat_seconds.
    Here in my version:
    If the next iteration is to trade, then cheat_seconds will be used to make the program wake up earlier.
    """

    # The code below to check the format of time_interval was in the beginning of next_run_time() in Xing's ver
    # I put the code here, because in my version
    # time_interval will also be used in the next step in sleep_until_run_time()
    # ===检测 time_interval 是否配置正确，并将 时间单位 转换成 可以解析的时间单位
    if time_interval.endswith('m') or time_interval.endswith('h'):
        pass
    elif time_interval.endswith('T'):  # 分钟兼容使用T配置，例如  15T 30T
        time_interval = time_interval.replace('T', 'm')
    elif time_interval.endswith('H'):  # 小时兼容使用H配置， 例如  1H  2H
        time_interval = time_interval.replace('H', 'h')
    else:
        print('time_interval格式不符合规范。程序exit')
        exit()

    # === 计算下次运行时间
    target_time = next_run_time(time_interval, ahead_time, cheat_seconds)
    print('local target_time:', target_time)

    # === to calculate the condition0: time for collecting Klines and condition1: time condition
    # to calculate time difference automatically
    utc_offset = int(time.localtime().tm_gmtoff / 60 / 60)  # 获取服务器所在的当前时区
    time_difference = pd.Timedelta(hours=-utc_offset)
    # to compare utc_target_time of next iteration with trading_target_utc, the time to trade
    utc_target_time = target_time + time_difference
    print('utc_target_time', utc_target_time)

    # 在这个版本里，run_time 和 target_time 是一致的，不需要作区别。
    run_time = target_time
    # utc_run_time = utc_target_time
    # 如果监控时间很短，计算获得的 run_time 小于 now, sleep就会睡 一天
    print('程序下次运行的时间,local run_time：', run_time, '\n')

    # to calculate the seconds needed to sleep, then sleep
    if if_sleep:
        _now = datetime.now()
        if run_time > _now:
            time.sleep(max(0, (run_time - _now).seconds))
        while True:  # 在靠近目标时间时
            if datetime.now() > run_time:
                break

    return target_time, utc_target_time, time_difference


def save_net_value(df_acc_bal_mini, utc_target_time):
    """
    This function is to export daily net value data to a csv file.
    With standardized names of functions, folder, file, cols. 20260301
    """
    # 获取前一天的日期
    previous_day = (utc_target_time - timedelta(days=1)).date()
    # 获取当前月份，用于创建文件名
    current_month = (utc_target_time - timedelta(days=1)).strftime("%Y%m")
    # 创建文件夹路径
    folder_path = "data/net_value_data"     # standardized folder name 20260228
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    # 生成文件名
    file_name = f"{folder_path}/net_value_{current_month}.csv"  # standardized file name 20260228

    # 重命名列  # standardized column name  20260301
    df_acc_bal_mini = df_acc_bal_mini.rename(columns={
        'marginBalance': 'net_value',
    })
    # 调整一下输出的数据的排版
    df_acc_bal_mini['date'] = previous_day
    df_acc_bal_mini = df_acc_bal_mini[
        ['date', 'asset', 'net_value', 'walletBalance', 'unrealizedProfit', 'availableBalance', 'initialMargin',
         'total_pos_value', 'exposure_pos_value', 'total_pos_value_ratio', 'exposure_pos_value_ratio']]
    # 如果文件不存在，创建文件并写入表头
    if not os.path.exists(file_name):
        df_acc_bal_mini.to_csv(file_name, mode='w', index=False, header=True)

    else:
        # 如果文件存在，追加数据到文件
        df_acc_bal_mini.to_csv(file_name, mode='a', index=False, header=False)

    print(f"Account balance(equity) saved to {file_name}")


def save_acc_pos_bn(df_acc_pos_mini, utc_target_time):
    # 获取前一天的日期
    previous_day = (utc_target_time - timedelta(days=1)).strftime("%Y%m%d")

    # 获取当前月份，用于创建文件夹
    current_month = (utc_target_time - timedelta(days=1)).strftime("%Y%m")

    # 创建文件夹路径
    folder_path = f"data/positions/{current_month}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # 生成文件名
    file_name = f"{folder_path}/positions_{previous_day}.csv"

    # 保存数据到文件
    df_acc_pos_mini.to_csv(file_name, index=True)
    print(f"Positions data saved to {file_name}")


