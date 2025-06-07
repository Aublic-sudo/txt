import requests
import json
from pyrogram.types import Message
import cloudscraper
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode
import os

async def universal_login(bot, m: Message, host: str, user: str = None, passwd: str = None, token: str = None):
    host = host.replace("https://", "").replace("http://", "").strip("/")
    s = requests.Session()
    scraper = cloudscraper.create_scraper()

    # 🔐 Login with ID*Password if token not given
    if token and user:
        userid = user
        await m.reply_text("✅ **Token Login Successful!**")
    else:
        editable = await m.reply_text("Send **ID*Password** (e.g., `id*pass`):")
        input1: Message = await bot.listen(m.chat.id)
        raw = input1.text.strip()
        await input1.delete()
        email, passwd = raw.split("*")
        login_url = f"https://{host}/post/userLogin"
        hdr = {
            "Auth-Key": "appxapi",
            "User-Id": "-2",
            "Authorization": "",
            "User_app_category": "",
            "Language": "en",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "okhttp/4.9.1"
        }
        try:
            res = scraper.post(login_url, data={"email": email, "password": passwd}, headers=hdr).content
            output = json.loads(res)
            userid = output["data"]["userid"]
            token = output["data"]["token"]
            await editable.edit("✅ **Login Successful!**")
        except Exception as e:
            await editable.edit(f"❌ Login failed: {e}")
            return

    headers = {
        "Host": host,
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "User-Id": userid,
        "Authorization": token
    }

    # 👤 If only token provided, extract user ID from token
    if not userid and token:
        try:
            payload = token.split('.')[1]
            padded = payload + '=' * (-len(payload) % 4)
            decoded = json.loads(b64decode(padded).decode())
            userid = str(decoded.get("id"))
            headers["User-Id"] = userid
        except Exception as e:
            return await m.reply_text(f"❌ Token decode failed: {e}")

    # 🎓 Fetch course
    try:
        res1 = s.get(f"https://{host}/get/mycourse?userid={userid}", headers=headers)
        b_data = res1.json().get("data", [])
        if not b_data:
            return await m.reply_text("❌ No batches found.")

        txt = ""
        for data in b_data:
            cname = data.get("course_name") or data.get("courseName") or "NoName"
            cid = data.get("id") or data.get("courseId")
            txt += f"```{cid}``` - **{cname}**\n\n"
        await m.reply_text(f"**You have these batches:**\n\n{txt}")
    except Exception as e:
        return await m.reply_text(f"❌ Failed to fetch courses: {e}")

    # 📘 Get Batch ID
    editable = await m.reply_text("**Now send the Batch ID to Download**")
    input2 = await bot.listen(m.chat.id)
    courseid = input2.text.strip()
    await input2.delete()

    # 📙 Get Subject ID
    try:
        r = scraper.get(f"https://{host}/get/allsubjectfrmlivecourseclass?courseid={courseid}", headers=headers).content
        subdata = json.loads(r)["data"]
        await m.reply_text(str(subdata))
    except Exception as e:
        return await m.reply_text(f"❌ Failed to fetch subject list: {e}")

    editable = await m.reply_text("**Enter the Subject ID shown above**")
    input3 = await bot.listen(m.chat.id)
    subjectid = input3.text.strip()
    await input3.delete()

    # 📂 Get Topic IDs
    try:
        r = s.get(f"https://{host}/get/alltopicfrmlivecourseclass?courseid={courseid}&subjectid={subjectid}", headers=headers)
        topiclist = r.json()["data"]
        topic_ids, topic_details = "", ""
        for data in topiclist:
            tid = data["topicid"]
            name = data["topic_name"]
            topic_ids += f"{tid}&"
            topic_details += f"```{tid}``` - **{name}**\n"
        await m.reply_text(f"**Topic Details:**\n\n{topic_details}")
    except Exception as e:
        return await m.reply_text(f"❌ Failed to fetch topics: {e}")

    editable = await m.reply_text(f"Send Topic IDs (like `1&2&3`) or use below for full:\n\n```{topic_ids}```")
    input4 = await bot.listen(m.chat.id)
    raw_topics = input4.text.strip()
    await input4.delete()

    editable = await m.reply_text("**Now send the Resolution (360, 480, etc.)**")
    input5 = await bot.listen(m.chat.id)
    resolution = input5.text.strip()
    await input5.delete()

    # 🎥 Fetch and Decrypt
    outtxt = f"AUBLIC_{courseid}_{subjectid}.txt"
    try:
        for t in raw_topics.split("&"):
            if not t.strip(): continue
            url = f"https://{host}/get/livecourseclassbycoursesubtopconceptapiv3?topicid={t}&start=-1&conceptid=1&courseid={courseid}&subjectid={subjectid}"
            res = s.get(url, headers=headers).json()
            for data in res["data"]:
                encrypted = data.get("download_link") or data.get("pdf_link")
                title = data["Title"]
                key = b"638udh3829162018"
                iv = b"fedcba9876543210"
                cipher = AES.new(key, AES.MODE_CBC, iv)
                try:
                    ciphertext = bytearray.fromhex(b64decode(encrypted.encode()).hex())
                    decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size).decode()
                except Exception as e:
                    decrypted = f"❌ Failed to decrypt: {e}"
                with open(outtxt, "a", encoding="utf-8") as f:
                    f.write(f"{title}: {decrypted}\n")
        await m.reply_document(outtxt)
        os.remove(outtxt)
    except Exception as e:
        await m.reply_text(f"❌ Error: {e}")

    await m.reply_text("✅ **Done! File Sent.**")
