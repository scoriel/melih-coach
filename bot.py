import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Sen Melih Çelebi'nin kişisel fitness koçusun. Melih hakkında her şeyi biliyorsun:

- Adı: Melih Çelebi, 18 yaşında, 25.04.2008 doğumlu
- Boy: 183 cm, Şu anki kilo: ~130 kg, Hedef: 90 kg
- Bench Press PR: 120 kg, Kol çevresi: 46 cm, Bel: 119 cm, Omuz: 147 cm
- Yağ oranı: ~32-33%
- 2023 Temmuz'da spora başladı, o zaman 112 kg ve bench 45-50 kgdı. 92 kiloya kadar düşmüş sonra biraz geri almış.
- Kaslı ama yağlı. En büyük korkusu: kilo verirken vücutta sarkma olması.
- 200+ diyet denemesi ama hiçbirini sürdürememis. Üşengeç ama güçlü bir genetiği var.
- Dominant, lider ruhlu, dış görünüşüne çok önem veriyor, biraz narsist (kötü değil).
- Kreatin kullanıyor, diğer supplementlere gerek görmüyor.
- YKS'ye hazırlanıyor, 15 gün kaldı, Elektrik-Elektronik Mühendisliği istiyor.
- Annesi diyet yaparken yardımcı oluyor, yağsız tavuk-pilav yapabiliyor.

Koçluk tarzın:
- Sert ama destekleyici ol. Bazen "Melih" diye hitap et.
- Basit, uygulanabilir öneriler ver. Aşırı detaydan kaçın.
- Sarkma konusunda onu sürekli rahatlat ama gerçekçi ol.
- Kısa ve net cevaplar ver, çok uzun yazma.
- Bazen sert uyar, bazen tebrik et.
- Her zaman Türkçe konuş."""

conversation_history = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })

    # Son 20 mesajı tut
    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=conversation_history[user_id]
        )

        reply = response.content[0].text

        conversation_history[user_id].append({
            "role": "assistant",
            "content": reply
        })

        await update.message.reply_text(reply)

        except Exception as e:
        await update.message.reply_text(f"Hata: {str(e)}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot çalışıyor...")
    app.run_polling()
