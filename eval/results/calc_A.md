# 계산 정확도: 조건 A

- 방식: LLM calculates from rule excerpts as stored (formulas missing)
- 문제 28개 x 3회, 정답과 1% 이내면 맞음 (괄호는 회차별 최저~최고)

| 전체 | easy | medium | hard | refuse | 근거 조항 정확 | 지어낸 값 | 오류 | 평균 시간(초) |
|---|---|---|---|---|---|---|---|---|
| 25.0% (25~25) | 16.7% | 22.2% | 0.0% | 100.0% | 66.7% | 0/12 | 0 | 1.8 |

## 틀린 답

| 회차 | id | 난이도 | 상태 | 받은 값 | 정답 | 근거 조항 / 이유 |
|---|---|---|---|---|---|---|
| 1 | c04 | medium | refused | - | 10.06 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] / Missing lateral pressure P and elementary panel dimensions a and b required by the formula in Pt.3 Ch.6 Sec.4 [1.1.1] or add |
| 1 | c05 | hard | refused | - | 9.591 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] / Rule length L = 320 m exceeds the applicability range for length in the standard table or required values (a, b) and lateral |
| 1 | c06 | easy | calculated | 7 | 7.75 | Pt.3 Ch.6 Sec.3 [1.1.1] |
| 1 | c07 | medium | refused | - | 10.27 | Pt.3 Ch.6 Sec.3 [1.1] / Missing stiffener spacing or elementary plate panel breadth (s or b) required for minimum thickness calculation of inner bottom plating  |
| 1 | c08 | easy | refused | - | 8.504 |  / Missing inputs or cannot calculate automatically with provided rule excerpts. |
| 1 | c09 | hard | calculated | 11.23 | 10.66 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 1 | c10 | medium | refused | - | 10.75 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1] / Missing plate breadth b, stiffener spacing s, or specific formula parameters for DNV Pt.3 Ch.6 Sec.4 [1.1] plating net thick |
| 1 | c11 | hard | refused | - | 9.186 |  / Input pressure unit N/mm2 does not match the rule formula requirement (kN/m2). |
| 1 | c12 | hard | refused | - | 6.771 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] / Formula definition references variables not provided or fully extractable from excerpts (specifically missing formula equa |
| 1 | c13 | easy | calculated | 313.2 | 318.1 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 1 | c14 | medium | refused | - | 442 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] / Bottom longitudinal with lateral pressure acting on the plate side and compressive hull girder stress does not have a dire |
| 1 | c15 | hard | refused | - | 302.3 |  / Required intermediate values such as k for A36 steel or specific pressure application parameters are missing or the exact input combination needs more contex |
| 1 | c16 | hard | refused | - | 164.3 |  / Formula from DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] requires values or coefficients not fully defined in the provided excerpts (specifically the net section mod |
| 1 | c17 | medium | refused | - | 463.9 |  / Required data for calculation is incomplete or outside range. |
| 1 | c18 | hard | refused | - | 346.4 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] / Insufficient input: The material factor k or specified minimum yield stress ReH is required to calculate the section modul |
| 1 | c19 | medium | refused | - | 28.44 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Formula in clause [1.3] requires missing parameters (like Cw0, k, etc. or specific formula text not fully detailed in excerp |
| 1 | c20 | hard | refused | - | 1.059 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Rule requirement in Pt.3 Ch.5 Sec.2 [1.3] relies on wave parameter Cw0 and rule length, but the provided excerpts do not con |
| 1 | c21 | medium | refused | - | 5.171 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Formula requires parameters not provided in the excerpts (specifically Cw0 and Z_0-n50 or similar components for the full ca |
| 1 | c22 | easy | refused | - | 51.36 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / L exceeds the applicability range of the provided Cw0 formula or L > 300m rule requirement not fully specified in excerpts f |
| 1 | c23 | easy | refused | - | 296.3 |  / Formula not explicitly typed out in the excerpt. |
| 1 | c24 | hard | refused | - | 1558 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.5.1] / The requirement in [1.5.2] applies to self-propelled ships with length above 90 m and up to 350 m (or 500 m depending on w |
| 2 | c04 | medium | refused | - | 10.06 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] / Missing required input parameters: stiffener spacing s or elementary plate panel breadth b, and design lateral pressure P. |
| 2 | c05 | hard | refused | - | 9.591 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] / Rule length L = 320 m exceeds the applicability range for length in the standard table or required inputs like panel dimensi |
| 2 | c06 | easy | calculated | 7.035 | 7.75 | Pt.3 Ch.6 Sec.3 [1.1.1] |
| 2 | c07 | medium | refused | - | 10.27 | Pt.3 Ch.6 Sec.3 [1.1] / Missing stiffener spacing or elementary plate panel breadth (s or b) required to evaluate the minimum thickness formula. |
| 2 | c08 | easy | refused | - | 8.504 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1] / Insufficient information to calculate: s (stiffener spacing) is missing, which is required to determine the elementary plate |
| 2 | c09 | hard | calculated | 11.23 | 10.66 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] |
| 2 | c10 | medium | refused | - | 10.75 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1] / Missing inputs or cannot be fully solved with provided excerpts (missing spacing 's' or pressure/stress details specific to  |
| 2 | c11 | hard | refused | - | 9.186 |  / The design pressure unit in the rule is kN/m2 (or kPa), but 0.15 N/mm2 (150 kN/m2) is outside the typical rule pressure range or requires conversion not spec |
| 2 | c12 | hard | refused | - | 6.771 |  / Formula for plate thickness under lateral pressure [12] is missing from the provided DNV rule excerpts. |
| 2 | c13 | easy | calculated | 313.1 | 318.1 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 2 | c14 | medium | refused | - | 442 |  / Formula for stiffener section modulus is cut off in the provided rule excerpts. |
| 2 | c15 | hard | refused | - | 302.3 |  / Not enough input data to compute the required net section modulus (missing factors or specific parameters required by the formula in the excerpts, or calcula |
| 2 | c16 | hard | refused | - | 164.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] / Missing inputs: material factor k or specific formula variables not fully evaluable without explicit formula string from e |
| 2 | c17 | medium | refused | - | 463.9 |  / D32 steel material factor k is not provided in excerpt [4] (only 235: 1.00, 315: 0.78, 355: 0.72, 390: 0.66/0.68, 460: 0.62). |
| 2 | c18 | hard | refused | - | 346.4 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] / Missing material yield stress ReH or material factor k for A36 steel in the prompt inputs for the section modulus formula  |
| 2 | c19 | medium | refused | - | 28.44 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Missing required input or formula excerpt parameter in the provided rules (formula for minimum section modulus Z not fully s |
| 2 | c20 | hard | refused | - | 1.059 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Rule length L = 85 m is less than the applicable range for the formula in [1.3] or requires L > 90 m based on Ch.5 Sec.2 [1. |
| 2 | c21 | medium | refused | - | 5.171 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Formula requires parameters not provided in the excerpts (specifically Cw0/Cw and basic hull girder section modulus formula  |
| 2 | c22 | easy | refused | - | 51.36 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / The rule formula in [1.3] requires Cw or Cw0, which for L > 300 m depends on parameters not provided in the rule excerpt. |
| 2 | c23 | easy | refused | - | 296.3 |  / Formula for minimum hull girder moment of inertia at midship is not fully provided in excerpt [8] |
| 2 | c24 | hard | refused | - | 1558 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.5] / L = 420 m is outside the range for the standard formula or L > 350 m applicability limit for the hull girder moment of inert |
| 3 | c04 | medium | refused | - | 10.06 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] / Required lateral pressure and panel dimensions (a and b) for bottom shell plating minimum thickness calculation are not prov |
| 3 | c05 | hard | refused | - | 9.591 | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1] / Rule length L = 320 m exceeds the applicability range for container ship or specific rule formula parameters are missing. |
| 3 | c06 | easy | calculated | 7.325 | 7.75 | Pt.3 Ch.6 Sec.3 [1.1.1] |
| 3 | c07 | medium | refused | - | 10.27 | Pt.3 Ch.6 Sec.3 [1.1] / Missing stiffener spacing s or elementary plate panel breadth b required for the minimum thickness formula. |
| 3 | c08 | easy | refused | - | 8.504 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1.1] / Insufficient input: missing parameters like stiffener spacing s or panel dimensions definitions required for the formula. |
| 3 | c09 | hard | calculated | 11.23 | 10.66 | Pt.3 Ch.6 Sec.4 [1.1.1] |
| 3 | c10 | medium | refused | - | 10.75 | DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [1.1] / Missing stiffener spacing s or plate breadth b definition context for panel dimensions (a and b) in the formula. |
| 3 | c11 | hard | refused | - | 9.186 |  / Missing plate breadth b (s is given as spacing, but plate dimensions a and b are needed for plating thickness calculation according to DNV-RU-SHIP Pt.3 Ch.6  |
| 3 | c12 | hard | refused | - | 6.771 |  / Formula for plate thickness under lateral pressure [12] is incomplete in the provided rule text excerpts. |
| 3 | c13 | easy | calculated | 506.7 | 318.1 | Pt.3 Ch.6 Sec.5 [1.1.2] |
| 3 | c14 | medium | refused | - | 442 |  / Missing formula text in DNV excerpts for stiffener section modulus [1.1.2] to perform calculation. |
| 3 | c15 | hard | refused | - | 302.3 |  / Required intermediate values such as k or Cs for the specific stiffener configuration/load combination are not fully computable from the provided excerpts wi |
| 3 | c16 | hard | refused | - | 164.3 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] / Formula incomplete in rule text excerpt provided |
| 3 | c17 | medium | refused | - | 463.9 |  / D32 steel material factor k is needed for the section modulus formula in Pt.3 Ch.6 Sec.5 [1.1.2], but k is not directly provided in the text excerpts for D32 |
| 3 | c18 | hard | refused | - | 346.4 | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] / Missing material yield stress ReH or material factor k for A36 steel in the prompt inputs for stiffener calculation. |
| 3 | c19 | medium | refused | - | 28.44 |  / Formula for minimum midship section modulus (Z) is missing from the provided DNV rule excerpts. |
| 3 | c20 | hard | refused | - | 1.059 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Rule length L = 85 m is less than 90 m where Cw0 formula differs or wave parameter depends on L > 90 m criteria, or L <= 90  |
| 3 | c21 | medium | refused | - | 5.171 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / Formula requires Cw which needs additional input or rule wave parameter, but let's check if excerpt [7] can be evaluated. Ex |
| 3 | c22 | easy | refused | - | 51.36 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.3] / L exceeds the applicability range for the provided excerpt formula (L <= 300 m in the excerpt table or formula applicability |
| 3 | c23 | easy | refused | - | 296.3 |  / The formula for minimum moment of inertia midship requires the wave parameter and other specific inputs not fully computable or provided explicitly in the ex |
| 3 | c24 | hard | refused | - | 1558 | DNV-RU-SHIP Pt.3 Ch.5 Sec.2 [1.5.1] / The requirement in [1.5.2] applies to self propelled ships with length above 90 m up to 350 m (or 500 m depending on table |
