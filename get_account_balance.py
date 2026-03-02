"""
Strategy F 净值监控程序 V1.1
"""
import time
import traceback
import warnings
warnings.filterwarnings('ignore')
from config import *
from commons import *
from wechat import send_wechat_message
from position import get_balance_and_positions_bn
pd.set_option('display.max_rows', 1000)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.unicode.ambiguous_as_wide', True)  # 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.east_asian_width', True)


def run():
    while True:
        # ===sleep直到下一个整点小时
        target_time, utc_target_time, time_difference = sleep_until_run_time('1h', if_sleep=True, cheat_seconds=0)

        # ===获取U本位合约账户的最新净值与持仓
        df_acc_bal_mini, df_acc_pos_mini, equity = get_balance_and_positions_bn(exchange, equity_min, utc_target_time,
                                                                                report_schedule_utc)
        print('Local time:', datetime.now())
        # === things needed to do in the beginning of a new day
        print('utc_target_time: ', utc_target_time)
        if utc_target_time.strftime("%H%M%S") == '000000':
            print('A peaceful new day!')
            # === 保存权益每日的权益数据与持仓数据
            save_net_value(df_acc_bal_mini, utc_target_time)
            save_acc_pos_bn(df_acc_pos_mini, utc_target_time)
            print('Local time:', datetime.now())

        # 本次循环结束
        print('-' * 20, '本次循环结束，%f秒后进入下一次循环' % 20, '-' * 20)
        print('\n')
        time.sleep(20)


if __name__ == '__main__':
    send_wechat_message('策略F，权益记录程序，本地电脑，代码测试。')

    while True:
        try:
            run()
        except Exception as err:
            msg = '系统出错，10s之后重新运行，出错原因: ' + str(err)
            print(msg)
            print(traceback.format_exc())
            send_wechat_message(msg)
            time.sleep(10)

            # traceback.format_exc() is used to print the full traceback (error stack trace) as a string,
            # explained by GPT