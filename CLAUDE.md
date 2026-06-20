# 일일 업무 브리핑 자동화

이 세션이 시작되면 아래 지침에 따라 일일 업무 브리핑을 **즉시** 생성하고 Telegram으로 발송하세요.

## 실행 순서

1. Google Calendar에서 오늘/내일 일정 조회 (`mcp__Google-Calendar__list_events`)
2. Gmail에서 미읽음 중요 이메일 조회 (`mcp__Gmail__search_threads`)
3. AI 뉴스 검색 (네이버 뉴스 웹 검색)
4. 날씨 정보 조회 (웹 검색)
5. 브리핑 텍스트 생성 (아래 형식 참고)
6. `python send_telegram.py` 실행하여 Telegram 발송
7. 결과 보고

---

## 1. 일정 (Schedule)

`mcp__Google-Calendar__list_events`로 오늘과 내일의 일정을 조회합니다.

포함 항목:
- 일정명, 날짜 및 시간, 참석자, 장소 또는 회의 링크
- 사전 준비 사항, 참고 자료

정렬: 시간순, 당일 일정 우선

---

## 2. 중요 이메일 (Important Emails)

`mcp__Gmail__search_threads`로 미읽음 이메일 조회 (`query: "is:unread"`, `maxResults: 20`).

긴급도 분류:
- 🔴 긴급: 즉시 응답 필요
- 🟠 중요: 오늘 중 처리
- 🟡 일반: 여유 시 처리

포함 항목: 발신자, 제목, 수신 시각, 핵심 내용 요약, 필요한 조치

---

## 3. 조치 사항 (Action Items)

이메일 및 일정에서 도출된 할 일 목록.

- 🔴 높음 / 🟠 중간 / 🟢 낮음
- 작업명, 현재 상태, 마감일, 다음 행동(Next Action)

---

## 4. AI 뉴스 브리핑 (AI News Briefing)

네이버 뉴스에서 최신 AI 관련 기사 5건 검색.

검색 키워드: `생성형 AI`, `ChatGPT`, `OpenAI`, `Gemini`, `Claude`, `AI Agent`, `AI 자동화`

포함 항목: 기사 제목, 요약(2~3문장), 기사 링크, 언론사, 게시일

---

## 5. 날씨 브리핑 (Weather Briefing)

서울 기준 오늘/내일 날씨 조회.

오늘: 현재 기온, 최고/최저 기온, 강수 확률, 습도, 미세먼지, 외출 시 참고사항
내일: 최고/최저 기온, 강수 확률, 주의사항

---

## 6. 브리핑 작성 규칙

- 중요도 순 정렬
- 간결하고 읽기 쉬운 형식
- 내용 없는 섹션은 생략
- 전체 분량 3분 이내 읽기 가능
- Telegram Markdown 호환 형식 사용

---

## 7. Telegram 발송

브리핑 생성 완료 후 아래 명령 실행:

```bash
python send_telegram.py
```

스크립트는 stdin에서 브리핑 텍스트를 읽어 Telegram으로 발송합니다.

환경변수:
- `Bot_Token` — Telegram 봇 토큰
- `Chat_ID` — 발송 대상 채팅 ID

발송 형식:
```
📋 일일 업무 브리핑
📅 YYYY-MM-DD

[섹션별 내용]
```

---

## 8. 발송 결과 보고

완료 후 결과를 출력합니다:

```
✅ 브리핑 생성 완료
✅ Telegram 발송 성공 (메시지 N건)
📱 Chat ID: XXXXXXXXX
```

오류 시:
```
❌ 실패 단계: [단계명]
❌ 오류: [메시지]
```
