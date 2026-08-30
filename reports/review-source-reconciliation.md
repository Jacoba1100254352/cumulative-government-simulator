# Review Source Reconciliation

Generated: `2026-05-12T02:04:25+00:00`

This report compares the imported Supreme Court Simulator Design review source with the companion Constitutional Review Simulator source. It is a schema and construct audit, not a claim that the two sources can be merged.

## Summary

| Category | Count |
| --- | --- |
| shared configured metric | 10 |
| imported-only configured metric | 6 |
| companion-only configured metric | 2 |
| missing from both review sources | 0 |
| companion adaptive candidate | 16 |

## Configured Static Review Metrics

| Construct | Imported | Companion | Status | Static eligibility | Denominator risk |
| --- | --- | --- | --- | --- | --- |
| directionalScore | True | True | shared configured metric | candidate after denominator check | medium |
| stabilityRightsScore | True | False | imported-only configured metric | current static metric only | high |
| legitimacyControlScore | True | False | imported-only configured metric | current static metric only | high |
| legalStability | True | True | shared configured metric | candidate after denominator check | medium |
| rightsProtection | True | True | shared configured metric | candidate after denominator check | medium |
| democraticResponsiveness | True | True | shared configured metric | candidate after denominator check | medium |
| independenceAccountabilityBalance | True | True | shared configured metric | candidate after denominator check | medium |
| legitimacy | True | True | shared configured metric | candidate after denominator check | medium |
| publicConfidence | True | False | imported-only configured metric | current static metric only | high |
| lowerCourtCompliance | True | False | imported-only configured metric | current static metric only | high |
| partisanAlignment | True | True | shared configured metric | candidate after denominator check | medium |
| shadowDocketAbuse | True | True | shared configured metric | candidate after denominator check | medium |
| emergencyLegitimacyRisk | True | False | imported-only configured metric | current static metric only | high |
| constitutionalConflict | True | True | shared configured metric | candidate after denominator check | medium |
| reversalRate | True | True | shared configured metric | candidate after denominator check | medium |
| administrativeCost | True | False | imported-only configured metric | current static metric only | high |
| totalInstitutionalCost | False | True | companion-only configured metric | candidate static metric after mapping | high |
| implementationComplexity | False | True | companion-only configured metric | candidate static metric after mapping | high |

## Companion Adaptive Candidates

| Construct | Direction | Adaptive use | Recommendation |
| --- | --- | --- | --- |
| complianceRate | positive | Adaptive bridge compliance/recovery input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| defianceRate | negative | Adaptive bridge institutional noncompliance input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| workaroundRate | negative | Adaptive bridge evasion/noncompliance input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| executiveImplementationRate | positive | Agency/executive implementation capacity input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| agencyNonacquiescenceRate | negative | Agency noncompliance and implementation-friction input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| localGovernmentComplianceRate | positive | Federalism/local compliance input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| publicTrust | positive | Public trust and legitimacy feedback input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| legislativeConflict | negative | Interbranch conflict and court-curbing pressure input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| courtCurbingPressure | negative | Court retaliation/adaptation input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| amendmentPressure | negative | Constitutional transition-pressure input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| implementationCapacity | positive | Administrative capacity input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| legislativeResponseCredibility | positive | Weak-form response and correction-cycle input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| democraticConstitutionalism | positive | Composite democratic constitutionalism cross-check. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| vetoRelocationRisk | negative | Institutional veto relocation risk input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| legalTransplantFeasibility | positive | Transition feasibility and comparative-transfer input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
| politicalCultureSensitivity | negative | Political-culture fragility input candidate. | Map as Adaptive Bridge or stress input before using it as a ranking metric. |
