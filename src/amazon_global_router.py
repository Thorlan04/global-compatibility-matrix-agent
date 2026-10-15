"""
Module de Routage Mondial Amazon Partenaires (Zero Erreur 404).

Gère la génération d'URLs de recherche et d'achat Amazon ciblées géographiquement
avec injection automatique des tags d'affiliation (OneLink & Multi-Store),
gestion des replis automatiques (fallback), et métadonnées pour le commutateur
navigateur dynamique par fuseau horaire / pays.
"""

from __future__ import annotations

import os
import urllib.parse
from typing import Any, Dict, List, Optional


# Configuration des domaines Amazon par code pays ISO
AMAZON_DOMAINS: Dict[str, Dict[str, str]] = {
    "us": {
        "domain": "amazon.com",
        "name": "United States",
        "flag": "🇺🇸",
        "currency": "USD",
        "default_lang": "en",
    },
    "uk": {
        "domain": "amazon.co.uk",
        "name": "United Kingdom",
        "flag": "🇬🇧",
        "currency": "GBP",
        "default_lang": "en",
    },
    "ca": {
        "domain": "amazon.ca",
        "name": "Canada",
        "flag": "🇨🇦",
        "currency": "CAD",
        "default_lang": "en",
    },
    "au": {
        "domain": "amazon.com.au",
        "name": "Australia",
        "flag": "🇦🇺",
        "currency": "AUD",
        "default_lang": "en",
    },
    "de": {
        "domain": "amazon.de",
        "name": "Deutschland / Österreich",
        "flag": "🇩🇪",
        "currency": "EUR",
        "default_lang": "de",
    },
    "fr": {
        "domain": "amazon.fr",
        "name": "France / Belgique",
        "flag": "🇫🇷",
        "currency": "EUR",
        "default_lang": "fr",
    },
    "es": {
        "domain": "amazon.es",
        "name": "España",
        "flag": "🇪🇸",
        "currency": "EUR",
        "default_lang": "es",
    },
    "it": {
        "domain": "amazon.it",
        "name": "Italia",
        "flag": "🇮🇹",
        "currency": "EUR",
        "default_lang": "it",
    },
    "jp": {
        "domain": "amazon.co.jp",
        "name": "日本 (Japan)",
        "flag": "🇯🇵",
        "currency": "JPY",
        "default_lang": "ja",
    },
    "br": {
        "domain": "amazon.com.br",
        "name": "Brasil",
        "flag": "🇧🇷",
        "currency": "BRL",
        "default_lang": "pt",
    },
    "nl": {
        "domain": "amazon.nl",
        "name": "Nederland",
        "flag": "🇳🇱",
        "currency": "EUR",
        "default_lang": "nl",
    },
    "mx": {
        "domain": "amazon.com.mx",
        "name": "México",
        "flag": "🇲🇽",
        "currency": "MXN",
        "default_lang": "es",
    },
}

# Cartographie Langue -> Magasins prioritaires et alternatifs
LANGUAGE_STORE_MAP: Dict[str, Dict[str, Any]] = {
    "en": {
        "primary": "us",
        "alternates": ["uk", "ca", "au"],
        "buy_label": "Check Price on Amazon",
        "disclaimer": "As an Amazon Associate, we earn from qualifying purchases.",
    },
    "de": {
        "primary": "de",
        "alternates": [],
        "buy_label": "Preis auf Amazon prüfen",
        "disclaimer": "Als Amazon-Partner verdienen wir an qualifizierten Verkäufen.",
    },
    "fr": {
        "primary": "fr",
        "alternates": ["ca"],
        "buy_label": "Voir les modèles certifiés sur Amazon",
        "disclaimer": "En tant que Partenaire Amazon, nous réalisons un bénéfice sur les achats remplissant les conditions requises.",
    },
    "es": {
        "primary": "es",
        "alternates": ["mx", "us"],
        "buy_label": "Verificar precio en Amazon",
        "disclaimer": "Como afiliado de Amazon, percibo ingresos por las compras adscritas que cumplen los requisitos aplicables.",
    },
    "it": {
        "primary": "it",
        "alternates": [],
        "buy_label": "Verifica prezzo su Amazon",
        "disclaimer": "In qualità di Affiliato Amazon, ricevo un guadagno per ciascun acquisto idoneo.",
    },
    "ja": {
        "primary": "jp",
        "alternates": [],
        "buy_label": "Amazonで適合商品を確認する",
        "disclaimer": "Amazonのアソシエイトとして、適格販売により収入を得ています。",
    },
    "pt": {
        "primary": "br",
        "alternates": ["es"],
        "buy_label": "Verificar preço na Amazon",
        "disclaimer": "Como associado da Amazon, recebo por compras qualificadas.",
    },
    "nl": {
        "primary": "nl",
        "alternates": ["de"],
        "buy_label": "Bekijk prijzen op Amazon",
        "disclaimer": "Als Amazon-partner verdien ik aan in aanmerking komende aankopen.",
    },
}


def get_partner_tag(country_code: str) -> str:
    """
    Récupère le tag partenaire pour un pays donné.
    Ordre de priorité :
    1. Variable d'environnement AMAZON_TAG_{CODE} (ex: AMAZON_TAG_UK)
    2. Variable d'environnement AMAZON_PARTNER_TAG (tag global par défaut)
    3. Valeur de repli sécurisée 'autocompat-21'
    """
    country_code = country_code.strip().lower()
    env_var_name = f"AMAZON_TAG_{country_code.upper()}"
    specific_tag = os.environ.get(env_var_name)
    if specific_tag and specific_tag.strip():
        return specific_tag.strip()

    global_tag = os.environ.get("AMAZON_PARTNER_TAG")
    if global_tag and global_tag.strip():
        return global_tag.strip()

    return "autocompat-21"


def build_search_url(country_code: str, query: str) -> str:
    """
    Construit une URL de recherche Amazon propre, sans risque de 404,
    avec le mot-clé encodé et le tag d'affiliation officiel.
    """
    country_code = country_code.strip().lower()
    store_meta = AMAZON_DOMAINS.get(country_code, AMAZON_DOMAINS["us"])
    domain = store_meta["domain"]
    tag = get_partner_tag(country_code)

    encoded_query = urllib.parse.quote_plus(query.strip())
    # Format standard de recherche Amazon international
    return f"https://www.{domain}/s?k={encoded_query}&tag={tag}"


def get_localized_buy_options(lang: str, search_query: str) -> List[Dict[str, Any]]:
    """
    Fournit la liste ordonnée des options d'achat pour une langue donnée :
    - Boutique principale (ex: US pour EN, FR pour FR, DE pour DE)
    - Boutiques secondaires / régionales (ex: UK, CA, AU pour EN)
    """
    lang_key = lang if lang in LANGUAGE_STORE_MAP else "en"
    lang_info = LANGUAGE_STORE_MAP[lang_key]

    options: List[Dict[str, Any]] = []

    # 1. Boutique principale
    primary_country = lang_info["primary"]
    primary_meta = AMAZON_DOMAINS[primary_country]
    options.append({
        "country_code": primary_country,
        "name": primary_meta["name"],
        "flag": primary_meta["flag"],
        "domain": primary_meta["domain"],
        "currency": primary_meta["currency"],
        "tag": get_partner_tag(primary_country),
        "url": build_search_url(primary_country, search_query),
        "button_label": lang_info["buy_label"],
        "is_primary": True,
    })

    # 2. Boutiques alternatives / régionales
    for alt_country in lang_info.get("alternates", []):
        if alt_country in AMAZON_DOMAINS:
            alt_meta = AMAZON_DOMAINS[alt_country]
            options.append({
                "country_code": alt_country,
                "name": alt_meta["name"],
                "flag": alt_meta["flag"],
                "domain": alt_meta["domain"],
                "currency": alt_meta["currency"],
                "tag": get_partner_tag(alt_country),
                "url": build_search_url(alt_country, search_query),
                "button_label": f"{lang_info['buy_label']} ({alt_meta['flag']} {alt_meta['name'].split('/')[0].strip()})",
                "is_primary": False,
            })

    return options


def get_disclaimer(lang: str) -> str:
    """Retourne la mention obligatoire d'affiliation Amazon traduite selon la langue."""
    lang_key = lang if lang in LANGUAGE_STORE_MAP else "en"
    return LANGUAGE_STORE_MAP[lang_key]["disclaimer"]


def get_client_router_config() -> Dict[str, Any]:
    """
    Génère la configuration légère injectée côté client (JS)
    pour adapter instantanément les boutons Amazon selon le fuseau horaire ou locale.
    """
    stores_data: Dict[str, Dict[str, str]] = {}
    for code, info in AMAZON_DOMAINS.items():
        stores_data[code] = {
            "domain": info["domain"],
            "flag": info["flag"],
            "name": info["name"],
            "tag": get_partner_tag(code),
        }

    return {
        "stores": stores_data,
        "timezone_to_country": {
            "Europe/London": "uk",
            "America/Toronto": "ca",
            "America/Montreal": "ca",
            "America/Vancouver": "ca",
            "America/Edmonton": "ca",
            "America/Winnipeg": "ca",
            "America/Halifax": "ca",
            "Australia/Sydney": "au",
            "Australia/Melbourne": "au",
            "Australia/Brisbane": "au",
            "Australia/Perth": "au",
            "Australia/Adelaide": "au",
            "Europe/Berlin": "de",
            "Europe/Vienna": "de",
            "Europe/Zurich": "de",
            "Europe/Paris": "fr",
            "Europe/Brussels": "fr",
            "Europe/Madrid": "es",
            "America/Mexico_City": "mx",
            "Europe/Rome": "it",
            "Asia/Tokyo": "jp",
            "America/Sao_Paulo": "br",
            "Europe/Amsterdam": "nl",
        },
    }
