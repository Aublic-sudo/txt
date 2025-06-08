import requests
import json
import cloudscraper
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode
import os
from pyrogram.types import Message

def decode_appx(enc):
    key = b"638udh3829162018"
    iv = b"fedcba9876543210"
    try:
        ciphertext = bytearray.fromhex(b64decode(enc.encode()).hex())
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return plaintext.decode('utf-8')
    except Exception as e:
        return f"DECRYPT_ERROR: {e}"

async def universal_login(bot, m: Message):
    # Step 1: Get host
    editable = await m.reply_text("Paste your API host (e.g. `lastexamapi.teachx.in`, `missionapi.appx.co.in`, etc):")
    input1 = await bot.listen(m.chat.id)
    host = input1.text.strip().replace("https://", "").replace("http://", "").strip("/")
    await input1.delete()
    s = requests.Session()
    scraper = cloudscraper.create_scraper()

    # Step 2: Login
    editable = await m.reply_text("Send **ID*Password** (e.g., `id*pass`):")
    input2 = await bot.listen(m.chat.id)
    raw = input2.text.strip()
    await input2.delete()
    try:
        email, passwd = raw.split("*")
    except Exception:
        await editable.edit("❌ Invalid format. Use `id*pass`.")
        return

    # Try both login endpoints
    login_urls = [
        f"https://{host}/post/userLogin",
        f"https://{host}/post/login"
    ]
    login_success = False
    for login_url in login_urls:
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
            res = scraper.post(login_url, data={"email": email, "password": passwd}, headers=hdr, timeout=15).content
            output = json.loads(res)
            if output.get("status") is False or "data" not in output or not output["data"].get("userid") or not output["data"].get("token"):
                continue
            userid = output["data"]["userid"]
            token = output["data"]["token"]
            login_success = True
            break
        except Exception:
            continue

    if not login_success:
        await editable.edit("❌ Login failed. Wrong credentials or host.")
        return

    await editable.edit("✅ **Login Successful!**")

    # Step 3: Prepare headers
    headers = {
        "Host": host,
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "User-Id": userid,
        "Authorization": token,
        "User_app_category": "",
        "Language": "en",
        "User-Agent": "okhttp/4.9.1"
    }

    # Step 4: Get courses/batches
    try:
        res1 = s.get(f"https://{host}/get/mycourse?userid={userid}", headers=headers, timeout=15)
        b_data = res1.json().get("data", [])
        if not b_data:
            await m.reply_text("❌ No batches found.")
            return
        txt = ""
        for data in b_data:
            cname = data.get("course_name") or data.get("courseName") or "NoName"
            cid = data.get("id") or data.get("courseId")
            txt += f"```{cid}``` - **{cname}**\n"
        await m.reply_text(f"**You have these batches:**\n\n{txt}")
    except Exception as e:
        await m.reply_text(f"❌ Failed to fetch courses: {e}")
        return

    # Step 5: Get batch ID
    editable = await m.reply_text("**Now send the Batch ID to Download**")
    input3 = await bot.listen(m.chat.id)
    courseid = input3.text.strip()
    await input3.delete()

    # Step 6: Get subjects
    try:
        r = scraper.get(f"https://{host}/get/allsubjectfrmlivecourseclass?courseid={courseid}", headers=headers, timeout=15).content
        subdata = json.loads(r).get("data", [])
        if not subdata:
            await m.reply_text("❌ No subjects found.")
            return
        subtxt = ""
        for sub in subdata:
            subtxt += f"```{sub.get('subjectid')}``` - **{sub.get('subject_name')}**\n"
        await m.reply_text(f"**Subjects:**\n{subtxt}")
    except Exception as e:
        await m.reply_text(f"❌ Failed to fetch subject list: {e}")
        return

    editable = await m.reply_text("**Enter the Subject ID shown above**")
    input4 = await bot.listen(m.chat.id)
    subjectid = input4.text.strip()
    await input4.delete()

    # Step 7: Get topics
    try:
        r = s.get(f"https://{host}/get/alltopicfrmlivecourseclass?courseid={courseid}&subjectid={subjectid}", headers=headers, timeout=15)
        topiclist = r.json().get("data", [])
        if not topiclist:
            await m.reply_text("❌ No topics found.")
            return
        topic_ids, topic_details = "", ""
        for data in topiclist:
            tid = str(data.get("topicid"))
            name = data.get("topic_name", "NoName")
            topic_ids += f"{tid}&"
            topic_details += f"```{tid}``` - **{name}**\n"
        await m.reply_text(f"**Topic Details:**\n\n{topic_details}")
    except Exception as e:
        await m.reply_text(f"❌ Failed to fetch topics: {e}")
        return

    editable = await m.reply_text(f"Send Topic IDs (like `1&2&3`) or use below for full:\n\n```{topic_ids}```")
    input5 = await bot.listen(m.chat.id)
    raw_topics = input5.text.strip()
    await input5.delete()

    # Step 8: Get resolution (optional, for future use)
    editable = await m.reply_text("**Now send the Resolution (360, 480, etc.)**")
    input6 = await bot.listen(m.chat.id)
    resolution = input6.text.strip()
    await input6.delete()

    # Step 9: Fetch and decrypt links
    outtxt = f"{host.replace('.', '_')}_{courseid}_{subjectid}.txt"
    try:
        with open(outtxt, "w", encoding="utf-8") as f:
            for t in raw_topics.split("&"):
                t = t.strip()
                if not t:
                    continue
                url = f"https://{host}/get/livecourseclassbycoursesubtopconceptapiv3?topicid={t}&start=-1&conceptid=1&courseid={courseid}&subjectid={subjectid}"
                res = s.get(url, headers=headers, timeout=15).json()
                for data in res.get("data", []):
                    # Handle both new and old JSON
                    if data.get("encrypted_links"):
                        for enc in data["encrypted_links"]:
                            quality = enc.get("quality", "N/A")
                            path = enc.get("path", "")
                            key_b64 = enc.get("key", "")
                            f.write(f"{data.get('Title','NoTitle')} [{quality}]: {path} | KEY: {key_b64}\n")
                    else:
                        enc = data.get("download_link") or data.get("pdf_link")
                        title = data.get("Title", "NoTitle")
                        if not enc:
                            continue
                        dec = decode_appx(enc)
                        f.write(f"{title}: {dec}\n")
        await m.reply_document(outtxt)
        os.remove(outtxt)
    except Exception as e:
        await m.reply_text(f"❌ Error: {e}")
        return

    await m.reply_text("✅ **Done! File Sent.**")
