import requests as r
from datetime import datetime
import telebot

# tokens
mpstats_api_token = ""
telegram_bot_token = ""

cur_date = str(datetime.now())[0:10]


def last_day_maker(data):
    lday = str(int(data[8:10]) - 1)
    last_day = cur_date[0:8] + lday
    return last_day


last_day = last_day_maker(cur_date)

mpstats_api = {
    'X-Mpstats-TOKEN': mpstats_api_token,
    'Content-Type': 'application/json'
  }

wb_id = '27860309'
date1 = '2021-10-23'
date2 = last_day

sell_summ = 0
cum_sum = 0
balance = 0

print(f"""Смотрим сводку по артикулу {wb_id} через API MPStats!
""")

for i in range(7):

    sku = r.get(f'https://mpstats.io/api/wb/get/item/{wb_id}/sales?d1={last_day}&d2={last_day}&fbs=1',
                   headers=mpstats_api)

    if sku.status_code == 200:
        pass
    elif sku.status_code == 500:
        print(f"WB ID not found, please try later")
        exit()
    else:
        print(f"Error {sku.status_code}, please try later")
        exit()

    result = sku.json()
    # print(result)

    print(f'За {result[0]["data"]} было продано {result[0]["sales"]}шт')
    sell_summ = sell_summ + int(result[0]['sales'])
    cum_sum = cum_sum + (int(result[0]['sales']) * int(result[0]['client_price']))

    if balance == 0:
        balance = balance + int(result[0]['balance'])
    else:
        pass

    last_day = last_day_maker(last_day)

med_sales = (sell_summ / 7).__round__(2)
average_days_in_stock = (balance / med_sales).__round__(2)

print(" ")
print(f"За 7 дней было продано {sell_summ} шт.")
print(f'Выручка составила {cum_sum} руб.')
print(f'Среднее количество продаж в день:  {med_sales}')
print(f'Актуальный остаток:  {balance}')
print(" ")
print(f"При актуальных продажах товар будет в наличии ещё {average_days_in_stock} дней.")

if average_days_in_stock < 10:
    print('Во избежание вылета, рекоммендуется сделать заказ.')
