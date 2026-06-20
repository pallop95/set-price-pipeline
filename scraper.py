"""ดึงราคาหุ้น SET จาก TradingView แล้วเซฟเป็น JSON และ CSV"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from tvDatafeed import Interval, TvDatafeed

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# แมป string interval จาก config ไปยัง Interval enum
INTERVAL_MAP = {
    "1m": Interval.in_1_minute,
    "5m": Interval.in_5_minute,
    "15m": Interval.in_15_minute,
    "30m": Interval.in_30_minute,
    "1H": Interval.in_1_hour,
    "4H": Interval.in_4_hour,
    "1D": Interval.in_daily,
    "1W": Interval.in_weekly,
    "1M": Interval.in_monthly,
}


def load_config(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def fetch(tv: TvDatafeed, symbol: str, exchange: str, interval: Interval, n_bars: int) -> pd.DataFrame | None:
    df = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=n_bars)
    if df is None or df.empty:
        return None
    return df


def save(df: pd.DataFrame, symbol: str, interval_str: str, data_dir: Path) -> None:
    tag = f"{symbol}_{interval_str}"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON — snapshot ล่าสุด
    json_dir = data_dir / "json"
    json_dir.mkdir(parents=True, exist_ok=True)
    out = df.reset_index()
    out["datetime"] = out["datetime"].astype(str)
    (json_dir / f"{tag}.json").write_text(out.to_json(orient="records", indent=2))

    # CSV — append dedup ตาม datetime index
    csv_dir = data_dir / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_path = csv_dir / f"{tag}.csv"

    if csv_path.exists():
        existing = pd.read_csv(csv_path, index_col="datetime", parse_dates=True)
        combined = pd.concat([existing, df[~df.index.isin(existing.index)]])
    else:
        combined = df

    combined.sort_index().to_csv(csv_path)
    log.info("บันทึก %s → json + csv (%d rows)", tag, len(combined))


def main():
    config = load_config(Path("symbols.json"))
    n_bars = config.get("n_bars", 10)

    tv_user = os.getenv("TV_USERNAME", "")
    tv_pass = os.getenv("TV_SECRET", "")
    # ใช้ nologin เป็นค่าเริ่มต้น ถ้าไม่มี credential
    tv = TvDatafeed(tv_user, tv_pass) if tv_user else TvDatafeed()

    data_dir = Path("data")
    success, failed = 0, 0

    for entry in config["symbols"]:
        symbol = entry["symbol"]
        exchange = entry["exchange"]
        for interval_str in config["intervals"]:
            interval = INTERVAL_MAP.get(interval_str)
            if interval is None:
                log.warning("ไม่รู้จัก interval '%s' ข้ามไป", interval_str)
                continue
            log.info("กำลังดึง %s:%s interval=%s", exchange, symbol, interval_str)
            try:
                df = fetch(tv, symbol, exchange, interval, n_bars)
                if df is None:
                    log.error("ไม่ได้ข้อมูล %s:%s", exchange, symbol)
                    failed += 1
                    continue
                save(df, symbol, interval_str, data_dir)
                success += 1
            except Exception as e:
                log.error("เกิดข้อผิดพลาด %s:%s — %s", exchange, symbol, e)
                failed += 1

    log.info("สรุป: สำเร็จ %d / ล้มเหลว %d", success, failed)
    if success == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
