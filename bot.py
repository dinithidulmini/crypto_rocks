from binance.client import Client
import threading
from tradingview_ta import TA_Handler, Interval, Exchange
from numerize import numerize
from discord import SyncWebhook
from datetime import datetime
import psycopg2
from emoji import emojize

#establishing the connection
conn = psycopg2.connect(
   database="gpu", user='postgres', password='postgres', host='127.0.0.1', port= '5432')

# Creating a cursor object using the cursor() method
cursor = conn.cursor()

# Executing an MYSQL function using the execute() method
cursor.execute("select version()")

# Fetch a single row using fetchone() method.
data = cursor.fetchone()

client = Client()

blue_circle = emojize(":blue_circle:")
red_circle = emojize(":red_circle:")
fire = emojize(":fire:")


def send_discord(symbol,percentage_change,current_price,now_price,position_type):
    if percentage_change > 0:
        percentage = f"+{round(percentage_change, 5)}%"
    else:
        percentage = f"{round(percentage_change, 5)}%"

    print(f"HIT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ({symbol}) ")
    print(f"{symbol} : Price increased by {percentage}\nInitial price = {current_price}\nPrice now = {now_price}")

    binance_ticker_info = client.futures_ticker(symbol=symbol)
    daily_volume = float(binance_ticker_info["volume"])
    volume_in_usdt = daily_volume * now_price
    daily_volume_millions = numerize.numerize(volume_in_usdt)
    vol_for_message = f"${daily_volume_millions}"
    print(f"Daily volume in millions = {daily_volume_millions}")

    symbol_tv = f"{symbol}PERP"
    sol_handler = TA_Handler(symbol=symbol_tv, screener="Crypto", exchange="Binance",
                             interval=Interval.INTERVAL_5_MINUTES)
    sol_indicators = sol_handler.get_indicators()
    bb_upper = float(sol_indicators["BB.upper"])
    bb_lower = float(sol_indicators["BB.lower"])
    if now_price > bb_upper:
        bb_value = "SELL"
    elif now_price < bb_lower:
        bb_value = "BUY"
    else:
        bb_value = "NEUTRAL"
    rsi = float(sol_indicators["RSI"])

    klines_percentage_change = client.futures_klines(symbol=symbol, interval="1m", limit=60)

    open_price_one_hr = float(klines_percentage_change[0][1])
    open_price_thirty_mins = float(klines_percentage_change[-30][1])
    open_price_ten_mins = float(klines_percentage_change[-10][1])
    close_price = float(klines_percentage_change[-1][4])

    percentage_change_one_hr = ((close_price - open_price_one_hr) / open_price_one_hr) * 100
    percentage_for_message_1hr = f"{round(percentage_change_one_hr, 2)}%"
    percentage_change_thirty_mins = ((close_price - open_price_thirty_mins) / open_price_thirty_mins) * 100
    percentage_for_message_30mins = f"{round(percentage_change_thirty_mins, 2)}%"
    percentage_change_ten_mins = ((close_price - open_price_ten_mins) / open_price_ten_mins) * 100
    percentage_for_message_10mins = f"{round(percentage_change_ten_mins, 2)}%"

    if position_type == "LONG":
        circle = blue_circle
    if position_type == "SHORT":
        circle = red_circle

    if rsi > 70:
        discord_message = f"\n=====================\n{circle} {position_type} : {symbol} {circle}\n=====================\n\nPrice ${round(now_price, 4)} ({percentage})\n\nRSI 5m: {round(rsi, 2)} {fire}OVERBOUGHT{fire}\nBB 5m: \u2757{bb_value}\u2757\nVOL: {vol_for_message}\n\nVAR. 1hr: {percentage_for_message_1hr}\nVAR. 30m: {percentage_for_message_30mins}\nVAR. 10m: {percentage_for_message_10mins}"
        print(discord_message)
    elif rsi < 30:
        discord_message = f"\n=====================\n{circle} {position_type} : {symbol} {circle}\n=====================\n\nPrice ${round(now_price, 4)} ({percentage})\n\nRSI 5m: {round(rsi, 2)} {fire}OVERSOLD{fire}\nBB 5m: \u2757{bb_value}\u2757\nVOL: {vol_for_message}\n\nVAR. 1hr: {percentage_for_message_1hr}\nVAR. 30m: {percentage_for_message_30mins}\nVAR. 10m: {percentage_for_message_10mins}"
        print(discord_message)
    else:
        discord_message = f"\n=====================\n{circle} {position_type} : {symbol} {circle}\n=====================\n\nPrice ${round(now_price, 4)} ({percentage})\n\nRSI 5m: {round(rsi, 2)}\nBB 5m: \u2757{bb_value}\u2757\nVOL: {vol_for_message}\n\nVAR. 1hr: {percentage_for_message_1hr}\nVAR. 30m: {percentage_for_message_30mins}\nVAR. 10m: {percentage_for_message_10mins}"
        print(discord_message)


    webhook = SyncWebhook.from_url(
        "https://discordapp.com/api/webhooks/1045410061960364132/rW-QCqn_qCkZKUsLVfvhCe5nUbI_D9YCPVXUDCTGn-LnNtvbXtsLyD23_fgzvz6W6cbu")
    webhook.send(discord_message)


def start_bot():
    print("Starting...")

    sql = ''' DELETE FROM crypto_rocks_table '''
    cursor.execute(sql)
    conn.commit()

    exchange_info = client.futures_exchange_info()
    symbol_details = exchange_info["symbols"]
    # print(symbol_details)

    list_of_all_futures_symbols = []
    for symbol in symbol_details:
        if symbol["contractType"] == "PERPETUAL" and symbol["quoteAsset"] == "USDT" and symbol["status"] == "TRADING":
            pair_name = symbol["symbol"]
            list_of_all_futures_symbols.append(pair_name)

    # print(list_of_all_futures_symbols)

    initial_price_list = client.futures_symbol_ticker()
    print(initial_price_list)

    for symbol in list_of_all_futures_symbols:
        for pair in initial_price_list:
            if symbol == pair["symbol"]:
                current_price = float(pair["price"])
                cursor.execute("insert into crypto_rocks_table(symbol, current_price) values (%s, %s)",
                               [symbol, current_price])
                conn.commit()

    while True:
        now_price_list = client.futures_symbol_ticker()
        # print(now_price_list)
        for symbol in list_of_all_futures_symbols:
            cursor.execute("select current_price from crypto_rocks_table where symbol = %s", [symbol])
            r_3 = cursor.fetchall()
            current_price = float(r_3[0][0])

            current_plus_five = (current_price * 105) / 100
            # print(f"Current price plus ({symbol}) = {current_plus_five}")
            current_minus_five = (current_price * 95) / 100
            # print(f"Current price minus ({symbol}) = {current_minus_five}")
            for pair in now_price_list:
                if symbol == pair["symbol"]:
                    now_price = float(pair["price"])
                    if now_price >= current_plus_five:
                        percentage_change = ((now_price - current_price) / current_price) * 100
                        if percentage_change < 10:
                            cursor.execute("update crypto_rocks_table set current_price = %s where symbol = %s",
                                           [now_price, symbol])
                            conn.commit()
                            t2 = threading.Thread(
                                target=lambda: send_discord(symbol=symbol, percentage_change=percentage_change,
                                                            current_price=current_price, now_price=now_price,
                                                            position_type="SHORT"))
                            t2.start()

                    if now_price <= current_minus_five:
                        percentage_change = ((now_price - current_price) / current_price) * 100
                        if percentage_change > -10:
                            cursor.execute("update crypto_rocks_table set current_price = %s where symbol = %s",
                                           [now_price, symbol])
                            conn.commit()
                            t3 = threading.Thread(
                                target=lambda: send_discord(symbol=symbol, percentage_change=percentage_change,
                                                            current_price=current_price, now_price=now_price,
                                                            position_type="LONG"))
                            t3.start()


while True:
    utc_time = datetime.utcnow().hour
    spain_time = utc_time + 1
    if spain_time == 2:
        start_bot()
        break









