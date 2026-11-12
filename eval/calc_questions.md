# 계산 문제 세트

- 난이도: easy 6, medium 9, hard 9, refuse 4
- 문제 28개, 정답은 formulas 엔진으로 계산, 정답과 1% 안이면 맞음
- refuse: 계산하지 말고 범위 밖이거나 값이 빠졌다고 답해야 맞음

| id | 난이도 | 질문 | 공식 | 정답 | 메모 |
|---|---|---|---|---|---|
| c01 | easy | What material factor k applies to hull steel with a specified minimum yield stress of 355 N/mm2? | material_factor | k = 0.72 |  |
| c02 | medium | We upgraded the bottom plates from grade A to D32. What is the material factor k now? | material_factor | k = 0.78 | D32 -> R_eH 315 (Ch.3 Sec.1 Table 1) |
| c03 | medium | Deck plating changed to E40 steel and no fatigue assessment is planned. Which material factor k should we use? | material_factor | k = 0.68 | E40 -> 390, without fatigue assessment k = 0.68 |
| c04 | medium | Minimum net thickness of bottom shell plating for a ship with rule length 180 m, plates in A32 steel? | min_plate_thickness | t = 10.06 mm | A32 -> 315 |
| c05 | hard | Rule length 320 m container ship, weather deck plating in D36. What is the minimum net plate thickness? | min_plate_thickness | t = 9.591 mm | L2 = 300 (L capped) |
| c06 | easy | Side shell plating between TSC + 4.6 m and TSC + 6.9 m, rule length 150 m, mild steel with ReH 235 N/mm2. Minimum net thickness? | min_plate_thickness | t = 7.75 mm |  |
| c07 | medium | Bulk carrier, L = 225 m: inner bottom plating in cargo holds loaded through hatches, D36 steel. Minimum net thickness? | min_plate_thickness | t = 10.27 mm |  |
| c08 | easy | Longitudinally stiffened bottom plating, design pressure 120 kN/m2, plate panel 3200 mm x 780 mm, ReH 315 N/mm2, hull girder stress 0, acceptance criteria AC-I. Required net thickness? | plate_lateral_pressure | t = 8.504 mm |  |
| c09 | hard | Transversely stiffened deck plating on a longitudinal member, lateral pressure 85 kN/m2, panel 2800 mm long and 700 mm wide, mild steel (grade A), hull girder stress -120 N/mm2, AC-I. Net thickness required? | plate_lateral_pressure | t = 10.66 mm | sigma_hg used in C_a |
| c10 | medium | Under AC-II, longitudinally stiffened side shell plating sees 210 kN/m2 with a hull girder stress of 90 N/mm2. Panel 4000 x 850 mm, D36 steel. Required net thickness? | plate_lateral_pressure | t = 10.75 mm |  |
| c11 | hard | Longitudinal stiffener spacing is 0.8 m and the plate field is 3.6 m long; design pressure 0.15 N/mm2 on A36 longitudinally stiffened bottom plating, AC-I, no hull girder stress. Net thickness? | plate_lateral_pressure | t = 9.186 mm | 0.15 N/mm2 = 150 kN/m2, 0.8 m = 800 mm |
| c12 | hard | Short plate panel 1200 mm long and 900 mm wide, pressure 60 kN/m2, mild steel (ReH 235), other member under AC-I, no hull girder stress. Required net plate thickness? | plate_lateral_pressure | t = 6.771 mm | alpha_p < 1.0 |
| c13 | easy | Side longitudinal, T-profile with fixed ends, spacing 750 mm, bending span 3.2 m, pressure 150 kN/m2 acting on the plate side, ReH 355 N/mm2, hull girder stress 0, AC-I. Required net section modulus? | stiffener_section_modulus | Z = 318.1 cm3 |  |
| c14 | medium | Bottom longitudinal, bulb profile, both ends fixed, s = 800 mm, span 2.8 m, P = 180 kN/m2 on the plate side, A32 steel, hull girder stress -80 N/mm2 (compression), AC-I. Required net section modulus? | stiffener_section_modulus | Z = 442 cm3 | fixed + compression + plate side -> C_s = beta_s - alpha_s sigma/R_eH |
| c15 | hard | Deck longitudinal with an angle (L) profile, fixed ends, spacing 700 mm, span 4.0 m, 95 kN/m2 on the plate side, hull girder tension 60 N/mm2, A36 steel, AC-II. Required net section modulus? | stiffener_section_modulus | Z = 302.3 cm3 | fixed + tension + plate side -> f_m (1.60 for AC-II) |
| c16 | hard | Simply supported flat bar stiffener, spacing 600 mm, span 2.5 m, 70 kN/m2 acting on the stiffener side, hull girder tension 40 N/mm2, mild steel (ReH 235), longitudinal member, AC-I. Net section modulus? | stiffener_section_modulus | Z = 164.3 cm3 | simply supported + tension + stiffener side -> C_s = C_s-max |
| c17 | medium | Vertical stiffener on a transverse bulkhead, checking the lower end (fixed ends), spacing 780 mm, span 3.5 m, 130 kN/m2 on the plate side, D32 steel, T-profile, other member under AC-I, no hull girder stress. Required net section modulus? | stiffener_section_modulus | Z = 463.9 cm3 | f_bdg = 10 |
| c18 | hard | Longitudinal with one end fixed and the other simply supported, spacing 820 mm, span 3.0 m, pressure 110 kN/m2 on the stiffener side, hull girder compression 100 N/mm2, A36 bulb profile, AC-I. Net section modulus? | stiffener_section_modulus | Z = 346.4 cm3 | fixed + compression + stiffener side -> f_m = 1.77 |
| c19 | medium | Minimum midship section modulus for L = 250 m, B = 40 m, CB = 0.82, deck and bottom in A36 steel, unrestricted service. | hull_girder_min_modulus | Z_R-gr = 28.44 m3 |  |
| c20 | hard | Small vessel, rule length 85 m, breadth 14 m, block coefficient 0.68, mild steel hull, unrestricted service: minimum gross midship section modulus? | hull_girder_min_modulus | Z_R-gr = 1.059 m3 | L <= 90 -> C_w0 = 5.7 + 0.0222 L |
| c21 | medium | Ship with service area notation R1, L = 150 m, B = 24 m, CB = 0.75, deck and bottom in A32. Minimum midship section modulus? | hull_girder_min_modulus | Z_R-gr = 5.171 m3 | f_r = 0.9 |
| c22 | easy | L = 320 m, B = 48 m, CB = 0.65, ReH 355 N/mm2 for deck and bottom, service area R0. Rule minimum midship section modulus? | hull_girder_min_modulus | Z_R-gr = 51.36 m3 | C_w = 10.75 |
| c23 | easy | Minimum hull girder moment of inertia at midship for a self-propelled ship, L = 250 m, B = 40 m, CB = 0.82, service area R0. | hull_girder_min_inertia | I_yR-gr = 296.3 m4 |  |
| c24 | hard | Self-propelled ship, L = 420 m, B = 60 m, CB = 0.70, service area R2. Minimum midship moment of inertia? | hull_girder_min_inertia | I_yR-gr = 1558 m4 | 350 < L <= 500 branch of C_w; f_r multiplies directly |
| c25 | refuse | Bottom plating of a 200 m ship made of steel with yield stress 500 N/mm2: what is the minimum net thickness? | min_plate_thickness | 계산 거부 | R_eH above 460: k not defined in Table 2 (case-by-case) |
| c26 | refuse | Minimum midship moment of inertia for an 80 m self-propelled ship, B = 13 m, CB = 0.70? | hull_girder_min_inertia | 계산 거부 | [1.5.2] applies only for L above 90 m |
| c27 | refuse | Required net thickness of longitudinally stiffened side shell plating with 800 mm stiffener spacing and A36 steel? | plate_lateral_pressure | 계산 거부 | design pressure and panel length missing |
| c28 | refuse | Minimum midship section modulus for a 180 m ship with breadth 30 m and mild steel deck and bottom? | hull_girder_min_modulus | 계산 거부 | block coefficient missing |
