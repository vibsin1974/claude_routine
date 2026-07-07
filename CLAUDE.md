# 일일 업무 브리핑 자동화

이 세션이 시작되면 아래 지침에 따라 일일 업무 브리핑을 **즉시** 생성하고 Telegram으로 발송하세요.

## ⚠️ 날짜 기준 (필수 확인)
- **모든 날짜는 한국 표준시(KST, Asia/Seoul, UTC+9) 기준**
- 실행 전 반드시 현재 KST 날짜를 확인 후 오늘/내일 날짜 변수 설정
- Calendar 조회: `startTime=오늘T00:00:00+09:00`, `endTime=내일T23:59:59+09:00`
- 브리핑 헤더에 `YYYY년 MM월 DD일 (요일)` 형식으로 날짜 명시

---

## 실행 순서

1. KST 현재 날짜/시각 확인
2. Google Calendar에서 오늘/내일 일정 조회
3. Gmail에서 미읽음 이메일 조회
4. 주식 시황 조회 (한국/미국)
5. 날씨 정보 조회 (부산 기준)
6. AI 뉴스 검색
7. 브리핑 텍스트 생성
8. `python send_telegram.py` 실행하여 Telegram 발송
9. 결과 보고

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

## 3. 조치 사항 (Action Items)

이메일 및 일정에서 도출된 할 일 목록.
- 🔴 높음 / 🟠 중간 / 🟢 낮음
- 작업명, 현재 상태, 마감일, Next Action

조치 사항이 없으면 섹션 생략.

---

## 4. 주식 시황 (Stock Briefing)

아래 Python 코드를 실행한다.
**반드시 KST(Asia/Seoul, UTC+9) 기준으로 날짜를 계산할 것.**

```python
from pykrx import stock
import yfinance as yf
from datetime import datetime, timedelta
import pytz

# KST 기준 오늘 날짜
KST = pytz.timezone("Asia/Seoul")
now_kst = datetime.now(KST)
today = now_kst.strftime("%Y%m%d")
start = (now_kst - timedelta(days=14)).strftime("%Y%m%d")  # 공휴일/주말 감안 14일 조회

# 한국 주식 (최근 5거래일 종가)
kr_tickers = {"삼성전자": "005930", "두산에너빌리티": "034020"}
print("=== 한국 주식 (최근 5거래일 종가) ===")
for name, code in kr_tickers.items():
    df = stock.get_market_ohlcv(start, today, code)
    if not df.empty:
        recent = df["종가"].tail(5)
        print(f"\n{name}")
        for date, price in recent.items():
            print(f"  {date.strftime('%m/%d')}: {int(price):,}원")
        chg = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100
        print(f"  5일 등락: {chg:+.2f}%")
    else:
        print(f"{name}: 데이터 없음")

# 미국 주식 (최근 5거래일 종가)
us_tickers = {"NVIDIA": "NVDA"}
print("\n=== 미국 주식 (최근 5거래일 종가) ===")
for name, t in us_tickers.items():
    hist = yf.Ticker(t).history(period="10d")
    if not hist.empty:
        recent = hist["Close"].tail(5)
        print(f"\n{name}")
        for date, price in recent.items():
            print(f"  {date.strftime('%m/%d')}: ${price:,.2f}")
        chg = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100
        print(f"  5일 등락: {chg:+.2f}%")
```

네이버 뉴스 API로 종목별 최신 뉴스 3건 조회:

```python
import urllib.request
import urllib.parse
import json
import os
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
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode("utf-8"))
    return data["items"]

keywords = ["삼성전자 주가", "두산에너빌리티", "엔비디아 NVIDIA"]
for kw in keywords:
    print(f"\n=== {kw} 뉴스 ===")
    items = get_naver_news(kw)
    for item in items:
        title = item["title"].replace("<b>","").replace("</b>","")
        desc = item["description"].replace("<b>","").replace("</b>","")
        print(f"제목: {title}")
        print(f"요약: {desc}")
        print(f"날짜: {item['pubDate']}")
```

---

## 5. 날씨 브리핑 (Weather Briefing)

`weather_fetch` 도구 사용:
- `location_name`: `부산광역시`
- `latitude`: `35.1796`
- `longitude`: `129.0756`

오늘: 현재 기온, 최고/최저 기온, 강수 확률, 습도, 미세먼지, 외출 시 참고사항
내일: 최고/최저 기온, 강수 확률, 주의사항

---

## 6. AI 뉴스 브리핑 (AI News Briefing)

웹 검색으로 최신 AI 관련 기사 5건 조회.
검색 키워드: `생성형 AI`, `ChatGPT`, `OpenAI`, `Gemini`, `Claude`, `AI Agent`, `AI 자동화`

포함 항목: 기사 제목, 요약(2~3문장), 기사 링크, 언론사, 게시일

---

## 7. 브리핑 작성 규칙

- 브리핑 상단에 날짜 헤더 포함: `📅 YYYY년 MM월 DD일 (요일) 업무 브리핑`
- 중요도 순 정렬
- 간결하고 읽기 쉬운 형식
- 내용 없는 섹션은 생략
- 전체 분량 3분 이내 읽기 가능
- Telegram Markdown 호환 형식 사용 (`*굵게*`, `` `코드` ``, 이모지 활용)

### 브리핑 출력 형식

```
📅 YYYY년 MM월 DD일 (요일) 업무 브리핑

📆 *일정*
- [오늘] HH:MM 일정명
- [내일] HH:MM 일정명

📧 *중요 이메일*
🔴 발신자 | 제목 | 수신시각
→ 핵심요약 / 조치사항

✅ *조치사항*
🔴 작업명 | 상태 | 마감 | Next Action

📈 *주식 시황*

🔹 삼성전자
  06/23  56,000원
  06/24  56,500원
  06/25  55,800원
  06/26  57,000원
  06/27  57,200원
  5일 등락: +2.14%
  📰 (관련 뉴스 핵심 1~2줄)

🔹 두산에너빌리티
  (동일 형식)
  📰 (관련 뉴스 핵심 1~2줄)

🔹 NVIDIA
  06/23  $131.20
  06/24  $133.50
  06/25  $132.80
  06/26  $135.00
  06/27  $136.40
  5일 등락: +3.96%
  📰 (관련 뉴스 핵심 1~2줄)

🌤 *날씨 (부산)*
오늘: 기온 / 강수확률 / 습도 / 참고사항
내일: 기온 / 강수확률 / 주의사항

🤖 *AI 뉴스*
1. 제목 | 언론사 | 날짜
   요약 2~3문장
   🔗 링크
(5건 동일 형식)
```

---

## 8. Telegram 발송

브리핑 생성 완료 후 실행:

```bash
python send_telegram.py
```

발송 후 성공/실패 여부 보고.

---

## ⚠️ 주의사항
- **날짜/시각은 반드시 KST(Asia/Seoul, UTC+9) 기준** — pytz로 명시적 변환
- pykrx 당일 데이터 없으면 tail(5) 자동으로 직전 거래일 기준 반환
- 공휴일/주말 감안해 14일 범위 조회 후 최근 5거래일 추출
- 뉴스 HTML 태그(`<b>`, `</b>`) 제거 후 출력
- .env 파일은 실행 스크립트와 같은 디렉토리에 위치
- Telegram 메시지 4096자 초과 시 분할 발송 처리
