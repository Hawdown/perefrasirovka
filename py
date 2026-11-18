import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "9015412459:AAEwbaxRq3z0ugmVj8WINnn5YHUctRnC9DA"
PROXYAPI_KEY = "sk-Puf1u6JeY80t1KGui9kCXew7V35OVqkM"

API_URL = "https://proxyapi.ru"
MODEL_NAME = "gpt-4o-mini"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

SYSTEM_PROMPT = """
Твоя задача — глубоко переработать и перефразировать предоставленный текст так, 
чтобы он звучал максимально естественно, как будто его написал живой человек (студент или школьник), 
и успешно проходил проверки на AI-генерацию.

Строгие правила переработки:
1. Удали все типичные канцеляризмы и клише нейросетей (например: «в современном мире», «подводя итог», «неотъемлемой частью», «крайне важно», «таким образом», «давайте рассмотрим»).
2. Меняй структуру предложений: чередуй короткие и длинные фразы. Используй более разговорный, живой синтаксис.
3. Заменяй сложные академические слова на более простые и естественные синонимы.
4. Сохраняй исходный смысл, факты и логику текста, но пересказывай их своими словами.
5. Не используй слишком идеальную, шаблонную структуру с маркерами, если в исходнике ее не было.
6. Выдай ТОЛЬКО переработанный текст без своих комментариев, вступлений и приветствий.
"""

async def humanize_text(text: str) -> str:
    headers = {
        "Authorization": f"Bearer {PROXYAPI_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Перепиши этот текст:\n\n{text}"}
        ],
        "temperature": 0.85
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    err_text = await resp.text()
                    logging.error(f"Ошибка API ({resp.status}): {err_text}")
                    return f"Ошибка ProxyAPI (код {resp.status}). Проверь баланс или ключ."
    except Exception as e:
        logging.error(f"Ошибка соединения: {e}")
        return "Произошла ошибка при обработке текста."

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Отправь мне текст, сгенерированный нейросетью, "
        "и я перепишу его живым человеческим языком."
    )

@dp.message(F.text)
async def handle_text(message: types.Message):
    if len(message.text) < 20:
        await message.answer("Текст слишком короткий. Пришлите хотя бы пару предложений.")
        return

    wait_msg = await message.answer("⏳ Переписываю текст, подождите пару секунд...")
    rewritten_text = await humanize_text(message.text)
    await wait_msg.delete()
    await message.answer(rewritten_text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
