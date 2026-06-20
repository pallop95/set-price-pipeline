# Prompt สำหรับ Phase 5–6 — Supabase + Nuxt FE

> **ต้องทำก่อนใช้ prompt นี้:**
> 1. ไปที่ supabase.com → สร้าง project ใหม่
> 2. Table Editor → New Table ชื่อ `stock_prices` ตาม schema ด้านล่าง
> 3. Project Settings → API → copy `Project URL` และ `service_role key`
> 4. ใส่ `SUPABASE_URL` และ `SUPABASE_KEY` ใน GitHub Secrets ของ set-price-pipeline
>
> **Schema ที่ต้องสร้างใน Supabase:**
> ```sql
> create table stock_prices (
>   symbol    text        not null,
>   exchange  text        not null,
>   interval  text        not null,
>   datetime  timestamptz not null,
>   open      float8,
>   high      float8,
>   low       float8,
>   close     float8,
>   volume    float8,
>   primary key (symbol, interval, datetime)
> );
> ```

---

## ── PART A · repo: set-price-pipeline ──
> รัน `claude` ในโฟลเดอร์ set-price-pipeline แล้ว paste บล็อกนี้

```
ช่วยเพิ่ม Supabase upsert เข้าใน scraper.py ที่มีอยู่แล้ว

สำคัญมาก — ทำทีละ PHASE แล้วหยุดรอ "ไปต่อ" ก่อนเริ่มถัดไปเสมอ

═══════════════════════════════════════════════
PHASE 0 — SPIKE: ทดสอบ Supabase connection
═══════════════════════════════════════════════
เป้าหมาย: รู้ว่า supabase-py เชื่อมและ upsert ได้จริงก่อนแก้โค้ดหลัก
ทำ:
1. pip install supabase (ยังไม่แก้ requirements.txt)
2. เขียน spike_supabase.py สั้นๆ:
   - อ่าน SUPABASE_URL และ SUPABASE_KEY จาก env (ให้ผมใส่เองใน terminal)
   - upsert 1 แถวทดสอบลง stock_prices
   - SELECT กลับมาตรวจว่าเข้าจริง
3. รันและรายงานผล
🛑 หยุด รายงานผล แล้วรอ "ไปต่อ"

═══════════════════════════════════════════════
PHASE 1 — INTEGRATE: เพิ่ม upsert ใน scraper.py
═══════════════════════════════════════════════
เป้าหมาย: scraper.py เซฟลง Supabase ควบคู่กับ CSV/JSON เดิม
ทำ:
- เพิ่ม supabase ใน requirements.txt (pin version ล่าสุด)
- เพิ่มฟังก์ชัน upsert_supabase(df, symbol, exchange, interval_str)
  ใน scraper.py เรียกหลัง save() ในทุก loop
- ถ้าไม่มี SUPABASE_URL ใน env → log warning แล้วข้าม ไม่ crash
- เพิ่ม SUPABASE_URL และ SUPABASE_KEY ใน .env.example
- เพิ่ม env vars ใน .github/workflows/scrape-tradingview.yml
ทดสอบ: รัน python scraper.py จริง แล้วไปดูใน Supabase Table Editor ว่ามีข้อมูล
🛑 หยุด โชว์ผล แล้วรอ "ไปต่อ"

ข้อกำหนด:
- ใช้ pathlib แทน os.path
- ห้าม hardcode credential อ่านจาก env var เท่านั้น
- คอมเมนต์ภาษาไทยอธิบายส่วนสำคัญ
```

---

## ── PART B · repo ใหม่: set-price-frontend ──
> สร้าง repo ใหม่ที่ github.com/new ชื่อ `set-price-frontend`
> แล้วรัน:
> ```
> npx nuxi init set-price-frontend
> cd set-price-frontend
> git init && git remote add origin https://github.com/<user>/set-price-frontend.git
> claude
> ```
> จากนั้น paste บล็อกนี้

```
ช่วยสร้าง Nuxt 3 dashboard แสดงราคาหุ้น SET ดึงข้อมูลจาก Supabase

สำคัญมาก — ทำทีละ PHASE แล้วหยุดรอ "ไปต่อ" ก่อนเริ่มถัดไปเสมอ

ข้อมูลที่ต้องมีก่อนเริ่ม:
- SUPABASE_URL = Project URL จาก Supabase dashboard
- SUPABASE_ANON_KEY = anon/public key (ไม่ใช่ service role)
  (Settings → API → Project API keys)

═══════════════════════════════════════════════
PHASE 0 — SPIKE: ทดสอบดึงข้อมูลจาก Supabase
═══════════════════════════════════════════════
เป้าหมาย: ยืนยันว่า Nuxt ดึงข้อมูลจาก Supabase ได้ก่อนสร้าง UI
ทำ:
1. npm install @supabase/supabase-js
2. สร้าง .env กับ SUPABASE_URL และ SUPABASE_ANON_KEY
3. เขียน server/api/prices.get.ts ดึง 10 แถวล่าสุดจาก stock_prices
4. รัน nuxt dev แล้วเรียก /api/prices ดูว่าได้ข้อมูลไหม
🛑 หยุด รายงานผล แล้วรอ "ไปต่อ"

═══════════════════════════════════════════════
PHASE 1 — CORE: หน้า dashboard พื้นฐาน
═══════════════════════════════════════════════
เป้าหมาย: หน้าเดียวที่แสดงตารางราคาหุ้นล่าสุดได้
สร้าง:
- pages/index.vue: ตาราง OHLCV แสดง 5 symbol ล่าสุด
  (symbol, datetime, open, high, low, close, volume)
- composables/useStockPrices.ts: ดึงข้อมูลจาก /api/prices
- nuxt.config.ts: ตั้ง runtimeConfig สำหรับ SUPABASE_URL/KEY
ทดสอบ: รัน nuxt dev แล้วเปิด localhost:3000 ดูว่าตารางแสดงข้อมูลจริง
🛑 หยุด โชว์ screenshot / output แล้วรอ "ไปต่อ"

═══════════════════════════════════════════════
PHASE 2 — POLISH: UX + filter + deploy config
═══════════════════════════════════════════════
เป้าหมาย: ใช้งานได้จริง พร้อม deploy
เพิ่ม:
- filter เลือก symbol และ interval ได้
- แสดงเวลาอัปเดตล่าสุด
- loading state และ error state
- .env.example
- vercel.json (ถ้าต้องการ config พิเศษ)
- README.md: วิธีรันในเครื่อง, วิธีตั้ง env, วิธี deploy Vercel
ทดสอบ: รัน nuxt build ต้องไม่มี error
🛑 สรุปงานทั้งหมดที่ส่งมอบ

═══════════════════════════════════════════════
PHASE 3 — DEPLOY: ขึ้น Vercel
═══════════════════════════════════════════════
เป้าหมาย: มี URL สาธารณะใช้งานได้จริง
ทำ:
1. push โค้ดขึ้น GitHub repo set-price-frontend
2. ไป vercel.com → Import Project → เลือก repo
3. ใส่ environment variables ใน Vercel dashboard:
   SUPABASE_URL และ SUPABASE_ANON_KEY
4. กด Deploy
🛑 แชร์ URL ที่ได้

ข้อกำหนดทั่วไป:
- TypeScript ทุกไฟล์
- ห้าม hardcode credential อ่านจาก env เท่านั้น
- ใช้ Nuxt server routes (/server/api/) ไม่ expose key ฝั่ง client
- mobile-friendly
```

---

## หมายเหตุ

- **anon key vs service role key** — FE ใช้ anon key เท่านั้น, scraper ใช้ service role key
- **Supabase free tier** จะ pause หลัง 7 วันที่ไม่มี request — FE query อยู่แล้วจะช่วย keep alive
- **Row Level Security** — ถ้าอยากให้ข้อมูลเป็น public read ให้เปิด RLS และเพิ่ม policy `SELECT` สำหรับ anon role
