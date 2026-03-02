import ccxt

# ===== 每天自动向手机发送账户净值和持仓数据的时间点（UTC Time）
report_schedule_utc = ['030000', '090000', '130000']             # '030000' means utc time 03:00:00

# =====交易所配置
# 如果使用代理 注意替换IP和Port
# proxy = {}
proxy = {'http': 'http://127.0.0.1:10081', 'https': 'http://127.0.0.1:10081'}  # new code for vilavpn
# proxy = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}  # flclash VPN setting
# 创建交易所
exchange = ccxt.binance({
    'apiKey': '',  # bn acc4,
    'secret': '',   # bn acc4,
    'timeout': 30000,                         # Xing's setting
    'rateLimit': 10,                          # Xing's setting
    'enableRateLimit': False,                  # Xing's setting
    'options': {
        'adjustForTimeDifference': True,      # Xing's setting
        'recvWindow': 10000,                  # Xing's setting
    },
    'proxies': proxy
})

# ===== 当账户金额小于设定值时，程序自动终止, 单位为USDT。
equity_min = 200

# 企业微信配置
WECHAT_CONFIG = {
    'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=96251ee3-fb29-4127-a641-0fa704fc2974',  #sub4
}