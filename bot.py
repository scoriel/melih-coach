import os
from groq import Groq
from supabase import create_client
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

SYSTEM_PROMPT = "Sen Melih Celebi'nin kisisel fitness kocusun. 18 yasinda, 183 cm, 130 kg baslangic, hedef 90 kg. Bench Press PR 120 kg, kol 47 cm, bel 119 cm, omuz 140 cm, yag orani 32-33%. 2023 Temmuzda spora basladi, 92 kiloya inmis sonra geri almis. En buyuk korkusu sarkma. 200 diyet denemis hicbirini surdurememis, usengec ama guclu genetigi var. Dominant lider ruhlu. Kreatin kullaniyor. YKS ye hazirlaniyor 15 gun kaldi, Elektrik-Elektronik Muhendisligi istiyor. Kocluk tarzi: sert ama destekleyici, kisa net cevaplar, sarkma konusunda rahatlatici, her zaman Turkce."

conversation_history = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Melih! Kocun burada. 130dan 90a gidiyoruz.\n\n"
        "Komutlar:\n"
        "/kilo 129.5 - Kilo gir (web panele de kaydeder)\n"
        "/ilerleme - Ilerlemeyi gor\n"
        "/olcum 47 140 120 119 - Kol Omuz Gogus Bel gir\n\n"
        "Ya da direkt yaz, konusalim!"
    )

async def kilo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = float(context.args[0])
        supabase.table("weights").insert({"weight": weight}).execute()
        lost = round(130 - weight, 1)
        remaining = round(weight - 90, 1)
        pct = round((lost / 40) * 100, 1)
        await update.message.reply_text(
            f"Kaydedildi! {weight} kg\n"
            f"Verilen: {lost} kg\n"
            f"Kalan: {remaining} kg\n"
            f"Ilerleme: %{pct}\n"
            f"Web panelde de gozukuyor!"
        )
    except:
        await update.message.reply_text("Kullanim: /kilo 129.5")

async def olcum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        data = {}
        if len(args) >= 1: data['kol'] = float(args[0])
        if len(args) >= 2: data['omuz'] = float(args[1])
        if len(args) >= 3: data['gogus'] = float(args[2])
        if len(args) >= 4: data['bel'] = float(args[3])
        if len(args) >= 5: data['kalca'] = float(args[4])
        if len(args) >= 6: data['quads'] = float(args[5])
        if len(args) >= 7: data['baldir'] = float(args[6])
        supabase.table("measurements").insert(data).execute()
        msg = "Olcumler kaydedildi!\n"
        for k, v in data.items():
            msg += f"{k.capitalize()}: {v} cm\n"
        msg += "Web panelde de gozukuyor!"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text("Kullanim: /olcum 47 140 120 119\n(Kol Omuz Gogus Bel)")

async def ilerleme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = supabase.table("weights").select("*").order("created_at", desc=True).limit(5).execute()
        if not result.data:
            await update.message.reply_text("Henuz kilo girisi yok. /kilo 130 ile basla!")
            return
        msg = "Son kilolar:\n"
        for row in result.data:
            msg += f"{row['date']}: {row['weight']} kg\n"
        latest = result.data[0]['weight']
        lost = round(130 - latest, 1)
        remaining = round(latest - 90, 1)
        progress = round((lost / 40) * 100, 1)
        msg += f"\nToplam verilen: {lost} kg"
        msg += f"\nKalan: {remaining} kg"
        msg += f"\nIlerleme: %{progress}"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Hata: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    conversation_history[user_id].append({"role": "user", "content": user_message})
    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history[user_id]
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            messages=messages
        )
        reply = response.choices[0].message.content
        conversation_history[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"Hata: {str(e)}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kilo", kilo))
    app.add_handler(CommandHandler("ilerleme", ilerleme))
    app.add_handler(CommandHandler("olcum", olcum))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot calisiyor...")
    app.run_polling()
