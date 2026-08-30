# Review Harmonization Manifest

Generated: `2026-08-30T16:31:21+00:00`

This manifest separates comparable static review fields from source-specific metrics and adaptive candidates. The harmonized source is intentionally conservative: it includes only fields with the same column name, direction, and defensible 0-1 scenario interpretation in both review projects.

## Action Counts

| Action | Count |
| --- | --- |
| adaptive candidate | 16 |
| excluded | 8 |
| included | 20 |
| not present | 8 |

## Included Harmonized Static Fields

| Metric | Source | Direction | Denominator |
| --- | --- | --- | --- |
| directionalScore | Supreme Court Simulator Design | positive | case-weighted scenario mean over the imported Supreme Court Design campaign rows |
| legalStability | Supreme Court Simulator Design | positive | case-weighted scenario mean over the imported Supreme Court Design campaign rows |
| rightsProtection | Supreme Court Simulator Design | positive | case-weighted scenario mean over the imported Supreme Court Design campaign rows |
| democraticResponsiveness | Supreme Court Simulator Design | positive | case-weighted scenario mean over the imported Supreme Court Design campaign rows |
| independenceAccountabilityBalance | Supreme Court Simulator Design | positive | case-weighted scenario mean over the imported Supreme Court Design campaign rows |
| legitimacy | Supreme Court Simulator Design | positive | case-weighted scenario mean over the imported Supreme Court Design campaign rows |
| partisanAlignment | Supreme Court Simulator Design | negative | case-weighted scenario mean over the imported Supreme Court Design campaign rows |
| shadowDocketAbuse | Supreme Court Simulator Design | negative | case-weighted scenario mean over the imported Supreme Court Design campaign rows |
| constitutionalConflict | Supreme Court Simulator Design | negative | case-weighted scenario mean over the imported Supreme Court Design campaign rows |
| reversalRate | Supreme Court Simulator Design | negative | case-weighted scenario mean over the imported Supreme Court Design campaign rows |
| directionalScore | Constitutional Review Simulator | positive | unweighted sensitivity-case scenario mean; caseWeight is absent and treated as 1.0 |
| legalStability | Constitutional Review Simulator | positive | unweighted sensitivity-case scenario mean; caseWeight is absent and treated as 1.0 |
| rightsProtection | Constitutional Review Simulator | positive | unweighted sensitivity-case scenario mean; caseWeight is absent and treated as 1.0 |
| democraticResponsiveness | Constitutional Review Simulator | positive | unweighted sensitivity-case scenario mean; caseWeight is absent and treated as 1.0 |
| independenceAccountabilityBalance | Constitutional Review Simulator | positive | unweighted sensitivity-case scenario mean; caseWeight is absent and treated as 1.0 |
| legitimacy | Constitutional Review Simulator | positive | unweighted sensitivity-case scenario mean; caseWeight is absent and treated as 1.0 |
| partisanAlignment | Constitutional Review Simulator | negative | unweighted sensitivity-case scenario mean; caseWeight is absent and treated as 1.0 |
| shadowDocketAbuse | Constitutional Review Simulator | negative | unweighted sensitivity-case scenario mean; caseWeight is absent and treated as 1.0 |
| constitutionalConflict | Constitutional Review Simulator | negative | unweighted sensitivity-case scenario mean; caseWeight is absent and treated as 1.0 |
| reversalRate | Constitutional Review Simulator | negative | unweighted sensitivity-case scenario mean; caseWeight is absent and treated as 1.0 |
