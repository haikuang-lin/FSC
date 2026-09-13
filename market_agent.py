#!/usr/bin/env python3
"""Create a US-market close research brief and optionally deliver it to Telegram."""
from __future__ import annotations

import json
import os
import pathlib
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import yfinance as yf

ROOT = pathlib.Path(__file__).resolve().parent
WATCHLIST = json.loads((ROOT / "config" / "watchlist.json").read_text())
ET = ZoneInfo("America/New_York")


def quote(symbol: str) -> dict | None:
    try:
        hist = yf.Ticker(symbol).history(period="5d", auto_adjust=True)
        if len(hist) < 2:
            return None
        close = float(hist["Close"].iloc[-1])
        prior = float(hist["Close"].iloc[-2])
        return {"symbol": symbol, "close": close, "change": (close / prior - 1) * 100,
                "volume": int(hist["Volume"].iloc[-1])}
    except Exception:
        return None


def build_prompt(groups: dict[str, list[dict]]) -> str:
    data = json.dumps(groups, ensure_ascii=False)
    return f"""You are a cautious US-equity research editor. Write Traditional Chinese.
Using only this close-price data, produce a concise daily research brief. Do not invent news,
earnings, price targets, or catalysts. Label all interpretations as observations, not advice.
Cover each of the three themes, name unusual moves (absolute change >= 3%), and finish with
'明日觀察清單'. Mention that this is not investment advice. Data: {data}"""


def ai_summary(groups: dict[str, list[dict]]) -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return "未設定 OPENAI_API_KEY；以下僅提供收盤數據，未產生 AI 研究摘要。"
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "temperature": 0.2,
              "messages": [{"role": "user", "content": build_prompt(groups)}]},
        timeout=90,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def render_table(rows: list[dict]) -> str:
    if not rows:
        return "資料暫時無法取得。"
    lines = ["| 代號 | 收盤價 | 單日變動 | 成交量 |", "|---|---:|---:|---:|"]
    lines += [f"| {r['symbol']} | ${r['close']:,.2f} | {r['change']:+.2f}% | {r['volume']:,} |" for r in rows]
    return "\n".join(lines)


def telegram_send(report: str, report_path: pathlib.Path) -> None:
    token, chat_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram secrets not configured; report saved without delivery.")
        return
    api = f"https://api.telegram.org/bot{token}"
    headline = report[:3500]
    response = requests.post(f"{api}/sendMessage", json={"chat_id": chat_id, "text": headline}, timeout=30)
    response.raise_for_status()
    with report_path.open("rb") as f:
        response = requests.post(f"{api}/sendDocument", data={"chat_id": chat_id},
                                 files={"document": (report_path.name, f, "text/markdown")}, timeout=60)
    response.raise_for_status()


def main() -> None:
    now = datetime.now(ET)
    groups = {theme: [item for s in symbols if (item := quote(s))] for theme, symbols in WATCHLIST.items()}
    summary = ai_summary(groups)
    sections = [f"# 美股每日收盤研究報告｜{now:%Y-%m-%d}（美東）", "", summary]
    labels = {"aerospace_space": "航太太空", "ai": "AI", "sports": "運動"}
    for theme, rows in groups.items():
        sections += ["", f"## {labels[theme]}", render_table(rows)]
    report = "\n".join(sections) + "\n"
    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    path = out / f"us-market-close-{now:%Y-%m-%d}.md"
    path.write_text(report, encoding="utf-8")
    telegram_send(report, path)


if __name__ == "__main__":
    main()
