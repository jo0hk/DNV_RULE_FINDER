# 계산 정확도: 조건 B2

- 방식: LLM writes Python code from rule excerpts with formulas added
- 문제 28개 x 3회, 정답과 1% 이내면 맞음 (괄호는 회차별 최저~최고)

| 전체 | easy | medium | hard | refuse | 근거 조항 정확 | 지어낸 값 | 오류 | 평균 시간(초) |
|---|---|---|---|---|---|---|---|---|
| 72.6% (68~79) | 66.7% | 88.9% | 59.3% | 75.0% | 93.1% | 0/12 | 8 | 2.9 |

## 틀린 답

| 회차 | id | 난이도 | 상태 | 받은 값 | 정답 | 근거 조항 / 이유 |
|---|---|---|---|---|---|---|
| 1 | c05 | hard | calculated | 7.09 | 9.591 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 1 | c06 | easy | calculated | 9.75 | 7.75 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1.1] |
| 1 | c08 | easy | error | - | 8.504 |  / code failed: Traceback (most recent call last):
  File "C:\Users\jooha\AppData\Local\Temp\tmpu0x6fn24\llm_code.py", line 1, in <module>
    math
NameError: n |
| 1 | c10 | medium | error | - | 10.75 |  / code failed: Traceback (most recent call last):
  File "C:\Users\jooha\AppData\Local\Temp\tmpfy_rjq67\llm_code.py", line 1, in <module>
    math
NameError: n |
| 1 | c15 | hard | calculated | 308.5 | 302.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c16 | hard | calculated | 0.16 | 164.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c18 | hard | calculated | 440.5 | 346.4 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c20 | hard | error | - | 1.059 |  / code failed: Traceback (most recent call last):
  File "C:\Users\jooha\AppData\Local\Temp\tmpa73hmhfu\llm_code.py", line 15, in <module>
    Z_R_gr = k * ((1 |
| 1 | c28 | refuse | error | - | refuse |  / no JSON in answer: '' |
| 2 | c05 | hard | calculated | 5.11 | 9.591 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1.1] |
| 2 | c06 | easy | calculated | 9.75 | 7.75 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1.1] |
| 2 | c07 | medium | calculated | 9.32 | 10.27 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 2 | c13 | easy | calculated | 0.32 | 318.1 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c16 | hard | calculated | 0.16 | 164.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c17 | medium | calculated | 0.39 | 463.9 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c18 | hard | calculated | 0.31 | 346.4 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c28 | refuse | error | - | refuse |  / no JSON in answer: '' |
| 3 | c05 | hard | calculated | 5.09 | 9.591 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 3 | c06 | easy | calculated | 9.75 | 7.75 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1.1] |
| 3 | c08 | easy | error | - | 8.504 |  / code failed: Traceback (most recent call last):
  File "C:\Users\jooha\AppData\Local\Temp\tmp26796syl\llm_code.py", line 1, in <module>
    math
NameError: n |
| 3 | c15 | hard | error | - | 302.3 |  / code failed: Traceback (most recent call last):
  File "C:\Users\jooha\AppData\Local\Temp\tmpjaqkbi6o\llm_code.py", line 48, in <module>
    Z = fu * abs(P)  |
| 3 | c16 | hard | calculated | 0.16 | 164.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c28 | refuse | error | - | refuse |  / no JSON in answer: '' |
