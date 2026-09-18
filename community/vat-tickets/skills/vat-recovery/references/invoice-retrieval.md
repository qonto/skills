# references/invoice-retrieval.md

*Sourced knowledge base — where and how to retrieve the invoice for a past purchase, supplier by supplier. Research conducted on 13/07/2026. Every entry cross-checks at least one official help page against a third-party source, unless explicitly stated otherwise.*

---

## How to read this file

**Effort levels**
- ⚡ **< 2 min** — you're logged in, the invoice is self-service, 2-3 clicks.
- 🔧 **2-10 min** — you have to search, filter, enable an option, or download document by document.
- 🧗 **> 10 min or depends on a third party** — support ticket, duplicate to request, in-store visit, reply from a marketplace seller. The outcome is not guaranteed.

**Reliability levels**
- ✅ **verified, 2 sources** — path confirmed by the supplier's official help page AND a second source.
- ⚠️ **1 source** — plausible, coherent, but not cross-checked. Verify before relying on it.
- ❌ **not verified** — we found no reliable source. **We do not make it up.** Treat it as unknown.

**Golden rule of this file:** a false navigation path costs more than an "I don't know". When it's marked ❌, it's ❌.

---

## 🏆 THE 3 REFLEXES THAT PAY OFF THE MOST

### 1. The intra-EU VAT number on foreign SaaS — the hidden reservoir
Without a VAT ID on file, an Irish/US SaaS supplier charges you **its local VAT**, which is **not** recoverable on your French CA3 return (you'd have to go through the heavy 8th/13th Directive refund procedure). With the VAT ID, it bills you **net under reverse charge** — you collect and deduct simultaneously, net cost zero.

**Every month of waiting = VAT permanently lost.** The catch-up windows are brutally short:

| Supplier | Retroactive possible? | Window |
|---|---|---|
| **Google Workspace** | ✅ **Yes, written procedure** ("Get credit for previous VAT charges") | No stated limit — but **Google Ireland Ltd entity only** |
| **AWS** | ✅ Yes — invoices re-issued via a support case | No stated limit |
| **OpenAI** | ⚠️ Yes, **on explicit request** with invoice numbers + amounts | "limited by timing" (not quantified) |
| **Slack** | ⚠️ Yes, via ticket | **90 days** |
| **Figma** | ⚠️ "may refund", via ticket | **30 days** |
| **Canva** | ⚠️ "limited cases" | **~30 days** |
| **Notion** | ❌ VAT not refunded | Refund: **3 days** (monthly) / 30 days (annual) |
| **Microsoft 365** | ❌ Presumed no | — |
| **Adobe** | ❌ No ("upcoming invoices") | — |
| **Anthropic** | ❌ No, explicitly excluded | — |
| **LinkedIn** | ❌ **Non-retroactivity written in black and white** | — |
| **Vercel** | ❌ No | — |

**Immediate action:** do the VAT-ID rounds **today**, before the next billing cycle. Then, in order of payoff: Google Workspace ticket → AWS ticket → OpenAI email → Slack/Figma/Canva tickets (if < 30-90 days).

### 2. Recurring telecom invoices — 24 months to scoop up in one go
A pro mobile line at €40/month = ~€8 of VAT/month = **~€190 over 24 months**, never declared because nobody downloads their Orange invoices. The catch-up is mechanical and risk-free.

- **Orange Pro**: bulk download **by calendar year**, **6-year** history (if electronic invoicing is enabled). The best on the market.
- **Bouygues Pro/Entreprises**: **"Export multi-CF"** button.
- **SFR Business**: 3 years of history, filters + PDF/CSV export.
- **Orange consumer**: rolling 24 months, one PDF at a time — and **since 10/03/2026 Orange no longer issues duplicates** beyond that. Whatever isn't downloaded is lost.

⚠️ **But**: an invoice in a natural person's name allows **no** deduction. If the subscription is in the director's personal name, the past 24 months are **unrecoverable** — see reflex no. 3.

### 3. Hardware purchases in a personal name — the corrective invoice
A MacBook at €2,000 gross = **€333 of VAT**. Billed to "M. Dupont" instead of "Dupont SARL", that's €333 down the drain. The invoice must carry **the name and address of the taxable person** (art. 242 nonies A ann. II CGI).

**What works:** ask the seller for a **corrective invoice** in the company's name, providing SIREN + intra-EU VAT number + registered-office address. Darty, Fnac, Boulanger, LDLC and Amazon sellers often agree — **if you ask**.

**What does not work:** retroactively attaching a personal order to a pro account (Amazon Business: ❌ not documented, treat as impossible).

**The real lesson: create the pro accounts BEFORE buying.** Darty Pro, Fnac Pro, Amazon Business, LDLC.pro, Casto Pro, Leroy Merlin Pro, Boulanger Pro. It's 10 minutes once, and it secures 100% of future VAT.

---

## 🚫 DON'T GO LOOKING — the invoice is useless, the VAT is not deductible

Don't waste a second on these expenses. The supporting document is still needed as proof of the **expense** (booked gross), but there is **nothing to recover**.

| Expense | Why | Reference |
|---|---|---|
| **Taxi / ride-hailing (Uber, Bolt, G7)** | Passenger transport → zero admission coefficient | CGI ann. II art. 206-IV-2-5° · [BOI-TVA-DED-30-30-20](https://bofip.impots.gouv.fr/bofip/1192-PGP.html/identifiant=BOI-TVA-DED-30-30-20-20250723) |
| **Train (SNCF), plane, metro, bus** | Same — passenger transport | same text |
| **Hotel: the room night** of the director or an employee | Excluded accommodation expense, **even for a 100% business trip** | [BOI-TVA-DED-30-30-10](https://bofip.impots.gouv.fr/bofip/1190-PGP.html/identifiant=BOI-TVA-DED-30-30-10-20130304) |
| **Passenger-car (VP) rental** | Vehicle designed to transport people → excluded | CGI ann. II art. 206-IV |
| **Stamps, postage, registered letters, Colissimo dropped at a post office** | **VAT-exempt** (universal postal service) → there is **no VAT on the document** | CGI art. 261-4-11° and 261 C-3° · [aide.laposte.fr](https://aide.laposte.fr/contenu/pourquoi-certains-produits-ne-sont-pas-soumis-a-la-tva) |
| **Foreign VAT** on a purchase consumed abroad (hotel in Berlin, fuel in Belgium) | No French VAT → **outside the CA3 return**. Possible route: 8th Directive refund (heavy, thresholds, delays) | — |
| **Anonymous fuel receipt** (petrol station, without a pro card) | No company name on the document → no BOFiP tolerance (unlike tolls) | [BOI-TVA-DECLA-30-20-20-20](https://bofip.impots.gouv.fr/bofip/142-PGP.html/identifiant=BOI-TVA-DECLA-30-20-20-20-20190925) |
| **Gifts** > €73 gross/year/beneficiary | Excluded from the right to deduct | CGI ann. II art. 206-IV |

### ⚠️ The 4 exceptions to know (here, you MUST look)

1. **Breakfast, meals, parking and hotel internet** are deductible — **provided they are billed on a separate line with their rate**. Demand the breakdown at check-out.
2. **Uber Eats = catering = deductible** (10% on meals, 20% on the service/delivery fees). Unlike Uber rides.
3. **Renting a utility vehicle** (2 seats, van, light truck) is **100% deductible**. At Sixt/Hertz/Europcar, that's the real reservoir.
4. **Chronopost** (express, outside the universal service) is **20% deductible**, unlike stamps.

---

# PRIORITY 1 — The big volumes of recoverable VAT in an SME

## Hardware & equipment

### Darty
- **Where**: darty.com > se connecter > **Mon espace client** (`darty.com/espace_client/accueil`) > **Mes commandes** (`/espace_client/mes-commandes`) > open the order > download the invoice (PDF). Pro account: **pro.darty.com** (opened via form: SIRET, intra-EU VAT number, APE code, Kbis < 3 months).
- **Effort**: ⚡ for an online purchase. 🔧 if it's an in-store purchase not attached to the account.
- **Prerequisites**: Darty customer account; the order confirmation email. For Darty Pro: the account must exist **before** the purchase.
- **Pitfalls**:
  - **Darty Marketplace**: the invoice is issued not by Darty but by the partner seller → risk of a summary without VAT.
  - **In-store purchase**: attachment to the account depends on what was given at the register. ⚠️ not guaranteed.
  - Purchase on a personal account → invoice in the individual's name → corrective invoice to request.
- **If it fails**: Darty customer service (chat/phone via `darty.com/achat/contacts/chat-service-client`), request a **duplicate invoice** with date, amount, store, ticket number. Marketplace: contact the seller from the order.
- **Sources**: [Darty FAQ "comment imprimer facture"](https://www.darty.com/services/solutions/foire_aux_questions?question=comment-imprimer-facture) · [sav.darty.com — Accéder à mes factures](https://sav.darty.com/thematic/ACCEDER-A-MES-FACTURES-D-ACHAT-SUR-LE-SITE-DARTY/709) · [Partner-seller invoice FAQ](https://www.darty.com/services/solutions/foire_aux_questions?question=comment-obtenir-facture-suite-une-commande-aupres-dun-vendeur-partenaire) · [Darty Pro form (PDF)](https://www.darty.com/res3/pdf/dpro/formulaire_ouverture_compte_dartypro.pdf)
- **Reliability**: ✅ (online path + Darty Pro). ⚠️ The "in-store purchase retrievable online" point remains to be confirmed.

### Fnac
- **Where**: **Mon compte > Mes commandes > Voir le détail > Télécharger ma facture** (PDF). Pro account: **fnacpro.com** (free creation, quotes, deferred payment).
- **Effort**: ⚡ online. 🧗 for an in-store purchase not invoiced at the time.
- **Prerequisites**: Fnac customer account + order placed on that account. **In store: ask for the invoice at the register at the time of purchase.**
- **Pitfalls**:
  - The **till receipt** (even the emailed AGEC-law version) **is not a named invoice**.
  - **Fnac Marketplace**: invoice issued by the seller, not by Fnac.
  - "Invisible" orders in the customer area (dedicated FAQ): typically placed off-account or with a different email.
- **If it fails**: Fnac customer service; or go to the store with the till receipt + ID to have an invoice issued after the fact.
- **Sources**: [Fnac FAQ — partner-seller invoice](https://www.fnac.com/aide?question=comment-obtenir-facture-suite-une-commande-aupres-d-un-vendeur-partenaire) · [FAQ — missing orders](https://www.fnac.com/aide?question=je-ne-retrouve-pas-toutes-mes-commandes-dans-mon-espace-client-que-faire) · [fnacpro.com](https://www.fnacpro.com/) · [toutfacture.com](https://toutfacture.com/guide/comment-demander-une-facture-sur-fnac/)
- **Reliability**: ✅

### Amazon (personal account)
- **Where**: **Vos comptes > Vos commandes** > select the order > **"Facture"** button > *Télécharger la facture* (PDF). If the seller did not provide a VAT invoice: "Facture" menu > **"Demander une facture"** → the seller must reply within ~2 business days.
- **Effort**: ⚡ if sold and shipped by Amazon. 🧗 if a marketplace seller.
- **Prerequisites**: the Amazon account used for the order. For a VAT invoice in the company's name: intra-EU VAT number on file for the account.
- **Pitfalls (CRITICAL)**:
  - **Third-party seller**: Amazon explicitly documents that some marketplace sellers **do not provide an invoice mentioning VAT**. You only get an **order summary** → **non-probative document, VAT not deductible**.
  - **Invoice in the individual's name**: an order on a personal account generates an invoice in the individual's name. Amazon documents "VAT invoice corrections", but **changing the recipient name is not guaranteed**.
- **If it fails — template email to the seller** (via Amazon messaging):
  > *Order no. XXX-XXXXXXX-XXXXXXX of [date]. I am a VAT-registered taxable person in France (VAT no. FRxxxxxxxxxxx, company [X], address [Y]). Please send me an invoice compliant with article 242 nonies A of annex II to the CGI, mentioning your VAT number, the net amount, the rate and the VAT amount, made out to [company].*
- **Sources**: [Amazon Help — VAT invoices](https://www.amazon.fr/gp/help/customer/display.html?nodeId=GRPUHK7RCNVRBURD) · [Amazon Help — request an invoice](https://www.amazon.fr/gp/help/customer/display.html?nodeId=G4M33F6BWMYDTRZU) · [Amazon Help — VAT invoice corrections](https://www.amazon.fr/gp/help/customer/display.html?nodeId=GUTWQJ4DGPN6ADZP) · [probleme-paiement.fr](https://probleme-paiement.fr/comment-avoir-facture-amazon/)
- **Reliability**: ✅

### Amazon Business
- **Where**: **business.amazon.fr** → VAT invoices downloadable on most purchases; bulk export via **Business Analytics > Commandes** (choose the period) > download the invoices.
- **Effort**: ⚡ per invoice, 🔧 for a period export.
- **Prerequisites**: Amazon Business account (SIRET/intra-EU VAT); **order placed from the Business account**.
- **Pitfalls**:
  - **Retroactively attaching orders placed on a personal account: ❌ not verified.** No Amazon source supports it → **assume it's impossible**. You must buy from the Business account from the start.
  - Even on Amazon Business, **third-party sellers** may not issue a VAT invoice. Amazon flags on the product page the items "with a downloadable VAT invoice" → **filter on this criterion before buying**.
- **If it fails**: "Demander une facture" from the order; otherwise Amazon Business support.
- **Sources**: [Amazon Business Help — invoices](https://www.amazon.fr/gp/help/customer/display.html?nodeId=202119460) · [Amazon Business Help — Business Analytics](https://www.amazon.fr/gp/help/customer/display.html?nodeId=202133720)
- **Reliability**: ⚠️ 1 main source (Amazon help, several pages). Attaching past orders = ❌ not verified.

### LDLC
- **Where**:
  - **LDLC.com**: customer account > left-hand menu **"Mes commandes"** > icon in the **"facture"** column to download.
  - **LDLC.pro**: log in > left-hand menu **"Suivi de commandes et factures"** (`secure.ldlc.pro/fr-fr/Orders`). The invoice is also sent automatically by email.
- **Effort**: ⚡
- **Prerequisites**: customer account (or LDLC.pro for company billing). **Order fully shipped.**
- **Pitfalls**:
  - **The invoice is only issued once the order has shipped in full.** Order in several parcels → until the last one leaves, **no invoice exists**. A classic trap at the end of a VAT quarter.
  - Purchase on ldlc.com with a personal account → invoice in the individual's name. LDLC explicitly invites companies to create an account on ldlc.pro.
- **If it fails**: LDLC.pro "Demande de justificatifs" FAQ; customer service **04 27 46 60 05** (Mon-Fri 8:30-12:30 / 14:00-17:30).
- **Sources**: [ldlc.pro/faq — obtain an invoice](https://www.ldlc.pro/faq/297-obtenir-une-facture/) · [ldlc.com — get an invoice](https://www.ldlc.com/en/help/38-get-an-invoice/) · [ldlc.pro — request for supporting documents](https://www.ldlc.pro/faq/298-demande-de-justificatifs/)
- **Reliability**: ✅

### Boulanger
- **Where**:
  - **Online order**: **Mon compte > Mes commandes** (`boulanger.com/account/my-orders`); a **digital duplicate** stays available in "Mon compte". See also **Compte > Mes documents**.
  - **In-store purchase**: dedicated official FAQ "**Obtenir un duplicata de facture pour un achat effectué en magasin**".
- **Effort**: ⚡ online. 🔧 for an in-store duplicate (via customer service).
- **Prerequisites**: customer account / loyalty card linked to the purchase; failing that: date + amount + store + payment method.
- **Pitfalls**:
  - ⚠️ **Limited retention period**: customer service reportedly provides the supporting document **up to 2 years after the purchase** (third-party source, not confirmed by Boulanger).
  - Boulanger Marketplace: third-party seller → invoice not issued by Boulanger.
- **If it fails**: customer service **09 69 32 32 23** (7 days/week, 8:00-22:00) → duplicate sent by email.
- **Sources**: [Boulanger FAQ — in-store duplicate](https://www.boulanger.com/evenement/faq?question=27747-obtenir-un-duplicata-facture-un-achat-effectue-magasin) · [boulanger.com/account/my-orders](https://www.boulanger.com/account/my-orders) · [banqueswiki.com](https://banqueswiki.com/comment-recuperer-une-facture-chez-boulanger/)
- **Reliability**: ⚠️ (the existence of the "in-store duplicate" FAQ is certain; its exact content could not be read — JS page). The "2 years" delay = ⚠️ not confirmed.

### Apple Store (France)
- **Where**:
  - **Hardware (Apple Store online)**: `apple.com` > **Compte > Afficher vos commandes** (`apple.com/fr/shop/account/home`) > click the order price > **"Renvoyer la facture"** → sent by email.
  - **App Store / subscriptions**: **`reportaproblem.apple.com`** → purchase history. (Or the App Store app > profile photo > **Historique des achats**, adjustable "Ces 90 derniers jours" filter.)
- **Effort**: ⚡ (Apple Store online). 🔧 (App Store).
- **Prerequisites**: the Apple account used for the purchase; order number / confirmation email.
- **Pitfalls**:
  - **`reportaproblem.apple.com` gives a history, not an accounting invoice.** Apple invoices arrive by email.
  - **Multiple Apple accounts**: a purchase made with another Apple ID doesn't show up.
  - **Purchases via alternative EU payments (DMA)**: **not invoiced by the App Store** → you must request the invoice **from the app developer**. Major VAT trap.
  - Consumer purchases billed in the personal account's name → for a company invoice, go through **Apple Business Manager / Apple Store for Business** before the purchase.
  - An 18-month availability limit mentioned by third-party sources: ❌ **not verified**.
- **If it fails**: Apple Store **0800 046 046** (Mon-Fri 9:00-20:00, Sat 9:00-18:00).
- **Sources**: [support.apple.com/fr-fr/118212 (purchase history)](https://support.apple.com/fr-fr/118212) · [apple.com/fr/shop/help/orderstatus](https://www.apple.com/fr/shop/help/orderstatus) · [apple.com/fr/shop/help/viewing_changing_orders](https://www.apple.com/fr/shop/help/viewing_changing_orders)
- **Reliability**: ✅ for the App Store history. ⚠️ The exact wording **"Renvoyer la facture"** comes from an Apple community source + snippets, not from a rendered help page → to be re-checked.

## DIY / home improvement

### Leroy Merlin
- **Where**:
  - **Online purchase**: customer account > **Mes commandes** > open the order > invoice (PDF). Also sent by email on delivery.
  - **In-store purchase**: the invoice is issued **at the register at the time of purchase**, on request.
  - Pro account: `leroymerlin.fr/pro`.
- **Effort**: ⚡ online. 🧗 for an in-store purchase not invoiced at the time.
- **Prerequisites**: customer account; in store: **till receipt** (ticket number, register number, date, amount, store) and/or loyalty card.
- **Pitfalls**:
  - **The till receipt is not an invoice** (no customer name/address).
  - After-the-fact invoice requests are **handled case by case by the store** — **no self-service tool** for automatic generation.
- **If it fails**: contact the **after-sales service of the store where the purchase was made** (date, amount, ticket number, store postal code), via `leroymerlin.fr/contact/`. Some stores have reprint kiosks.
- **Sources**: [leroymerlin.fr/aide-et-contact](https://www.leroymerlin.fr/aide-et-contact/) · [Official LM forum — invoice request from a receipt](https://communaute.leroymerlin.fr/app/629/channel/forum-d-entraide-1263/details/demande-de-facture-a-partir-du-ticket-de-31484595) · [leroymerlin.fr/pro](https://www.leroymerlin.fr/pro/)
- **Reliability**: ⚠️ The principle is sourced (official forum + third parties), but **the exact path "Mes commandes > Voir la facture" could not be read on a rendered official help page**.

### Castorama
- **Where** (path **confirmed word for word on the official FAQ**):
  - **Drive 2h** → invoice sent by email **on the day of collection**. **Delivery** → invoice sent by email **as soon as it ships**.
  - In all cases: **customer account > "Historique de commandes" > click the order** > get the invoice.
  - Pro account: **Casto Pro** (`castorama.fr/casto-pro`).
- **Effort**: ⚡
- **Prerequisites**: customer account + order placed online.
- **Pitfalls**:
  - **Marketplace**: invoice sent **by the partner seller** after delivery. If nothing arrives: "Contacter le vendeur" from the history.
  - **Pure in-store purchase**: the FAQ **documents no** online retrieval → ❌ not verified for a self-service duplicate. Ask for the invoice at the register.
- **If it fails**: `commande@castorama.fr` (with the order number) or `castorama.fr/services/contactez-nous`.
- **Sources**: [Castorama FAQ — your order](https://www.castorama.fr/faq/votre-commande-sur-castorama-fr) · [Castorama FAQ — marketplace](https://www.castorama.fr/faq/marketplace-et-vendeurs-partenaires) · [castorama.fr/casto-pro](https://www.castorama.fr/casto-pro)
- **Reliability**: ✅

### Bricomarché / Bricorama
- **Where**: e-commerce customer account (`bricomarche.com/my-account` or `bricorama.fr`) → invoice available for a delivered order. Bricomarché **PRO** area: "Mon espace PRO" link at the top of the site.
- **Effort**: 🔧 — 🧗 for a click & collect or an in-store purchase.
- **Prerequisites**: online customer account created **and activated**; order number.
- **Pitfalls**:
  - **Click & collect**: it's **the store that issues the invoice, on request** — it is not automatically in the account.
  - **Marketplace**: the invoice only appears once generated by the reseller.
  - Classic in-store purchase: no documented online retrieval.
  - Bricomarché ≠ Bricorama (separate brands, separate FAQs, both Les Mousquetaires).
- **If it fails**: e-commerce customer service **09 69 32 80 10** (Mon-Sat 9:00-19:00); for a click & collect, go through the store.
- **Sources**: [Bricomarché FAQ — orders](https://www.bricomarche.com/aide-contact/faq-commandes) · [Bricorama FAQ — customer account](https://www.bricorama.fr/aide-contact/faq-compte-client)
- **Reliability**: ⚠️ / ❌ — **the precise navigation path is not confirmed** (JS FAQs not rendered). Only the principle is sourced.

## Telecom

> **The 24-month catch-up dashboard**

| Operator | Online history | Bulk export |
|---|---|---|
| Orange consumer | **24 months** ✅ | No (1 PDF/month) |
| **Orange Pro** | **6 years** ✅ | **Yes — by calendar year** |
| Orange Business | **12 months** ✅ (duplicate €15 net beyond) | Yes (multi-select) |
| SFR / RED consumer | last 24 invoices ⚠️ | No |
| SFR Business | **3 years** ✅ | Yes (PDF/CSV) |
| Bouygues consumer | 36 months ⚠️ (of which only **12 itemized**) | No |
| **Bouygues Pro/Entreprises** | ✅ | **Yes — "Export multi-CF"** |
| Free / Freebox | ❌ not officially quantified | No |
| Free Pro | ❌ not quantified | PDF + CSV, one by one |

### Orange (consumer)
- **Where**: Customer area > **Facture** > **Historique des factures** (`espace-client.orange.fr/facture-paiement/historique-des-factures`). Contractual documents / mobile purchase receipts: `espace-client.orange.fr/documents`.
- **Effort**: 🔧 (~24 clicks for 24 months, no bulk export).
- **Prerequisites**: the Orange login of the **line holder**.
- **Pitfalls**:
  - **Rolling 24 months, no more.**
  - **Since 10 March 2026, Orange no longer issues paid duplicates** of mobile/internet invoices → beyond 24 months, the invoice is **permanently lost**.
  - A mobile bought by card on the online store **is not on the subscription invoice**: it's a separate document under "Documents contractuels".
- **If it fails**: online-store purchase → duplicate by email to `infos.commande@orange.com` (up to 2 years after the purchase). Physical-store purchase → go there in person with ID.
- **Sources**: [assistance.orange.fr — duplicate / receipt](https://assistance.orange.fr/article/facture-ou-justificatif-d-achat-comment-obtenir-un-duplicata_40936) · [assistance.orange.fr — view your invoice](https://assistance.orange.fr/article/facture-comment-consulter-sa-facture-orange_846059)
- **Reliability**: ✅

### Orange Pro
- **Where**: **espaceclientpro.orange.fr > Facture** > "Accéder à vos factures" → history + **bulk download by calendar year (PDF)**.
- **Effort**: ⚡ for a full year. **The best bulk download on the market.**
- **Prerequisites**: an Orange Pro plan; **having subscribed to electronic invoicing** (that's what unlocks the long history).
- **Pitfalls**: **history up to 6 years, but conditional on electronic invoicing**. Without it, the history is short. Don't confuse it with Orange Business (different rules).
- **If it fails**: first enable electronic invoicing (free, same tax value), then go back to the history.
- **Sources**: [espaceclientpro.orange.fr/facture](https://espaceclientpro.orange.fr/facture) · [assistancepro.orange.fr — view your invoices](https://assistancepro.orange.fr/facture/consulter_ma_facture/espace_client_pro__consulter_vos_factures_clients_internet_open_pro_fixe_ou_mobile_orange_business-396474)
- **Reliability**: ✅

### Orange Business
- **Where**: Espace Client Entreprise > **Facture > Facture Électronique** > choose the domain (Mobile/Internet) > **Appliquer** > tick the invoices > **"Télécharger les factures"**.
- **Effort**: 🔧
- **Prerequisites**: **being the account administrator** AND **having activated the invoice service**.
- **Pitfalls**: **rolling 12 months only**. **A duplicate beyond that costs €15 net.** Orange explicitly recommends saving them regularly.
- **Sources**: [assistance.orange-business.com — Mobile invoices](https://assistance.orange-business.com/mobile/telecharger-vos-factures-mobile) · [— Internet invoices](https://assistance.orange-business.com/internet-et-reseau/telecharger-et-exporter-vos-factures-internet)
- **Reliability**: ✅

### SFR / RED by SFR (consumer)
- **Where**: SFR customer area > **"Conso & Factures"** > "Consulter l'historique de mes factures". RED: Compte Client > **Infos conso** > **Factures** tab.
- **Effort**: 🔧 (no bulk).
- **Prerequisites**: the holder's credentials.
- **Pitfalls**:
  - **Last 24 invoices** on the web area. **The SFR & Moi app only shows 6 months** → **always use the web** for a 24-month catch-up.
  - **After termination**, access to the last 24 invoices remains possible **with the new login shown on the last invoice**. A classic trap.
- **If it fails**: **Duplicata** section of the help center.
- **Sources**: [assistance.red-by-sfr.fr — view my invoice](https://assistance.red-by-sfr.fr/consulter-facture-mobile.html) · [— duplicate](https://assistance.red-by-sfr.fr/obtenir-duplicata-facture.html)
- **Reliability**: ⚠️ The path is sure; **the exact depth on the SFR consumer side is not confirmed by an official sfr.fr page** (assistance.sfr.fr not fetchable).

### SFR Business
- **Where**: SFR Business customer area (`sfrbusiness.fr/espace-client/authentification/`) > **"Vos factures" > "Factures"** > filters (invoice number, period, billing account, contract) > **"Télécharger"** (full duplicate, cover page, breakdown by offer… in PDF or CSV). Account statements: **Vos factures > Paiements > Vos extraits de compte**.
- **Effort**: 🔧
- **Pitfalls**: **stated history: 3 years.** Multi-account companies must select the right **billing account** — a fleet split across several billing centers causes missed invoices.
- **Sources**: [sfrbusiness.fr — invoice duplicate](https://www.sfrbusiness.fr/assistance/factures/duplicata-facture.html) · [sfrbusiness.fr — invoice help](https://www.sfrbusiness.fr/assistance/factures.html)
- **Reliability**: ✅

### Bouygues Telecom (consumer)
- **Where**: Customer area > **"Mes factures et paiements"** > **Factures** tab > download as PDF.
- **Effort**: 🔧
- **Pitfalls**:
  - **36 months of history, but only the last 12 invoices are itemized** — the previous 24 months are in a **simplified version**, potentially insufficient for fine accounting reconstruction.
  - **The app only gives access to the last 12 invoices** → use the web.
  - Duplicate: free by email, **€7.50 by post** (secondary source).
- **Sources**: [bouyguestelecom.fr/mon-compte/mes-factures](https://www.bouyguestelecom.fr/mon-compte/mes-factures) · [assistance.bouyguestelecom.fr](https://www.assistance.bouyguestelecom.fr/s/article/consultation-facture-internet-forfait)
- **Reliability**: ⚠️ The "36 months of which 12 itemized" is consistent across sources but **the official help page (Salesforce) can't be read in a fetch**.

### Bouygues Telecom Pro / Entreprises
- **Where**: Espace Client Gestionnaire (`espaceclient.bouyguestelecom-entreprises.fr`) > **Facture > E-facture** > select a radical > **"Export multi-CF"** button (bottom right) > choose the level of detail + the billing centers > **Télécharger** (Excel/CSV). Separate **"Factur-X"** tab for the new invoices.
- **Effort**: ⚡ once you know the path. **Excellent bulk export.**
- **Prerequisites**: manager account; SIRET for certified electronic invoicing.
- **Pitfalls**:
  - Invoices only available **at D+2** after the cycle date.
  - **Only the electronic version is recognized by the tax authorities** — Bouygues recommends archiving every month.
  - **Factur-X invoices are in a SEPARATE tab**: you think you've downloaded everything when a whole tab is missing.
- **If it fails**: `comptaclients@bouyguestelecom.fr`.
- **Sources**: [bouyguestelecom-pro.fr — view and export your invoices](https://www.bouyguestelecom-pro.fr/assistance/espaces-clients/espace-client-gestionnaire/facture)
- **Reliability**: ✅

### Free / Freebox
- **Where**: **Espace Abonné Freebox** (`moncompte.free.fr`) > **"Mes Factures"** table > click > PDF. Free Mobile: **separate area** (`mobile.free.fr/account/`).
- **Effort**: 🔧
- **Pitfalls**:
  - **Two separate subscriber areas (Freebox ≠ Mobile)** — trap no. 1 at Free.
  - **History depth: ❌ not verified on an official source.** Secondary sources: last 12 invoices on the Mobile side, "beyond a year" on the Freebox side. No Free page quantifies it.
  - **Free duplicates are paid and expensive** → archive as you go.
- **Sources**: [assistance.free.fr — Freebox invoices](https://assistance.free.fr/articles/consulter-mes-factures-freebox-298) · [assistance.free.fr — Free Mobile invoices](https://assistance.free.fr/articles/931)
- **Reliability**: ⚠️ (path ✅ / **depth ❌ not verified**)

### Free Pro
- **Where**: **Espace Client Free Pro** (`pro.free.fr/espace-client/connexion/`) > **"Mes Factures"** tab > **PDF** (summary) **or CSV** (usage detail).
- **Effort**: ⚡ per invoice; 🔧 for 24 months.
- **Pitfalls**: the **CSV** is the right format for batch accounting processing — many people only take the PDF. History depth: ❌ not officially stated.
- **Sources**: [support-pro.free.fr — where to find my invoice](https://support-pro.free.fr/ou-trouver-ma-facture/)
- **Reliability**: ✅ (path) / ⚠️ (depth)

### ⚠️ Switching a personal subscription → pro account (the 4 operators)
- **❌ not verified — no operator documents a "individual → legal entity" switch.**
- What **is** sourced: **line transfer** exists (Orange, SFR, Bouygues), but **Orange explicitly states that "the party taking over your offer must be an adult natural person (and not a company)"**.
- **Practical consequence:** you generally have to **terminate + subscribe to a pro offer**. **Past invoices in the personal name will stay in the personal name → VAT unrecoverable on them.** Do it early.
- **Sources**: [assistance.orange.fr — offer transfer](https://assistance.orange.fr/assistance-commerciale/la-gestion-des-informations-personnelles/changer-le-titulaire-de-votre-ligne/cession-d-offre-changer-de-titulaire_42169-42947) · [SFR — holder change form (PDF)](https://static.s-sfr.fr/media/formulaire_changement_titulaire_b2b-gp_particulier.pdf)
- **Reliability**: ⚠️/❌

## Fuel

### 🧾 The rule to know before you go looking
**There is NO administrative tolerance for petrol-station receipts** (unlike tolls). The BOFiP tolerance targets **tolls** and **parking machines**, not the pumps.
→ **A till receipt or a card slip from a station, without the company name, does not allow you to deduct the VAT.** You need an **invoice** with the details of art. 242 nonies A ann. II CGI.
**Sources**: [BOI-TVA-DECLA-30-20-20-20](https://bofip.impots.gouv.fr/bofip/142-PGP.html/identifiant=BOI-TVA-DECLA-30-20-20-20-20190925) · [BOI-TVA-DED-30-30-40 (petroleum products)](https://bofip.impots.gouv.fr/bofip/1194-PGP.html/identifiant=BOI-TVA-DED-30-30-40-20210224) · **Reliability**: ✅

*(Reminder: on a passenger car, diesel and petrol are deductible at **80%**; at 100% on a utility vehicle.)*

### TotalEnergies — pro fuel card (Fleet / Mobility Corporate)
- **Where**: **Espace Client Mobility Business** (`mobility.totalenergies.com`) > billing section. Subscription: `souscription.mobility.totalenergies.com`.
- **Effort**: 🧗 at setup — then ⚡ every month.
- **What it solves**: **a single invoice** grouping fuel, EV charging, car wash, **electronic tolling (Liber-t and PASSango)**, parking, maintenance — in the company's name, VAT itemized.
- **Pitfalls**:
  - **Pitfall no. 1**: the Fleet card is also distributed by **regional distributors** (Alvea, CLMB, CPO, T-PNE…) who have **their own billing extranets**. If you went through a distributor, **your invoices are NOT in the Mobility Business area**.
  - Charge cards **fall outside the BOFiP tolerance** → they must carry all mandatory details (they do).
- **Sources**: [proxi.totalenergies.fr — Fleet card](https://proxi.totalenergies.fr/professionnels/carburants/cartes-carburant/la-carte-fleet-une-gestion-simplifiee-des-frais-de-deplacement) · [mobility.totalenergies.com](https://mobility.totalenergies.com/)
- **Reliability**: ✅

### TotalEnergies — filling up in-station WITHOUT a pro card
- **Where**: **❌ not verified.** **No official TotalEnergies page describes a duplicate or named-invoice procedure for a fill-up paid at the station.** The "duplicate" FAQs on totalenergies.fr concern electricity/gas/heating oil.
- **Is the fuel receipt a valid invoice?** → **No.** No company name or address, no BOFiP tolerance.
- **Effort**: 🧗 and **uncertain outcome** (asking for an invoice at the register depends on the manager, it's not a nationwide process).
- **Pitfalls**: at **24/7 automated pumps (DAC)**, there is **no one** to issue an invoice → impossible after the fact.
- **If it fails**: **the only robust solution is the pro fuel card.** VAT on past fill-ups paid via anonymous receipt is **lost**.
- **Sources**: [BOI-TVA-DECLA-30-20-20-20](https://bofip.impots.gouv.fr/bofip/142-PGP.html/identifiant=BOI-TVA-DECLA-30-20-20-20-20190925) · [Cegid — fuel VAT](https://www.cegid.com/fr/blog/gestion-parc-flotte-automobile-recuperation-tva-carburant/) · [Indy — fuel VAT](https://www.indy.fr/guide/fiscalite/taxes/tva/recuperer/frais-de-carburant/)
- **Reliability**: ❌ for an official path / ✅ for the tax conclusion (receipt ≠ invoice)

### Leclerc / Carrefour / Intermarché / Esso stations
- **Where (reliable route)**: **the brand's pro fuel card**.
  - **E.Leclerc Carte Carburant Pro** (SIPLEC): €2.90/month/card, +1,100 stations, online customer area, **integrated Liber-t tolling badge** — `cartecarburant.leclerc`.
  - **Multi-brand cards** (e.g. Easyfuel: Intermarché, Netto, Roady, E.Leclerc, Shell, Esso, Avia, BP, ENI): **PDF + EDI invoices sent 2×/month by email**, archived online, **single invoice for fuel + tolls + parking**.
- **Where ("I already filled up at the pump")**: ask for an invoice at the store's reception desk with the Kbis or the company details + intra-EU VAT number. The merchant is required to issue an invoice to a taxable person who requests it.
- **Effort**: ⚡ with a card / 🧗 without a card (often refused on old receipts).
- **Pitfalls**: **none of the brands publishes an official page "how to obtain a fuel invoice after the fact"** → **❌ not verified for retroactive**.
- **Sources**: [cartecarburant.leclerc — invoices FAQ](https://www.cartecarburant.leclerc/faq?thematic=factures) · [lacartecarburant.com — Easyfuel FAQ](https://www.lacartecarburant.com/faq) · [compta-online — DAC](https://www.compta-online.com/quest-ce-quun-dac-ao2525)
- **Reliability**: ⚠️ (pro card ✅; **after-the-fact in-station invoice ❌ not verified**)

## Tolls

### 🧾 The good news: the toll receipt IS an invoice (under conditions)
> **BOFiP BOI-TVA-DECLA-30-20-20-20, §§ 80 to 120**: as a **simplification measure**, the **receipt issued at each pass through the toll barriers** is **treated as an invoice** if it mentions the VAT rate and amount, the details of the service and a sequential number, and if it includes **a space reserved for the information to be filled in by the user**.
> **BUT** the deduction is **strictly conditional** on the customer **filling in that part themselves**: **name or business name + registered-office address** (+ registration number, user, purpose of the trip for justification).

- **Is the VAT shown on a toll receipt?** → **Yes**, rate and amount.
- **Are paper receipts sufficient?** → **Yes, but ONLY if the identification box has been filled in.** A blank receipt = **VAT not deductible**. That's the massive trap: 99% of the receipts in glove boxes are blank.
- ⚠️ This tolerance **does not apply to subscriptions or charge cards** — those must carry all mandatory details (they do, via the monthly invoice).
- **Sources**: [BOI-TVA-DECLA-30-20-20-20](https://bofip.impots.gouv.fr/bofip/142-PGP.html/identifiant=BOI-TVA-DECLA-30-20-20-20-20190925) · [LégiFiscal — toll/parking receipts](https://www.legifiscal.fr/tva/tva-francaise/tva-recuperable/facture-electronique-tickets-peage-parking.html) · **Reliability**: ✅

### 🧾 Does the company tolling badge give a monthly summary invoice with VAT?
**YES — confirmed with all three operators (Ulys, Bip&Go, Fulli).** This is **THE** right answer: one invoice/month, in the company's name, VAT itemized, usable in accounting.

> ⚠️ **Correcting a widespread error**: **Bip&Go is a subsidiary of the Sanef group** (not APRR). The tolling brand of **APRR/AREA is Fulli**. And **"Liber-t" is an interoperable standard, not an operator**: your Liber-t badge is **issued and billed** by Bip&Go, Fulli, Ulys, Leclerc or TotalEnergies. **It's with the badge issuer, not the motorway concessionaire, that you find the invoice.** A very common reasoning error.

### Ulys (VINCI Autoroutes)
- **Where (trip receipt, consumer)**: `account.ulys.com` > **"Factures & Consos" > "mes consos"** tab > **orange round symbol to the right of the line** to download the receipt. Ulys app: **"Consos" > "Télécharger le reçu télépéage"** tab.
- **Where (monthly invoice, Ulys Pro)**: the **"Facture dématérialisée"** service, **included** in every pro subscription but **to be activated**: **Espace Abonnés > "OPTIONS" section > "MES OPTIONS"**. Then: monthly invoices (toll **+ parking**) in the customer area, **history up to 24 months**.
- **Effort**: ⚡ (setup 🔧)
- **Prerequisites**: Ulys pro subscription (1-5 badges: €1.90 net/month/badge; no commitment, deferred payment).
- **Pitfalls**:
  - ⚠️ **The receipt is "issued for information only" and does not account for discounts.** The definitive information is on **the monthly invoice**. **Never book from the receipt.**
  - **The "facture dématérialisée" service is included but not activated by default** — many directors look for invoices that don't exist.
  - **Without a badge, at a toll plaza**: you have to press the "Reçu" button **in the lane**. **VINCI does NOT issue duplicates.**
  - **Free-flow**: non-subscriber → pay online **within 72h**, the supporting document is then sent.
- **Sources**: [ulys.com — pro digital invoice (24 months)](https://ulys.com/professionnel/les-offres-telepeage-ulys/services/facture-dematerialisee/) · [ulys.com — obtaining a receipt](https://ulys.com/faq/obtenir-un-recu-de-paiement-au-peage-comment-faire/) · [vinci-autoroutes.com — toll receipt](https://www.vinci-autoroutes.com/fr/faq/le-peage/comment-obtenir-un-recu-de-paiement-de-peage/)
- **Reliability**: ✅

### Bip&Go (Sanef group, Liber-t badge)
- **Where**: **Espace Abonné** `account.bipandgo.com/mon_compte/` > **"documents en dépôt"** > **PDF** invoices. Also via the Bip&Go app.
- **Effort**: ⚡
- **Monthly VAT summary invoice?** → **YES.** Official: "Once a month, you receive the summary invoice. This single invoice groups your usage of: classic tolls, free-flow tolls, tolling parking, charging." "This centralization simplifies companies' accounting management **and VAT tracking**."
- **Pitfalls**: Bip&Go = **Sanef**. A director who drives on APRR has an interoperable badge but **their invoice comes from their issuer** — look in the right place. Automatic direct debit → people forget to download.
- **If it fails**: free-flow non-subscriber → pay on the concessionaire's site (license plate) then **download the invoice**; **within 72h**, otherwise a **€90** penalty.
- **Sources**: [bipandgo.com — toll invoices](https://www.bipandgo.com/actualites/factures-peage) · [bipandgo.com — professional badge](https://www.bipandgo.com/actualites/badge-professionnel-pour-passer-le-telepeage) · [bipandgo.com — billing pro](https://www.bipandgo.com/en/professional-service/billing)
- **Reliability**: ✅

### APRR / AREA (Fulli badge)
- **Where**: Fulli customer area (`fulli.com`) > trip tracking, **viewing and downloading invoices**. **Fleet manager: "Flotte" tab** → all of a company's badges → **invoice per vehicle or overall summary**, **CSV export**.
- **Effort**: ⚡
- **Monthly VAT summary invoice?** → **YES**, monthly, grouping all trips. **Pro/Perso** option: **two separate invoices** at month-end (company account / employee's personal account) depending on the trip type — very relevant for a director who mixes usage.
- **Official APRR position**: tolling customer → "keep your invoices and your detailed trip statements. They will serve as supporting documents to the tax authorities."
- **Pitfalls**: **Fulli ≠ Bip&Go ≠ Ulys** — three separate customer areas.
- **If it fails**: [APRR — duplicate payment receipt](https://voyage.aprr.fr/aide-contact/peage/paiement/comment-obtenir-un-duplicata-de-justificatif-de-paiement); customer service 0806 004 004.
- **Sources**: [voyage.aprr.fr — recovering VAT on tolls](https://voyage.aprr.fr/aide-contact/ma-formule-et-mes-factures/mes-factures/comment-recuperer-la-tva-sur-les-peages) · [fulli.com — customer area](https://www.fulli.com/en/customer-area) · [fulli.com — pro offer](https://www.fulli.com/en/electronic-toll-badge-professionals)
- **Reliability**: ✅

### Sanef / SAPN
- **Where**:
  - **Receipt at the toll**: dedicated button in the lane. If it doesn't come out → **red "Assistance" button**.
  - **Duplicate**: customer service **+33 9 708 08 709** (Mon-Fri 8:00-20:00, Sat 8:00-13:00), **or** email themed "Demande de justificatif de paiement" providing **the first 6 and last 4 digits of the bank card**.
- **Effort**: 🔧 — 🧗 if several passes to reconstruct.
- **Prerequisites**: date, amount, **first 6 + last 4 digits of the card**.
- **Pitfalls**: 🚨 **Cash payment → NO duplicate possible.** Confirmed word for word by Sanef ("*if you have paid your toll in cash, we will be unable to edit a duplicate of your receipt*"). Same for VINCI.
- **Sources**: [sanef — how do I get a receipt](https://www.autoroutes.sanef.com/en/assistance/how-do-I-get-a-receipt) · [sanef — payment history](https://www.autoroutes.sanef.com/en/assistance/customer-account/payment-history)
- **Reliability**: ✅

---

# PRIORITY 2 — Foreign SaaS (the Tax-ID reservoir)

> **Reminder of the mechanism.** With a valid VAT ID, a supplier established outside France (Ireland, US…) bills you **net under reverse charge**: you carry the VAT as both collected AND deductible on the CA3 return → net cost zero. Without a VAT ID, it bills you **its local VAT** → **not deductible on the CA3 return**, the only way out = the 8th/13th Directive refund procedure (heavy, thresholds, delays).
> **⚠️ The nuance that changes everything: check the billing entity at the top of the invoice.** Some suppliers have a **French branch** and bill you **French VAT at 20%** — that VAT is **deductible normally**, it is NOT a lost reservoir. This is the case for **AWS** (FR branch of AWS EMEA SARL), and potentially for **Google France SARL** and **Microsoft** (LRD model).

### Anthropic (Claude Pro/Max, Team, Console API)
- **Where (invoice)**: claude.ai > click your initials (bottom left) > **Settings > Billing > "Invoices" section > "View"**. Also by email ("Your receipt from Anthropic"). Console API: `platform.claude.com/settings/billing`.
- **Where (Tax ID)**:
  - Pro/Max/Team: **Settings > Billing > "Update" button next to the payment method > "Tax or VAT ID" field** > Save.
  - Console (API): **`platform.claude.com/settings/organization` > tax/VAT ID field > "Save changes"**.
- **Retroactive?**: ❌ **NO, explicitly excluded.** "*Updates to your billing details will only apply to future billing cycles. Previously completed invoices cannot be updated retroactively.*" And: "*Once an invoice is paid, there isn't a way to edit the information on the finalized invoice. Additionally, our internal teams cannot reissue paid invoices or modify information on previous invoices.*"
- **Effort**: ⚡
- **Prerequisites**: intra-EU VAT number (FRxx999999999); billing address = actual place of establishment (it determines the tax jurisdiction).
- **Pitfalls**: (1) the VAT field **only appears if the billing address is eligible**; (2) to bill in the company's name, tick **"Use a different name on invoices"** and fill in "Bill to"; (3) the billing address is the card's address.
- **If it fails**: support (support.claude.com). Don't expect a paid invoice to be re-issued.
- **Sources**: [Add/update Tax or VAT ID (Pro/Max)](https://support.claude.com/en/articles/9889408-add-or-update-your-paid-claude-account-s-tax-or-vat-id) · [Add/update Tax or VAT ID (Console)](https://support.claude.com/en/articles/9889428-add-or-update-your-claude-console-organization-s-tax-or-vat-id) · [Paid Plan Billing FAQs](https://support.claude.com/en/articles/8325618-paid-plan-billing-faqs) · [Billing address & tax calculation](https://support.claude.com/en/articles/12997130-understanding-your-billing-address-and-tax-calculation)
- **Reliability**: ✅ (4 official pages)

### OpenAI (ChatGPT Plus/Pro/Business + API)
- **Where (invoice)**: ChatGPT > profile > **Settings > Account > Payment > "Manage"** (Stripe portal) > **"Invoice History"**. Business: `chatgpt.com/admin/billing` > Billing tab > Invoices. API: `platform.openai.com` > Settings > Organization > Billing.
- **Where (Tax ID)**: ChatGPT: **Settings > Account > Payment > Manage > "Billing information" > "Update information"** > Tax ID field. API: **`platform.openai.com/settings/organization/billing/preferences`**.
- **Retroactive?**: ⚠️ **YES, on explicit request to support, case by case — the most open of the lot.** Official text: "*Approved exemptions apply only to future invoices and do not automatically apply to past charges. **If you have already been charged tax and would like us to review those invoices, please include the specific invoice number(s), the associated organization ID or ChatGPT account email, and the amount(s) in your email, and explicitly request whether you would like (1) a refund only or (2) a refund and a rebilled invoice without tax.** Eligibility for credits or refunds is reviewed on a case-by-case basis and may be limited by jurisdiction and timing.*" → **you MUST ask explicitly**, listing the invoice numbers and amounts. Refund within 5-10 business days after approval.
- **Effort**: 🔧 (entry ⚡ + argued support email for the retroactive part)
- **Prerequisites**: email to `support@openai.com` with invoice numbers + amounts + org ID or account email; specify API **or** ChatGPT.
- **Pitfalls**: (1) subscription taken via **App Store / Google Play** → **no OpenAI invoice**, go through Apple/Google; (2) "limited by **timing**" = the older the invoice, the more likely the refusal → **act fast**.
- **Sources**: [Change billing details](https://help.openai.com/en/articles/8156143-how-can-i-change-the-billing-details-on-my-invoice) · [VAT exemption + refund process](https://help.openai.com/en/articles/7232908-how-do-i-submit-a-vat-exemption-request) · [Find your invoices](https://help.openai.com/en/articles/12356340-how-can-i-find-my-past-chatgpt-invoices) · [Updating Tax ID / VAT ID](https://help.openai.com/en/articles/9038389-updating-billing-information-tax-id-and-vat-id)
- **Reliability**: ✅ (paths + refund policy). ⚠️ on the exact time limit (not quantified by OpenAI).

### Google Workspace
- **Where (invoice)**: **Admin console > Facturation > Comptes de paiement** (`admin.google.com/ac/billing/accounts`) > **"Afficher les factures"** > under "Documents", click the invoice number > PDF or CSV. "Billing management" privilege required.
- **Where (Tax ID)**: **Admin console > Facturation > Comptes de paiement > "Plus" (next to the subscription) > "Afficher les paramètres de paiement" > "Informations fiscales <Pays>" section > Modifier** > enter the VAT number > Enregistrer. If you pay **by monthly invoice** (invoiced account), the field doesn't exist → **go through support**.
- **Retroactive?**: ✅ **YES — the ONLY one with a retroactive credit procedure written in black and white**, section "**Get credit for previous VAT charges**": "*If Google charged you VAT but you qualify to self-assess VAT charges, contact Google Workspace support with your business details and VAT ID. We'll update your account. We'll notify you by email if you're eligible for a credit for previously charged VAT. ... Google Ireland Limited will handle your refund, and the amount will be credited to your account. It can take several weeks to process your credit.*" → **credit to the account**, not a bank transfer; **several weeks**; no month limit indicated.
  **Bonus**: on past invoices, **"Regenerate invoice with updated information"** lets you regenerate the PDF with the VAT number (cosmetic/evidential, **not** a refund).
- **⚠️ CRITICAL FRANCE NUANCE**: if the billing entity is **Google France SARL**, Google bills **French VAT at 20%** → **deductible normally**, **not** a reservoir. The reservoir only exists if the entity is **Google Ireland Limited**. **Check the entity at the top of the invoice before doing anything.**
- **Effort**: 🔧 (entry ⚡; retroactive credit = ticket + several weeks)
- **Pitfalls**: (1) **the billing country is NOT editable after the account is created** → if the wrong country was chosen, you have to recreate a billing account; (2) account bought via a **reseller** → everything goes through the reseller.
- **Sources**: [Taxes in your region ("Get credit for previous VAT charges")](https://knowledge.workspace.google.com/admin/billing/taxes-in-your-region) · [Update your tax information](https://knowledge.workspace.google.com/admin/billing/update-your-tax-information) · [VAT overview](https://knowledge.workspace.google.com/admin/billing/vat-overview) · [Download or print monthly invoices](https://knowledge.workspace.google.com/admin/billing/download-or-print-monthly-invoices)
- **Reliability**: ✅ (5 official pages)

### Microsoft 365 (business) / Microsoft Advertising
**Microsoft 365**
- **Where (invoice)**: `admin.microsoft.com` > **Facturation > Factures et paiements** > PDF.
- **Where (Tax ID)** — **depends on the account type** (check first: Billing > Billing accounts):
  - **MCA account**: **Facturation > Comptes de facturation > select the account > "Ajouter un ID fiscal"** > enter > Enregistrer.
  - **MOSA account**: **Facturation > Vos produits > select the subscription > "Adresse d'utilisation du service" > "Modifier l'adresse d'utilisation du service" > "Numéro de TVA, GST ou PAN" field** > Enregistrer.
- **Retroactive?**: ⚠️ **Not documented, presumed NO.** No retroactive refund procedure in the docs. Microsoft Q&A replies indicate that **existing invoices cannot be updated retroactively**. → **enter the VAT ID BEFORE the next renewal.**
- **Prerequisites**: VAT number **verifiable in VIES** ("*before we can validate your VAT ID, it must be available for verification in the VIES*").
- **Pitfalls**: (1) some regions don't support self-service entry (no "Add tax ID" button); (2) **LRD model** — France is part of it: you may be billed **French VAT** even with a VAT ID, **and that VAT is deductible normally**.

**Microsoft Advertising**
- **Where (Tax ID)**: **Paramètres > Paramètres du compte** > pencil icon > fill in **Business location** then **Business address** → the **VAT registration number** field appears. Validation: **up to 3 days**.
- **Retroactive?**: ⚠️ **On support request only, with tax justification** → credit **on the next billing cycle**, not a bank transfer. ❌ **not verified in a primary source** (help.ads.microsoft.com pages in JS, content obtained via snippets).
- **Pitfall**: the VAT ID is **per ad account**, not global → **check ALL your accounts**.
- **Sources**: [Tax information for M365 for business](https://learn.microsoft.com/en-us/microsoft-365/commerce/billing-and-payments/tax-information?view=o365-worldwide) · [Microsoft Q&A — add company VAT number](https://learn.microsoft.com/en-us/answers/questions/5435626/how-do-i-add-the-company-vat-number-to-the-account) · [MS Ads — Tax or VAT information](https://help.ads.microsoft.com/apex/index/3/en/52032)
- **Reliability**: ✅ for M365 · ⚠️ for Microsoft Advertising · ⚠️ for the absence of retroactivity on M365 (deduced from docs + support Q&A, not from a formal sentence)

### Adobe (Creative Cloud)
- **Where (invoice)**: `account.adobe.com` > **Plans > "Historique de facturation" / "Voir la facture"**.
- **Where (Tax ID)**: `account.adobe.com/plans` > **"Votre formule" > "Modifier le paiement" > "Modifier" or "Ajouter" a card** → the tax-ID field (VAT/GST/CIF) appears **inside the card form** > Enregistrer.
  - ⚠️ **PITFALL NO. 1: the field ONLY appears when editing/adding a card.** That's THE reason thousands of directors never find it.
  - ⚠️ **PayPal**: the field doesn't exist on the Adobe side → you have to **update the VAT in the PayPal settings**, the data then flows back.
- **Retroactive?**: ❌ **NO.** "*Once you enter a VAT ID (or CIF ID) in your Adobe account, **your upcoming invoices** will be processed without VAT charges.*" Strictly prospective. No documented refund procedure.
- **Effort**: ⚡ (but a counter-intuitive path)
- **Pitfalls**: if you **remove** the VAT ID or leave it blank, **the VAT comes back**. Reported cases of invoices issued with the **old** VAT ID after a change.
- **If it fails**: Adobe Customer Care chat (`helpx.adobe.com/contact.html`) — ask for a credit note + re-issuance. **Uncertain outcome.**
- **Sources**: [Update your tax identification number](https://helpx.adobe.com/account/individual/billing-and-payments/view-billing-and-invoices/update-tax-identification-number.html) · [Find your Adobe invoice](https://helpx.adobe.com/account/individual/billing-and-payments/view-billing-and-invoices/view-download-email-adobe-invoice.html) · [Adobe Community — Wrong (old) VAT number](https://community.adobe.com/t5/account-payment-plan-discussions/wrong-old-vat-number-on-invoice/m-p/15086719)
- **Reliability**: ✅ (path + absence of retroactivity). ⚠️ for Creative Cloud **Teams/Enterprise** (Admin Console path not verified).

### Notion
- **Where (invoice)**: **Settings > Billing > under "Invoices" > "View invoice"**. ⚠️ **Notion does NOT email invoices** ("*We don't send email invoices at this time*") → nobody ever retrieves them. **A classic reservoir.**
- **Where (Tax ID)**: **Settings > Billing** > **VAT Number / Tax Registration Number** field. France format: **`FRAB123456789`**. "*If you're using Notion for business purposes and provide a valid VAT Number ..., you will not be charged VAT **on subsequent invoices**.*"
- **Retroactive?**: ⚠️ **Two things NOT to confuse:**
  1. **VAT refund: not documented**, and the official keyword is "**on subsequent invoices**". The general refund policy gives the de facto limit: "*we can process a refund if you contact us **within three days of the invoice date for monthly billing, or within 30 days ... for annual billing***" → **3 days (monthly) / 30 days (annual)**. Brutal.
  2. **Adding the VAT number to already-issued invoices: ✅ YES, Notion does it manually.** "*How can I update my invoices to include my billing address and/or VAT number? — **We can update this info for you!** Just message us in the app… or email us at team@makenotion.com.*" → useful for **document compliance**, but this is **not** a refund.
- **Effort**: ⚡ (entry) / 🧗 (retroactive, nearly dead beyond 3 days on monthly)
- **If it fails**: `team@makenotion.com` — ask for (a) the VAT number added to past invoices (granted) and (b) the VAT credit (out of window = likely refused).
- **Sources**: [notion.com/help/sales-tax](https://www.notion.com/help/sales-tax) · [notion.com/help/invoices](https://www.notion.com/help/invoices) · [notion.com/help/refunds](https://www.notion.com/help/refunds)
- **Reliability**: ✅ (3 official pages). ⚠️ on the specific VAT refund (cautious interpretation, flagged as such).

### Figma
- **Where (invoice)**: **Admin > Billing > Invoices tab**. On Professional: Admin > **Settings** > Plan and Billing section.
- **Where (Tax ID)**: **Admin > Settings > "Plan and Billing" > "Value Added Tax / Goods and Services Tax"** (Professional plan). On **Organization/Enterprise**: **Admin > Billing > "Value Added Tax / Goods and Services Tax"**.
- **Retroactive?**: ⚠️ **YES but 30 days only.** "*If a valid VAT number is entered and VAT has previously been charged ..., upon request, Figma **may** refund for VAT included on invoices issued in the **30 days prior** to a valid VAT number being provided **and notified to Figma**. However, VAT will not be refunded on any invoices issued outside this 30 day period.*"
  → **Adding the VAT ID is not enough: you must NOTIFY Figma** via the support form (`help.figma.com/hc/en-us/requests/new`).
- **Effort**: ⚡ (adding) / 🔧 (refund request)
- **Pitfalls**: the VAT ID is set at **team/org** level, not at the personal-account level — a "personal" team billed without a VAT ID keeps being taxed.
- **Sources**: [help.figma.com — Sales tax and VAT](https://help.figma.com/hc/en-us/articles/4418838088983-Sales-tax-and-VAT) · [help.figma.com — Manage payment and invoice details](https://help.figma.com/hc/en-us/articles/360040532093-Manage-payment-and-invoice-details)
- **Reliability**: ✅

### Slack
- **Where (invoice)**: **Admin > Manage billing > Billing history tab** (`my.slack.com/admin/billing`).
- **Where (Tax ID)**: **Admin > Manage billing > Billing page > Settings tab** > enter the **"VAT or GST/HST ID number"** > **Save settings**. Reserved for the **Workspace Owner**.
- **Retroactive?**: ⚠️ **YES, 90 days.** "*if a valid tax registration number is entered and VAT/GST has previously been charged ..., then upon request by you, Slack **may** refund VAT/GST included invoices issued in the **ninety days prior** to a valid tax ID being provided.*" Procedure: article "Claim a tax refund for exempt workspaces" → add the tax ID **then contact support** ("*past invoices won't be updated*" automatically).
- **Effort**: 🔧 (adding ⚡ + **mandatory support ticket**)
- **Pitfalls**: (1) the field exists, but **if the "VAT/GST Registered" status is not selected, nothing changes**; (2) **the refund is not automatic**: without a ticket, the 90 days run out for nothing.
- **If it fails**: `my.slack.com/help/requests/new` or `tax@slack.com` (workspace URL + invoice numbers).
- **Sources**: [slack.com/help — Sales tax and VAT](https://slack.com/help/articles/226166647-Sales-tax-and-VAT) · [slack.com/help — Claim a tax refund for exempt workspaces](https://slack.com/help/articles/49040453999507-Claim-a-tax-refund-for-exempt-workspaces)
- **Reliability**: ✅

### AWS (Amazon Web Services)
- **Where (invoice)**: **Billing console > Bills page** (`console.aws.amazon.com/billing/home#/bills`) > select the month > **"Tax Invoices"** section.
- **Where (Tax ID)**: **Billing console > Tax Settings** (`console.aws.amazon.com/billing/home#/tax`) > **"Manage Tax Registration"** > country (France) > enter the **TRN** + the **Business Legal Address**. A payer account can update **multiple linked accounts in bulk** from its own Tax Settings page.
- **Retroactive?**: ✅ **YES, documented procedure, no stated day limit.** "*Once you are satisfied with the update(s), please contact Customer Support to have your affected Request(s) for Payment and applicable VAT invoices **credited and re-issued**.*" → open a **billing support case / VAT category**.
- **⚠️ MAJOR NUANCE**: AWS EMEA SARL has a **French branch** → for a FR customer, AWS bills **French VAT (20%) even with a valid TRN**, and **that VAT is deductible normally on the CA3 return** — this is **not** reverse charge. The AWS reservoir is therefore not "unrecoverable VAT" but "**non-compliant invoice for lack of the customer's VAT number**".
- **Effort**: 🔧 (update) / 🧗 (re-issuing earlier invoices)
- **Pitfalls**: (1) **pitfall no. 1 = consolidated billing**: the payer has its TRN, **the linked accounts do NOT inherit it** → wrong invoices. **Handle each linked account individually**; (2) the VAT is frozen **at the time of billing**: changing the address/TRN mid-month has no automatic retroactive effect; (3) a foreign card can flip the account's country.
- **Sources**: [aws.amazon.com/legal/aws-emea/](https://aws.amazon.com/legal/aws-emea/) · [aws.amazon.com/tax-help/trn/](https://aws.amazon.com/tax-help/trn/) · [repost.aws — update tax registration number](https://repost.aws/knowledge-center/update-tax-registration-number)
- **Reliability**: ✅

### Vercel
- **Where (invoice)**: **Dashboard > team selector > Settings > Billing** (or **Invoices** tab) > PDF download icon. `vercel.com/account/invoices`.
- **Where (Tax ID)**: **Dashboard > Settings > Billing** > **"Billing Tax ID"** field (`vercel.com/account/billing`).
- **Retroactive?**: ❌ **NO.** "*Changes are reflected on future invoices only. Details on previous invoices will remain as they were issued and cannot be changed.*" No documented VAT refund procedure → **❌ not verified** on the refund side. Only contact: **tax@vercel.com**.
- **Effort**: ⚡
- **Pitfalls**: (1) **Vercel only collects VAT on invoices issued from 01/04/2026** → **no retroactive reservoir on 2024-2025**; (2) apparent contradiction in the docs (old FAQ: "Vercel is a US-based entity and does not have a VAT ID") → **check what your latest invoice actually says**; (3) the "Billing Tax ID" field has historically been for **display** — verify that reverse charge is actually applied after adding it.
- **Sources**: [vercel.com/docs/pricing/taxes](https://vercel.com/docs/pricing/taxes) · [vercel.com/docs/plans/pro-plan/billing](https://vercel.com/docs/plans/pro-plan/billing) · [vercel.com/blog/advanced-invoice-settings](https://vercel.com/blog/advanced-invoice-settings)
- **Reliability**: ⚠️ (paths ✅; retroactive VAT policy not documented)

### GitHub
- **Where (invoice)**: **Profile photo > (Settings, or Your organizations > Settings) > "Billing & Licensing" > Payment history** > icon under "Receipt"/"Invoice".
- **Where (Tax ID)**: **"Billing & Licensing" > Payment information**. ⚠️ **The current docs do NOT document a dedicated VAT field.** The old docs described a free-text **"Additional information" > Add information** field that let a "*VAT or GST identification number*" appear on receipts — but that field is **declarative/cosmetic**: **it prints the number, it is not documented as triggering reverse charge**. → **partially ❌ unverified path.**
- **Retroactive?**: ❌ **not verified.** No published policy. The only documented tax procedure is **US-only** ("Adding a sales tax certificate"). Community discussions (#48483, #102804, #124077) confirm the reverse-charge topic isn't handled properly on the docs side.
- **Effort**: 🧗 (uncertainty + support)
- **Pitfalls**: **personal account vs organization**: a Copilot/Pro subscription taken on a personal account is treated as B2C — go through an **organization** to hope for B2B treatment.
- **If it fails**: ticket on **support.github.com** (Billing category) explicitly requesting the EU reverse charge + re-issuance.
- **Sources**: [docs.github.com — manage payment info](https://docs.github.com/en/billing/how-tos/set-up-payment/manage-payment-info) · [docs.github.com — adding information to your receipts](https://docs.github.com/en/billing/managing-your-github-billing-settings/adding-information-to-your-receipts) · [github community discussion #48483](https://github.com/orgs/community/discussions/48483)
- **Reliability**: ⚠️ (invoice ✅; **VAT field and retroactivity not documented**)

### Canva
- **Where (invoice)**: **Profile > Settings > "Orders and invoices" tab** > **View / Download invoice** (PDF). Only **owners/admins** see the team's invoices.
- **Where (Tax ID)** — **TWO distinct paths, absolutely not to be confused**:
  1. **Display Tax ID**: **Settings > Billing > "Billing details" > Add or update > "Invoice information" > "Tax ID" > "Add tax ID"** > Save.
  2. **Exemption / reverse charge (THE real lever)**: same screen, then **"Request tax exemption"** > choose the **Issuing Country** > entity name + tax ID > **Request**. Automatic validation against **VIES**.
- **Retroactive?**: ❌ **near zero.** "*The tax exemption will apply only to invoices issued after you submit your details. ... **We can only modify the most recent or previous month's invoice in limited cases.***" and "***We can't update invoices older than 30 days.** If you were charged tax based on outdated info, contact your local tax authority to request a refund.*"
- **Effort**: 🔧
- **Pitfalls**: (1) **THE CENTRAL PITFALL: adding a "Tax ID" does NOT remove the VAT** — "*Adding a non-exempt Tax ID does not waive tax charges*". **You absolutely must click "Request tax exemption".** (2) make the request **from the website** (impossible from the mobile app); (3) purchases via App Store/Google Play = **out of scope**.
- **Sources**: [canva.com/help/billing-details/](https://www.canva.com/help/billing-details/) · [canva.com/help/tax-exempt-invoice/](https://www.canva.com/help/tax-exempt-invoice/) · [canva.com/help/general-sales-tax/](https://www.canva.com/help/general-sales-tax/)
- **Reliability**: ✅

### LinkedIn (Premium / Sales Navigator / LinkedIn Ads)
- **Where (invoice)**: **Subscriptions**: LinkedIn **Admin Center > Purchases** → download the receipts. **LinkedIn Ads**: **Campaign Manager > Account settings > Billing > Billing history tab** (bulk export possible).
- **Where (Tax ID)** — **TWO separate places depending on the product**:
  1. **Subscriptions**: **Admin Center > "Tax information" (left panel) > "Add tax ID" > Country/Region > Next > "Tax number" > Add.** (At purchase: tick **"I'm purchasing as a business"** in the checkout.)
  2. **LinkedIn Ads**: **Campaign Manager > Account settings > Billing > "Billing setup" tab > "How you'll pay" > "Manage" menu > "Add Tax ID"** → **prefix with the country code** (e.g. `FR…`).
- **Retroactive?**: ❌ **NO — non-retroactivity written in black and white.** "***Tax registration numbers are applied to future purchases or receipts. They won't be applied to past purchases or receipts.***" Billing by **LinkedIn Ireland**: without a valid VAT number, the customer's country VAT is applied.
- **Effort**: ⚡ (adding) / 🧗 (retroactive: nearly doomed to fail)
- **Pitfalls**:
  - **It's the worst lost reservoir**: LinkedIn charges VAT and **never refunds retroactively** → **every month of waiting = VAT permanently lost**.
  - **VAT wrongly paid here is unrecoverable on the CA3 return** (VAT of another member state) → the only route: the 8th Directive, heavy.
  - **The VAT of the personal Premium account ≠ that of the Ads account: both must be done separately.**
  - **One VAT number per billing admin** — several Ads accounts with different VAT numbers → you need different billing admins.
- **If it fails**: LinkedIn Billing Support — **expect a refusal** (written policy). **Absolute priority: add the VAT ID immediately to stop the bleeding.**
- **Sources**: [linkedin.com/help — a1344289](https://www.linkedin.com/help/linkedin/answer/a1344289) · [linkedin.com/help sales-navigator — a417903](https://www.linkedin.com/help/sales-navigator/answer/a417903) · [linkedin.com/help — a1340134](https://www.linkedin.com/help/linkedin/answer/a1340134)
- **Reliability**: ✅

---

# PRIORITY 3 — Mobility, travel, logistics

### Uber (ride-hailing)
- **VAT deductibility**: ❌ **NO.** Passenger transport → zero admission coefficient. Exceptions: transport on behalf of a public passenger-transport company, or a permanent contract for home-to-work transport of staff.
- **Where**: **no need to look for the VAT.** The supporting document is still useful as proof of the **expense** (gross, account 625). If needed: `riders.uber.com/trips` > Mes trajets > the ride > *Voir le détail* > *Télécharger la facture*. Uber for Business: consolidated monthly invoice on `business.uber.com`.
- **Effort**: ⚡ (and zero effort if you apply the rule: you don't look)
- **Pitfalls**: (1) **pitfall no. 1 is believing you recover the VAT — you don't**; (2) the tax profile (`riders.uber.com/tax-profiles`) **is not retroactive**.
- **Sources**: [BOI-TVA-DED-30-30-20](https://bofip.impots.gouv.fr/bofip/1192-PGP.html/identifiant=BOI-TVA-DED-30-30-20-20250723) · [compta-online — taxi/ride-hailing VAT](https://www.compta-online.com/tva-taxi-vtc-ao2511) · [Uber Help — ride invoice](https://help.uber.com/en/riders/article/jai-besoin-dune-facture-pour-ma-course?nodeId=4cca71a5-0a69-4923-9f9f-870efa9356c7)
- **Reliability**: ✅

### Uber Eats
- **VAT deductibility**: ✅ **YES.** This is not passenger transport but **catering** — an express exception to the "accommodation" exclusion. Meals 10%, alcohol 20%, service/delivery fees 20%. Condition: company interest + invoice in the company's name.
- **Where**: `ubereats.com` (or app) > ☰ > **Commandes** > the order > **Télécharger la facture** (PDF). Tax profile: `riders.uber.com/tax-profiles` (shared Uber/Uber Eats account).
- **Effort**: ⚡
- **Prerequisites**: **company tax profile filled in BEFORE the order.**
- **Pitfalls**: (1) **the invoice can't be modified once issued** — without a tax profile, it stays in the individual's name; (2) the invoice mixes **several rates (10/20%)** — don't apply a single rate; (3) document the business purpose (who, what, why).
- **Sources**: [Uber Eats Help — request the invoice](https://help.uber.com/en/ubereats/stores/article/demander-la-facture-dune-commande?nodeId=246f0b6b-8c6c-4a6c-94d5-60482b045752) · [Weblex — hotel/restaurant: is VAT deductible?](https://www.weblex.fr/articles/hotel-restaurant-frais-de-deplacement-la-tva-est-elle-toujours-deductible) · [BOI-TVA-DED-30-30-10](https://bofip.impots.gouv.fr/bofip/1190-PGP.html/identifiant=BOI-TVA-DED-30-30-10-20130304)
- **Reliability**: ✅

### Booking.com and hotels
- **VAT deductibility**: **PARTIAL.**
  - ❌ **The director's or employee's room night: NOT deductible**, **whatever the reason**, even 100% business.
  - ✅ **Deductible if billed separately**: catering, **breakfast**, parking, phone, internet, laundry.
  - ✅ Exception: accommodation for a **third party** (client, supplier) is deductible.
- **Where**: ⚠️ **Booking.com issues NO invoice to the traveler.** Official partner docs: "Booking.com cannot send invoices to partners or their customers for reservations" — **only the accommodation provider is entitled to invoice**, and it must do so at check-out **for the total amount of the reservation** (even if Booking took its commission upstream).
  → **The invoice is requested AT THE HOTEL, at the front desk, at check-out.**
  On `account.booking.com` > Réservations, you only find the **reservation confirmation** — **that is not an invoice**.
  Chains (Accor, Marriott…): customer area > stay history > "invoice / folio".
- **Effort**: 🔧 (remember to claim the invoice at check-out) — 🧗 after the fact.
- **Pitfalls**: (1) confusing the **Booking confirmation** and the **invoice** → non-probative document; (2) **if breakfast is not itemized on a separate line with its rate, no VAT is recoverable on it** — demand it; (3) prepaid reservation via Booking: some hotels are reluctant to invoice, **yet they are required to**.
- **If it fails**: call the hotel back (reservation number + dates) for a duplicate by email. **The bank statement alone does not allow you to deduct the VAT.**
- **Sources**: [Booking Partner Hub — Do I supply guests with invoices?](https://partner.booking.com/en-us/help/policies-payments/guest-payments/do-i-supply-guests-invoices) · [Booking Partner Hub — Providing guests with invoices](https://partner.booking.com/en-us/help/policies-payments/guest-payments/providing-guests-invoices) · [BOI-TVA-DED-30-30-10](https://bofip.impots.gouv.fr/bofip/1190-PGP.html/identifiant=BOI-TVA-DED-30-30-10-20130304) · [Lefebvre Dalloz — mission expenses VAT](https://formation.lefebvre-dalloz.fr/actualite/deduction-tva-sur-frais-mission)
- **Reliability**: ✅ (tax rule + "Booking doesn't invoice the traveler") / ⚠️ (exact path in the Booking customer area not verified screen by screen)

### SNCF (Connect / Pro)
- **VAT deductibility**: ❌ **NO.** Passenger transport → same exclusion as taxi/ride-hailing. The ticket is booked **gross in 625**; the VAT (10%) goes **neither** to 44566 **nor** to line 20/21 of the CA3 return. **Same for plane, metro, bus.**
- **Where**: **useless for the VAT** — but a supporting document is still needed as an accounting record.
  - **Purchase receipt**: SNCF Connect > **Billets** > the trip > **"Justificatifs d'achat et de voyage"** > *Obtenir le justificatif par e-mail*. Available **up to 13 months** after the arrival date.
  - **Travel receipt**: SNCF Connect > **Vos voyages passés** > the trip > *Justificatifs d'achat et de voyage*. ⚠️ **Accessible only 60 days after departure.**
  - ⚠️ SNCF **does not issue an invoice in the strict sense** for a single ticket — the purchase receipt stands in for it.
- **Effort**: ⚡
- **Pitfalls**: (1) **60-day window** for the travel receipt; (2) purchase at a station/kiosk without an account → no online retrieval; (3) **deducting the VAT on the ticket is a classic reassessment**.
- **Sources**: [SNCF Connect — the purchase receipt](https://www.sncf-connect.com/aide/le-justificatif-d-achat) · [SNCF Connect — your travel receipts](https://www.sncf-connect.com/aide/vos-justificatifs-de-voyage) · [BOI-TVA-DED-30-30-20](https://bofip.impots.gouv.fr/bofip/1192-PGP.html/identifiant=BOI-TVA-DED-30-30-20-20250723) · [compta-online — VAT on train/plane tickets](https://www.compta-online.com/la-tva-sur-les-billets-de-train-ou-avion-est-pas-deductible-ao1724)
- **Reliability**: ✅

### Car rental — Sixt / Hertz / Europcar
- **VAT deductibility**: **PARTIAL, depending on the vehicle.**
  - ❌ **Passenger car (VP, or mixed use)**: VAT on the **rental** (even short-term) **NOT deductible**. The criterion is **the use the vehicle was designed for**, not its actual use. Same for maintenance/repair of the passenger car.
  - ✅ **Utility vehicle** (2 seats, light truck, van, truck): VAT on the rental **fully deductible**. **That's the real lever.**
  - **Fuel** follows a separate regime (80% on passenger cars, 100% on utility vehicles).
  - ⚠️ BOI-RES-TVA-000161 (30/04/2025): risk of **reclassification as a passenger car** for "passenger-car derivatives" (5 seats with a bench).
- **Where**:
  - **Sixt**: final invoice sent by email after return; Sixt account > **Mes réservations / Mes locations**. Help center > *Facturation et paiements* > **"Factures et reçus"** (lets you change the VAT details / address). Sixt Business account for pros.
  - **Europcar**: `europcar.fr` > **Mon Compte** > **"Duplicatas de factures"** (dedicated page). Contract customers: e-invoicing portal (2-year archiving, 24/7).
  - **Hertz**: **electronic receipt** by email after return; `hertz.fr` > **Mon compte** > **Activité du compte**. Duplicate: Customer Relations with the **rental contract number**.
- **Effort**: 🔧 — 🧗 for a Hertz duplicate after the fact.
- **Prerequisites**: contract number + contract name; **company VAT details entered AT THE COUNTER or in the profile**, otherwise the invoice comes out in the driver's name.
- **Pitfalls**: (1) **renting a passenger car thinking you'll recover the VAT** — the biggest loss; **rent a utility vehicle when possible**; (2) the final invoice ≠ the quote/pre-authorization: it arrives **after the return**; (3) fines and damage charges are billed **separately**; (4) **Sixt bills from varying entities depending on the country** → possible foreign VAT (8th Directive, not the CA3 return).
- **Sources**: [BOI-TVA-DED-30-30-20](https://bofip.impots.gouv.fr/bofip/1192-PGP.html/identifiant=BOI-TVA-DED-30-30-20-20250702) · [BOFiP ACTU-2024-00189 — mixed-use vehicles](https://bofip.impots.gouv.fr/bofip/14401-PGP.html/ACTU-2024-00189) · [Sixt — Factures et reçus](https://www.sixt.fr/help-center/sections/factures-et-recus/) · [Europcar — Duplicatas de factures](https://www.europcar.fr/EBE/module/render/Mon-Compte-duplicatas-de-factures) · [Hertz — Reçu électronique](https://www.hertz.fr/rentacar/productservice/index.jsp?targetPage=HEL_eReceipt.jsp)
- **Reliability**: ✅ (tax rule) / ✅ (Europcar) / ⚠️ (Sixt and Hertz: official pages exist but **menu labels not verified in a logged-in session**)

### La Poste / Colissimo / Chronopost
- **VAT deductibility**: **VARIABLE — and often NIL. This is the point to remember.**
  - ❌ **Stamps, ordinary postage, plain/registered letter, Colissimo dropped at a post office** = **universal postal service → VAT-EXEMPT.** **There is no VAT on the invoice, so nothing to recover.** Basis: **CGI art. 261-4-11°** and **art. 261 C-3°**. Confirmed by La Poste itself: "Part of postal activities falls under the Universal Service, which is VAT-exempt (decree no. 2007-29 of 5 January 2007)."
  - ✅ **VAT 20% applicable and deductible** on: **Chronopost** (express, outside the universal service), bulk postage, routing/mailing, **Colissimo business contracts**, packaging, supplies, La Poste Solutions Business.
- **Where**:
  - **Purchase at a post office**: till receipt. Retrievable from the **Espace client Pro** (official FAQ: "Comment consulter et télécharger mes factures d'achats réalisés en point de vente La Poste depuis mon Espace client Pro").
  - **laposte.fr**: Espace client > **Mes achats** > order detail > **"Voir l'intégralité de la commande" > "Télécharger la facture"**. **History: last 18 months.** ⚠️ **"Your invoices are not notified to you by email"** — you have to go and get them.
  - **Colissimo business**: `colissimo.fr/entreprise` > customer account > **Vos Outils / Colissimo et moi / Factures / Consulter**. Monthly invoice posted **around the 15th of the following month**, **rolling 12-month history**.
  - **Chronopost**: `chronopost.fr/moncompte` > **"Mes factures"**; contract customers: **e-Facture** platform (`chronopost.e-facture.net`, free and unlimited access).
- **Effort**: ⚡ (laposte.fr, Chronopost e-facture) / 🔧 (in-office purchases without an attached pro account)
- **Pitfalls**: (1) **the major pitfall: looking for VAT where there is none** (stamps = exempt); (2) a La Poste invoice can **mix** exempt lines and 20% lines → **only recover on the latter**; (3) cash purchase in-office without a pro account = **paper receipt only, not reconstructable online**; (4) retention: **18 months** (laposte.fr), **12 months** (Colissimo business) → beyond that, lost.
- **If it fails**: La Poste Pro Customer Service **3634** (Mon-Fri 9:00-18:00); Chronopost "Je n'ai pas reçu ma facture" page.
- **Sources**: [BOI-TVA-CHAMP-30-10-60-10 — universal postal service](https://bofip.impots.gouv.fr/bofip/823-PGP.html/identifiant=BOI-TVA-CHAMP-30-10-60-10-20250709) · [La Poste — why some products are not subject to VAT](https://aide.laposte.fr/contenu/pourquoi-certains-produits-ne-sont-pas-soumis-a-la-tva) · [La Poste — download my invoices](https://aide.laposte.fr/contenu/comment-telecharger-et-ou-imprimer-mes-factures) · [La Poste Pro — point-of-sale invoices](https://aide.laposte.fr/professionnel/contenu/comment-consulter-et-telecharger-mes-factures-d-achats-realises-en-point-de-vente-la-poste-depuis-mon-espace-client-pro) · [Chronopost e-facture](https://chronopost.e-facture.net/)
- **Reliability**: ✅ (exemption: La Poste + BOFiP + Légifrance; laposte.fr and Chronopost paths) / ⚠️ (exact Colissimo business path not verified in a logged-in session)

---

## Summary of the ❌ UNVERIFIED points (do not assert them to the user)

| Point | Status |
|---|---|
| Retroactively attaching personal orders to Amazon Business | ❌ not documented → **assume impossible** |
| Precise navigation path for Bricomarché / Bricorama | ❌ JS FAQs not rendered |
| "Mes commandes > Voir la facture" path for Leroy Merlin | ⚠️ probable, not certified on an official page |
| Exact "Renvoyer la facture" wording for Apple Store | ⚠️ community source, not confirmed on a help page |
| 18-month limit on Apple invoices | ❌ not verified |
| "2 years" duplicate window at Boulanger | ⚠️ third-party source only |
| History depth of Free / Free Pro invoices | ❌ never officially quantified |
| Exact depth for SFR consumer | ⚠️ 24 invoices (RED source), not confirmed on sfr.fr |
| After-the-fact fuel invoice at the station (TotalEnergies, Leclerc, Carrefour, Intermarché) | ❌ no official procedure published |
| Personal → legal-entity switch for a telecom subscription | ❌ not documented (and Orange explicitly excludes it in self-care) |
| GitHub VAT ID field triggering reverse charge | ❌ not documented (the existing field is cosmetic) |
| GitHub retroactive refund policy | ❌ nothing published |
| Microsoft Advertising retroactivity | ⚠️ official pages not retrievable (content via snippets) |
| Absence of retroactivity on Microsoft 365 | ⚠️ deduced from docs + support Q&A, not from a formal sentence |
| Adobe Creative Cloud **Teams/Enterprise** path | ⚠️ Admin Console not verified |
| Exact path in the Booking.com customer area | ⚠️ not verified screen by screen |
| Sixt and Hertz menu labels | ⚠️ pages exist, menus not verified in a logged-in session |
| Exact Colissimo business path | ⚠️ labels taken from a PDF FAQ |

---

*File produced on 13/07/2026. Supplier URLs and navigation paths change: re-verify the ⚠️ and ❌ entries before any production use. The tax rules cited (BOFiP, CGI) are up to date as of that date.*
