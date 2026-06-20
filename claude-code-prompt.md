# Prompt สำหรับสั่ง Claude Code — set-price-pipeline (TradingView Scraper Cronjob แบบแบ่ง Phase)

> **โปรเจกต์:** `set-price-pipeline` — ดึงราคาหุ้น SET จาก TradingView อัตโนมัติด้วย GitHub Actions
>
> **เตรียม repo ก่อน:**
> 1. สร้าง repo ที่ github.com/new ชื่อ `set-price-pipeline` (ติ๊ก Add README + .gitignore แบบ Python)
> 2. `git clone https://github.com/<user>/set-price-pipeline.git && cd set-price-pipeline`
> 3. รัน `claude` แล้ว copy บล็อกด้านล่างวาง เริ่มที่ Phase 0
> 4. ก่อน Phase 3: ตั้ง Secrets ที่ Settings → Secrets and variables → Actions
>    (TV_USERNAME, TV_SECRET, WEBHOOK_URL — ใส่เฉพาะที่ใช้)

> **วิธีใช้:** เปิด terminal ในโฟลเดอร์โปรเจกต์ (หรือโฟลเดอร์ว่างใหม่) แล้วรัน `claude`
> จากนั้น copy ทั้งบล็อกด้านล่างวางแล้ว Enter
>
> **หัวใจ:** prompt นี้บังคับให้ Claude Code ทำทีละ phase แล้ว **หยุดรอคุณยืนยัน**
> ก่อนไป phase ถัดไป คุณจึงเห็นและตรวจงานได้ทีละก้อน ไม่ถล่มมารวดเดียว

---

```
ช่วยสร้างโปรเจกต์ Python ที่ดึงข้อมูลราคาหุ้นไทย (SET) จาก TradingView
ด้วย library tvdatafeed แล้วตั้งให้รันอัตโนมัติผ่าน GitHub Actions cronjob

สำคัญมาก — ให้ทำงานแบบแบ่งเป็น PHASE ตามด้านล่าง จบแต่ละ phase ให้
**หยุดสรุปผลแล้วรอฉันพิมพ์ว่า "ไปต่อ" ก่อนเริ่ม phase ถัดไป** ห้ามทำรวดเดียว
จบทุก phase โดยไม่หยุด เพราะฉันต้องการตรวจงานทีละขั้น

═══════════════════════════════════════════════
PHASE 0 — SPIKE: พิสูจน์ว่า library ใช้ได้จริง (ห้ามข้าม)
═══════════════════════════════════════════════
เป้าหมาย: รู้ให้ชัดว่า tvdatafeed ดึงข้อมูล SET ได้ไหม ก่อนลงทุนสร้างอย่างอื่น
ทำ:
1. ติดตั้ง tvdatafeed จาก fork ที่ยัง maintained คือ rongardF/tvdatafeed
   (ไม่ใช่ StreamAlpha เดิมที่หยุดอัปเดต) โดย PIN commit SHA ล่าสุด
   ห้ามดึง branch main ลอยๆ
2. เขียนสคริปต์สั้นๆ ดึง SET:KTB interval 1D 10 bars แบบ nologin
3. รายงานผล: nologin ใช้กับหุ้น SET ได้ไหม
   - ได้ → ใช้ nologin เป็นค่าเริ่มต้น (เสถียรกว่าบน CI)
   - ไม่ได้ → ค่อยวางแผนรองรับ login ผ่าน env var
🛑 หยุด รายงานผล Phase 0 แล้วรอฉันสั่ง "ไปต่อ"

═══════════════════════════════════════════════
PHASE 1 — CORE: ให้ scraper รันในเครื่องได้ก่อน (ยังไม่แตะ GitHub)
═══════════════════════════════════════════════
เป้าหมาย: ดึง 1 symbol แล้วได้ไฟล์ออกมาจริง
สร้าง:
- requirements.txt (tvdatafeed pin SHA + pin pandas, websocket-client, requests)
- symbols.json (config แยกจากโค้ด เริ่มด้วย SET:KTB ตัวเดียวพอ)
- scraper.py เวอร์ชันพื้นฐาน: อ่าน config → ดึง 1 symbol →
  เซฟ data/json/<...>.json และ data/csv/<...>.csv
ทดสอบ: รัน python scraper.py จริง ต้องได้ไฟล์ออกมา
🛑 หยุด โชว์ผลไฟล์ที่ได้ แล้วรอ "ไปต่อ"

═══════════════════════════════════════════════
PHASE 2 — ROBUST: ทำให้ทนทาน รันหลาย symbol ได้
═══════════════════════════════════════════════
เป้าหมาย: รันครบทุก symbol โดยไม่ล้มทั้ง job เพราะตัวเดียวพัง
เพิ่มเข้า scraper.py:
- วน loop หลาย symbol / หลาย interval จาก config
- retry logic (3 ครั้ง backoff) ต่อ symbol
- ถ้าตัวไหนล้ม log error แล้วข้าม ไม่ crash ทั้งงาน
- ใช้ logging module (ไม่ใช่ print)
- จัดการ timezone เป็น Asia/Bangkok ให้สม่ำเสมอ
- จัดการ empty DataFrame ไม่ให้ crash
- CSV append แบบ dedup ตาม timestamp (ห้ามแถวซ้ำ) + แยกไฟล์รายเดือนกัน repo บวม
- หน่วงเวลาเล็กน้อยระหว่าง request กัน WebSocket หลุด
- print summary ท้ายงาน + exit code != 0 ถ้าล้มทั้งหมด
ทดสอบ: เพิ่ม symbol ใน config เป็น 3 ตัว แล้วรันจริง
🛑 หยุด โชว์ log + ไฟล์ แล้วรอ "ไปต่อ"

═══════════════════════════════════════════════
PHASE 3 — AUTOMATE: ตั้ง GitHub Actions cronjob
═══════════════════════════════════════════════
เป้าหมาย: ให้รันเองตามเวลาแล้ว commit ผลกลับ repo
สร้าง .github/workflows/scrape-tradingview.yml:
- schedule (cron UTC) รันทุก 30 นาที ช่วงตลาด SET เปิด
  (ไทย 10:00–16:30 = 03:00–09:30 UTC) วันจันทร์–ศุกร์: "0,30 3-9 * * 1-5"
- workflow_dispatch ให้กดรันเองได้
- concurrency group กันรอบที่รันทับกัน
- setup Python 3.12 + cache pip + install requirements
- รัน scraper.py
- commit + push: git pull --rebase ก่อน push เสมอ (กัน non-fast-forward),
  commit เฉพาะตอนไฟล์เปลี่ยนจริง, retry push ถ้าชน
ทดสอบ: validate YAML ว่า syntax ถูก
🛑 หยุด อธิบาย workflow แล้วรอ "ไปต่อ"

═══════════════════════════════════════════════
PHASE 4 — POLISH: เก็บงาน + เอกสาร + แจ้งเตือน
═══════════════════════════════════════════════
สร้าง/เพิ่ม:
- ขั้นแจ้งเตือนเมื่อ FAIL: ส่ง webhook (Discord/Line) ถ้ามี secret WEBHOOK_URL
  (ใช้ if: failure()) ถ้าไม่มี secret ให้ข้ามเงียบๆ
- .gitignore (__pycache__, .env, venv/, *.log)
- .env.example (TV_USERNAME, TV_SECRET, WEBHOOK_URL — ทุกตัว optional)
- README.md: โปรเจกต์ทำอะไร, วิธีรัน local, วิธีเพิ่ม/ลบ symbol,
  วิธีตั้ง GitHub Secrets, คำเตือน 2 ข้อ:
  (ก) tvdatafeed เป็น unofficial อาจพังถ้า TradingView เปลี่ยน protocol
  (ข) GitHub ปิด scheduled workflow อัตโนมัติถ้า repo เงียบ 60 วัน
ตรวจ DEFINITION OF DONE ทั้งหมด:
  1. Phase 0 ผ่าน — ยืนยันแล้วว่าดึง SET ได้
  2. python scraper.py ได้ไฟล์ JSON+CSV จริง
  3. ไม่มี syntax/import error
  4. workflow YAML syntax ถูก
  5. README ครบ ทำตามแล้วรันต่อได้
🛑 สรุปงานทั้งหมดที่ส่งมอบ

═══════════════════════════════════════════════
ข้อกำหนดทั่วไป (ใช้ทุก phase)
═══════════════════════════════════════════════
- ใช้ pathlib แทน os.path
- ห้าม hardcode credential อ่านจาก env var เท่านั้น
- คอมเมนต์ภาษาไทยอธิบายส่วนสำคัญ
- config (symbol/interval) ต้องแก้ได้โดยไม่แตะโค้ดหลัก
```

---

## หมายเหตุสำคัญก่อนใช้งานจริง

1. **tvdatafeed ไม่ใช่ official API** — community library ที่ reverse-engineer จาก
   WebSocket (StreamAlpha เดิมหยุดอัปเดต ~1 ปี จึงใช้ fork rongardF) อาจพังได้
2. อ่าน **Terms of Service ของ TradingView** เรื่องดึงข้อมูลอัตโนมัติก่อนใช้จริงจัง
3. **nologin** ดึงได้แต่ข้อมูลจำกัดบาง symbol ถ้าต้องการเต็มต้องใส่ credential
4. **cron UTC เท่านั้น** — ตลาดไทย 10:00–16:30 = 03:00–09:30 UTC
5. **private repo มี quota** — รันถี่กินโควต้า (public repo ฟรีไม่จำกัด)

## ทำไมต้องแบ่ง phase + หยุด checkpoint?
- เจอปัญหาเร็ว (โดยเฉพาะ Phase 0 ที่เสี่ยงสุด) ไม่ต้องรื้อทีหลัง
- ตรวจงานได้ทีละก้อน เข้าใจทุกชิ้นว่าทำอะไร
- ถ้า phase ไหนพลาด แก้เฉพาะจุด ไม่กระทบทั้งระบบ
- ถ้าอยากให้ทำรวดเดียวไม่ต้องหยุด ลบประโยค "หยุดรอ...ไปต่อ" ออกได้
