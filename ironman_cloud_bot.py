import os
import time
import pytz
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8469797335:AAET6kWid3eBwjqFph0_aHbSEV7TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7849801313")
MIN_SCORE = 4
ATR_PERIOD = 14
ATR_SL_MULT = 1.5
RR_RATIO = 2.0
EMA_HTF_PERIOD = 50
LONDON_OPEN = 8
LONDON_CLOSE = 12
NY_OPEN = 13
NY_CLOSE = 17
CHECK_INTERVAL = 60
BLOCKED_DATES = {
 "2026-06-06": "NFP",
 "2026-07-04": "NFP",
 "2026-06-11": "FOMC",
 "2026-07-29": "FOMC",
 "2026-06-10": "CPI",
 "2026-07-15": "CPI",
}
IST = pytz.timezone("Asia/Kolkata")
UTC = pytz.UTC
def send_telegram(msg):
 try:
 url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
 data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
 r = requests.post(url, json=data, timeout=10)
 return r.status_code == 200
 except Exception as e:
 print("Telegram error: " + str(e))
 return False
def get_session():
 now_utc = datetime.now(UTC)
 now_ist = now_utc.astimezone(IST)
 h = now_utc.hour
 in_london = LONDON_OPEN <= h < LONDON_CLOSE
 in_ny = NY_OPEN <= h < NY_CLOSE
 in_kz = in_london or in_ny
 return {
 "in_london": in_london,
 "in_ny": in_ny,
 "in_killzone": in_kz,
 "name": "London" if in_london else "New York" if in_ny else "Closed",
 "ist_str": now_ist.strftime("%I:%M %p IST"),
 "today": now_utc.strftime("%Y-%m-%d"),
 "ist_hour": now_ist.hour,
 "ist_minute": now_ist.minute,
 }
def fetch_data():
 try:
 df = yf.Ticker("GC=F").history(period="5d", interval="1h")
 if df.empty or len(df) < 15:
 return None
 df.index = pd.to_datetime(df.index, utc=True)
 return df
 except Exception as e:
 print("Data error: " + str(e))
 return None
def calc_atr(df):
 h = df["High"]
 l = df["Low"]
 c = df["Close"]
 tr = pd.concat([h - l, abs(h - c.shift(1)), abs(l - c.shift(1))], axis=1).max(axis=1)
 return float(tr.rolling(ATR_PERIOD).mean().iloc[-1])
def calc_trend(df):
 df4 = df.resample("4h").agg({
 "Open": "first",
 "High": "max",
 "Low": "min",
 "Close": "last"
 }).dropna()
 src = df4["Close"] if len(df4) >= EMA_HTF_PERIOD else df["Close"]
 ema = src.ewm(span=EMA_HTF_PERIOD, adjust=False).mean()
 last = float(src.iloc[-1])
 ema_val = float(ema.iloc[-1])
 return {"bull": last > ema_val, "bear": last < ema_val, "close": last}
def score(df, session, atr, trend):
 c0 = df["Close"].iloc[-1]
 o0 = df["Open"].iloc[-1]
 h0 = df["High"].iloc[-1]
 l0 = df["Low"].iloc[-1]
 c1 = df["Close"].iloc[-2]
 o1 = df["Open"].iloc[-2]
 h1 = df["High"].iloc[-2]
 l1 = df["Low"].iloc[-2]
 h2 = df["High"].iloc[-3]
 l2 = df["Low"].iloc[-3]
 bull = trend["bull"]
 bear = trend["bear"]
 kz = session["in_killzone"]
 ob_bull = (c1 < o1) and (c0 > o0) and ((c0 - o0) > atr * 0.7)
 sh = float(df["High"].iloc[-6:-1].max())
 l = {
 "HTF": bull,
 "KZ": kz,
 "OB": ob_bull and (l0 <= h1) and (l0 >= l1),
 "Sweep": (l0 < l1) and (c0 > l1),
 "BOS": (sh > 0) and (c0 > sh),
 "FVG": (l0 > h2) and ((l0 - h2) >= 0.5),
 }
 ob_bear = (c1 > o1) and (c0 < o0) and ((o0 - c0) > atr * 0.7)
 sl_ = float(df["Low"].iloc[-6:-1].min())
 s = {
 "HTF": bear,
 "KZ": kz,
 "OB": ob_bear and (h0 >= l1) and (h0 <= h1),
 "Sweep": (h0 > h1) and (c0 < h1),
 "BOS": (sl_ > 0) and (c0 < sl_),
 "FVG": (h0 < l2) and ((l2 - h0) >= 0.5),
 }
 ls = sum(l.values())
 ss = sum(s.values())
 return {
 "long_score": ls,
 "short_score": ss,
 "long_conds": l,
 "short_conds": s,
 "price": c0,
 "sl_l": round(c0 - atr * ATR_SL_MULT, 2),
 "tp_l": round(c0 + atr * ATR_SL_MULT * RR_RATIO, 2),
 "sl_s": round(c0 + atr * ATR_SL_MULT, 2),
 "tp_s": round(c0 - atr * ATR_SL_MULT * RR_RATIO, 2),
 }
def make_msg(direction, r, session, sc):
 if direction == "LONG":
 sl = r["sl_l"]
 tp = r["tp_l"]
 conds = r["long_conds"]
 else:
 sl = r["sl_s"]
 tp = r["tp_s"]
 conds = r["short_conds"]
 p = r["price"]
 active = [k for k, v in conds.items() if v]
 inactive = [k for k, v in conds.items() if not v]
 return (
 "<b>IRON MAN " + direction + " SIGNAL</b>\n\n"
 "<b>XAUUSD</b> Score: <b>" + str(sc) + "/6</b>\n"
 "Session : " + session["name"] + " Kill Zone\n"
 "Time : " + session["ist_str"] + "\n\n"
 "Entry : <b>" + str(round(p, 2)) + "</b>\n"
 "SL : <b>" + str(sl) + "</b> (" + str(round(abs(p - sl), 1)) + " pts)\n"
 "TP : <b>" + str(tp) + "</b> (" + str(round(abs(tp - p), 1)) + " pts)\n"
 "RR : 1:" + str(RR_RATIO) + "\n\n"
 "Active : " + " | ".join(active) + "\n"
 "Inactive : " + (" | ".join(inactive) if inactive else "None")
 )
last_alert_dir = None
last_alert_time = 0
eco_warned_today = None
def main():
 print("IRON MAN CLOUD BOT STARTING")
 send_telegram(
 "<b>Iron Man Bot Online</b>\n"
 "Monitoring XAUUSD 24/7\n"
 "London KZ : 1:30 PM - 5:30 PM IST\n"
 "New York KZ: 6:30 PM - 10:30 PM IST\n"
 "Min score: " + str(MIN_SCORE) + "/6 RR: 1:" + str(RR_RATIO)
 )
 global last_alert_dir, last_alert_time, eco_warned_today
 errors = 0
 while True:
 try:
 sess = get_session()
 today = sess["today"]
 if sess["ist_hour"] == 9 and sess["ist_minute"] == 0:
 send_telegram(
 "<b>Iron Man - Daily Check</b>\n"
 "Date: " + today + "\n"
 "Status: Running OK\n"
 "London KZ : 1:30 PM IST\n"
 "New York KZ: 6:30 PM IST"
 )
 time.sleep(70)
 continue
 eco = BLOCKED_DATES.get(today)
 if eco:
 if eco_warned_today != today:
 eco_warned_today = today
 send_telegram("<b>" + eco + " DAY</b>\nAll signals paused. No trades toda print("ECO BLOCK: " + eco)
 time.sleep(CHECK_INTERVAL * 10)
 continue
 df = fetch_data()
 if df is None:
 errors += 1
 if errors > 10:
 send_telegram("Iron Man Bot: Data fetch failing. Check internet.")
 errors = 0
 time.sleep(CHECK_INTERVAL)
 continue
 errors = 0
 atr = calc_atr(df)
 trend = calc_trend(df)
 result = score(df, sess, atr, trend)
 ls = result["long_score"]
 ss = result["short_score"]
 price = result["price"]
 print(
 "[" + sess["ist_str"] + "] " + sess["name"]
 + " KZ:" + str(sess["in_killzone"])
 + " Price:" + str(round(price, 2))
 + " L:" + str(ls) + "/6 S:" + str(ss) + "/6"
 + " Trend:" + ("BULL" if trend["bull"] else "BEAR")
 )
 now = time.time()
 cooldown_ok = (now - last_alert_time) > 3600
 if ls >= MIN_SCORE and sess["in_killzone"]:
 if last_alert_dir != "LONG" or cooldown_ok:
 send_telegram(make_msg("LONG", result, sess, ls))
 last_alert_dir = "LONG"
 last_alert_time = now
 print("LONG ALERT SENT")
 elif ss >= MIN_SCORE and sess["in_killzone"]:
 if last_alert_dir != "SHORT" or cooldown_ok:
 send_telegram(make_msg("SHORT", result, sess, ss))
 last_alert_dir = "SHORT"
 last_alert_time = now
 print("SHORT ALERT SENT")
 else:
 print("WAIT - score low or outside Kill Zone")
 time.sleep(CHECK_INTERVAL)
 except KeyboardInterrupt:
 print("Bot stopped.")
 send_telegram("Iron Man Bot stopped.")
 break
 except Exception as e:
 print("Error: " + str(e))
 time.sleep(CHECK_INTERVAL)
if __name__ == "__main__":
 main()
