import asyncio
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# Словарь для хранения ценовых уровней пользователей
user_targets = {}

# Биржа HTX API
API_URL = "https://api.huobi.com/market/detail/merged"

# Функция для получения текущей цены криптовалюты
def get_crypto_price(pair):
    try:
        response = requests.get(f"{API_URL}?symbol={pair.replace('/', '').lower()}")
        response.raise_for_status()
        data = response.json()
        return float(data['tick']['close'])
    except Exception as e:
        logging.error(f"Ошибка получения w для {pair}: {e}")
        return None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для отслеживания. Используйте команду /take_point, чтобы установить целевой уровень."
    )

# Команда /take_point
async def take_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 2:
            await update.message.reply_text("Используйте: /take_point [пара] [цена].")
            return
        
        pair = context.args[0].upper()
        target_price = float(context.args[1])
        
        if pair not in ["BTC/USDT", "ETH/USDT", "WLD/USDT"]:
            await update.message.reply_text("Доступны только пары: BTC/USDT, ETH/USDT, WLD/USDT.")
            return

        user_targets[update.effective_chat.id] = (pair, target_price)
        await update.message.reply_text(f"Целевой уровень для {pair} установлен на {target_price}.")
    except ValueError:
        await update.message.reply_text("Укажите правильную цену. Пример: /take_point B/U 35000")

# Фоновая задача для проверки цен
async def price_checker(app):
    while True:
        for user_id, (pair, target_price) in list(user_targets.items()):
            current_price = get_crypto_price(pair)
            if current_price is not None and current_price >= target_price:
                await app.bot.send_message(chat_id=user_id, text=f"point {current_price} had taken for {pair}.")
                del user_targets[user_id]
        await asyncio.sleep(10)  # Проверяем каждые 10 секунд

# Запуск бота
if __name__ == "__main__":
    TOKEN = "8156444383:AAF7b3WToXBYoGY2ldMcCvSu5NNl7QI_j_s"
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("take_point", take_point))
    
    # Фоновая задача
    app.job_queue.run_repeating(lambda _: asyncio.create_task(price_checker(app)), interval=10)

    print("Бот запущен!")
    app.run_polling()
