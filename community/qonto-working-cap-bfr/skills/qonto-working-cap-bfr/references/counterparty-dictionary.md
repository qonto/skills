# Counterparty dictionary and tax calendar by country

Use the section matching `get_organization.legal_country`. Matching is case-insensitive on `clean_counterparty_name`, then `label`, then transfer `reference`/`note`.

Calendar dates are **typical** due dates, used only to place cash flows in the forecast. The customer's own history always wins: if past VAT payments landed on the 19th, forecast the 19th. Never present these dates as tax advice.

Also applies everywhere: Qonto fees (`operation_type: qonto_fee`) are Bank fees; common SaaS (Google, Microsoft, OVH, AWS, Adobe, Slack, Notion, LinkedIn ads, Meta ads) map to Technology or Marketing.

---

## France (FR)

| Pattern | Class |
|---|---|
| URSSAF | Social charges |
| DGFIP, SIE, TRESOR PUBLIC, IMPOTS, "TVA" in reference | VAT or Corporate tax (use reference and timing to split) |
| AGIRC-ARRCO, Malakoff Humanis, AG2R, Klesia, Humanis, PRO BTP | Social charges (pension, provident) |
| CIBTP, caisse de congés payés BTP | Social charges (trades) |
| Mutuelle, prévoyance, Alan, Harmonie | Social charges or Insurance |
| PayFit, Silae, ADP (as payer of salaries) | Payroll |
| EDF, Engie, TotalEnergies (electricity, gas) | Utilities |
| TotalEnergies, Esso, BP, Shell, Avia (stations, card) | Travel and fuel |
| Orange, SFR, Bouygues Telecom, Free | Utilities and telecom |
| AXA, MAAF, MMA, Allianz, Groupama, SMABTP | Insurance |
| DIAC, Leasecom, Grenke, BNP Leasing | Loan and financing repayments (leasing) |
| Point.P, Leroy Merlin, Bricoman, Brico Dépôt, Castorama, Gedimat, Lafarge | Suppliers (for trades businesses) |
| Keywords: salaire, paie, acompte salaire | Payroll |
| Keywords: loyer | Rent |

Typical calendar:
- URSSAF: monthly, on the 5th or 15th of the following month depending on company size.
- VAT (régime réel normal): monthly, between the 15th and 24th of the following month. Simplified regime: two instalments, July and December.
- Corporate tax instalments: 15 March, 15 June, 15 September, 15 December.
- CFE: mid-December.

## Germany (DE)

| Pattern | Class |
|---|---|
| Finanzamt, "USt", "Umsatzsteuer" | VAT |
| Finanzamt, "Lohnsteuer", "LSt" | Social charges (payroll tax) |
| Finanzamt, "Körperschaftsteuer", "KSt" | Corporate tax |
| Stadt, Gemeinde, "Gewerbesteuer" | Corporate tax (trade tax) |
| AOK, TK (Techniker), Barmer, DAK, IKK, BKK, KKH, Knappschaft | Social charges (social security via health insurer) |
| Berufsgenossenschaft, BG BAU, VBG | Social charges (accident insurance) |
| SOKA-BAU | Social charges (construction) |
| DATEV, Personio (as payer) | Payroll |
| Telekom, Vodafone, O2, 1&1 | Utilities and telecom |
| Stadtwerke, E.ON, Vattenfall, EnBW, RWE | Utilities |
| ARD ZDF Beitragsservice, Rundfunkbeitrag | Other taxes |
| Keywords: Gehalt, Lohn | Payroll |
| Keywords: Miete | Rent |

Typical calendar:
- VAT pre-return (USt-Voranmeldung) and wage tax (Lohnsteuer): 10th of the following month (one month later with a permanent extension).
- Social security contributions: third-to-last banking day of the current month.
- Trade tax prepayments: 15 February, 15 May, 15 August, 15 November.
- Corporate tax prepayments: 10 March, 10 June, 10 September, 10 December.

## Italy (IT)

| Pattern | Class |
|---|---|
| F24, DELEGA F24, Agenzia delle Entrate | VAT, payroll withholding or corporate tax (F24 can bundle several; split by amount pattern or ask) |
| INPS | Social charges |
| INAIL | Social charges (accident insurance) |
| Cassa Edile | Social charges (construction) |
| Enel, Eni Plenitude, A2A, Hera, Edison | Utilities |
| TIM, Vodafone, WindTre, Fastweb, Iliad | Utilities and telecom |
| Keywords: stipendio, cedolino, retribuzione | Payroll |
| Keywords: affitto, canone locazione | Rent |

Typical calendar:
- F24 payments (monthly VAT, withholding on salaries, INPS contributions): 16th of the following month.
- Quarterly VAT payers: 16th of the second month after the quarter.
- IRES/IRAP: balance and first instalment around 30 June, second instalment 30 November.
- INAIL: 16 February.

## Spain (ES)

| Pattern | Class |
|---|---|
| AEAT, Agencia Tributaria, "Modelo 303" | VAT |
| AEAT, "Modelo 111" | Social charges (payroll withholding) |
| AEAT, "Modelo 202", "Impuesto Sociedades" | Corporate tax |
| TGSS, Seguridad Social, "SEG SOCIAL" | Social charges |
| Mutua (Fremap, Asepeyo, Ibermutua) | Social charges |
| Iberdrola, Endesa, Naturgy, Repsol (electricity, gas) | Utilities |
| Movistar, Telefónica, Vodafone, Orange | Utilities and telecom |
| Keywords: nómina, salario | Payroll |
| Keywords: alquiler | Rent |

Typical calendar:
- VAT (Modelo 303) and withholding (Modelo 111): quarterly, by the 20th of the month after the quarter (30 January for Q4). Large companies file monthly.
- Social security: last business day of the following month.
- Corporate tax instalments (Modelo 202): 20 April, 20 October, 20 December.

## Netherlands (NL)

| Pattern | Class |
|---|---|
| Belastingdienst, "BTW", "omzetbelasting" | VAT |
| Belastingdienst, "loonheffing" | Social charges (payroll tax and premiums) |
| Belastingdienst, "vennootschapsbelasting", "VPB" | Corporate tax |
| bpfBOUW, PFZW, ABP, pensioenfonds | Social charges (pension) |
| UWV | Social charges |
| Eneco, Vattenfall, Essent, Greenchoice | Utilities |
| KPN, Ziggo, Odido, Vodafone | Utilities and telecom |
| Keywords: salaris, loon | Payroll |
| Keywords: huur | Rent |

Typical calendar:
- VAT: usually quarterly, by the end of the month after the quarter.
- Payroll taxes (loonheffing): monthly, by the end of the following month.
- Corporate tax: provisional assessment instalments, usually monthly.
