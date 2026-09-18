# 🧑‍🚀 qonto-crew-onboard — L'onboarding financier d'un salarié en une phrase

> **Hackathon Qonto × Anthropic MCP (10-13/07/2026)** · Agent Skill pour le MCP Qonto
> « Alex arrive lundi comme dev » → l'invitation part, la demande de carte plafonnée attend la SCA, la page d'accueil est prête.

---

## 🎯 Le pitch

À chaque arrivée, le dirigeant refait tout à la main : inviter la personne sur Qonto, créer sa carte avec les bons plafonds, préparer son premier jour. `qonto-crew-onboard` transforme ce rituel en une phrase :

1. **Policy par rôle** — définie **une fois** avec toi (type de carte, plafonds, online-only, équipe par rôle), puis appliquée à chaque arrivée. Jamais inventée : rôle sans policy = questions
2. **Onboarding en une phrase** — « Alex arrive lundi comme dev » : `create_membership` (l'invitation part), `create_team` si l'équipe est nouvelle, `create_card_request` — une **demande** de carte plafonnée conforme à la policy, approuvée dans l'app (SCA)
3. **Pack d'accueil multi-MCP** — page d'accueil Notion, événement J1 Google Calendar, brouillon Gmail de bienvenue — si ces MCP sont connectés, sinon le skill le dit et continue
4. **Offboarding miroir** — « Sam part vendredi » : cartes **gelées** (`change_card_status`) + checklist de récupération. Rien n'est supprimé — les révocations définitives restent dans l'app

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Universel** — membres, équipes et cartes fonctionnent pareil dans tous les pays Qonto (FR, DE, ES, IT, AT, NL, BE, PT). Aucune logique fiscale ici | ℹ️ |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Rôle **Admin/Owner** | Inviter un membre et demander une carte l'exigent — vérifié via `get_authenticated_membership`, annoncé honnêtement sinon | ✅ |
| Policy par rôle | Définie une fois avec toi (tableau ci-dessous). **Jamais inventée** | ✅ décidée par toi |
| Plan Qonto avec sièges dispo | La grille n'est pas lisible via MCP (`get_subscription` → 403) → le skill **demande ton plan** et compare au nombre de membres avant d'inviter | ℹ️ vérifié en le demandant |
| Notion · Google Calendar · Gmail | Pack d'accueil optionnel — détectés dynamiquement, le cœur marche en Qonto pur | ⭕ |

## 🗂 La policy par rôle (exemple — la tienne est définie avec toi)

| Rôle | Carte | Plafond mensuel | Online-only | Équipe |
|---|---|---|---|---|
| Développeur·se | Virtuelle | 200 € | Oui | Tech |
| Commercial·e | Physique | 1 000 € | Non | Sales |
| Ops | Virtuelle | 500 € | Oui | Operations |

> ⚠️ Tableau **inventé** pour l'exemple. La policy est **toujours** décidée par l'utilisateur, jamais par le skill — un rôle sans policy déclenche des questions, pas une supposition.

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Photographie du compte** : `get_organization` d'abord, `get_authenticated_membership` (rôle du demandeur — Admin/Owner requis pour écrire, dit honnêtement sinon), membres, équipes et cartes existants, détection des MCP optionnels
2. **Policy par rôle** : chargée ou définie avec toi ; limite de membres du plan vérifiée **avant** d'inviter (plan demandé, membres comptés)
3. **Une phrase** : « Alex arrive lundi comme dev » → prénom, rôle, date extraits ; l'email est demandé (jamais deviné) ; **récapitulatif complet affiché avant la moindre écriture**
4. **Exécution — chaque écriture confirmée une à une** : `create_membership` (invitation), `create_team` si nouvelle équipe, `create_card_request` — une *demande* de carte plafonnée qui attend l'approbation SCA dans l'app, jamais présentée comme une carte active
5. **Pack d'accueil** (MCP optionnels) : page Notion, événement J1 Google Calendar, **brouillon** Gmail (jamais envoyé par le skill)
6. **Offboarding miroir** : cartes gelées (`change_card_status`, réversible), checklist de récupération — carte, matériel, accès. Rien de supprimé : les révocations définitives se font dans l'app Qonto

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : les lectures (trait plein) sont sans risque ; chaque écriture (trait pointillé) exige une confirmation explicite dans la conversation. Et la carte n'est **jamais** créée directement : `create_card_request` produit une *demande* qui atterrit dans la section Demandes de l'app Qonto, où un Admin/Owner l'approuve avec sa propre SCA. **C'est le modèle de sécurité, pas une limitation.**

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : récap onboarding (✅ fait / 🕐 en attente SCA / ⏭ sauté), statut de la demande de carte, pack d'accueil, checklist d'offboarding | **Toujours** — c'est la base |
| **Fiche d'onboarding** | Fichier/artifact **HTML** une page : qui arrive, quand, ce qui est prêt, ce qui attend | Si l'hôte affiche les fichiers ; repli automatique sur les tableaux |
| **Page d'accueil Notion** | Page Notion : infos J1, qui-est-qui, policy de carte applicable | Si le MCP Notion est connecté |
| **Brouillon Gmail** | Email de bienvenue en **brouillon** — relu et envoyé par toi | Si le MCP Gmail est connecté |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le rituel manuel → la policy définie une fois → « Alex arrive lundi comme dev » → **l'invitation partie + la demande de carte en attente de SCA + la page d'accueil prête** → l'offboarding-gel en une commande. Le script détaillé (textes à dire, checklist tournage) est dans **`_SCRIPT-VIDEO.md`** — fichier interne, **exclu de la PR**.

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Policy persistée dans un doc Notion relu à chaque arrivée | Faible | Multi-MCP optionnel — la policy vit chez l'utilisateur |
| Onboarding par lot (« 3 stagiaires arrivent le 1er ») | Faible | Même workflow, récap groupé, confirmations une à une |
| Rappel J-1 au manager (Google Calendar) | Faible | Détection dynamique du MCP |
| Suivi des demandes de carte en attente (`list_requests`) | Faible | « Où en est la carte d'Alex ? » |
| Passerelle avec qonto-reimburse-batch pour les frais du nouvel arrivant | Moyen | Les deux skills partagent la lecture des membres |

## 🛡 Garde-fous

- **Jamais** d'écriture sans confirmation explicite : récap complet d'abord, puis chaque écriture (`create_membership`, `create_team`, `create_card_request`, `change_card_status`) confirmée une à une ; une demande en attente n'est jamais présentée comme exécutée
- **La policy est décidée par toi, jamais inventée** — rôle inconnu = questions
- Limite de membres du plan : grille non lisible via MCP (`get_subscription` → 403) → le skill demande le plan et compte les membres avant d'inviter
- **L'offboarding ne supprime jamais rien** : gel (réversible) + checklist ; les révocations définitives se font dans l'app
- Rôle Admin/Owner vérifié d'abord (`get_authenticated_membership`), dégradation honnête sinon
- Emails jamais devinés · pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-crew-onboard.fr.html`.*
