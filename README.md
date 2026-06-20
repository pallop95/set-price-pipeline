# set-price-pipeline

ดึงราคาหุ้นไทย (SET) จาก TradingView อัตโนมัติผ่าน GitHub Actions ทุก 30 นาทีช่วงตลาดเปิด แล้ว commit ผลลัพธ์กลับเข้า repo เป็น JSON และ CSV

## โปรเจกต์ทำอะไร

- ใช้ [tvdatafeed (rongardF fork)](https://github.com/rongardF/tvdatafeed) ดึงข้อมูล OHLCV จาก TradingView
- รันอัตโนมัติผ่าน GitHub Actions วันจันทร์–ศุกร์ ทุก 30 นาที ช่วง 10:00–16:30 น. (BKK)
- เซฟข้อมูลเป็น `data/json/<SYMBOL>_<INTERVAL>.json` และ `data/csv/<SYMBOL>_<INTERVAL>_<YYYYMM>.csv`
- CSV แยกรายเดือน ป้องกัน repo บวม และ dedup ตาม timestamp อัตโนมัติ

## วิธีรันในเครื่อง

```bash
pip install -r requirements.txt
python scraper.py
```

ผลลัพธ์จะอยู่ใน `data/json/` และ `data/csv/`

## วิธีเพิ่ม/ลบ symbol

แก้ไขไฟล์ `symbols.json` โดยไม่ต้องแตะโค้ด:

```json
{
  "symbols": [
    {"symbol": "KTB", "exchange": "SET"},
    {"symbol": "PTT", "exchange": "SET"}
  ],
  "intervals": ["1D"],
  "n_bars": 10
}
```

interval ที่รองรับ: `1m` `5m` `15m` `30m` `1H` `4H` `1D` `1W` `1M`

## วิธีตั้ง GitHub Secrets

ไปที่ **Settings → Secrets and variables → Actions** แล้วเพิ่ม:

| Secret | จำเป็น | คำอธิบาย |
|--------|--------|----------|
| `TV_USERNAME` | ไม่ | username TradingView (ถ้า login ด้วย Google ไม่ต้องใส่) |
| `TV_SECRET` | ไม่ | รหัสผ่าน TradingView |
| `WEBHOOK_URL` | ไม่ | URL สำหรับแจ้งเตือนเมื่อ job ล้มเหลว (Discord/Slack) |

> ไม่ใส่ secret ก็ได้ — scraper จะใช้ nologin ซึ่งดึงหุ้น SET ได้ครบ

## คำเตือน

1. **tvdatafeed เป็น unofficial library** — reverse-engineer จาก WebSocket ของ TradingView อาจหยุดทำงานได้ถ้า TradingView เปลี่ยน protocol โดยไม่แจ้ง
2. **GitHub ปิด scheduled workflow อัตโนมัติ** ถ้า repo ไม่มี activity นาน 60 วัน ให้ push หรือกด Run workflow ด้วยมือเพื่อ keep alive
