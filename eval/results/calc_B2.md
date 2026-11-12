# 계산 정확도: 조건 B2

- 방식: LLM writes Python code from rule excerpts with formulas added
- 문제 28개 x 3회, 정답과 1% 이내면 맞음 (괄호는 회차별 최저~최고)

| 전체 | easy | medium | hard | refuse | 근거 조항 정확 | 지어낸 값 | 오류 | 평균 시간(초) |
|---|---|---|---|---|---|---|---|---|
| 72.6% (71~75) | 83.3% | 70.4% | 63.0% | 83.3% | 94.4% | 0/12 | 5 | 2.8 |

## 틀린 답

| 회차 | id | 난이도 | 상태 | 받은 값 | 정답 | 근거 조항 / 이유 |
|---|---|---|---|---|---|---|
| 1 | c04 | medium | calculated | 1006 | 10.06 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1.1] |
| 1 | c05 | hard | calculated | 1738 | 9.591 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 1 | c06 | easy | calculated | 568.5 | 7.75 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1.1] |
| 1 | c07 | medium | calculated | 9.32 | 10.27 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 1 | c12 | hard | error | - | 6.771 |  / code failed: Traceback (most recent call last):
  File "C:\Users\jooha\AppData\Local\Temp\tmpca5zkths\llm_code.py", line 1, in <module>
    math
NameError: n |
| 1 | c15 | hard | calculated | 0.3 | 302.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c17 | medium | error | - | 463.9 |  / code rejected by safety check: ['__import__'] |
| 1 | c18 | hard | calculated | 352.4 | 346.4 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c05 | hard | calculated | 1529 | 9.591 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 2 | c06 | easy | calculated | 566.5 | 7.75 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 2 | c07 | medium | calculated | 9.318 | 10.27 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 2 | c15 | hard | calculated | 0.3 | 302.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c17 | medium | error | - | 463.9 |  / code rejected by safety check: ['__import__'] |
| 2 | c18 | hard | calculated | 0.36 | 346.4 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c28 | refuse | error | - | refuse |  / no JSON in answer: '' |
| 3 | c05 | hard | calculated | 1738 | 9.591 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 3 | c06 | easy | calculated | 566.5 | 7.75 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1.1] |
| 3 | c07 | medium | calculated | 1079 | 10.27 | Pt.3 Ch.6 Sec.3 [1.1] |
| 3 | c14 | medium | calculated | 361.9 | 442 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c15 | hard | calculated | 0.3 | 302.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c17 | medium | calculated | 0.46 | 463.9 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c18 | hard | calculated | 440.5 | 346.4 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c28 | refuse | error | - | refuse |  / no JSON in answer: '' |
