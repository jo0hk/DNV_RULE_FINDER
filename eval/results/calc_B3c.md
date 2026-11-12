# 계산 정확도: 조건 B3c

- 방식: LLM writes Python code from excerpts with formulas and structured tables (table-text RAG)
- 문제 28개 x 3회, 정답과 1% 이내면 맞음 (괄호는 회차별 최저~최고)

| 전체 | easy | medium | hard | refuse | 근거 조항 정확 | 지어낸 값 | 오류 | 평균 시간(초) |
|---|---|---|---|---|---|---|---|---|
| 83.3% (79~86) | 88.9% | 100.0% | 66.7% | 75.0% | 90.3% | 0/12 | 6 | 2.4 |

## 틀린 답

| 회차 | id | 난이도 | 상태 | 받은 값 | 정답 | 근거 조항 / 이유 |
|---|---|---|---|---|---|---|
| 1 | c15 | hard | calculated | 308.5 | 302.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c18 | hard | calculated | 440.5 | 346.4 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c22 | easy | refused | - | 51.36 |  / Rule length L = 320 m exceeds the upper limit of 300 m for the formula $Z_{R-gr}$ given in DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] (or wave coefficient range for $ |
| 1 | c28 | refuse | error | - | refuse |  / no JSON in answer: '' |
| 2 | c12 | hard | error | - | 6.771 |  / code rejected by safety check: ['__import__'] |
| 2 | c15 | hard | calculated | 308.5 | 302.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c18 | hard | calculated | 440.5 | 346.4 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c28 | refuse | error | - | refuse |  / no JSON in answer: '' |
| 3 | c12 | hard | error | - | 6.771 |  / code rejected by safety check: ['__import__'] |
| 3 | c15 | hard | calculated | 308.5 | 302.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c18 | hard | error | - | 346.4 |  / no JSON in answer: '' |
| 3 | c22 | easy | refused | - | 51.36 |  / Ship length L = 320 m exceeds the upper limit of 300 m for the formula range $90 \le L \le 300$ for $C_w$ in DNV-RU-SHIP Pt.3 Ch.4 Sec.4. |
| 3 | c24 | hard | refused | - | 1558 |  / The ship length L = 420 m exceeds the rule application range (90 <= L <= 300 m) specified in DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.5.2]. |
| 3 | c28 | refuse | error | - | refuse |  / no JSON in answer: '' |
