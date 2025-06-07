from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from plugins.universal import universal_login

@Client.on_message(filters.command("MasterAppx") & filters.private)
async def master_appx(bot, message: Message):
    buttons = [
        [InlineKeyboardButton("🔍 Find Appx URL", callback_data="find_appx")],
    ]
    await message.reply_text(
        "**Send Appx API URL (host only e.g. `rgvikramjeetapi.classx.co.in`)**\n\n"
        "If you don't know the Appx API URL, use the 'Find Appx URL' button below.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    try:
        input1 = await bot.listen(message.chat.id)
        api_url = input1.text.strip()
        await input1.delete()
    except Exception:
        return await message.reply_text("❌ Failed to read API URL input.")

    api_url = api_url.replace("https://", "").replace("http://", "").strip().strip("/")

    await message.reply_text(
        "Send credentials in **one** of these formats:\n"
        "- For ID/Password: `ID*Password`\n"
        "- For Token login: `UserID:Token`"
    )

    try:
        input2 = await bot.listen(message.chat.id)
        creds = input2.text.strip()
        await input2.delete()
        if "*" in creds:
            user, passwd = creds.split("*", 1)
            await universal_login(bot, message, api_url, user=user, passwd=passwd)
        elif ":" in creds:
            userid, token = creds.split(":", 1)
            await universal_login(bot, message, api_url, user=userid, token=token)
        else:
            return await message.reply_text("❌ Invalid format. Use `ID*Password` or `UserID:Token`.")
    except Exception:
        return await message.reply_text("❌ Failed to read credentials input.")
