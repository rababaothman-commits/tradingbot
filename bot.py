from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import yfinance as yf
import asyncio

TOKEN = "8456213095:AAEJTfNQJ5ncz3h_DKeeECfcqGtnYJLLEz4"

PAIRS = {
    "GOLD":"GC=F","SILVER":"SI=F","NASDAQ":"NQ=F",
    "DOW_JONES":"YM=F","EURUSD":"EURUSD=X","USDJPY":"USDJPY=X",
    "GBPUSD":"GBPUSD=X","BITCOIN":"BTC-USD","OIL":"CL=F"
}

def get_data(pair):
    try:
        h = yf.Ticker(PAIRS[pair]).history(period="1mo",interval="1d")
        if h.empty: return None
        c = round(h['Close'].iloc[-1],2)
        hi = round(h['High'].max(),2)
        lo = round(h['Low'].min(),2)
        delta = h['Close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean().iloc[-1]
        loss = -delta.where(delta<0,0).rolling(14).mean().iloc[-1]
        rsi = 100.0 if loss==0 else round(100-(100/(1+gain/loss)),1)
        trend = "UP" if c>h['Close'].rolling(20).mean().iloc[-1] else "DOWN"
        piv = round((hi+lo+c)/3,2)
        r1=round(2*piv-lo,2); r2=round(piv+(hi-lo),2)
        s1=round(2*piv-hi,2); s2=round(piv-(hi-lo),2)
        if rsi<30: sig="BUY";entry=c;tp=round(c*1.005,2);sl=round(c*0.997,2)
        elif rsi>70: sig="SELL";entry=c;tp=round(c*0.995,2);sl=round(c*1.003,2)
        else: sig="WAIT";entry=tp=sl=None
        return {"c":c,"trend":trend,"rsi":rsi,"r1":r1,"r2":r2,"s1":s1,"s2":s2,"sig":sig,"entry":entry,"tp":tp,"sl":sl}
    except: return None

def kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("GOLD",callback_data="GOLD"),InlineKeyboardButton("SILVER",callback_data="SILVER")],
        [InlineKeyboardButton("NASDAQ",callback_data="NASDAQ"),InlineKeyboardButton("DOW JONES",callback_data="DOW_JONES")],
        [InlineKeyboardButton("EUR/USD",callback_data="EURUSD"),InlineKeyboardButton("USD/JPY",callback_data="USDJPY")],
        [InlineKeyboardButton("GBP/USD",callback_data="GBPUSD"),InlineKeyboardButton("BITCOIN",callback_data="BITCOIN")],
        [InlineKeyboardButton("OIL",callback_data="OIL")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Trading Bot - Choose pair:",reply_markup=kb())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    if q.data=="back":
        await q.edit_message_text("Trading Bot - Choose pair:",reply_markup=kb())
        return
    d=get_data(q.data)
    if not d:
        await q.edit_message_text("Error - try again")
        return
    msg=f"{q.data}\nPrice:{d['c']}\nTrend:{d['trend']}\nRSI:{d['rsi']}\nR1:{d['r1']} R2:{d['r2']}\nS1:{d['s1']} S2:{d['s2']}\nSignal:{d['sig']}"
    if d['entry']: msg+=f"\nEntry:{d['entry']} TP:{d['tp']} SL:{d['sl']}"
    await q.edit_message_text(msg,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back",callback_data="back")]]))

if _name_ == "_main_":
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot is running!")
    app.run_polling(drop_pending_updates=True)
