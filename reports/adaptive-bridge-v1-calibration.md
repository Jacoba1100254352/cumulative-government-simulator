# Adaptive Bridge v1 Research Calibration Notes

Generated: `2026-08-30T16:35:23+00:00`

Status: `evidence-informed priors; not empirically fitted`

The Deep Research reports justify directionally different priors for mechanism families, but they do not estimate a unified causal model for these portfolios.

## Source reports

| Report |
| --- |
| Constitutional Review - Sequencing Constitutional and Institutional Reform.md |
| Legislative Simulator - Public Feedback Loops in Democratic Politics.md |
| Institutional Design Simulator - Adaptive Bridge Calibration and Validation Strategy.md |
| Institutional Reform Simulator - Comparative Reform Bundles.md |
| Constitutional Review - Emergency Powers Courts and Crisis Governance.md |
| Legislative Simulator - Federalism Agency Capacity and Implementation Failure.md |
| Lobby Capture Simulator - Venue Shifting Under Constraint.md |
| Legislative Simulator - Citizen Agenda Setting Mechanisms.md |

## Evidence-informed priors

| Area | Empirical basis | Model use |
| --- | --- | --- |
| Lobby venue shifting | Constraints on formal lobbying can shift influence to alternate venues and intermediaries; disclosure and sanctions help most when enforcement reaches those substitutes. | Anti-capture rows with audit, machine-readable logs, venue-shift detection, or sanctions reduce lobby adaptation and capture pressure; narrow caps and budget tools keep a substitution-risk caveat. |
| Emergency powers | Emergency abuse risk rises with long duration, weak sunsets, low judicial access, court backlogs, information control, and executive appointment or jurisdiction pressure. | Emergency-integrity rows reduce rights-threat inflow, court adaptation, court-curbing pressure, and review backlog only when review is fast, reason-giving, and anti-evasion oriented. |
| Sequencing and transition costs | Reform enactment and operational commencement should be separated; legality, staffing, data, transparency, and review capacity need to come before high-complexity redesigns. | Sequencing readiness reduces transition load, agency gaps, and delivery bottlenecks; complex one-shot redesigns carry higher transition and direct-evidence penalties. |
| Federalism and agency capacity | Implementation failure depends on intergovernmental conflict, capability shortfalls, demand-to-capacity pressure, and recovery speed, not a single generic capacity term. | The bridge now tracks federalism resistance, delivery bottleneck pressure, and recovery capacity separately before combining them into agency implementation gaps. |
| Public feedback | Dissatisfaction is corrective only when citizens have credible voice, efficacy, fair procedures, and trusted intermediaries; trust erosion is faster than trust recovery. | Feedback correction capacity can turn backlash into alignment and policy correction, while weak voice causes faster legitimacy erosion. |
| Citizen agenda setting | Hybrid and deliberative mechanisms are safer than standalone plebiscitary mechanisms; open participation without authentication or response duties can overload institutions or amplify capture. | Citizen assemblies, random public review panels, and comment-authenticity rules improve agenda correction; initiatives and petition channels also add rights-risk or overload pressure. |
| Comparative evidence strength | Emergency review, audit/sanction regimes, participatory budgeting-style channels, and democracy vouchers have more direct evidence than pairwise amendment tournaments, portfolio-hybrid legislatures, or budgeted disclosed lobbying. | Low-direct-evidence families can rank highly synthetically, but the recommendation gate labels them as calibration gray-zone or do-not-recommend rather than provisional recommendations. |

## Validation requirements

| Requirement |
| --- |
| Elicit score weights from an explicit loss function or stakeholder tradeoff exercise. |
| Backtest transition-load, agency-gap, voter-feedback, court-adaptation, and lobby-adaptation coefficients against historical reform episodes. |
| Use temporal holdouts and adversarial stress checks before treating any gate as decision-ready. |
| Require direct family-specific simulator work for pairwise, portfolio-hybrid, and budgeted-lobbying rows before recommending them. |

## Configured coefficient families

| Family | Evidence tier | Use |
| --- | --- | --- |
| audit-and-sanctions anti-capture | evidence-anchored prior | Model broad audit, detection, and sanction regimes as reducing capture growth and venue-shifting pressure, with modest transition benefits from clearer enforcement architecture. |
| venue-shifting detection | evidence-anchored prior | Give the largest lobby-adaptation reduction to mechanisms that explicitly track substitute venues and produce auditable records. |
| democracy vouchers | evidence-informed prior | Treat vouchers as public-input and campaign-finance pluralism aids, not as full substitutes for audit or venue-shift enforcement. |
| budgeted disclosed lobbying | low-direct-evidence prior | Preserve modest disclosure benefits while adding substitution pressure because hard limits can move influence to less visible channels. |
| intermediary and dark-money substitution | evidence-anchored risk prior | Increase adaptation and pressure where influence can migrate through intermediaries, dark money, revolving-door channels, or low-salience venues. |
| emergency integrity | evidence-anchored prior | Give reason-giving, merits follow-up, recusal, and anti-evasion emergency reforms the largest review-side adaptive safeguard effects. |
| jurisdiction and pre-enactment review | evidence-informed prior | Model front-loaded review and jurisdictional safeguards as reducing downstream emergency and curbing pressure, but below the emergency-integrity package. |
| citizen assembly threshold | evidence-informed prior | Treat deliberative agenda channels as strong public-feedback correctives with manageable but real overload costs. |
| random public review panel | evidence-informed prior | Model randomly selected review panels as deliberative correction channels with lower rights-risk than plebiscitary devices. |
| citizens agenda petition | speculative-to-evidence-informed prior | Give petitions meaningful agenda access benefits while retaining overload risk when filtering and response duties are weak. |
| citizen initiative referendum | risk-weighted prior | Model initiatives as high agenda-capacity but higher overload, capture, and rights-risk channels unless paired with deliberative safeguards. |
| authenticated public participation | evidence-informed prior | Model authenticated comments and public-interest representation as lower-amplitude but broadly useful correction and anti-capture inputs. |
| pairwise alternatives | low-direct-evidence prior | Treat pairwise alternatives as plausible comparison-improving institutions with explicit transition and evidence penalties. |
| portfolio hybrid | low-direct-evidence prior | Penalize one-shot portfolio hybrids for transition and delivery bottlenecks unless sequencing is separately modeled. |
| default pass | risk-weighted prior | Represent default-passage rules as increasing throughput but also weak-mandate, rights, and capture pressure. |

## Claim boundary

- Empirical claims belong to the named Deep Research reports and the imported simulator artifacts.
- Synthetic findings are produced by the configured bridge equations and generated CSVs.
- Speculative design recommendations remain research directions until weights, thresholds, and mechanism coefficients are calibrated.
