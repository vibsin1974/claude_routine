#!/usr/bin/env python3
"""주식 시황 조회 스크립트 — 한국(네이버 금융) + 미국(yfinance + requests 세션)"""

import os
import sys
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

CA_BUNDLE = "/root/.ccr/ca-bundle.crt"

# curl_cffi가 CA bundle을 무시하는 문제 우회
os.environ["SSL_CERT_FILE"] = CA_BUNDLE
os.environ["CURL_CA_BUNDLE"] = CA_BUNDLE

session = requests.Session()
session.verify = CA_BUNDLE
session.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://finance.naver.com/"})


# ── 한국 주식: 네이버 금융 XML API ─────────────────────────────────────────────
def get_kr_stock(code: str, name: str, count: int = 10) -> list:
    url = (
        f"https://fchart.stock.naver.com/sise.nhn"
        f"?symbol={code}&timeframe=day&count={count}&requestType=0"
    )
    resp = session.get(url, timeout=15)
    resp.encoding = "euc-kr"
    root = ET.fromstring(resp.text)
    rows = []
    for item in root.findall(".//item"):
        parts = item.get("data", "").split("|")
        if len(parts) >= 5 and parts[4] and parts[4] != "0":
            rows.append((datetime.strptime(parts[0], "%Y%m%d"), int(parts[4])))
    recent = rows[-5:]
    print(f"\n{name} ({code})")
    for dt, price in recent:
        print(f"  {dt.strftime('%m/%d')}: {price:,}원")
    if len(recent) >= 2:
        chg = (recent[-1][1] - recent[0][1]) / recent[0][1] * 100
        print(f"  5일 등락: {chg:+.2f}%")
    return recent


# ── 미국 주식: yfinance + requests 세션 (curl_cffi TLS 오류 우회) ─────────────
def get_us_stock(ticker: str, name: str) -> None:
    import yfinance as yf

    yf_session = requests.Session()
    yf_session.verify = CA_BUNDLE
    yf_session.headers.update({"User-Agent": "Mozilla/5.0"})

    hist = yf.Ticker(ticker, session=yf_session).history(period="10d")
    if hist.empty:
        print(f"\n{name} ({ticker}): 데이터 없음")
        return
    recent = hist["Close"].tail(5)
    print(f"\n{name} ({ticker})")
    for dt, price in recent.items():
        print(f"  {dt.strftime('%m/%d')}: ${price:.2f}")
    chg = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100
    print(f"  5일 등락: {chg:+.2f}%")


# ── 네이버 뉴스 API: 종목별 최신 3건 ──────────────────────────────────────────
def get_naver_news(query: str, display: int = 3) -> list:
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        return []
    enc_query = urllib.parse.quote(query)
    url = (
        f"https://openapi.naver.com/v1/search/news.json"
        f"?query={enc_query}&display={display}&sort=date"
    )
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", client_id)
    req.add_header("X-Naver-Client-Secret", client_secret)
    try:
        return json.loads(urllib.request.urlopen(req).read())["items"]
    except Exception:
        return []


def print_news(keyword: str) -> None:
    items = get_naver_news(keyword)
    if not items:
        return
    print(f"\n  📰 {keyword} 뉴스")
    for item in items:
        title = item["title"].replace("<b>", "").replace("</b>", "")
        print(f"    · {title} | {item['pubDate']}")


# ── 메인 ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== 한국 주식 (최근 5거래일 종가) ===")
    get_kr_stock("005930", "삼성전자")
    print_news("삼성전자 주가")

    get_kr_stock("034020", "두산에너빌리티")
    print_news("두산에너빌리티")

    print("\n=== 미국 주식 (최근 5거래일 종가) ===")
    get_us_stock("NVDA", "NVIDIA")
    print_news("엔비디아 NVIDIA")
