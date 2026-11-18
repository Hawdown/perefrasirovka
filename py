import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart

TELEGRAM_TOKEN = "9015412459:AAEwbaxRq3z0ugmVj8WINnn5YHUctRnC9DA"
PROXYAPI_KEY = "sk-8wzLxinkog6osQ0AT5bDbyqdkuAg4yXT"

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
    domain = "api." + "proxyapi.ru"
    configs = [
        (f"https://{domain}/openrouter/v1/chat/completions", "openai/gpt-4.1-mini"),
        (f"https://{domain}/openai/v1/chat/completions", "gpt-4.1-mini"),
        (f"https://{domain}/openai/v1/chat/completions", "gpt-4o-mini"),
    ]
    
    headers = {
        "Authorization": f"Bearer {PROXYAPI_KEY}",
        "Content-Type": "application/json"
    }
    
    last_error = None
    
    async with aiohttp.ClientSession() as session:
        for url, model_name in configs:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Перепиши этот текст:\n\n{text}"}
                ],
                "temperature": 0.85
            }
            try:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        first_choice = data["choices"].pop(0)
                        return first_choice["message"]["content"].strip()
                    else:
                        err_text = await resp.text()
                        last_error = f"Код {resp.status} ({model_name}): {err_text[:150]}"
                        logging.warning(f"Не сработало {url}: {last_error}")
            except Exception as e:
                last_error = str(e)
                logging.warning(f"Ошибка соединения с {url}: {e}")
                
    return f"Все варианты перебраны, ошибка: {last_error}"

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
