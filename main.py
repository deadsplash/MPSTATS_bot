import requests as r
from datetime import datetime
import telebot
import pandas as pd
from auth_data import mpstats_api_token, telegram_bot_token
import os

cur_date = str(datetime.now())[0:10]

mpstats_api = {
    'X-Mpstats-TOKEN': mpstats_api_token,
    'Content-Type': 'application/json'
  }

bot = telebot.TeleBot(telegram_bot_token)


def last_day_maker(data):
    lday = str(int(data[8:10]) - 1)
    last_day = cur_date[0:8] + lday
    return last_day


def parse_mpstats(src, name='test'):

    # data = pd.read_excel('input.xlsx')
    data = pd.read_excel(src)

    wb_id_list = list()

    try:
        wb_id_list = list(data['Артикул WB'].values)
        if len(wb_id_list) == 0:
            print("There is no WB ID's in the file.")
            exit()
    except Exception as ex:
        print('Something went wrong: ', ex)
        exit()

    last_day = last_day_maker(cur_date)

    print("Started parsing ID's!")

    for wb_id in wb_id_list:

        # print(wb_id)
        sell_summ, cum_sum , balance, med_sales, expected_days_in_stock = (0, 0, 0, 0, 0)

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

            # print(f'За {result[0]["data"]} было продано {result[0]["sales"]}шт')

            sell_summ = sell_summ + int(result[0]['sales'])

            if balance == 0:
                balance = balance + int(result[0]['balance'])
            else:
                pass

            last_day = last_day_maker(last_day)

        med_sales = (sell_summ / 7).__round__(2)

        if med_sales == 0:
            pass
        else:
            med_sales = (sell_summ / 7).__round__(2)
            expected_days_in_stock = (balance / med_sales).__round__(2)

        data.loc[data['Артикул WB'] == wb_id, 'Остаток WB'] = balance
        data.loc[data['Артикул WB'] == wb_id, 'Продаж 7 дней'] = sell_summ
        data.loc[data['Артикул WB'] == wb_id, 'Ср. продаж в день'] = med_sales
        data.loc[data['Артикул WB'] == wb_id, 'Остаток на дней:'] = expected_days_in_stock
        if expected_days_in_stock < 10:
            data.loc[data['Артикул WB'] == wb_id, 'Нужно заказывать? '] = str("да")
        else:
            data.loc[data['Артикул WB'] == wb_id, 'Нужно заказывать? '] = str("нет")

    print('Making output....')

    result_dir = f'./results/result_{name}_{cur_date}.xlsx'

    with pd.ExcelWriter(result_dir) as writer:
        data.to_excel(writer)

    print('Done!')
    return result_dir


@bot.message_handler(commands='help')
def helper(message):
    help_text = """
Приветствую! 

Этот бот обрабатывает WB ID, давая чёткую сводку продаж за последние 7 дней, и формирует необходимость в новом заказе.

Ниже будет пример файла для заполнения. 
Переименовывать столбцы нельзя, можно добавлять новые.

Спасибо за внимание.
    """
    bot.send_message(message.chat.id, text=help_text)
    bot.send_document(message.chat.id, open('input_test.xlsx', 'rb'))


@bot.message_handler(commands='sample')
def helper(message):
    bot.send_document(message.chat.id, open('input_test.xlsx', 'rb'))


@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        src = file_info.file_path
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
            bot.send_message(message.chat.id, text=f'Начата работа над файлом. Это займёт до 5 минут.')
        result_dir = parse_mpstats(src, name=message.chat.id)

        bot.send_message(message.chat.id, text=f'Готово!')
        bot.send_document(message.chat.id, open(result_dir, 'rb'))

        os.remove(src)

    except Exception as ex:
        print(ex)
        bot.reply_to(message, 'Неизвестная ошибка. Проверьте файл, или введите /help')


if __name__ == '__main__':
    bot.infinity_polling()
