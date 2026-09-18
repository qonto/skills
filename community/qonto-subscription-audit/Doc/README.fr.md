# 🔍 qonto-subscription-audit — L'audit complet des dépenses récurrentes

> **Skill #9 · l'audit complet des dépenses récurrentes** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> 100 % Qonto pur, 100 % lecture — l'audit que tout le monde repousse, en un prompt

---

## 🎯 Le pitch

Les abonnements s'empilent, les prix montent en douce, les essais deviennent payants, personne ne résilie. `qonto-subscription-audit` fait l'audit COMPLET des dépenses récurrentes sur **24-36 mois** :

1. **L'inventaire total** — tous les prélèvements récurrents (cartes ET prélèvements SEPA), cadence mensuelle/trimestrielle/**annuelle**, avec le **coût annuel TOTAL** (le chiffre choc) et le statut de chaque ligne : ✅ actif utile · 👥 doublon (deux outils qui font pareil) · 🧟 zombie (toujours confirmé par toi) · 🎣 essai devenu payant
2. **Les nouveaux 🌱** — chaque contrepartie récente jamais vue est évaluée. Premier signal : **la culture générale de Claude** — streaming & logiciels (Netflix, Adobe, Microsoft 365), IA (OpenAI), design (Figma, Slack, Notion), **plateformes de formation (Systeme.io, Skool, Kajabi, Podia…)**, **hébergeurs & noms de domaine (OVH, PlanetHoster, Gandi, IONOS — renouvellement ANNUEL, le plus facile à rater)**… : **une seule première occurrence suffit** pour le tag 🌱, aucun historique nécessaire. Puis les signaux comportementaux : montant rond typique, libellé (subscription/monthly/plan), 2e occurrence à ~30 j → « abonnement probable, à confirmer ». La détection **précoce** : attraper l'essai avant qu'il devienne une rente
3. **Chaque hausse détectée** — paliers de prix (≥ 2 prélèvements ±2 %, saut persistant ≥ 2 cycles), change et TVA exclus (comparaison HT via les factures fournisseurs), tag 🟢 ≤ inflation · 🟡 au-dessus · 🔴 agressive · ⚪ usage variable, et le **surcoût annuel cumulé** de toutes les hausses
4. **Le dashboard + les emails** — dashboard construit **directement dans Claude**, exportable en fichier HTML autoportant aux couleurs Qonto ; email de renégociation argumenté (ancienneté, volume, historique des hausses) et **digest mensuel** (actifs, total du mois, prévisionnel 3 mois, hausses) — brouillons Gmail si le MCP est là, texte à copier sinon, **jamais envoyés sans toi**

Pour ensuite **protéger un abonnement par carte plafonnée** : c'est le skill `qonto-subscription-guardian` (lui seul écrit sur Qonto).

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Cœur agnostique** : inventaire, statuts et détection des hausses marchent dans tous les pays Qonto (FR, DE, ES, IT…). Seul le référentiel d'inflation est localisé — inflation du pays si connue, zone euro sinon, référence annoncée | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Historique **≥ 24 mois** | Un abonnement ANNUEL ne se repère qu'avec 2 occurrences : sur 12 mois, les annuels passent sous le radar. En dessous : audit de ce qui est visible + annonce honnête de ce qui peut manquer | ⭕ recommandé |
| MCP Gmail | Détecté dynamiquement : présent → digest mensuel + brouillons de négo dans Gmail ; absent → texte à copier-coller. Le cœur n'a besoin que de Qonto | ⭕ optionnel |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Analyse de l'historique** (24-36 mois, débits, paginé ≤ 50, fenêtres de 3 mois) : normalisation des contreparties — références, dates et préfixes carte (`PAYPAL *`, `SUMUP *`…) nettoyés, variantes SEPA/carte d'un même fournisseur fusionnées. Cadence calée sur `emitted_at`, pas `settled_at`
2. **Inventaire des récurrents** : contrepartie normalisée + cadence 28-32 j / 85-95 j / **350-380 j** + ≥ 3 occurrences (2 en annuel), cartes ET prélèvements. Série de prix datée par ligne, montants HT préférés quand `list_supplier_invoices` a la facture → **coût annuel total**
3. **Statuts + nouveaux** : ✅ actifs · 👥 doublons · 🧟 zombies (hypothèse, confirmée par toi) · 🎣 essais devenus payants — et section **🌱 Nouveaux** : contreparties < 3 occurrences évaluées comme abonnements naissants — marchand d'abonnement notoire reconnu par Claude **dès la 1re occurrence**, montant rond, libellé, 2e occurrence à ~30 j
4. **Détection des hausses** : un palier = ≥ 2 prélèvements stables (±2 %), une hausse = un saut qui **persiste ≥ 2 cycles** ; outliers, prorata, change et TVA exclus ; usage variable ⚪ à part → **surcoût annuel cumulé**, tags 🟢🟡🔴 vs inflation
5. **Dashboard** : tableaux markdown toujours, dashboard rendu **directement dans Claude** quand l'hôte le permet, export **HTML autoportant** charte Qonto (violet/noir/blanc, clair/sombre) — coût total, répartition par catégorie, statuts, hausses, prévisionnel 3 mois
6. **Emails** : négo argumentée (ancienneté, volume, hausses datées) pour les grosses lignes 🔴/🟡 + digest mensuel — **brouillons** Gmail avec ton accord, sinon texte à copier

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : ce skill n'a **aucune écriture Qonto** — que des lectures, sans risque par construction. Les seuls artefacts « sortants » sont des **brouillons** d'email (négo, digest), que tu relis, modifies et envoies (ou pas) toi-même. La carte virtuelle plafonnée, seule vraie écriture utile ici, appartient au skill `qonto-subscription-guardian`.

## 📊 Les statuts du portefeuille (le tableau métier)

| Statut | Critère | Lecture | Action proposée |
|---|---|---|---|
| ✅ Actif utile | Cadence régulière, usage confirmé **par toi** (le skill ne décrète jamais) | Le socle du budget | Suivi, alerte à la prochaine hausse |
| 👥 Doublon | Deux fournisseurs de la même catégorie (2 visios, 2 hébergeurs…) | Un des deux est de trop | En garder un, chiffrer l'économie |
| 🧟 Zombie | Prélevé ≥ 6 mois, zéro variation, catégorie dormante — **hypothèse à confirmer** | Probablement plus utilisé | Résiliation après ta confirmation |
| 🎣 Essai devenu payant | Première charge plein tarif récente, précédée de rien ou d'un montant symbolique | Conversion silencieuse | Décision immédiate : garder ou couper |
| 🌱 Nouveau (probable) | Marchand d'abonnement notoire (reconnu dès la 1re occurrence, sans historique) · montant rond · libellé abonnement · 2e occurrence ~30 j | Abonnement naissant, à confirmer | Section « Nouveaux » — l'attraper tôt |
| ⚪ Usage variable | Variabilité forte (API, cloud, pub) | Facture qui monte ≠ prix qui monte | Prix implicite si isolable, sinon dit tel quel |

Hausses : 🟢 ≤ inflation (indexation normale) · 🟡 au-dessus (dérive à surveiller) · 🔴 ≥ 3× l'inflation ou ≥ 10 % d'un coup (**email de négo proposé d'office**). Alertes transverses : 💥 double prélèvement < 72 h · 🔁 changement de cadence (souvent un repricing déguisé).

## 📤 Formats de sortie (où atterrit l'audit ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : chiffre choc, portefeuille trié par coût annuel, section Nouveaux 🌱, hausses, usage variable à part | **Toujours** — c'est la base |
| **Dashboard dans Claude** | Rendu **directement dans la conversation** (artifact) : compteur de coût annuel, répartition par catégorie, listes par statut ✅👥🧟🎣🌱, hausses avec deltas, prévisionnel 3 mois | Quand l'hôte le permet (claude.ai, Claude Desktop, Claude Code) |
| **Export HTML** | Le **même dashboard** en fichier HTML autoportant, charte Qonto (violet #6B4EFF / noir #1D1B29 / blanc, clair/sombre) — à garder ou partager | Sur demande |
| **Emails** | Brouillon **Gmail** (MCP présent + ton accord) ou texte à copier : négo + digest mensuel | Jamais envoyés sans toi |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : problème → inventaire live et statuts → hausses + surcoût → **le dashboard qui se construit dans Claude avec le chiffre choc, et la section Nouveaux 🌱 qui attrape un essai récent** → wrap-up. Le script détaillé (textes à dire, checklist tournage, notes de montage) est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Veille continue : alerte au premier prélèvement d'un 🌱 confirmé ou d'un nouveau palier | Faible | Le rituel mensuel devient automatique |
| Benchmark prix public : comparer au tarif affiché du fournisseur | Moyen | Détecte aussi les clients « grandfathered » qui paient trop |
| Catégorisation Qonto des abonnements détectés (labels) | Faible | Le portefeuille devient lisible dans l'app aussi |
| Suivi post-négo : vérifier que le prix a vraiment baissé | Faible | Boucle fermée — la série de prix existe déjà |
| Passerelle carte plafonnée : enchaîner sur `qonto-subscription-guardian` | Faible | L'audit trouve, le guardian protège |

## 🛡 Garde-fous

- **Zéro écriture Qonto** — lectures seules ; la carte plafonnée est le territoire de `qonto-subscription-guardian`
- 🧟 = hypothèse, toujours confirmée par toi ; 🌱 = « probable, à confirmer », jamais affirmé
- Jamais accuser un fournisseur quand la donnée dit usage, change ou TVA — au doute, la ligne part en « usage variable » avec l'explication
- Emails = **brouillons**, jamais envoyés, jamais de destinataire ajouté sans toi ; estimations depuis les paiements ≠ audit de contrat
- Dégradation honnête sous 24 mois d'historique (les annuels peuvent manquer — c'est dit) ; IBAN masqués (4 derniers chiffres) ; pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-subscription-audit.fr.html` · `docs/doc-qonto-subscription-audit.fr.docx`.*
