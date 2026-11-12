# 계산 정확도: 조건 B

- 방식: LLM calculates from rule excerpts with formulas added as text
- 문제 28개 x 3회, 정답과 1% 이내면 맞음 (괄호는 회차별 최저~최고)

| 전체 | easy | medium | hard | refuse | 근거 조항 정확 | 지어낸 값 | 오류 | 평균 시간(초) |
|---|---|---|---|---|---|---|---|---|
| 27.4% (25~29) | 33.3% | 22.2% | 0.0% | 91.7% | 86.1% | 1/12 | 0 | 1.9 |

## 틀린 답

| 회차 | id | 난이도 | 상태 | 받은 값 | 정답 | 근거 조항 / 이유 |
|---|---|---|---|---|---|---|
| 1 | c04 | medium | calculated | 11.22 | 10.06 | Pt.3 Ch.6 Sec.3 [1.1] |
| 1 | c05 | hard | calculated | 11.54 | 9.591 | Pt.3 Ch.6 Sec.3 [1.1.1] |
| 1 | c06 | easy | calculated | 7.45 | 7.75 | Pt.3 Ch.6 Sec.3 [1.1.1] |
| 1 | c07 | medium | calculated | 11.23 | 10.27 | Pt.3 Ch.6 Sec.3 [1.1] |
| 1 | c08 | easy | calculated | 11.23 | 8.504 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 1 | c09 | hard | calculated | 11.23 | 10.66 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 1 | c10 | medium | calculated | 16.39 | 10.75 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 1 | c11 | hard | refused | - | 9.186 | Pt.3 Ch.6 Sec.4 [1.1.1] / Design pressure unit in the formula must be in kN/m2. Given pressure 0.15 N/mm2 = 150 kN/m2 is out of typical range or unit mismatch.  |
| 1 | c12 | hard | calculated | 7.42 | 6.771 | Pt.3 Ch.6 Sec.4 [1.1] |
| 1 | c14 | medium | calculated | 315.6 | 442 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c15 | hard | calculated | 116.9 | 302.3 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c16 | hard | calculated | 52.34 | 164.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c17 | medium | calculated | 526.5 | 463.9 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c18 | hard | calculated | 319.5 | 346.4 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c19 | medium | calculated | 24.01 | 28.44 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] |
| 1 | c20 | hard | calculated | 0.5488 | 1.059 | Pt.3 Ch.5 Sec.2 [1.3] |
| 1 | c21 | medium | calculated | 2.213 | 5.171 | Pt.3 Ch.5 Sec.2 [1.3] |
| 1 | c22 | easy | refused | - | 51.36 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / The rule for minimum section modulus is applicable for L up to 300 m (L > 90 m and L <= 300 m via Cw0 / Cw formula limits, o |
| 1 | c23 | easy | calculated | 113.7 | 296.3 | Pt.3 Ch.5 Sec.2 [1.5.2] |
| 1 | c24 | hard | refused | - | 1558 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.5.2] / L = 420 m is outside the valid range for the moment of inertia formula (L <= 300 m, as Cw is defined for L <= 500 but exce |
| 1 | c28 | refuse | calculated | 17.52 | refuse | Pt.3 Ch.5 Sec.2 [1.3] |
| 2 | c04 | medium | calculated | 11.23 | 10.06 | Pt.3 Ch.6 Sec.3 [1.1] |
| 2 | c05 | hard | refused | - | 9.591 | Pt.3 Ch.6 Sec.1 [1.1.1] / Rule length 320 m exceeds the range 90 <= L <= 300 for Cw formula in note or L > 300 limitation (L <= 300 is required for formula appl |
| 2 | c06 | easy | calculated | 7.452 | 7.75 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 2 | c07 | medium | calculated | 11.24 | 10.27 | Pt.3 Ch.6 Sec.3 [1.1] |
| 2 | c08 | easy | calculated | 11.24 | 8.504 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c09 | hard | calculated | 11.23 | 10.66 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c10 | medium | calculated | 18.05 | 10.75 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c11 | hard | calculated | 11.23 | 9.186 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c12 | hard | calculated | 11.23 | 6.771 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c14 | medium | calculated | 313.4 | 442 | Pt.3 Ch.6 Sec.5 [1.1] |
| 2 | c15 | hard | calculated | 114.8 | 302.3 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c16 | hard | calculated | 53.6 | 164.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c17 | medium | calculated | 319.4 | 463.9 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c18 | hard | calculated | 319.5 | 346.4 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c19 | medium | calculated | 17.51 | 28.44 | Pt.3 Ch.5 Sec.2 [1.3] |
| 2 | c20 | hard | calculated | 0.4497 | 1.059 | Pt.3 Ch.5 Sec.2 [1.3] |
| 2 | c21 | medium | calculated | 2.216 | 5.171 | Pt.3 Ch.5 Sec.2 [1.3] |
| 2 | c22 | easy | refused | - | 51.36 | Pt.3 Ch.5 Sec.2 [1.3] / L = 320 m is outside the validity range for the formula in Pt.3 Ch.5 Sec.2 [1.3] (applicable for L <= 300 m via Cw0 / Cw definition, or  |
| 2 | c23 | easy | calculated | 139.8 | 296.3 | Pt.3 Ch.5 Sec.2 [1.5.2] |
| 2 | c24 | hard | refused | - | 1558 | Pt.3 Ch.5 Sec.2 [1.5.2] / The length L = 420 m is outside the validity range for the wave coefficient Cw formula in Ch.4 Sec.4 (valid for L <= 500, but Cw formu |
| 3 | c04 | medium | calculated | 11.23 | 10.06 | Pt.3 Ch.6 Sec.3 [1.1.1] |
| 3 | c05 | hard | refused | - | 9.591 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] / Rule length L = 320 m exceeds the applicability limit for L1 (250 m) or L2 (300 m) in the rule context, or L > 300 m where s |
| 3 | c06 | easy | calculated | 7.45 | 7.75 | Pt.3 Ch.6 Sec.3 [1.1.1] |
| 3 | c07 | medium | calculated | 11.23 | 10.27 | Pt.3 Ch.6 Sec.3 [1.1] |
| 3 | c08 | easy | calculated | 11.23 | 8.504 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 3 | c09 | hard | calculated | 11.23 | 10.66 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 3 | c10 | medium | calculated | 15.39 | 10.75 | Pt.3 Ch.6 Sec.4 [1.1] |
| 3 | c11 | hard | calculated | 11.24 | 9.186 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 3 | c12 | hard | calculated | 7.42 | 6.771 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 3 | c14 | medium | calculated | 319.5 | 442 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c15 | hard | calculated | 115.8 | 302.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c16 | hard | calculated | 110.9 | 164.3 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c17 | medium | calculated | 551.5 | 463.9 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c18 | hard | refused | - | 346.4 |  / Missing required input: ReH or yield stress for A36 is given in the general tables as 355 N/mm2, but let's check if we can proceed. Actually ReH for A36 is 3 |
| 3 | c19 | medium | calculated | 24.32 | 28.44 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] |
| 3 | c20 | hard | calculated | 0.4411 | 1.059 | Pt.3 Ch.5 Sec.2 [1.3] |
| 3 | c21 | medium | calculated | 1.489 | 5.171 | Pt.3 Ch.5 Sec.2 [1.3] |
| 3 | c22 | easy | refused | - | 51.36 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / The rule for minimum section modulus applies to L <= 300 m (or L > 90 m, but Cw formula ranges specify L <= 300 for that spe |
| 3 | c23 | easy | calculated | 110.8 | 296.3 | Pt.3 Ch.5 Sec.2 [1.5.2] |
| 3 | c24 | hard | refused | - | 1558 | Pt.3 Ch.5 Sec.2 [1.5.2] / The rule for minimum moment of inertia midship [1.5.2] specifies that L must not be greater than 300 m (or 350 m depending on Cw range |
