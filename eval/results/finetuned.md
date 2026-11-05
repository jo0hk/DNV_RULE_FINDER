# 검색 정확도: finetuned

- 임베딩 모델: `models/bge-small-dnv`
- 평가 질문: 80개, 검색 대상 chunk: 4781개
- LLM에 넘기는 발췌문은 상위 6개이므로 **하이브리드 R@6**가 실제 서비스 정확도에 해당한다

| 검색 방식 | R@1 | R@3 | R@6 | R@10 | MRR@10 |
|---|---|---|---|---|---|
| 벡터 검색 | 0.588 | 0.812 | 0.850 | 0.887 | 0.706 |
| 키워드 검색 (BM25) | 0.637 | 0.825 | 0.863 | 0.900 | 0.736 |
| 하이브리드 (서비스 방식) | 0.650 | 0.825 | 0.912 | 0.950 | 0.752 |

## Part별 하이브리드 R@6

| Part | 질문 수 | R@6 |
|---|---|---|
| Pt.2 | 11 | 0.909 |
| Pt.3 | 50 | 0.900 |
| Pt.5 | 19 | 0.947 |

## 상위 6개 안에 정답이 없던 질문 (7개)

| id | 질문 | 정답 | 하이브리드 순위 | 하이브리드 1등 |
|---|---|---|---|---|
| q09 | Electrogas welding of side shell with heat input of 80 kJ/cm on steel not approved for high heat input welding | DNV-RU-SHIP Pt.2 Ch.4 Sec.6 [2.1.2] | 23 | DNV-RU-SHIP Pt.2 Ch.4 Sec.5 [9.1] |
| q24 | Scallop in a side longitudinal located 100 mm from the toe of the end bracket | DNV-RU-SHIP Pt.3 Ch.3 Sec.6 [7.1.2] | 11 | DNV-RU-SHIP Pt.3 Ch.3 Sec.6 [4.4] |
| q32 | Keel plate net thickness reduced below the minimum plating thickness for bottom structure | DNV-RU-SHIP Pt.3 Ch.6 Sec.3 [1.1.1] | 13 | DNV-RU-SHIP Pt.5 Ch.10 Sec.12 [2.3] |
| q38 | Side longitudinal changed from HP 240x10 to HP 220x10, section modulus now lower | DNV-RU-SHIP Pt.3 Ch.6 Sec.5 [1.1.2] | 7 | DNV-RU-SHIP Pt.5 Ch.1 Sec.2 [5.2] |
| q40 | Side web frame face plate width reduced, section modulus of the primary member now below requirement | DNV-RU-SHIP Pt.3 Ch.6 Sec.6 [2.1.1] | - | DNV-RU-SHIP Pt.3 Ch.8 Sec.4 [2.1] |
| q45 | Tank bulkhead checked only for transverse sloshing, longitudinal sloshing pressure ignored | DNV-RU-SHIP Pt.3 Ch.10 Sec.4 [1.3.5] | 10 | DNV-RU-SHIP Pt.3 Ch.10 Sec.4 [1.3] |
| q66 | Bulk carrier loading steel coils: inner bottom longitudinal section modulus and web thickness not checked for coil loads | DNV-RU-SHIP Pt.5 Ch.1 Sec.3 [3.3.2] | 9 | DNV-RU-SHIP Pt.5 Ch.1 Sec.3 [3.1] |
