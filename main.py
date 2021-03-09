import os
import telebot
import db
import datetime
import requests
import json
import re
from plot import history_plot
import io
from dotenv import load_dotenv


load_dotenv()
KEY = os.environ.get('TELEGRAM_KEY')
TIME_THRESHOLD = datetime.timedelta(days=7)
bot = telebot.TeleBot(KEY)
db.setup()


@bot.message_handler(commands=['list', 'lst'])
def list_rates(message):
    data = db.get_request('list', datetime.datetime.now() - TIME_THRESHOLD)
    if not data:
        r = requests.get('https://api.exchangeratesapi.io/latest?base=USD')
        if not r.status_code == 200:
            bot.send_message(message, "Exchange api error")
            return
        data = r.text
        db.write('list', data, datetime.datetime.now())

    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        bot.send_message(message, "Response error")
        return

    if data.get('rates'):
        reply = ''.join('- {}: {:8.2f}\n'.format(k, v) for k, v in data.get('rates').items() if k != "USD")
        bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=['exchange'])
def exchange_rate(message):
    request = message.text
    res = re.search(r'/exchange ((\$([0-9]+))|(([0-9]+) USD)) to ([A-Z]{3})$', request)
    if not res:
        bot.send_message(message.chat.id, "Wrong format\nEX: /exchange $10 to CAD or /exchange 10 USD to CAD")
        return
    value, currency = float(res.group(3) if res.group(3) else res.group(5)), res.group(6)

    data = db.get_request(currency, datetime.datetime.now() - TIME_THRESHOLD)
    if not data:
        r = requests.get('https://api.exchangeratesapi.io/latest?base=USD&symbols={}'.format(currency))
        if r.status_code == 400:
            bot.send_message(message.chat.id, "No such currency")
            return
        elif not r.status_code == 200:
            bot.send_message(message.chat.id, "Exchange api connection error")
            return
        data = r.text
        db.write(currency, data, datetime.datetime.now())

    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        bot.reply_to(message.chat.id, "Response error")
        return

    if data.get('rates'):
        bot.send_message(message.chat.id, '$ {:.2f}'.format(value * float(data.get('rates')[currency])))


@bot.message_handler(commands=['history'])
def rate_history(message):
    request = message.text
    res = re.search(r'/history ([A-Z]{3})/([A-Z]{3}) for ([0-9]{1,3}) days$', request)
    if not res:
        bot.send_message(message.chat.id, "Wrong format\nEX: /history USD/CAD for 7 days")
        return
    cur1, cur2, time = res.group(1), res.group(2), res.group(3)

    data = db.get_request(cur1 + cur2 + time, datetime.datetime.now() - TIME_THRESHOLD)
    if not data:
        start_date = datetime.datetime.now().date() - datetime.timedelta(days=int(time))
        end_date = datetime.datetime.now().date()
        r = requests.get('https://api.exchangeratesapi.io/history?start_at={}&end_at={}&base={}&symbols={}'.format(
            start_date, end_date, cur1, cur2))
        if r.status_code == 400:
            bot.send_message(message.chat.id, "No such currency")
            return
        elif not r.status_code == 200:
            bot.send_message(message.chat.id, "Excange api connection error")
            return
        data = r.text
        db.write(cur1 + cur2 + time, data, datetime.datetime.now())

    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        bot.reply_to(message.chat.id, "Response decode error")
        return

    plot = history_plot(sorted([(k, v.get(cur2)) for k, v in data['rates'].items()], key=lambda x: x[0]),
                        cur1=cur1, cur2=cur2)
    if plot:
        buf = io.BytesIO()
        with buf:
            plot.savefig(buf, format='png')
            buf.seek(0)
            bot.send_photo(message.chat.id, buf)
    plot.close()


if __name__ == '__main__':
    bot.polling()

