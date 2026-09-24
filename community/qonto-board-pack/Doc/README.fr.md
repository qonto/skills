# 📦 qonto-board-pack — Le rapport mensuel investisseurs, prêt avant la fin de ton café

> **Skill #18 · NOUVEAU** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> Le pack complet en un prompt : chiffres du mois, comparaisons, faits marquants, narration exécutive, deck HTML + email d'envoi
> **Zéro écriture Qonto** — lecture seule ; rien ne part jamais sans ta relecture

---

## 🎯 Le pitch

Le rapport mensuel investisseurs/banquier, c'est la tâche que tout fondateur repousse au dernier soir. `qonto-board-pack` la fait pendant que tu regardes :

1. **Les chiffres du mois** depuis Qonto — encaissements, dépenses par poste (labels), trésorerie fin de mois (relevé officiel quand il existe), burn net et runway
2. **Comparaisons M-1 et année glissante** — variations chiffrées, saisonnalité signalée, encours clients en signal avancé — jamais de conclusion sur un seul mois
3. **Faits marquants détectés** — gros contrat encaissé, nouvelle dépense significative, client habituel absent — chaque fait relié à sa transaction ; le skill décrit le *quoi*, toi tu apportes le *pourquoi*
4. **Narration exécutive + mise en forme** — 3 paragraphes (highlights, chiffres, perspectives) que tu **relis et corriges AVANT** toute mise en forme, puis deck HTML autoportant 5-6 slides (ou export Canva si le MCP est là) + email d'envoi rédigé (brouillon Gmail si présent)

Et la confidentialité est une **feature** : banquier, investisseur et équipe interne ne reçoivent pas le même pack — tu choisis l'audience et le niveau de détail (chiffres exacts vs tendances).

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro valeur en dur) | ✅ |
| Pays | **Tous les pays Qonto** (FR, DE, ES, IT, AT, NL, BE, PT) — les chiffres sont universels ; seuls la devise et le wording s'adaptent | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Historique ≥ 2 mois | En dessous : chiffres du mois seuls, comparaisons sautées et annoncées (≥ 12 mois pour l'année glissante) | ⭕ |
| MCP Canva | Export du deck vers Canva — détecté dynamiquement, sinon deck HTML | ⭕ optionnel |
| MCP Gmail | Brouillon d'email dans ta boîte — détecté dynamiquement, sinon texte prêt à coller | ⭕ optionnel |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Cadrage** : mois cible (par défaut : le dernier mois plein) + audience — **banquier** (rassurer : trésorerie, couverture, stabilité), **investisseur** (trajectoire : croissance, burn, runway), **interne** (tout, non filtré) — et niveau de détail (chiffres exacts vs tendances)
2. **Chiffres du mois** : `list_transactions` paginé ≤ 50, **virements internes exclus** du CA et du burn, délais carte gérés en bord de mois (`emitted_at` vs `settled_at`), dépenses groupées par labels (les catégories de cash-flow renvoient 403 sur le connecteur claude.ai → repli labels), solde fin de mois depuis le **relevé officiel** quand il existe
3. **Comparaisons** : M-1 + année glissante, deltas en € et %, saisonnalité signalée, encours clients (`list_client_invoices`) en signal avancé
4. **Faits marquants** : plus gros encaissement vs l'habitude, première occurrence d'une dépense significative, paiement client récurrent manquant, pic inhabituel par poste — chaque fait cite ses transactions
5. **Narration exécutive** : 3 paragraphes factuels, ni vendeurs ni alarmistes — affichés dans la conversation, **arrêt obligatoire** : tu corriges ou tu valides avant toute mise en forme
6. **Pack & envoi** : deck HTML autoportant (CSS pur, thème clair/sombre, zéro dépendance) ou Canva si présent + email rédigé (brouillon Gmail si présent, **jamais envoyé**) → tu relis, tu envoies

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé** : ce skill n'écrit **rien** dans Qonto — lecture seule de bout en bout. Les seules « écritures » sont locales (deck HTML) ou des brouillons (Gmail). Un rapport investisseurs ne s'envoie jamais tout seul : la relecture de la narration (étape 5) est un arrêt obligatoire, et l'email reste un brouillon que toi seul envoies. **C'est le produit, pas une friction.**

## 👥 Les trois audiences (la confidentialité comme feature)

| Audience | Ce qu'elle attend | Contenu du pack | Niveau de détail |
|---|---|---|---|
| **Banquier** | De la stabilité : le compte est sain, les échéances sont couvertes | Trésorerie, encaissements, couverture des charges, régularité | Chiffres exacts |
| **Investisseur** | De la trajectoire : croissance, burn maîtrisé, runway | Highlights, croissance M-1/YoY, burn & runway, perspectives | Exacts **ou** tendances — tu choisis |
| **Interne** | Tout | Le pack complet, non filtré, y compris les postes de dépenses détaillés | Tout |

## 📊 Structure du deck (5-6 slides, charte sobre)

| # | Slide | Contenu |
|---|---|---|
| 1 | Couverture | Organisation · mois · audience |
| 2 | Faits marquants | 2-4 faits détectés, reliés aux transactions |
| 3 | Chiffres clés | Encaissements · dépenses · tréso fin de mois · burn/runway, avec deltas M-1 |
| 4 | Dépenses par poste | Répartition par labels, part « non taggé » annoncée |
| 5 | Trésorerie & runway | Courbe 12 mois glissants, runway si burn > 0 |
| 6 | Perspectives | Le paragraphe « outlook » validé par toi |

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (chiffres + deltas, postes, faits marquants) + narration 3 § | **Toujours** — c'est la base |
| **Deck HTML autoportant** | Fichier/artifact HTML 5-6 slides, CSS pur, clair/sombre, zéro dépendance | Si l'hôte affiche les fichiers ; sinon repli sur les tableaux |
| **Export Canva** | Design généré via le MCP Canva | Si le MCP Canva est présent |
| **Email d'envoi** | Brouillon Gmail (**jamais envoyé**) ou texte prêt à coller | Gmail présent → brouillon ; sinon texte |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le rapport repoussé depuis 3 jours → un prompt → chiffres, faits marquants, narration → **correction d'un adjectif en live** → deck + brouillon d'email prêts avant la fin du café. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Historique des packs : deltas vs le pack de M-1 (« ce qu'on leur a dit le mois dernier ») | Moyen | Mémoire de session ou dossier local |
| KPI métier optionnels (MRR, clients actifs) déclarés par l'utilisateur | Faible | Fusionnés dans la slide chiffres clés |
| Envoi calendrier : rappel « ton pack du mois est prêt à générer » | Faible | MCP calendrier détecté dynamiquement |
| Multi-langue du pack (deck FR pour le banquier, EN pour les investisseurs) | Faible | Même données, deux narrations |

## 🛡 Garde-fous

- **Lecture seule sur Qonto** — aucun outil d'écriture Qonto utilisé, jamais
- **Rien ne part** : emails = brouillons, decks = fichiers ; toi seul envoies
- La relecture de la narration est un **arrêt obligatoire** avant toute mise en forme
- Confidentialité d'audience : jamais de chiffres exacts dans un pack demandé « en tendances » ; jamais le pack investisseur recyclé pour le banquier sans re-demander
- Chaque chiffre traçable à ses transactions ; parts non taggées annoncées ; dégradation honnête (< 2 mois : pas de comparaison ; < 12 : pas d'année glissante)
- IBAN masqués (4 derniers chiffres) ; pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-board-pack.fr.html` · `docs/doc-qonto-board-pack.fr.docx`.*
