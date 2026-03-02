"""
Strategy C mamacita ver0.8
"""
import pandas as pd
from commons import retry_wrapper
from wechat import send_wechat_msg_for_position


def get_balance_and_positions_bn(exchange, equity_min, utc_target_time, report_schedule_utc):
    """
    I updated the fapi function below. because the version as well as the spelling of the function was outdated.
    Unlike V2, the 'positions' part of the data of V3GetAccount does not contain the coins that are not held,
    thus the data is more efficient.

    For the equity, Mr.Xing used walletBalance as equity, which did not contain unrealizedProfit;
    While I prefer to use marginBalance as equity.
    marginBalance = (walletBalance + unrealizedProfit)
    """
    # ===获取账户净值
    df_acc_bal_mini = get_balance_bn(exchange)

    # ===获取账户的实际持仓
    df_acc_pos_mini = get_position_bn(exchange)

    # ===to generate the data of position value, exposure value, as well as their ratios
    if not df_acc_pos_mini.empty:
        total_pos_value = round(df_acc_pos_mini['notional'].astype(float).abs().sum(), 4)
        exposure_pos_value = round(df_acc_pos_mini['notional'].astype(float).sum(), 4)
    else:
        total_pos_value = 0
        exposure_pos_value = 0

    df_acc_bal_mini['total_pos_value'] = total_pos_value
    df_acc_bal_mini['exposure_pos_value'] = exposure_pos_value

    df_acc_bal_mini['total_pos_value_ratio'] = round(
        df_acc_bal_mini['total_pos_value'][0] / df_acc_bal_mini['marginBalance'][0], 4)
    df_acc_bal_mini['exposure_pos_value_ratio'] = round(
        df_acc_bal_mini['exposure_pos_value'][0] / df_acc_bal_mini['marginBalance'][0],
        4)

    # ===marginBalance = (walletBalance + unrealizedProfit)
    equity = float(df_acc_bal_mini.loc[0, 'marginBalance'])

    print('账户最新权益:\n', df_acc_bal_mini)
    print('账户最新持仓:\n', df_acc_pos_mini)
    print('账户金额:', equity)

    # === stop the program if the equity is below the amount that we set in config.
    if equity <= equity_min:
        print(f'账户USDT权益小于预设的最小值{equity_min}， 无法进行交易，退出程序')
        exit()

    # ===发送wechat_message, according to the schedule
    if utc_target_time.strftime("%H%M%S") in report_schedule_utc:
        send_wechat_msg_for_position(equity, df_acc_pos_mini)

    return df_acc_bal_mini, df_acc_pos_mini, equity


def get_balance_bn(exchange):
    """
    I updated the fapi function below. because the version as well as the spelling of the function was outdated.
    Unlike V2, the 'positions' part of the data of V3GetAccount does not contain the coins that are not held,
    thus the data is more efficient
    """
    account_info = retry_wrapper(exchange.fapiPrivateV3GetAccount, func_name='fapiPrivateV3GetAccount')
    df_acc_bal = pd.DataFrame(account_info['assets'])

    # only remain the data of asset using 'USDT' as margin
    df_acc_bal = df_acc_bal[df_acc_bal['asset'] == 'USDT']
    df_acc_bal.reset_index(drop=True, inplace=True)

    # drop some cols to make the df easier to read
    df_acc_bal_mini = df_acc_bal[['asset', 'marginBalance', 'walletBalance', 'unrealizedProfit', 'availableBalance', 'initialMargin']]
    # convert the elements in the df from str to numeric
    df_acc_bal_mini.iloc[0, 1:6] = df_acc_bal_mini.iloc[0, 1:6].astype(float)

    # even though I have convert the numbers in df_acc_bal_mini into float in the previous step,...
    # ..., if without the .astype(float) part in the line below, it returns an error.
    df_acc_bal_mini.iloc[0, 2:6] = df_acc_bal_mini.iloc[0, 2:6].astype(float).round(4)
    # print(df_acc_bal_mini)

    return df_acc_bal_mini


# =====获取持仓
# 获取币安账户的实际持仓
def get_position_bn(exchange):
    """
    获取币安账户的实际持仓

    :param exchange:        交易所对象，用于获取数据
    :return:

              当前持仓量   均价  持仓盈亏
    symbol
    RUNEUSDT       -82.0  1.208 -0.328000
    FTMUSDT        523.0  0.189  1.208156

    I updated the fapi function below. because the version as well as the spelling of the function was outdated.
    """
    # === 获取原始数据
    positions_data = retry_wrapper(exchange.fapiPrivateV3GetPositionRisk, func_name='fapiPrivateV3GetAccount')
    if positions_data:
        df_acc_pos = pd.DataFrame(positions_data)    # 将原始数据转化为dataframe

        # to generate a col of position direction
        df_acc_pos.loc[df_acc_pos['positionAmt'].astype(float) > 0, 'pos_direction'] = 1
        df_acc_pos.loc[df_acc_pos['positionAmt'].astype(float) < 0, 'pos_direction'] = -1

        # keep only the necessary cols
        df_acc_pos_mini = df_acc_pos[['symbol', 'marginAsset', 'pos_direction', 'positionAmt', 'notional',
                                      'entryPrice', 'initialMargin', 'markPrice', 'unRealizedProfit']]
        df_acc_pos_mini.set_index('symbol', inplace=True)

        # convert the elements to numeric, and round some of the numbers
        df_acc_pos_mini.iloc[:, 1:8] = df_acc_pos_mini.iloc[:, 1:8].astype(float)
        df_acc_pos_mini.iloc[:, 3:8] = df_acc_pos_mini.iloc[:, 3:8].astype(float).round(4)
        # print(df_acc_pos_mini.dtypes)
        # exit()
    else:
        df_acc_pos_mini = pd.DataFrame()

    return df_acc_pos_mini
