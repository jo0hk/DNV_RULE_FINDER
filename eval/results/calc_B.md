# 계산 정확도: 조건 B

- 방식: LLM calculates from rule excerpts with formulas added as text
- 문제 28개 x 3회, 정답과 1% 이내면 맞음 (괄호는 회차별 최저~최고)

| 전체 | easy | medium | hard | refuse | 근거 조항 정확 | 지어낸 값 | 오류 | 평균 시간(초) |
|---|---|---|---|---|---|---|---|---|
| 25.0% (21~29) | 16.7% | 25.9% | 0.0% | 91.7% | 84.7% | 1/12 | 0 | 1.7 |

## 틀린 답

| 회차 | id | 난이도 | 상태 | 받은 값 | 정답 | 근거 조항 / 이유 |
|---|---|---|---|---|---|---|
| 1 | c04 | medium | calculated | 9.941 | 10.06 | Pt.3 Ch.6 Sec.3 [1.1] |
| 1 | c05 | hard | calculated | 11.23 | 9.591 | Pt.3 Ch.6 Sec.3 [1.1] |
| 1 | c06 | easy | calculated | 7.498 | 7.75 | Pt.3 Ch.6 Sec.3 [1.1] |
| 1 | c07 | medium | calculated | 11.24 | 10.27 | Pt.3 Ch.6 Sec.3 [1.1] |
| 1 | c08 | easy | calculated | 11.23 | 8.504 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 1 | c09 | hard | calculated | 15.35 | 10.66 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 1 | c10 | medium | calculated | 15.35 | 10.75 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 1 | c11 | hard | calculated | 11.23 | 9.186 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 1 | c12 | hard | calculated | 7.39 | 6.771 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 1 | c13 | easy | calculated | 1134 | 318.1 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c14 | medium | calculated | 313.4 | 442 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c15 | hard | calculated | 418 | 302.3 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c16 | hard | calculated | 56.45 | 164.3 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c18 | hard | refused | - | 346.4 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] / For stiffeners with one fixed end and one simply supported end, Table 5 and the rule excerpts do not provide a formula for |
| 1 | c19 | medium | calculated | 15.31 | 28.44 | Pt.3 Ch.5 Sec.2 [1.3] |
| 1 | c20 | hard | calculated | 0.4492 | 1.059 | Pt.3 Ch.5 Sec.2 [1.3] |
| 1 | c21 | medium | calculated | 1.259 | 5.171 | Pt.3 Ch.5 Sec.2 [1.3] |
| 1 | c22 | easy | refused | - | 51.36 | Pt.3 Ch.5 Sec.2 [1.3] / The formula for minimum gross midship section modulus in Pt.3 Ch.5 Sec.2 [1.3] applies to L <= 300 m (as Cw0 = Cw for L > 90 m, but L =  |
| 1 | c23 | easy | calculated | 526.4 | 296.3 | Pt.3 Ch.5 Sec.2 [1.5.2] |
| 1 | c24 | hard | refused | - | 1558 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.5.1] / The requirement in [1.5.2] applies to self propelled ships with length above 90 m and up to 350 m. For L = 420 m, it is ou |
| 2 | c04 | medium | calculated | 10.37 | 10.06 | Pt.3 Ch.6 Sec.3 [1.1] |
| 2 | c05 | hard | calculated | 11.23 | 9.591 | Pt.3 Ch.6 Sec.3 [1.1] |
| 2 | c06 | easy | calculated | 7.48 | 7.75 | Pt.3 Ch.6 Sec.3 [1.1] |
| 2 | c07 | medium | calculated | 11.23 | 10.27 | Pt.3 Ch.6 Sec.3 [1.1] |
| 2 | c08 | easy | calculated | 11.05 | 8.504 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c09 | hard | calculated | 15.36 | 10.66 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c10 | medium | calculated | 15.35 | 10.75 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c11 | hard | calculated | 11.23 | 9.186 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c12 | hard | calculated | 7.42 | 6.771 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c13 | easy | calculated | 566.2 | 318.1 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c14 | medium | calculated | 313.4 | 442 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c15 | hard | calculated | 43.1 | 302.3 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c16 | hard | calculated | 78.03 | 164.3 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c17 | medium | calculated | 566.2 | 463.9 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c18 | hard | refused | - | 346.4 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] / Formula for one fixed and one simply supported end with pressure on stiffener side and hull girder compression is not full |
| 2 | c19 | medium | calculated | 15.35 | 28.44 | Pt.3 Ch.5 Sec.2 [1.3] |
| 2 | c20 | hard | refused | - | 1.059 | Pt.3 Ch.5 Sec.2 [1.3] / The formula produces section modulus in m3, but the numerical result from the formula is abnormally small for an 85m ship due to unit/sc |
| 2 | c21 | medium | calculated | 2.216 | 5.171 | Pt.3 Ch.5 Sec.2 [1.3] |
| 2 | c22 | easy | calculated | 11.23 | 51.36 | Pt.3 Ch.5 Sec.2 [1.3] |
| 2 | c23 | easy | calculated | 111.4 | 296.3 | Pt.3 Ch.5 Sec.2 [1.5.2] |
| 2 | c24 | hard | refused | - | 1558 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.5.1] / The requirement in [1.5.2] applies to self propelled ships with length above 90 m and up to 350 m. The given length L = 42 |
| 3 | c04 | medium | calculated | 11.23 | 10.06 | Pt.3 Ch.6 Sec.1 [1.1.1] |
| 3 | c05 | hard | calculated | 11.23 | 9.591 | Pt.3 Ch.6 Sec.3 [1.1] |
| 3 | c06 | easy | calculated | 7.41 | 7.75 | Pt.3 Ch.6 Sec.3 [1.1] |
| 3 | c07 | medium | calculated | 11.23 | 10.27 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 3 | c08 | easy | calculated | 11.23 | 8.504 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 3 | c09 | hard | calculated | 15.35 | 10.66 | Pt.3 Ch.6 Sec.4 [1.1] |
| 3 | c10 | medium | calculated | 15.35 | 10.75 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 3 | c11 | hard | calculated | 11.23 | 9.186 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 3 | c12 | hard | calculated | 7.42 | 6.771 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 3 | c13 | easy | calculated | 1110 | 318.1 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c14 | medium | calculated | 469.7 | 442 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c15 | hard | calculated | 110.2 | 302.3 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c16 | hard | calculated | 111.2 | 164.3 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c17 | medium | calculated | 566.2 | 463.9 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c18 | hard | calculated | 319.5 | 346.4 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c19 | medium | calculated | 15.35 | 28.44 | Pt.3 Ch.5 Sec.2 [1.3] |
| 3 | c20 | hard | calculated | 0.5489 | 1.059 | Pt.3 Ch.5 Sec.2 [1.3] |
| 3 | c21 | medium | calculated | 1.701 | 5.171 | Pt.3 Ch.5 Sec.2 [1.3] |
| 3 | c22 | easy | calculated | 24.33 | 51.36 | Pt.3 Ch.5 Sec.2 [1.3] |
| 3 | c23 | easy | calculated | 113.6 | 296.3 | Pt.3 Ch.5 Sec.2 [1.5.2] |
| 3 | c24 | hard | refused | - | 1558 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.5.1] / The requirement in [1.5.2] applies to self propelled ships with length above 90 m and up to 350 m. For L = 420 m, it is ou |
| 3 | c28 | refuse | calculated | 1.762 | refuse | Pt.3 Ch.5 Sec.2 [1.3] |
