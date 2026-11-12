# 계산 정확도: 조건 B3

- 방식: LLM calculates from excerpts with formulas and structured tables (table-text RAG)
- 문제 28개 x 3회, 정답과 1% 이내면 맞음 (괄호는 회차별 최저~최고)

| 전체 | easy | medium | hard | refuse | 근거 조항 정확 | 지어낸 값 | 오류 | 평균 시간(초) |
|---|---|---|---|---|---|---|---|---|
| 28.6% (25~32) | 44.4% | 22.2% | 0.0% | 83.3% | 93.1% | 2/12 | 0 | 1.8 |

## 틀린 답

| 회차 | id | 난이도 | 상태 | 받은 값 | 정답 | 근거 조항 / 이유 |
|---|---|---|---|---|---|---|
| 1 | c04 | medium | calculated | 11.23 | 10.06 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 1 | c05 | hard | calculated | 10.9 | 9.591 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 1 | c07 | medium | calculated | 11.23 | 10.27 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 1 | c08 | easy | calculated | 11.23 | 8.504 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 1 | c09 | hard | refused | - | 10.66 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1] / Transversely stiffened plating uses alpha_a = 1.00. With sigma_hg = -120 N/mm2 (compression) and beta_a = 0.90 for AC-I, Ca  |
| 1 | c10 | medium | refused | - | 10.75 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1] / The plate panel breadth b (850 mm) and length a (4000 mm) must be verified against elementary plate panel definition in Ch.3 |
| 1 | c11 | hard | calculated | 11.23 | 9.186 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 1 | c12 | hard | calculated | 7.42 | 6.771 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 1 | c14 | medium | calculated | 469.7 | 442 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c15 | hard | calculated | 116.1 | 302.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c16 | hard | calculated | 55.77 | 164.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c17 | medium | calculated | 469.8 | 463.9 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c18 | hard | refused | - | 346.4 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] / Missing ship's main data (rule length L) required to determine L2 (or L) for applicable rules, or insufficient input param |
| 1 | c19 | medium | calculated | 24.36 | 28.44 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] |
| 1 | c20 | hard | refused | - | 1.059 |  / Missing inputs or outside rule range (rule length is 85 m, but formula for minimum moment of inertia requires L > 90 m, and minimum section modulus formula r |
| 1 | c21 | medium | refused | - | 5.171 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Steel grade A32 has ReH = 315 N/mm2, but the rule formula uses k (material factor) which requires specification or calculati |
| 1 | c22 | easy | refused | - | 51.36 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Rule length L = 320 m exceeds the applicable range for C_w formula and hull girder section modulus formulas given in the exc |
| 1 | c23 | easy | calculated | 115.8 | 296.3 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.5.2] |
| 1 | c24 | hard | refused | - | 1558 | Pt.3 Ch.5 Sec.2 [1.5.1] / The requirement in [1.5.2] applies to self propelled ships with length above 90 m and up to 350 m (or 500 m depending on C_w formulati |
| 2 | c04 | medium | calculated | 11.23 | 10.06 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 2 | c05 | hard | calculated | 10.14 | 9.591 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 2 | c07 | medium | calculated | 11.23 | 10.27 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 2 | c08 | easy | calculated | 11.59 | 8.504 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c09 | hard | calculated | 11.23 | 10.66 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c10 | medium | calculated | 18.25 | 10.75 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c11 | hard | calculated | 11.66 | 9.186 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c12 | hard | calculated | 6.89 | 6.771 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c14 | medium | calculated | 319.5 | 442 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c15 | hard | calculated | 113.9 | 302.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c16 | hard | refused | - | 164.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] / For simply supported stiffeners with lateral pressure acting on the stiffener side under tension, Table 3 specifies Cs = C |
| 2 | c17 | medium | calculated | 583.5 | 463.9 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c18 | hard | refused | - | 346.4 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] / Missing required ship main data (Rule length L) to determine L2 (or L is needed for length-dependent checks, but wait: let |
| 2 | c19 | medium | calculated | 24.16 | 28.44 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] |
| 2 | c20 | hard | refused | - | 1.059 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Rule length L = 85 m is less than 90 m for formula applicability in Sec.2 [1.3] (or requires special consideration / differe |
| 2 | c21 | medium | refused | - | 5.171 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / The formula requires C_w0 or C_w which depends on L and rule definitions, but the provided excerpts do not explicitly give t |
| 2 | c22 | easy | refused | - | 51.36 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Rule length L = 320 m exceeds the range L <= 300 m for C_w formula [6] or range in Pt.3 Ch.5 Sec.2. |
| 2 | c23 | easy | calculated | 116.6 | 296.3 | Pt.3 Ch.5 Sec.2 [1.5.2] |
| 2 | c24 | hard | refused | - | 1558 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.5.1] / The requirement in [1.5.2] applies to self propelled ships with length above 90 m and up to 350 m based on the wave coeffi |
| 2 | c28 | refuse | calculated | 18.07 | refuse | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] |
| 3 | c04 | medium | calculated | 11.22 | 10.06 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 3 | c05 | hard | calculated | 11.52 | 9.591 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 3 | c07 | medium | calculated | 11.23 | 10.27 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] |
| 3 | c08 | easy | calculated | 11.23 | 8.504 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 3 | c09 | hard | calculated | 15.35 | 10.66 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1] |
| 3 | c10 | medium | calculated | 18.06 | 10.75 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 3 | c11 | hard | calculated | 11.59 | 9.186 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 3 | c12 | hard | calculated | 7.42 | 6.771 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 3 | c13 | easy | calculated | 313.2 | 318.1 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c14 | medium | calculated | 312.8 | 442 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c15 | hard | calculated | 116.8 | 302.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c16 | hard | refused | - | 164.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] / For simply supported stiffeners with lateral pressure acting on the stiffener side under tension, Table 3 specifies Cs = C |
| 3 | c17 | medium | calculated | 315.6 | 463.9 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c18 | hard | refused | - | 346.4 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] / Missing ship's rule length L or rule length L2 to determine the maximum length limitation for the stiffener or check appli |
| 3 | c19 | medium | calculated | 24.58 | 28.44 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] |
| 3 | c20 | hard | refused | - | 1.059 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Rule length L = 85 m is less than 90 m, and minimum midship section modulus formula in Pt.3 Ch.5 Sec.2 [1.3] requires L > 90 |
| 3 | c21 | medium | refused | - | 5.171 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Steel grade A32 has ReH = 315 N/mm2, but the minimum section modulus formula in Pt.3 Ch.5 Sec.2 [1.3] uses the material fact |
| 3 | c22 | easy | refused | - | 51.36 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Rule length L = 320 m exceeds the upper limit of the rule formula range for C_w (maximum L = 500 m, but C_w formula has a ma |
| 3 | c23 | easy | calculated | 113.8 | 296.3 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.5.2] |
| 3 | c24 | hard | refused | - | 1558 | Pt.3 Ch.5 Sec.2 [1.5.1] / The requirement in [1.5.2] applies to self propelled ships with length above 90 m and up to 350 m (or 500 m depending on C_w formulati |
| 3 | c28 | refuse | calculated | 1.701 | refuse | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] |
