# 일일 업무 브리핑 자동화

이 세션이 시작되면 아래 지침에 따라 일일 업무 브리핑을 **즉시** 생성하고 Telegram으로 발송한다.

## ⚠️ 날짜 기준 (필수 확인)
- 모든 날짜는 **한국 표준시(KST, Asia/Seoul, UTC+9)** 기준
- 실행 전 반드시 현재 KST 날짜를 확인 후 오늘/내일 날짜 변수 설정
- Calendar 조회: `startTime=오늘T00:00:00+09:00`, `endTime=내일T23:59:59+09:00`
- 브리핑 헤더에 `YYYY년 MM월 DD일 (요일)` 형식으로 날짜 명시

---

## 실행 순서
1. KST 현재 날짜/시각 확인
2. Google Calendar → 오늘/내일 일정 조회
3. Gmail → 미읽음 이메일 조회
4. 주식 시황 조회 (한국/미국)
5. 날씨 조회 (부산)
6. 이슈가 되는 최신 인기뉴스 5건 검색
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

포함 항목: 일정명, 날짜·시간(KST), 장소/설명, 오늘/내일 구분, 시간순 정렬

---

## 2. 중요 이메일 (Important Emails)

`Gmail:search_threads` 호출 파라미터:
- `query`: `is:unread in:inbox`
- `pageSize`: 20
- `view`: `THREAD_VIEW_MINIMAL`

제목만으로 파악 어려우면 `Gmail:get_thread`로 본문 추가 조회.

긴급도 분류: 🔴 긴급 / 🟠 중요 / 🟡 일반
포함 항목: 발신자, 제목, 수신 시각(KST), 핵심 요약, 필요 조치
이메일 없으면 섹션 생략.

---

## 3. 조치 사항 (Action Items)

이메일·일정에서 도출된 할 일 목록.
- 🔴 높음 / 🟠 중간 / 🟢 낮음
- 작업명, 현재 상태, 마감일, Next Action
- 조치 사항 없으면 섹션 생략

---

## 4. 주식 시황 (Stock Briefing)

**반드시 KST(Asia/Seoul, UTC+9) 기준으로 날짜 계산.**

```python
from pykrx import stock
import yfinance as yf
from datetime import datetime, timedelta
import pytz

KST = pytz.timezone("Asia/Seoul")
now_kst = datetime.now(KST)
today = now_kst.strftime("%Y%m%d")
start = (now_kst - timedelta(days=14)).strftime("%Y%m%d")

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

종목별 최신 뉴스 3건 (네이버 뉴스 API):

```python
import urllib.request, urllib.parse, json, os
from dotenv import load_dotenv
load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def get_naver_news(query, display=3):
    url = f"https://openapi.naver.com/v1/search/news.json?query={urllib.parse.quote(query)}&display={display}&sort=date"
    req = urllib.request.Request(url, headers={
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    })
    return json.loads(urllib.request.urlopen(req).read())["items"]

for kw in ["삼성전자 주가", "두산에너빌리티", "엔비디아 NVIDIA"]:
    print(f"\n=== {kw} 뉴스 ===")
    for item in get_naver_news(kw):
        title = item["title"].replace("<b>","").replace("</b>","")
        desc = item["description"].replace("<b>","").replace("</b>","")
        print(f"제목: {title}\n요약: {desc}\n날짜: {item['pubDate']}")
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

## 6. 이슈 뉴스 브리핑 (Trending News Briefing)

특정 키워드 고정 검색이 아닌, 당일 이슈가 되는 최신 인기뉴스를 웹 검색으로 조회한다.

- 검색 방식: 특정 분야로 한정하지 않고 그날 화제가 된 주요 뉴스(정치·경제·사회·국제·이슈 전반)를 대상으로 검색
- 검색 예시 쿼리: `오늘 주요 뉴스`, `실시간 이슈`, `최신 화제 뉴스` 등 포괄적 키워드 사용
- 결과 중 신뢰도 높은 언론사 기사, 최근 게시일 기준으로 상위 5건 선정
- 특정 주제(AI 등)로 국한하지 않고 그 시점에 가장 이슈가 되는 뉴스 우선

포함 항목: 기사 제목, 요약(2~3문장), 기사 링크, 언론사, 게시일

---

## 7. 브리핑 작성 규칙

- 상단 날짜 헤더: `📅 YYYY년 MM월 DD일 (요일) 업무 브리핑`
- 중요도 순 정렬, 간결하고 읽기 쉬운 형식
- 내용 없는 섹션은 생략
- 전체 분량 3분 이내 읽기 가능
- Telegram Markdown 호환 형식 사용 (`*굵게*`, `` `코드` ``, 이모지 활용)

### 브리핑 출력 형식

```
📅 YYYY년 MM월 DD일 (요일) 업무 브리핑

📆 *일정*
- [오늘] HH:MM 일정명 (장소/설명)
- [내일] HH:MM 일정명 (장소/설명)

📧 *중요 이메일*
🔴 발신자 | 제목 | HH:MM
  요약 · 필요 조치

✅ *조치 사항*
🔴 작업명 | 상태 | 마감일 | Next Action

📈 *주식 시황*
- 삼성전자: N,NNN원 (5일 등락 ±N.NN%)
- 두산에너빌리티: N,NNN원 (5일 등락 ±N.NN%)
- NVIDIA: $NNN.NN (5일 등락 ±N.NN%)
- 관련 뉴스: 제목 - 요약

🌤️ *날씨 (부산)*
- 오늘: 최고/최저 N℃, 강수 확률 N%, 습도 N%, 미세먼지 상태
- 내일: 최고/최저 N℃, 강수 확률 N%

📰 *오늘의 이슈 뉴스*
1. 제목 (언론사, 게시일)
   요약
   링크
```

---

## 8. Telegram 발송

브리핑 생성 완료 후 실행:

```bash
python send_telegram.py
```

발송 후 성공/실패 여부 보고.
