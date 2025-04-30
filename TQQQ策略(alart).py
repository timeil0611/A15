import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.lib import resample_apply

from backtesting.test import SMA, GOOG

import yfinance as yf

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


    
# 下載歷史數據
df = yf.download('QQQ',start='2013-08-20')

# 移除 Ticker 層級
qqq = df.copy()
qqq.columns = qqq.columns.droplevel('Ticker')



class TQQQ(Strategy):

    def init(self):
        self.w_qqq_sma = resample_apply(
                    'W', SMA, self.data.Close, 8, plot=True)
    def send_email(self, subject, body):
        # Gmail 設定
        sender_email = "timeil0611@gmail.com"  # 你的 Gmail 地址
        receiver_email = "timeil0611@gmail.com"  # 接收者的郵件地址
        app_password = "rkeq myzl lqvq efdb"  # Google 應用程式專用密碼

        # 建立郵件
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        # 郵件內容
        message.attach(MIMEText(body, "plain"))

        try:
            # 連線到 Gmail 的 SMTP 伺服器
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()  # 啟用 TLS 加密
            server.login(sender_email, app_password)  # 登入
            server.sendmail(sender_email, receiver_email, message.as_string())  # 發送郵件
            server.quit()  # 關閉連線
            print(f"Email sent successfully: {subject}")
        except Exception as e:
            print(f"Failed to send email: {e}")
    def next(self):
        # 當前qqq價格
        qqq_current_price = self.data.Close[-1]
        # 獲取過去 80 天的最高價
        qqq_highest_high = self.data.Close[-80:].max()
        # print(self.data.index[-1],"close",self.data.Close[-1])
        # print(self.data.index[-1],"qqq_highest_high",qqq_highest_high)
        
        #賣的條件
        if (
            (
            (self.data.index[-1].month==9)
            or
            ((self.data.index[-1].month==8)and(self.data.index[-1].day==31))
            or
            (qqq_current_price <= 0.88 * qqq_highest_high)
            )
            and (self.position.is_long)):
            print(f"SELL ALERT: {self.data.index[-1]} - Closing position due to sell condition.")
            # 發送賣出提醒郵件
            self.send_email(
                subject="SELL ALERT: TQQQ",
                body=f"SELL ALERT at {self.data.index[-1]}: QQQ price = {qqq_current_price:.2f}, closed position due to sell condition."
            )
            self.position.close()
            
        # 買的策略
        if (
            not(
            (self.data.index[-1].month==9)
                or(
                    (self.data.index[-1].month==8)
                    and(self.data.index[-1].day==31)
                )
                or (qqq_current_price <= 0.88 * qqq_highest_high)
            )

            
            and
            (self.w_qqq_sma[-1] - self.w_qqq_sma[-2] > 0)
            and
            (not self.position)
            
        ):
            print(f"BUY ALERT: {self.data.index[-1]} - Initiating buy due to buy condition.")
            # 發送買入提醒郵件
            self.send_email(
                subject="BUY ALERT: TQQQ",
                body=f"BUY ALERT at {self.data.index[-1]}: QQQ price = {qqq_current_price:.2f}, initiated buy due to buy condition."
            )
            self.buy()


bt = Backtest(qqq, TQQQ,
              cash=10000, commission=.002,
              exclusive_orders=True)

output = bt.run()
bt.plot()