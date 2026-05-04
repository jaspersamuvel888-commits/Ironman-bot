# â€œâ€â€
IRON MAN FREE ALERT BOT â€” CLOUD VERSION

Deploy on PythonAnywhere (free) for 24/7 alerts
Your phone gets Telegram alerts even when offline

SETUP:

1. Go to pythonanywhere.com â†’ free account
1. Open Bash console â†’ pip install yfinance pandas requests pytz â€“user
1. Upload this file â†’ fill TOKEN and CHAT_ID
1. Dashboard â†’ Tasks â†’ Always-on task â†’ run this file
1. Done. 24/7 alerts forever free.
   â€œâ€â€

import os
import time
import pytz
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# CREDENTIALS â€” fill these directly OR set

# as environment variables on Railway/Render

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

TELEGRAM_TOKEN   = os.environ.get(â€œTELEGRAM_TOKENâ€,   â€œ8469797335:AAET6kWid3eBwjqFph0_aHbSEV7foEfZYTMâ€)
TELEGRAM_CHAT_ID = os.environ.get(â€œTELEGRAM_CHAT_IDâ€, â€œ7849801313â€)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# BOT SETTINGS

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

MIN_SCORE      = 4
ATR_PERIOD     = 14
ATR_SL_MULT    = 1.5
RR_RATIO       = 2.0
EMA_HTF_PERIOD = 50
LONDON_OPEN    = 8
LONDON_CLOSE   = 12
NY_OPEN        = 13
NY_CLOSE       = 17
CHECK_INTERVAL = 60   # seconds between checks

# Update these monthly

BLOCKED_DATES = {
â€œ2026-06-06â€: â€œNFPâ€,
â€œ2026-07-04â€: â€œNFPâ€,
â€œ2026-06-11â€: â€œFOMCâ€,
â€œ2026-07-29â€: â€œFOMCâ€,
â€œ2026-06-10â€: â€œCPIâ€,
â€œ2026-07-15â€: â€œCPIâ€,
}

IST = pytz.timezone(â€œAsia/Kolkataâ€)
UTC = pytz.UTC

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# TELEGRAM

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def send_telegram(msg: str) -> bool:
try:
url  = fâ€https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessageâ€
data = {â€œchat_idâ€: TELEGRAM_CHAT_ID, â€œtextâ€: msg, â€œparse_modeâ€: â€œHTMLâ€}
r    = requests.post(url, json=data, timeout=10)
return r.status_code == 200
except Exception as e:
print(fâ€Telegram error: {e}â€)
return False

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# SESSION CHECK

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def get_session() -> dict:
now_utc  = datetime.now(UTC)
now_ist  = now_utc.astimezone(IST)
h        = now_utc.hour

```
in_london   = LONDON_OPEN <= h < LONDON_CLOSE
in_ny       = NY_OPEN     <= h < NY_CLOSE
in_kz       = in_london or in_ny

return {
    "in_london":    in_london,
    "in_ny":        in_ny,
    "in_killzone":  in_kz,
    "name":         "London" if in_london else "New York" if in_ny else "Closed",
    "ist_str":      now_ist.strftime("%I:%M %p IST"),
    "today":        now_utc.strftime("%Y-%m-%d"),
    "ist_hour":     now_ist.hour,
    "ist_minute":   now_ist.minute,
}
```

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# FETCH DATA

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def fetch_data() -> pd.DataFrame | None:
try:
df = yf.Ticker(â€œGC=Fâ€).history(period=â€œ5dâ€, interval=â€œ1hâ€)
if df.empty or len(df) < 15:
return None
df.index = pd.to_datetime(df.index, utc=True)
return df
except Exception as e:
print(fâ€Data error: {e}â€)
return None

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# ATR

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def calc_atr(df: pd.DataFrame) -> float:
h, l, c = df[â€œHighâ€], df[â€œLowâ€], df[â€œCloseâ€]
tr = pd.concat([h-l, abs(h-c.shift(1)), abs(l-c.shift(1))], axis=1).max(axis=1)
return float(tr.rolling(ATR_PERIOD).mean().iloc[-1])

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# HTF TREND

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def calc_trend(df: pd.DataFrame) -> dict:
df4 = df.resample(â€œ4hâ€).agg({â€œOpenâ€:â€œfirstâ€,â€œHighâ€:â€œmaxâ€,â€œLowâ€:â€œminâ€,â€œCloseâ€:â€œlastâ€}).dropna()
src  = df4[â€œCloseâ€] if len(df4) >= EMA_HTF_PERIOD else df[â€œCloseâ€]
ema  = src.ewm(span=EMA_HTF_PERIOD, adjust=False).mean()
last = float(src.iloc[-1])
ema_val = float(ema.iloc[-1])
return {â€œbullâ€: last > ema_val, â€œbearâ€: last < ema_val, â€œemaâ€: ema_val, â€œcloseâ€: last}

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# CONFLUENCE ENGINE (6 conditions each side)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def score(df: pd.DataFrame, session: dict, atr: float, trend: dict) -> dict:
c0,o0,h0,l0 = df[â€œCloseâ€].iloc[-1], df[â€œOpenâ€].iloc[-1], df[â€œHighâ€].iloc[-1], df[â€œLowâ€].iloc[-1]
c1,o1,h1,l1 = df[â€œCloseâ€].iloc[-2], df[â€œOpenâ€].iloc[-2], df[â€œHighâ€].iloc[-2], df[â€œLowâ€].iloc[-2]
h2,l2       = df[â€œHighâ€].iloc[-3],  df[â€œLowâ€].iloc[-3]

```
bull = trend["bull"]
bear = trend["bear"]
kz   = session["in_killzone"]

# Long
ob_bull = (c1<o1) and (c0>o0) and ((c0-o0)>atr*0.7)
sh      = float(df["High"].iloc[-6:-1].max())
l = {
    "HTF":   bull,
    "KZ":    kz,
    "OB":    ob_bull and (l0<=h1) and (l0>=l1),
    "Sweep": (l0<l1) and (c0>l1),
    "BOS":   (sh>0) and (c0>sh),
    "FVG":   (l0>h2) and ((l0-h2)>=0.5),
}

# Short
ob_bear = (c1>o1) and (c0<o0) and ((o0-c0)>atr*0.7)
sl_     = float(df["Low"].iloc[-6:-1].min())
s = {
    "HTF":   bear,
    "KZ":    kz,
    "OB":    ob_bear and (h0>=l1) and (h0<=h1),
    "Sweep": (h0>h1) and (c0<h1),
    "BOS":   (sl_>0) and (c0<sl_),
    "FVG":   (h0<l2) and ((l2-h0)>=0.5),
}

ls = sum(l.values())
ss = sum(s.values())

return {
    "long_score":  ls,
    "short_score": ss,
    "long_conds":  l,
    "short_conds": s,
    "price":       c0,
    "sl_l": round(c0 - atr*ATR_SL_MULT, 2),
    "tp_l": round(c0 + atr*ATR_SL_MULT*RR_RATIO, 2),
    "sl_s": round(c0 + atr*ATR_SL_MULT, 2),
    "tp_s": round(c0 - atr*ATR_SL_MULT*RR_RATIO, 2),
}
```

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# FORMAT ALERT MESSAGE

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def make_msg(direction: str, r: dict, session: dict, sc: int) -> str:
if direction == â€œLONGâ€:
sl, tp, emoji, conds = r[â€œsl_lâ€], r[â€œtp_lâ€], â€œðŸš€â€, r[â€œlong_condsâ€]
else:
sl, tp, emoji, conds = r[â€œsl_sâ€], r[â€œtp_sâ€], â€œðŸ”»â€, r[â€œshort_condsâ€]

```
p       = r["price"]
active  = [k for k,v in conds.items() if v]
inactive= [k for k,v in conds.items() if not v]

return (
    f"{emoji} <b>IRON MAN {direction}</b>\n\n"
    f"ðŸ“Š <b>XAUUSD</b>  |  Score: <b>{sc}/6</b>\n"
    f"ðŸ• {session['name']} Kill Zone\n"
    f"â° {session['ist_str']}\n\n"
    f"Entry : <b>{p:.2f}</b>\n"
    f"SL    : <b>{sl:.2f}</b>  (risk: {abs(p-sl):.1f} pts)\n"
    f"TP    : <b>{tp:.2f}</b>  (gain: {abs(tp-p):.1f} pts)\n"
    f"RR    : 1:{RR_RATIO}\n\n"
    f"âœ… {' | '.join(active)}\n"
    f"âŒ {' | '.join(inactive) if inactive else 'None'}"
)
```

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# ALERT COOLDOWN STATE

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

last_alert_dir  = None
last_alert_time = 0
eco_warned_today = None

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# MAIN LOOP

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def main():
print(â€œIRON MAN CLOUD BOT STARTINGâ€¦â€)
send_telegram(
â€œâš™ï¸ <b>Iron Man Bot Online</b>\nâ€
â€œMonitoring XAUUSD 24/7\nâ€
fâ€Kill Zones:\nâ€
fâ€  London: 1:30â€“5:30 PM IST\nâ€
fâ€  New York: 6:30â€“10:30 PM IST\nâ€
fâ€Min score: {MIN_SCORE}/6 | RR: 1:{RR_RATIO}â€
)

```
global last_alert_dir, last_alert_time, eco_warned_today
errors = 0

while True:
    try:
        sess = get_session()
        today = sess["today"]

        # â”€â”€ Daily heartbeat at 9:00 AM IST â”€â”€
        if sess["ist_hour"] == 9 and sess["ist_minute"] == 0:
            send_telegram(
                f"â˜€ï¸ <b>Iron Man Bot â€” Daily Check</b>\n"
                f"Date: {today}\n"
                f"Status: Running 24/7 âœ…\n"
                f"London KZ starts: 1:30 PM IST\n"
                f"NY KZ starts: 6:30 PM IST"
            )
            time.sleep(70)  # avoid duplicate at 9:00
            continue

        # â”€â”€ Eco block â”€â”€
        eco = BLOCKED_DATES.get(today)
        if eco:
            if eco_warned_today != today:
                eco_warned_today = today
                send_telegram(f"âš ï¸ <b>{eco} DAY</b> â€” All signals paused today.\nNo trades. Stay safe.")
            print(f"  ECO BLOCK: {eco}")
            time.sleep(CHECK_INTERVAL * 10)
            continue

        # â”€â”€ Fetch & analyse â”€â”€
        df = fetch_data()
        if df is None:
            errors += 1
            if errors > 10:
                send_telegram("âš ï¸ Bot: Data fetch failing repeatedly. Check status.")
                errors = 0
            time.sleep(CHECK_INTERVAL)
            continue

        errors  = 0
        atr     = calc_atr(df)
        trend   = calc_trend(df)
        result  = score(df, sess, atr, trend)
        ls      = result["long_score"]
        ss      = result["short_score"]
        price   = result["price"]

        print(f"[{sess['ist_str']}] {sess['name']} | KZ:{sess['in_killzone']} | "
              f"Price:{price:.2f} | L:{ls}/6 S:{ss}/6 | "
              f"Trend:{'BULL' if trend['bull'] else 'BEAR'}")

        now = time.time()
        cooldown_ok = (now - last_alert_time) > 3600  # 1 hour between same direction

        if ls >= MIN_SCORE and sess["in_killzone"]:
            if last_alert_dir != "LONG" or cooldown_ok:
                send_telegram(make_msg("LONG", result, sess, ls))
                last_alert_dir  = "LONG"
                last_alert_time = now
                print("  >>> LONG ALERT SENT")

        elif ss >= MIN_SCORE and sess["in_killzone"]:
            if last_alert_dir != "SHORT" or cooldown_ok:
                send_telegram(make_msg("SHORT", result, sess, ss))
                last_alert_dir  = "SHORT"
                last_alert_time = now
                print("  >>> SHORT ALERT SENT")

        time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("Bot stopped.")
        send_telegram("âš™ï¸ Iron Man Bot stopped manually.")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(CHECK_INTERVAL)
```

if **name** == â€œ**main**â€:
main()
