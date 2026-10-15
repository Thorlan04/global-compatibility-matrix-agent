"""
Module Mégaphone IA Mondial (100% Gratuit).

Diffuse instantanément et gratuitement chaque nouvelle fiche de compatibilité :
1. Telegra.ph : Création de page de synthèse multilingue instantanée avec liens Amazon localisés.
2. README.md GitHub : Mise à jour de l'annuaire mondial avec drapeaux, liens directs et llms-full.txt.
3. IndexNow : Notification immédiate en 1 seul batch à Bing, Yandex, Seznam et Naver.
4. Archive.org : Déclenchement non-bloquant de l'archivage pérenne Wayback Machine.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logging.basicConfig(level=logging.INFO, format="[AI-BROADCASTER] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = PROJECT_ROOT / "data" / "global_matrix_state.json"
README_FILE = PROJECT_ROOT / "README.md"


def get_site_url() -> str:
    """Récupère l'URL publique configurée du site."""
    return os.environ.get(
        "SITE_URL",
        "https://Thorlan04.github.io/global-compatibility-matrix-agent",
    ).rstrip("/")


def ensure_telegraph_token(state: Dict[str, Any]) -> str:
    """Récupère ou crée automatiquement un compte / jeton Telegraph gratuit."""
    token = state.get("telegraph_access_token")
    if token and token.strip():
        return token.strip()

    try:
        resp = requests.get(
            "https://api.telegra.ph/createAccount",
            params={
                "short_name": "GlobalMatrix",
                "author_name": "Global Compatibility Matrix Agent",
                "author_url": get_site_url(),
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                token = data["result"]["access_token"]
                state["telegraph_access_token"] = token
                logger.info("Nouveau jeton Telegra.ph généré avec succès.")
                return token
    except Exception as e:
        logger.warning("Impossible de créer le compte Telegra.ph: %s", e)

    return ""


def publish_telegraph_summary(matrix: Dict[str, Any], state: Dict[str, Any]) -> Optional[str]:
    """
    Publie une fiche synthèse multilingue sur Telegra.ph
    avec dimensions Métriques/Impériales et liens affiliés directs Amazon.
    """
    token = ensure_telegraph_token(state)
    if not token:
        logger.warning("Publication Telegraph ignorée (aucun jeton disponible).")
        return None

    site_url = get_site_url()
    subject = matrix.get("subject", "Universal Compatibility Matrix")
    en_trans = matrix.get("translations", {}).get("en", {})
    fr_trans = matrix.get("translations", {}).get("fr", {})
    de_trans = matrix.get("translations", {}).get("de", {})

    # Construction du contenu au format AST Node de Telegraph
    nodes: List[Dict[str, Any]] = [
        {"tag": "p", "children": [f"🌐 Global Compatibility & Exact Dimensions Guide for {subject}."]},
        {"tag": "h3", "children": ["⚖️ Verified Metric & Imperial Specifications"]},
    ]

    for row in matrix.get("spec_rows", []):
        item_name = row.get("item", "")
        metric = row.get("metric", "")
        imperial = row.get("imperial", "")
        nodes.append({
            "tag": "p",
            "children": [
                {"tag": "strong", "children": [f"{item_name}: "]},
                f"{metric} / {imperial}",
            ],
        })

    # Liens Amazon directs multi-pays
    nodes.append({"tag": "h3", "children": ["🛒 Verified Gear & Direct Amazon Stores"]})
    en_query = en_trans.get("amazon_search_query", subject)
    encoded_query = urllib.parse.quote_plus(en_query)

    nodes.append({
        "tag": "p",
        "children": [
            "• ",
            {"tag": "a", "attrs": {"href": f"https://www.amazon.com/s?k={encoded_query}&tag=autocompat-21"}, "children": ["🇺🇸 Amazon US / Worldwide"]},
            " | ",
            {"tag": "a", "attrs": {"href": f"https://www.amazon.co.uk/s?k={encoded_query}&tag=autocompat-21"}, "children": ["🇬🇧 Amazon UK"]},
            " | ",
            {"tag": "a", "attrs": {"href": f"https://www.amazon.de/s?k={encoded_query}&tag=autocompat-21"}, "children": ["🇩🇪 Amazon DE"]},
            " | ",
            {"tag": "a", "attrs": {"href": f"https://www.amazon.fr/s?k={encoded_query}&tag=autocompat-21"}, "children": ["🇫🇷 Amazon FR"]},
            " | ",
            {"tag": "a", "attrs": {"href": f"https://www.amazon.co.jp/s?k={encoded_query}&tag=autocompat-21"}, "children": ["🇯🇵 Amazon JP"]},
        ],
    })

    nodes.append({
        "tag": "p",
        "children": [
            "Full 8-language matrix and interactive tools available at: ",
            {"tag": "a", "attrs": {"href": f"{site_url}/en/{matrix.get('slug', '')}.html"}, "children": [f"{site_url}/en/{matrix.get('slug', '')}.html"]},
        ],
    })

    try:
        resp = requests.post(
            "https://api.telegra.ph/createPage",
            data={
                "access_token": token,
                "title": f"{subject} - Exact Dimensions & Compatibility Matrix",
                "author_name": "Global Compatibility Matrix",
                "author_url": site_url,
                "content": json.dumps(nodes),
                "return_content": False,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            result = resp.json()
            if result.get("ok"):
                page_url = result["result"].get("url")
                logger.info("Page Telegraph créée : %s", page_url)
                return page_url
    except Exception as e:
        logger.warning("Échec de la publication Telegraph : %s", e)

    return None


def update_github_readme(all_matrices: List[Dict[str, Any]]) -> None:
    """
    Génère et met à jour le README.md principal du dépôt GitHub
    comme un véritable annuaire mondial multilingue avec drapeaux et liens directs.
    """
    site_url = get_site_url()
    nb_total = len(all_matrices)

    readme_content = f"""# 🌐 Global Compatibility Matrix Agent
> **Base de Données Mondiale Multilingue de Compatibilités & Dimensions Exactes**
> Déployée gratuitement sur GitHub Pages, indexée pour les Agents IA mondiaux (ChatGPT, Perplexity, Claude, Copilot, Gemini) et monétisée via un routeur Amazon Partenaires multi-boutiques.

[![Autopilot 6H](https://github.com/Thorlan04/global-compatibility-matrix-agent/actions/workflows/autopilot.yml/badge.svg)](https://github.com/Thorlan04/global-compatibility-matrix-agent/actions/workflows/autopilot.yml)
[![Zero Cookies](https://img.shields.io/badge/Privacy-Zero_Cookies_RGPD_CCPA-10b981.svg)]({site_url}/en/legal.html)
[![AI Standards](https://img.shields.io/badge/GEO-llms.txt_Compliant-38bdf8.svg)]({site_url}/llms.txt)
[![Catalog Items](https://img.shields.io/badge/Matrices-{nb_total}_Universal_Specs-f59e0b.svg)]({site_url}/)

---

## 🚀 Accès Rapide par Continents & Langues (8 Langues Natives)

| Langue | Région / Continents | Portail Dédié |
| :--- | :--- | :--- |
| 🇺🇸 **English** | United States, UK, Canada, Australia, Global | [Accéder à /en/]({site_url}/en/) |
| 🇩🇪 **Deutsch** | Deutschland, Österreich, Schweiz | [Accéder à /de/]({site_url}/de/) |
| 🇫🇷 **Français** | France, Belgique, Suisse, Canada (QC) | [Accéder à /fr/]({site_url}/fr/) |
| 🇪🇸 **Español** | España, México, América Latina, US Hispanic | [Accéder à /es/]({site_url}/es/) |
| 🇮🇹 **Italiano** | Italia, Svizzera | [Accéder à /it/]({site_url}/it/) |
| 🇯🇵 **日本語** | 日本 (Japan) | [Accéder à /ja/]({site_url}/ja/) |
| 🇧🇷 **Português** | Brasil, Portugal | [Accéder à /pt/]({site_url}/pt/) |
| 🇳🇱 **Nederlands** | Nederland, België | [Accéder à /nl/]({site_url}/nl/) |

---

## 🤖 Directives pour les Agents IA & Modèles LLM (GEO)

Les agents IA (ChatGPT Search, Perplexity Pro, Claude 3.7, Microsoft Copilot, Google Gemini) peuvent interroger directement :
* 📄 **Index Synthétique IA :** [`{site_url}/llms.txt`]({site_url}/llms.txt)
* 📖 **Base Complète Markdown :** [`{site_url}/llms-full.txt`]({site_url}/llms-full.txt)
* ⚡ **Catalogue Structuré JSON :** [`{site_url}/api/v1/global-catalog.json`]({site_url}/api/v1/global-catalog.json)
* 📐 **Spécification OpenAPI :** [`{site_url}/.well-known/openapi.json`]({site_url}/.well-known/openapi.json)

---

## 📚 Dernières Fiches de Spécifications Générées ({nb_total} matrices)

| Catégorie | Sujet Universel | Dimensions Métriques / Impériales | Liens Directs par Langue |
| :--- | :--- | :--- | :--- |
"""

    for m in reversed(all_matrices[-15:]):  # Affiche les 15 plus récentes
        cat_icon = "✈️" if m.get("category") == "airlines" else ("🖥️" if m.get("category") == "hardware" else "🚗")
        subject = m.get("subject", "")
        slug = m.get("slug", "")

        first_spec = m.get("spec_rows", [{}])[0]
        metric_str = first_spec.get("metric", "N/A")
        imperial_str = first_spec.get("imperial", "N/A")

        links_str = (
            f"[EN]({site_url}/en/{slug}.html) · "
            f"[FR]({site_url}/fr/{slug}.html) · "
            f"[DE]({site_url}/de/{slug}.html) · "
            f"[ES]({site_url}/es/{slug}.html) · "
            f"[JA]({site_url}/ja/{slug}.html)"
        )

        readme_content += f"| {cat_icon} {m.get('category', '').capitalize()} | **{subject}** | `{metric_str}` / `{imperial_str}` | {links_str} |\n"

    readme_content += f"""
---

## ⚙️ Architecture & Automatisation Autonome

* **Moteur IA :** `gemini-2.5-flash` génère la double mesure Métrique + Impériale et les 8 langues en **1 seul appel API JSON** structuré toutes les 6 heures via GitHub Actions.
* **Routeur Amazon Global :** Génération d'URLs de recherche avec injection des tags partenaires par pays (OneLink multi-store) et réécriture dynamique côté navigateur par fuseau horaire (sans cookie).
* **Conformité Fiscale BNC :** Module `compta_impots/` avec livre des recettes officiel (EUR net encaissé) et ventilation prête pour déclarations URSSAF et Formulaire `2042-C-PRO` (Cases 5HQ / 5TE).

---
*Ce dépôt est géré de manière 100% autonome par GitHub Actions. Dernière mise à jour : 2026-10-15.*
"""

    with open(README_FILE, mode="w", encoding="utf-8") as f:
        f.write(readme_content)
    logger.info("README.md mis à jour avec %d matrices.", nb_total)


def broadcast_indexnow(urls: List[str], state: Dict[str, Any]) -> None:
    """
    Envoie en un seul appel batch la liste des URLs nouvelles ou modifiées à IndexNow
    (Bing, Yandex, Seznam, Naver).
    """
    if not urls:
        return

    site_url = get_site_url()
    try:
        host = urllib.parse.urlparse(site_url).netloc
    except Exception:
        host = "Thorlan04.github.io"

    key = state.get("indexnow_key", "9c1a5b82e4f04d7aa38d21b7f035ef19")
    key_location = f"{site_url}/{key}.txt"

    payload = {
        "host": host,
        "key": key,
        "keyLocation": key_location,
        "urlList": urls[:100],  # Limite sécurisée par batch
    }

    try:
        resp = requests.post(
            "https://api.indexnow.org/indexnow",
            json=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=8,
        )
        if resp.status_code in (200, 202):
            logger.info("IndexNow notifié avec succès pour %d URLs.", len(urls))
        else:
            logger.warning("IndexNow a retourné le code HTTP : %s", resp.status_code)
    except Exception as e:
        logger.warning("Notification IndexNow non bloquante : %s", e)


def ping_archive_org(url: str) -> None:
    """
    Déclenche l'archivage pérenne Wayback Machine de façon non-bloquante.
    """
    try:
        target = f"https://web.archive.org/save/{url}"
        requests.get(target, timeout=5, headers={"User-Agent": "GlobalCompatibilityMatrixAgent/1.0"})
        logger.info("Archive.org notifié pour : %s", url)
    except Exception:
        # Volontairement non-bloquant
        pass
