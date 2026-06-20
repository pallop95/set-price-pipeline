"""Phase 0 spike — ทดสอบว่า tvdatafeed ดึงข้อมูล SET:KTB ได้ไหม (nologin)"""
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()  # nologin

print("กำลังดึง SET:KTB 1D 10 bars (nologin)...")
try:
    df = tv.get_hist(symbol="KTB", exchange="SET", interval=Interval.in_daily, n_bars=10)
    if df is None or df.empty:
        print("FAIL: ได้ DataFrame ว่างเปล่า")
    else:
        print("SUCCESS: ดึงข้อมูลได้!")
        print(df.to_string())
except Exception as e:
    print(f"FAIL: {e}")
