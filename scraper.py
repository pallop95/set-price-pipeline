"""ดึงราคาหุ้น SET จาก TradingView แล้วเซฟเป็น JSON และ CSV"""
import json
import logging
import os
import time
from pathlib import Path

import pandas as pd
from tvDatafeed import Interval, TvDatafeed

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

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

TIMEZONE = "Asia/Bangkok"
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 2   # วินาที (คูณ 2 ทุกรอบ)
REQUEST_DELAY = 1.5  # หน่วงระหว่าง symbol กัน WebSocket หลุด


def load_config(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def fetch_with_retry(tv: TvDatafeed, symbol: str, exchange: str, interval: Interval, n_bars: int) -> pd.DataFrame | None:
    """ดึงข้อมูลพร้อม retry 3 ครั้ง backoff เลขคู่"""
    delay = RETRY_BACKOFF
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            df = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=n_bars)
            if df is not None and not df.empty:
                return df
            log.warning("ครั้งที่ %d/%d: ได้ DataFrame ว่าง %s:%s", attempt, RETRY_ATTEMPTS, exchange, symbol)
        except Exception as e:
            log.warning("ครั้งที่ %d/%d: exception %s:%s — %s", attempt, RETRY_ATTEMPTS, exchange, symbol, e)
        if attempt < RETRY_ATTEMPTS:
            time.sleep(delay)
            delay *= 2
    return None


def localize(df: pd.DataFrame) -> pd.DataFrame:
    """ติด timezone Asia/Bangkok ให้ index (tvDatafeed ส่งมาเป็น naive แต่เป็นเวลา BKK อยู่แล้ว)"""
    if df.index.tz is None:
        df.index = df.index.tz_localize(TIMEZONE, ambiguous="infer", nonexistent="shift_forward")
    else:
        df.index = df.index.tz_convert(TIMEZONE)
    return df


def save(df: pd.DataFrame, symbol: str, interval_str: str, data_dir: Path) -> None:
    tag = f"{symbol}_{interval_str}"

    # JSON — snapshot ล่าสุด (เขียนทับทุกรอบ)
    json_dir = data_dir / "json"
    json_dir.mkdir(parents=True, exist_ok=True)
    out = df.reset_index()
    out["datetime"] = out["datetime"].astype(str)
    (json_dir / f"{tag}.json").write_text(out.to_json(orient="records", indent=2))

    # CSV — แยกรายเดือน + dedup ตาม datetime index (กัน repo บวม)
    csv_dir = data_dir / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)

    for month, group in df.groupby(df.index.strftime("%Y-%m")):
        csv_path = csv_dir / f"{tag}_{month}.csv"
        if csv_path.exists():
            existing = pd.read_csv(csv_path, index_col="datetime", parse_dates=True)
            # ทำให้ timezone ตรงกันก่อน concat
            if existing.index.tz is None:
                existing.index = existing.index.tz_localize(TIMEZONE)
            new_rows = group[~group.index.isin(existing.index)]
            combined = pd.concat([existing, new_rows]).sort_index()
        else:
            combined = group.sort_index()
        combined.to_csv(csv_path)

    total_rows = len(df)
    log.info("บันทึก %s → json + csv/%s_<YYYYMM>.csv (%d rows)", tag, tag, total_rows)


def main():
    config = load_config(Path("symbols.json"))
    n_bars = config.get("n_bars", 10)

    tv_user = os.getenv("TV_USERNAME", "")
    tv_pass = os.getenv("TV_SECRET", "")
    tv = TvDatafeed(tv_user, tv_pass) if tv_user else TvDatafeed()

    data_dir = Path("data")
    success, failed = 0, 0
    failed_list: list[str] = []

    symbols = config["symbols"]
    intervals = config["intervals"]
    total = len(symbols) * len(intervals)

    log.info("เริ่มดึงข้อมูล %d symbol × %d interval = %d งาน", len(symbols), len(intervals), total)

    for i, entry in enumerate(symbols):
        symbol = entry["symbol"]
        exchange = entry["exchange"]

        for interval_str in intervals:
            interval = INTERVAL_MAP.get(interval_str)
            if interval is None:
                log.warning("ไม่รู้จัก interval '%s' ข้ามไป", interval_str)
                failed += 1
                failed_list.append(f"{symbol}:{interval_str}(unknown interval)")
                continue

            log.info("[%d/%d] กำลังดึง %s:%s interval=%s", success + failed + 1, total, exchange, symbol, interval_str)

            df = fetch_with_retry(tv, symbol, exchange, interval, n_bars)

            if df is None:
                log.error("ล้มเหลวทุก retry: %s:%s interval=%s", exchange, symbol, interval_str)
                failed += 1
                failed_list.append(f"{exchange}:{symbol}@{interval_str}")
                continue

            try:
                df = localize(df)
                save(df, symbol, interval_str, data_dir)
                success += 1
            except Exception as e:
                log.error("บันทึกล้มเหลว %s:%s — %s", exchange, symbol, e)
                failed += 1
                failed_list.append(f"{exchange}:{symbol}@{interval_str}(save error)")

            # หน่วงเล็กน้อยระหว่าง request
            if i < len(symbols) - 1:
                time.sleep(REQUEST_DELAY)

    log.info("═══ สรุป: สำเร็จ %d / ล้มเหลว %d ═══", success, failed)
    if failed_list:
        log.warning("รายการที่ล้มเหลว: %s", ", ".join(failed_list))

    if success == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
