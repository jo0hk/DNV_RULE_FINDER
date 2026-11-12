# 계산 방식 비교

- 계산 문제 28개(eval/calc_questions.jsonl) x 3회, 정답과 1% 이내면 맞음
- A, B, B2에는 공식 6개에 필요한 규정 발췌문 15개를 모두 줬다 (검색 오류의 영향 제외)
- 거부 문제 4개: 값이 빠졌거나 적용 범위 밖이라 계산하면 안 되는 문제
- B, B2는 공식 표기를 고친(L_2, 곱셈 *) 2차 결과. 1차 결과(L2를 L의 제곱으로 읽는 오류 포함)는 results/archive/
- B3, B3c는 표·텍스트 결합 RAG: 발췌문이 언급한 표를 구조화된 표(tables.py)로 함께 준다

| 조건 | 방식 | 전체 (회차 최저~최고) | easy | medium | hard | refuse | 근거 조항 정확 | 지어낸 값 | 오류 | 평균 시간(초) |
|---|---|---|---|---|---|---|---|---|---|---|
| A | LLM calculates from rule excerpts as stored (formulas missing) | 25.0% (25~25) | 16.7% | 22.2% | 0.0% | 100.0% | 66.7% | 0/12 | 0 | 1.8 |
| B | LLM calculates from rule excerpts with formulas added as text | 25.0% (21~29) | 16.7% | 25.9% | 0.0% | 91.7% | 84.7% | 1/12 | 0 | 1.7 |
| B2 | LLM writes Python code from rule excerpts with formulas added | 72.6% (68~79) | 66.7% | 88.9% | 59.3% | 75.0% | 93.1% | 0/12 | 8 | 2.9 |
| B3 | LLM calculates from excerpts with formulas and structured tables (table-text RAG) | 28.6% (25~32) | 44.4% | 22.2% | 0.0% | 83.3% | 93.1% | 2/12 | 0 | 1.8 |
| B3c | LLM writes Python code from excerpts with formulas and structured tables (table-text RAG) | 83.3% (79~86) | 88.9% | 100.0% | 66.7% | 75.0% | 90.3% | 0/12 | 6 | 2.4 |
| C | LLM selects function and inputs, verified Python engine calculates | 100.0% (100~100) | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0/12 | 0 | 1.6 |

![조건별 정확도](calc_accuracy.svg)

![난이도별 정확도](calc_by_difficulty.svg)
