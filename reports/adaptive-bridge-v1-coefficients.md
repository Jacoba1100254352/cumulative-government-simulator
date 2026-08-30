# Adaptive Bridge v1 Coefficient Families

Generated: `2026-05-12T02:05:54+00:00`

These are mechanism-family coefficients loaded by `scripts/build_adaptive_bridge.py` from the v1 configuration. They are evidence-anchored priors, not fitted estimates.

| Family | Evidence | Additive coefficients | Multiplier coefficients | Boundary |
| --- | --- | --- | --- | --- |
| audit-and-sanctions anti-capture | evidence-anchored prior | captureControlBonus=0.060; recoveryCapacityBonus=0.020; transitionReadinessBonus=0.025 | lobbyAdaptationMultiplier=0.920 | Not a fitted deterrence estimate; magnitude remains a prior. |
| venue-shifting detection | evidence-anchored prior | captureControlBonus=0.050; feedbackCorrectionBonus=0.020; transitionReadinessBonus=0.035 | lobbyAdaptationMultiplier=0.880 | Evidence supports direction more strongly than magnitude. |
| democracy vouchers | evidence-informed prior | agendaCapacityBonus=0.040; captureControlBonus=0.020; feedbackCorrectionBonus=0.025 | lobbyAdaptationMultiplier=0.980 | Not enough project-specific evidence to treat vouchers as a complete anti-capture control. |
| budgeted disclosed lobbying | low-direct-evidence prior | captureControlBonus=0.025; capturePressureAdd=0.012; transitionReadinessBonus=0.010 | lobbyAdaptationMultiplier=0.980 | Should remain a validation target, not a recommendation driver. |
| intermediary and dark-money substitution | evidence-anchored risk prior | agendaOverloadAdd=0.020; capturePressureAdd=0.050 | lobbyAdaptationMultiplier=1.120 | Risk prior, not a measured venue-shift elasticity. |
| emergency integrity | evidence-anchored prior | courtCurbingReduction=0.045; emergencySafeguardBonus=0.100; recoveryCapacityBonus=0.030; reviewCapacityBonus=0.050; transitionReadinessBonus=0.040 |  | Direction is better supported than the exact effect size. |
| jurisdiction and pre-enactment review | evidence-informed prior | courtCurbingReduction=0.030; emergencySafeguardBonus=0.040; reviewCapacityBonus=0.030; transitionReadinessBonus=0.030 |  | Static review value and adaptive capacity remain partly confounded. |
| citizen assembly threshold | evidence-informed prior | agendaCapacityBonus=0.070; agendaOverloadAdd=0.025; feedbackCorrectionBonus=0.055; transitionReadinessBonus=0.020 | partyAdaptationMultiplier=0.960 | Requires direct mechanism simulator rows before recommendation use. |
| random public review panel | evidence-informed prior | agendaCapacityBonus=0.060; feedbackCorrectionBonus=0.050; rightsRiskAdd=-0.025 | partyAdaptationMultiplier=0.970 | Institutional design details determine whether this prior holds. |
| citizens agenda petition | speculative-to-evidence-informed prior | agendaCapacityBonus=0.060; agendaOverloadAdd=0.035; feedbackCorrectionBonus=0.035 | partyAdaptationMultiplier=0.970 | Threshold design and authentication are not yet separately modeled. |
| citizen initiative referendum | risk-weighted prior | agendaCapacityBonus=0.080; agendaOverloadAdd=0.050; capturePressureAdd=0.020; feedbackCorrectionBonus=0.025; rightsRiskAdd=0.045 |  | Plebiscitary risks need source-simulator validation. |
| authenticated public participation | evidence-informed prior | agendaCapacityBonus=0.035; captureControlBonus=0.030; feedbackCorrectionBonus=0.035; transitionReadinessBonus=0.020 |  | Implementation quality matters more than the current coefficient can represent. |
| pairwise alternatives | low-direct-evidence prior | deliveryBottleneckAdd=0.015; feedbackCorrectionBonus=0.025; transitionLoadAdd=0.035 | partyAdaptationMultiplier=0.980 | Needs family-specific source simulator before recommendation use. |
| portfolio hybrid | low-direct-evidence prior | deliveryBottleneckAdd=0.020; transitionLoadAdd=0.045; transitionReadinessBonus=-0.020 |  | Good synthetic performance should trigger validation, not recommendation. |
| default pass | risk-weighted prior | capturePressureAdd=0.020; partyAdaptationMultiplier=0.020; rightsRiskAdd=0.060 |  | Current coefficient only approximates the risk side of a more detailed legislative model. |
