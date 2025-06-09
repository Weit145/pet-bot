import requests
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from xml.etree import ElementTree as ET
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("NEWS_API_KEY")


"""Обработчик команды /start"""
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ *Добро пожаловать в InfoBot!* ✨\n\n"
        "Я ваш персональный помощник для получения актуальной информации:\n\n"
        "📌 *Основные команды:*\n"
        "🌊 /author - Об авторе проекта\n"
        "📰 /news - Свежие новости Санкт-Петербурга\n"
        "💹 /rates - Курсы валют от ЦБ РФ\n"
        "🔄 /convert [сумма] [из] [в] - Конвертер валют\n\n"
        "*Пример использования конвертера:*\n"
        "`/convert 100 USD RUB`\n\n"
        "Выберите нужную команду из меню или введите вручную 👇",
        parse_mode="Markdown"
    )

"""Получение курсов валют с ЦБ РФ"""
async def get_rates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = "https://www.cbr.ru/scripts/XML_daily.asp"
        response = requests.get(url)
        response.raise_for_status()
        
        root = ET.fromstring(response.text)
        date = root.attrib['Date']
        formatted_date = datetime.now().strftime('%d.%m.%Y')
        
        currencies = {
            'USD': '🇺🇸 Доллар США',
            'EUR': '🇪🇺 Евро',
            'CNY': '🇨🇳 Китайский юань'
        }
        
        message = f"📊 Курсы ЦБ РФ на {formatted_date}:\n\n"
        
        for code, name in currencies.items():
            valute = root.find(f".//Valute[CharCode='{code}']")
            value = valute.find('Value').text
            nominal = valute.find('Nominal').text
            message += f"{name}: {value} руб. (за {nominal} {code})\n"
            
        message += "\nℹ️ Курсы обновляются ежедневно в 12:00 по МСК"
        await update.message.reply_text(message, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(
            "⚠️ *Ошибка!* Не удалось получить курсы валют.\n"
            "Попробуйте позже или проверьте соединение.",
            parse_mode="Markdown"
        )
        print(f"Error in get_rates: {e}")

"""Конвертация валют"""
async def convert_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 3:
            raise ValueError("Неверное количество аргументов")
        
        amount = float(context.args[0])
        from_curr = context.args[1].upper()
        to_curr = context.args[2].upper()

        url = "https://www.cbr.ru/scripts/XML_daily.asp"
        response = requests.get(url)
        response.raise_for_status()
        root = ET.fromstring(response.text)

        def get_rate(currency):
            if currency == 'RUB':
                return 1.0
            valute = root.find(f".//Valute[CharCode='{currency}']")
            if valute is None:
                raise ValueError(f"Валюта {currency} не найдена")
            nominal = float(valute.find('Nominal').text.replace(',', '.'))
            value = float(valute.find('Value').text.replace(',', '.'))
            return value / nominal

        from_rate = get_rate(from_curr)
        to_rate = get_rate(to_curr)
        
        result = (amount * from_rate) / to_rate
        
        await update.message.reply_text(
            f"💱 *Результат конвертации:*\n\n"
            f"🔹 *{amount:.2f} {from_curr}* = *{result:.2f} {to_curr}*\n\n"
            f"📌 *Курс:* 1 {from_curr} = {from_rate/to_rate:.4f} {to_curr}\n\n"
            f"🔄 Обмен по курсу ЦБ РФ на {datetime.now().strftime('%d.%m.%Y')}",
            parse_mode="Markdown"
        )
    except ValueError as e:
        await update.message.reply_text(
            "❌ *Ошибка ввода!*\n\n"
            "🔹 *Правильный формат:*\n"
            "`/convert [сумма] [из валюты] [в валюту]`\n\n"
            "*Примеры использования:*\n"
            "• `/convert 100 USD RUB`\n"
            "• `/convert 5000 RUB CNY`\n\n"
            "ℹ️ Доступные валюты: USD, EUR, CNY, RUB и другие из списка ЦБ РФ",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(
            "⚠️ *Ошибка конвертации!*\n"
            "Проверьте правильность ввода и попробуйте снова.",
            parse_mode="Markdown"
        )

"""Получение новостей через NewsAPI"""
async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = f"https://newsapi.org/v2/everything?q=Санкт-Петербург&apiKey={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] != 'ok' or not data['articles']:
            raise ValueError("Новости не найдены")
        
        message = "📌 *Свежие новости России* 📌\n\n"
        for i, article in enumerate(data['articles'][:3], 1):
            title = article['title']
            url = article['url']
            source = article['source']['name']
            published_at = datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d.%m.%Y %H:%M')
            
            message += (
                f"📰 *{title}*\n"
                f"🔗 [Читать полностью]({url})\n"
                f"🏷 *Источник:* {source}\n"
                f"⏰ *Дата:* {published_at}\n\n"
            )
            
        message += "ℹ️ Новости обновляются автоматически"
        await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(
            "⚠️ *Не удалось загрузить новости!*\n"
            "Попробуйте позже или проверьте соединение с интернетом.",
            parse_mode="Markdown"
        )

async def author(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👨‍💻 *Об авторе этого бота*\n\n"
        "Этот проект создан *Weit* в качестве учебного проекта для изучения:\n"
        "• Работы с внешними API 🌐\n\n"
        "🔹 *Исходный код:* [GitHub](https://github.com/Weit145)\n"
        "_Бот создан с ❤️ для удобного доступа к информации_",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )


def main():
    app = Application.builder().token(TOKEN).build()

    handlers = [
        CommandHandler("start", start),
        CommandHandler("news", get_news),
        CommandHandler("rates", get_rates),
        CommandHandler("convert", convert_currency),
        CommandHandler("author", author)
    ]
    
    for handler in handlers:
        app.add_handler(handler)
        
    app.run_polling()

if __name__ == "__main__":
    main()