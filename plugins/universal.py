import requests
import json
from pyrogram.types import Message
import cloudscraper
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode

async def universal_login(bot, m: Message, host: str, user: str = None, passwd: str = None, token: str = None):
    s = requests.Session()
    scraper = cloudscraper.create_scraper()
    
    # If token and user id are provided, skip login API call
    if token and user:
        userid = user
        await m.reply_text("✅ **Token Login Successful!**")
    else:
        # Old flow: login with id/pass
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
        info = {"email": user, "password": passwd}
        try:
            res = scraper.post(login_url, data=info, headers=hdr).content
            output = json.loads(res)
            userid = output["data"]["userid"]
            token = output["data"]["token"]
            await m.reply_text("✅ **Login Successful!**")
        except Exception as e:
            await m.reply_text(f"❌ Login failed: {str(e)}")
            return

    hdr1 = {
        "Host": host,
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "User-Id": userid,
        "Authorization": token
    }

    # Rest of the code same as before
    try:
        cour_url = f"https://{host}/get/mycourse?userid={userid}"
        res1 = s.get(cour_url, headers=hdr1)
        b_data = res1.json()['data']
        cool = ""
        FFF = "**BATCH-ID - BATCH NAME - INSTRUCTOR**"
        for data in b_data:
            aa = f" ```{data['id']}```      - **{data['course_name']}**\n\n"
            if len(f'{cool}{aa}') > 4096:
                cool = ""
            cool += aa
        await m.reply_text(f'{"**You have these batches :-**"}\n\n{FFF}\n\n{cool}')
    except Exception as e:
        await m.reply_text(f"❌ Failed to fetch batches: {str(e)}")
        return

    await m.reply_text("**Now send the Batch ID to Download**")
    input2: Message = await bot.listen(m.chat.id)
    batch_id = input2.text
    await input2.delete(True)

    try:
        subj_url = f"https://{host}/get/allsubjectfrmlivecourseclass?courseid={batch_id}"
        html = scraper.get(subj_url, headers=hdr1).content
        output0 = json.loads(html)
        subjID = output0["data"]
        await m.reply_text(str(subjID))
    except Exception as e:
        await m.reply_text(f"❌ Failed to fetch subjects: {str(e)}")
        return

    await m.reply_text("**Enter the Subject Id Show in above Response**")
    input3: Message = await bot.listen(m.chat.id)
    subject_id = input3.text
    await input3.delete(True)

    try:
        topic_url = f"https://{host}/get/alltopicfrmlivecourseclass?courseid={batch_id}&subjectid={subject_id}"
        res3 = s.get(topic_url, headers=hdr1)
        b_data2 = res3.json()['data']
        vj = ""
        for data in b_data2:
            tids = (data["topicid"])
            idid = f"{tids}&"
            if len(f"{vj}{idid}") > 4096:
                vj = ""
            vj += idid
        cool1 = ""
        BBB = '**TOPIC-ID    - TOPIC     - VIDEOS**'
        for data in b_data2:
            t_name = (data["topic_name"])
            tid = (data["topicid"])
            zz = len(tid)
            hh = f"```{tid}```     - **{t_name} - ({zz})**\n"
            if len(f'{cool1}{hh}') > 4096:
                cool1 = ""
            cool1 += hh
        await m.reply_text(f'Batch details of **{t_name}** are:\n\n{BBB}\n\n{cool1}')
    except Exception as e:
        await m.reply_text(f"❌ Failed to fetch topics: {str(e)}")
        return

    editable = await m.reply_text(f"Now send the **Topic IDs** to Download\n\nSend like this **1&2&3&4** or copy/edit **below ids** for full batch:\n\n```{vj}```")
    input4: Message = await bot.listen(m.chat.id)
    topic_ids = input4.text
    await input4.delete(True)

    await m.reply_text("**Now send the Resolution**")
    input5: Message = await bot.listen(m.chat.id)
    resolution = input5.text
    await input5.delete(True)

    try:
        xv = topic_ids.split('&')
        mm = f"{host.replace('.', '_')}_batch"
        outtxt = f'{mm}.txt'
        for t in xv:
            if not t.strip():
                continue
            url = f"https://{host}/get/livecourseclassbycoursesubtopconceptapiv3?topicid={t}&start=-1&conceptid=1&courseid={batch_id}&subjectid={subject_id}"
            res4 = s.get(url, headers=hdr1).json()
            topicid = res4["data"]
            for data in topicid:
                b64 = data.get("download_link") or data.get("pdf_link")
                tid = data["Title"]
                key = "638udh3829162018".encode("utf8")
                iv = "fedcba9876543210".encode("utf8")
                ciphertext = bytearray.fromhex(b64decode(b64.encode()).hex())
                cipher = AES.new(key, AES.MODE_CBC, iv)
                try:
                    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
                    b = plaintext.decode('utf-8')
                except Exception as e:
                    b = f"Failed to decrypt: {e}"
                with open(outtxt, 'a', encoding='utf-8') as f:
                    f.write(f"{tid}:{b}\n")
        await m.reply_document(outtxt)
    except Exception as e:
        await m.reply_text(f"❌ Error: {str(e)}")
    await m.reply_text("Done ✅")
