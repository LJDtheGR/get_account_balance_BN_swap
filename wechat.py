"""
Strategy F 净值监控程序 V1.1
"""
from datetime import datetime
from config import WECHAT_CONFIG
import json
import requests


def send_wechat_message(message):
    webhook_url = WECHAT_CONFIG['webhook_url']

    # 构造消息内容
    # 后续把这里换成想输出的内容
    data = {
        "msgtype": "text",
        "text": {
            "content": message + "\n" + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    # 发送 POST 请求
    headers = {'Content-Type': 'application/json'}
    response = requests.post(webhook_url, headers=headers, data=json.dumps(data))
    # 检查响应
    if response.status_code == 200:
        print('消息发送成功:', response.json())
    else:
        print('消息发送失败:', response.text)


def send_wechat_msg_for_position(equity, df_acc_pos_mini):
    """
    发送持仓信息到企业微信
    """
    message = '策略F，选币对冲策略，程序自动运行中。\n'
    message += f'账户净值： {equity:8.2f}\n'
    # print(message)

    if not df_acc_pos_mini.empty:
        message += f'持仓浮盈: {df_acc_pos_mini["unRealizedProfit"].sum():8.2f}\n'
        message += '策略持仓\n\n'
        for index, row in df_acc_pos_mini.reset_index().iterrows():
            message += row[['symbol', 'positionAmt', 'notional', 'entryPrice', 'unRealizedProfit']].to_string()
            message += '\n\n'

    # print(message)
    send_wechat_message(message)

