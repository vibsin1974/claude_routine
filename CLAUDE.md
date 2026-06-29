# 일일 업무 브리핑 자동화

이 세션이 시작되면 아래 지침에 따라 일일 업무 브리핑을 **즉시** 생성하고 Telegram으로 발송하세요.

## ⚠️ 날짜 기준 (필수 확인)
- **모든 날짜는 한국 표준시(KST, Asia/Seoul, UTC+9) 기준**
- 실행 전 반드시 현재 KST 날짜를 확인 후 오늘/내일 날짜 변수 설정
- Calendar 조회: `startTime=오늘T00:00:00+09:00`, `endTime=내일T23:59:59+09:00`
- 브리핑 헤더에 `YYYY년 MM월 DD일 (요일)` 형식으로 날짜 명시

---

## 실행 순서

1. Google Calendar에서 오늘/내일 일정 조회
2. Gmail에서 미읽음 이메일 조회 (상세 내용 필요 시 `get_thread` 추가 호출)
3. 주식 시황 조회 (한국/미국) — 아래 Python 코드 실행
4. 날씨 정보 조회 (`wttr.in` API, 부산 기준)
5. AI 뉴스 검색 (웹 검색)
6. 브리핑 텍스트 생성
7. `python send_telegram.py` 실행하여 Telegram 발송
8. 결과 보고

---

## 1. 일정 (Schedule)

`Google Calendar:list_events` 호출 파라미터:
- `startTime`: 오늘 `00:00:00+09:00`
- `endTime`: 내일 `23:59:59+09:00`
- `timeZone`: `Asia/Seoul`
- `orderBy`: `startTime`
- `pageSize`: 20

포함 항목:
- 일정명, 날짜 및 시간(KST), 장소 또는 설명
- 오늘/내일 구분 표시
- 시간순 정렬, 당일 일정 우선

---

## 2. 중요 이메일 (Important Emails)

`Gmail:search_threads` 호출 파라미터:
- `query`: `is:unread in:inbox`
- `pageSize`: 20
- `view`: `THREAD_VIEW_MINIMAL`

제목만으로 내용 파악이 어려울 경우 `Gmail:get_thread`로 본문 추가 조회.

긴급도 분류:
- 🔴 긴급: 즉시 응답 필요
- 🟠 중요: 오늘 중 처리
- 🟡 일반: 여유 시 처리

포함 항목: 발신자, 제목, 수신 시각(KST), 핵심 내용 요약, 필요한 조치

이메일이 없으면 섹션 생략.

---

## 3. 주식 시황 (Stock Briefing)

아래 Python 코드를 실행한다. **pykrx/yfinance 직접 사용 금지** — 환경 네트워크 제한으로 동작하지 않음.

```python
import requests, xml.etree.ElementTree as ET, os, json
from datetime import datetime, timedelta
import pytz

session = requests.Session()
session.verify = '/root/.ccr/ca-bundle.crt'
session.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://finance.naver.com/"})

# ── 한국 주식: 네이버 금융 XML API ──────────────────────────
def get_kr_stock(code, name, count=10):
    url = f"https://fchart.stock.naver.com/sise.nhn?symbol={code}&timeframe=day&count={count}&requestType=0"
    resp = session.get(url, timeout=15)
    resp.encoding = 'euc-kr'
    root = ET.fromstring(resp.text)
    rows = []
    for item in root.findall(".//item"):
        parts = item.get("data", "").split("|")
        if len(parts) >= 5 and parts[4] and parts[4] != '0':
            rows.append((datetime.strptime(parts[0], "%Y%m%d"), int(parts[4])))
    recent = rows[-5:]
    print(f"\n{name}")
    for dt, price in recent:
        print(f"  {dt.strftime('%m/%d')}: {price:,}원")
    if len(recent) >= 2:
        chg = (recent[-1][1] - recent[0][1]) / recent[0][1] * 100
        print(f"  5일 등락: {chg:+.2f}%")
    return recent

print("=== 한국 주식 (최근 5거래일 종가) ===")
get_kr_stock("005930", "삼성전자")
get_kr_stock("034020", "두산에너빌리티")

# ── 미국 주식: yfinance + requests 세션 (curl_cffi 우회) ────
os.environ['SSL_CERT_FILE'] = '/root/.ccr/ca-bundle.crt'
os.environ['CURL_CA_BUNDLE'] = '/root/.ccr/ca-bundle.crt'
import yfinance as yf

yf_session = requests.Session()
yf_session.verify = '/root/.ccr/ca-bundle.crt'
yf_session.headers.update({"User-Agent": "Mozilla/5.0"})

print("\n=== 미국 주식 (최근 5거래일 종가) ===")
for name, ticker in {"NVIDIA": "NVDA"}.items():
    hist = yf.Ticker(ticker, session=yf_session).history(period="10d")
    if not hist.empty:
        recent = hist["Close"].tail(5)
        print(f"\n{name}")
        for dt, price in recent.items():
            print(f"  {dt.strftime('%m/%d')}: ${price:.2f}")
        chg = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100
        print(f"  5일 등락: {chg:+.2f}%")
```

네이버 뉴스 API로 종목별 최신 뉴스 3건 조회:

```python
import urllib.request, urllib.parse, json, os
from dotenv import load_dotenv
load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def get_naver_news(query, display=3):
    enc_query = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/news.json?query={enc_query}&display={display}&sort=date"
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", CLIENT_ID)
    req.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
    return json.loads(urllib.request.urlopen(req).read())["items"]

for kw in ["삼성전자 주가", "두산에너빌리티", "엔비디아 NVIDIA"]:
    print(f"\n=== {kw} 뉴스 ===")
    for item in get_naver_news(kw):
        title = item["title"].replace("<b>","").replace("</b>","")
        print(f"  {title} | {item['pubDate']}")
```

---

## 4. 조치 사항 (Action Items)

이메일 및 일정에서 도출된 할 일 목록.
- 🔴 높음 / 🟠 중간 / 🟢 낮음
- 작업명, 현재 상태, 마감일, Next Action

조치 사항이 없으면 섹션 생략.

---

## 5. AI 뉴스 브리핑 (AI News Briefing)

웹 검색으로 최신 AI 관련 기사 5건 조회.
검색 키워드: `생성형 AI`, `ChatGPT`, `OpenAI`, `Gemini`, `Claude`, `AI Agent`, `AI 자동화`

포함 항목: 기사 제목, 요약(2~3문장), 기사 링크, 언론사, 게시일

---

## 6. 날씨 브리핑 (Weather Briefing)

`wttr.in` JSON API 사용 (`weather_fetch` 도구 없음):

```python
import urllib.request, json

url = "https://wttr.in/Busan?format=j1"
data = json.loads(urllib.request.urlopen(url).read())

current = data["current_condition"][0]
today = data["weather"][0]
tomorrow = data["weather"][1]

print(f"현재 기온: {current['temp_C']}°C (체감 {current['FeelsLikeC']}°C)")
print(f"날씨: {current['weatherDesc'][0]['value']}")
print(f"습도: {current['humidity']}% | 강수량: {current['precipMM']}mm")
print(f"오늘 최고/최저: {today['maxtempC']}°C / {today['mintempC']}°C")
print(f"내일 최고/최저: {tomorrow['maxtempC']}°C / {tomorrow['mintempC']}°C")
```

오늘: 현재 기온, 최고/최저 기온, 강수 확률, 습도, 외출 시 참고사항
내일: 최고/최저 기온, 강수 확률, 주의사항

---

## 7. 브리핑 작성 규칙

- 브리핑 상단에 날짜 헤더 포함: `📅 YYYY년 MM월 DD일 (요일) 업무 브리핑`
- 중요도 순 정렬
- 간결하고 읽기 쉬운 형식
- 내용 없는 섹션은 생략
- 전체 분량 3분 이내 읽기 가능
- Telegram Markdown 호환 형식 사용 (`*굵게*`, `` `코드` ``, 이모지 활용)

---

## 8. Telegram 발송

브리핑 생성 완료 후 실행:

```bash
python send_telegram.py
```

발송 후 성공/실패 여부 보고.
