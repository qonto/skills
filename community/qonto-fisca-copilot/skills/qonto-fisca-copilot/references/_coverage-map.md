# Coverage map — legal forms → regime packs (Qonto's 8 countries)

The skill organizes rules by **tax/social regime**, not by legal form — many forms share a
regime. This map ensures **every legal form is explicitly accounted for**: each is either
**covered** by a pack, **mapped** to one (with a note), or **out of scope** (rare for a Qonto
SME/freelancer account). The regime router (SKILL.md) picks `rules-<cc>-<regime>.md`.

Status: ✅ covered by a pack · 🔵 mapped to another pack · ⬜ out of scope (rare / phase-2).
Pack verification: FR packs = hand-built + sourced, load-bearing figures human-checked (Opus,
11 Jul 2026). Non-FR packs = auto-generated DRAFT whose **load-bearing figures are human-checked
(Opus, 11 Jul 2026)** but whose long tail is only machine-checked — each still needs local
professional review before being treated as authoritative (see each file's banner).

---

## 🇫🇷 France
| Legal form | Regime | Pack | Status |
|---|---|---|---|
| Auto-entrepreneur / micro-entrepreneur | micro | `rules-fr-micro.md` | ✅ |
| EI (micro option) | micro | `rules-fr-micro.md` | ✅ |
| EI (réel, IR) | IR-réel + TNS | `rules-fr-ir-reel.md` | ✅ |
| EURL (IR, défaut) | IR-réel + TNS | `rules-fr-ir-reel.md` | ✅ |
| EURL (option IS) | IS + TNS | `rules-fr-is-tns.md` | ✅ |
| SARL (gérant majoritaire) | IS + TNS | `rules-fr-is-tns.md` | ✅ |
| SARL (gérant minoritaire/égalitaire) | IS + assimilé | `rules-fr-is-assimile.md` | ✅ |
| SASU / SAS (président) | IS + assimilé | `rules-fr-is-assimile.md` | ✅ |
| SA | IS + assimilé | 🔵 uses `rules-fr-is-assimile.md` (dirigeant assimilé; governance differs) |
| SNC | société de personnes (IR transparent) | ⬜ partnership — not modeled (rare) |
| SCI | immobilier | ⬜ out of scope |

## 🇩🇪 Germany
| Legal form | Regime | Pack | Status |
|---|---|---|---|
| Einzelunternehmen / Freiberufler | Einzelunternehmer (ESt) | `rules-de-kleinunternehmer.md` | ✅ (draft) |
| Kleinunternehmer (§19 UStG) | small-business VAT exemption | `rules-de-kleinunternehmer.md` | ✅ (draft) |
| UG (haftungsbeschränkt) / GmbH | Kapitalgesellschaft (KSt) | `rules-de-gmbh.md` | ✅ (draft) |
| AG | Kapitalgesellschaft | 🔵 uses `rules-de-gmbh.md` (same KSt) |
| GbR / OHG / KG / GmbH & Co. KG | Personengesellschaft (transparent) | ⬜ partnership — not modeled (phase-2) |

## 🇮🇹 Italy
| Legal form | Regime | Pack | Status |
|---|---|---|---|
| Ditta individuale / libero professionista (forfettario) | regime forfettario | `rules-it-forfettario.md` | ✅ (draft) |
| Ditta individuale (regime ordinario) | IRPF réel | 🔵 partial — see forfettario file; réel deductions apply (to add) |
| SRL / SRLS | società di capitali (IRES) | `rules-it-srl.md` | ✅ (draft) |
| SPA | società di capitali | 🔵 uses `rules-it-srl.md` |
| SNC / SAS / SS | società di persone (transparent) | ⬜ partnership — not modeled |

## 🇪🇸 Spain
| Legal form | Regime | Pack | Status |
|---|---|---|---|
| Autónomo / empresario individual | IRPF + RETA | `rules-es-autonomo.md` | ✅ (draft) |
| SL / SLU | Impuesto sobre Sociedades | `rules-es-sl.md` | ✅ (draft) |
| SA | Impuesto sobre Sociedades | 🔵 uses `rules-es-sl.md` |
| Sociedad civil / comunidad de bienes | atribución de rentas (transparent) | ⬜ not modeled |

## 🇦🇹 Austria
| Legal form | Regime | Pack | Status |
|---|---|---|---|
| Einzelunternehmer / Kleinunternehmer | Einkommensteuer | `rules-at-einzelunternehmer.md` | ✅ (draft) |
| GmbH / FlexKapG | Kapitalgesellschaft (KöSt) | `rules-at-gmbh.md` | ✅ (draft) |
| AG | Kapitalgesellschaft | 🔵 uses `rules-at-gmbh.md` |
| OG / KG | Personengesellschaft | ⬜ partnership — not modeled |

## 🇧🇪 Belgium
| Legal form | Regime | Pack | Status |
|---|---|---|---|
| Indépendant en personne physique | IPP + cotisations indépendants | `rules-be-independant.md` | ✅ (draft) |
| SRL / BV | Impôt des sociétés | `rules-be-srl.md` | ✅ (draft) |
| SA / NV | Impôt des sociétés | 🔵 uses `rules-be-srl.md` |
| SC / CV, SComm | société coopérative / de personnes | ⬜ not modeled |

## 🇳🇱 Netherlands
| Legal form | Regime | Pack | Status |
|---|---|---|---|
| ZZP / eenmanszaak | inkomstenbelasting (box 1) | `rules-nl-zzp.md` | ✅ (draft) |
| BV | vennootschapsbelasting (DGA) | `rules-nl-bv.md` | ✅ (draft) |
| NV | vennootschapsbelasting | 🔵 uses `rules-nl-bv.md` |
| VOF / CV / maatschap | transparent partnership | ⬜ not modeled |

## 🇵🇹 Portugal
| Legal form | Regime | Pack | Status |
|---|---|---|---|
| Trabalhador independente / ENI (recibos verdes) | IRS (simplificado/organizada) | `rules-pt-independente.md` | ✅ (draft) |
| Unipessoal Lda / Lda | IRC (gerente) | `rules-pt-lda.md` | ✅ (draft) |
| SA | IRC | 🔵 uses `rules-pt-lda.md` |

---

## Not-yet-modeled (explicit, not forgotten)
- **Partnerships / sociétés de personnes** across countries (GbR/OHG/KG, SNC, società di persone,
  VOF/CV, sociedad civil): transparent regimes → **phase-2**. When a user has one, the skill must
  say so and fall back to the **universal EU nudges** (reverse-charge VAT, invoice) only.
- **Public companies** (AG, SPA, SA, NV) → mapped to the country's corporate pack (governance
  differs but the tax base is the same); rare for a Qonto SME account.
- **Sector-specific** (SCI real-estate, coops): out of scope.
