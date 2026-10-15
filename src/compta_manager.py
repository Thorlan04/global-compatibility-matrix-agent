"""
Module de Gestion Comptable et Fiscale Micro-Entreprise (BNC - Bénéfices Non Commerciaux).

Conformité avec les règles fiscales françaises (URSSAF & Impôts gouv) :
- Enregistrement des commissions d'affiliation Amazon mondiales (FR, US, UK, DE, ES, IT, JP, etc.).
- Règle d'or fiscale : Comptabilisation de la somme EXACTE créditée en EUROS (EUR)
  sur le relevé bancaire professionnel français (après conversion de change par la banque/Amazon).
- Traitement de la TVA :
  * Facturation intra-UE (Amazon EU S.à r.l. Luxembourg) : Autoliquidation art. 262 ter I ou 283 du CGI (DES/Déclaration Européenne de Services).
  * Facturation hors UE (Amazon Services LLC US, Amazon UK, Amazon Japan) : Exonération art. 259 B du CGI.
- Calculs automatisés des déclarations :
  * Déclaration URSSAF (Prestations de services BNC - cotisations sociales).
  * Déclaration de Revenus 2042-C-PRO :
    - Case 5HQ : BNC Micro sans versement libératoire (abattement forfaitaire 34%).
    - Case 5TE : BNC Micro avec versement libératoire de l'IR (2.2%).
"""

from __future__ import annotations

import csv
import datetime
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMPTA_DIR = PROJECT_ROOT / "compta_impots"
CSV_FILE = COMPTA_DIR / "livre_des_recettes_officiel.csv"
HTML_DASHBOARD = COMPTA_DIR / "tableau_de_bord_fiscal.html"

# Taux officiels Micro-Entreprise BNC 2025/2026
TAUX_COTISATIONS_URSSAF_BNC = 0.232  # 23.2% cotisations sociales de base
TAUX_CFP_BNC = 0.002                # 0.2% Contribution à la Formation Professionnelle
TAUX_TOTAL_URSSAF = TAUX_COTISATIONS_URSSAF_BNC + TAUX_CFP_BNC  # 23.4%
TAUX_ABATTEMENT_BNC = 0.34          # 34% d'abattement forfaitaire pour frais professionnels
TAUX_VERSEMENT_LIBERATOIRE_BNC = 0.022  # 2.2% si option versement libératoire


def ensure_compta_dir() -> None:
    COMPTA_DIR.mkdir(parents=True, exist_ok=True)


def load_recettes() -> List[Dict[str, Any]]:
    """Charge l'intégralité du livre des recettes officiel."""
    ensure_compta_dir()
    if not CSV_FILE.exists():
        return []

    entries: List[Dict[str, Any]] = []
    with open(CSV_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                montant_eur = float(row.get("Montant_EUR_Credite_Banque", "0").replace(",", "."))
            except ValueError:
                montant_eur = 0.0

            entries.append({
                "date": row.get("Date", "").strip(),
                "piece": row.get("Numero_Piece", "").strip(),
                "client": row.get("Client_Debiteur", "").strip(),
                "nature": row.get("Nature_Prestation", "").strip(),
                "montant_devise": row.get("Montant_Devise_Origine", "").strip(),
                "devise": row.get("Devise", "EUR").strip(),
                "montant_eur": montant_eur,
                "mode_reglement": row.get("Mode_Reglement", "Virement bancaire").strip(),
                "regime_tva": row.get("Regime_TVA", "").strip(),
            })
    return entries


def add_recette(
    date_str: str,
    num_piece: str,
    client: str,
    nature: str,
    montant_devise: float,
    devise: str,
    montant_eur_credite: float,
    mode_reglement: str = "Virement bancaire",
    regime_tva: str = "Autoliquidation / Exonération",
) -> None:
    """Ajoute une ligne de recette au livre officiel."""
    ensure_compta_dir()
    file_exists = CSV_FILE.exists()

    with open(CSV_FILE, mode="a", encoding="utf-8", newline="") as f:
        fieldnames = [
            "Date",
            "Numero_Piece",
            "Client_Debiteur",
            "Nature_Prestation",
            "Montant_Devise_Origine",
            "Devise",
            "Montant_EUR_Credite_Banque",
            "Mode_Reglement",
            "Regime_TVA",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "Date": date_str,
            "Numero_Piece": num_piece,
            "Client_Debiteur": client,
            "Nature_Prestation": nature,
            "Montant_Devise_Origine": f"{montant_devise:.2f}",
            "Devise": devise.upper(),
            "Montant_EUR_Credite_Banque": f"{montant_eur_credite:.2f}",
            "Mode_Reglement": mode_reglement,
            "Regime_TVA": regime_tva,
        })


def compute_fiscal_metrics(entries: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Calcule tous les indicateurs et cases fiscales obligatoires.
    """
    if entries is None:
        entries = load_recettes()

    total_ca_eur = sum(item["montant_eur"] for item in entries)
    cotisations_urssaf = round(total_ca_eur * TAUX_TOTAL_URSSAF, 2)
    abattement_forfaitaire = round(total_ca_eur * TAUX_ABATTEMENT_BNC, 2)
    base_imposable_5hq = round(total_ca_eur - abattement_forfaitaire, 2)
    impot_versement_liberatoire_5te = round(total_ca_eur * TAUX_VERSEMENT_LIBERATOIRE_BNC, 2)
    revenu_net_apres_urssaf = round(total_ca_eur - cotisations_urssaf, 2)

    # Répartition par boutique / source
    by_client: Dict[str, float] = {}
    for item in entries:
        client = item["client"] or "Autre"
        by_client[client] = round(by_client.get(client, 0.0) + item["montant_eur"], 2)

    # Répartition par devise reçue
    by_currency: Dict[str, float] = {}
    for item in entries:
        curr = item["devise"] or "EUR"
        by_currency[curr] = round(by_currency.get(curr, 0.0) + item["montant_eur"], 2)

    return {
        "nb_operations": len(entries),
        "total_ca_eur": round(total_ca_eur, 2),
        "cotisations_urssaf": cotisations_urssaf,
        "taux_urssaf_pct": f"{TAUX_TOTAL_URSSAF * 100:.1f}%",
        "revenu_net_apres_urssaf": revenu_net_apres_urssaf,
        # Déclaration de revenus 2042-C-PRO
        "case_5hq_montant": round(total_ca_eur, 2),  # Sur la 5HQ, on déclare le CA BRUT total
        "case_5hq_abattement_estime": abattement_forfaitaire,
        "case_5hq_base_imposable": base_imposable_5hq,
        "case_5te_montant": round(total_ca_eur, 2),  # Idem, base = CA Brut total si option
        "case_5te_impot_paye": impot_versement_liberatoire_5te,
        "by_client": by_client,
        "by_currency": by_currency,
        "dernier_virement": entries[-1]["date"] if entries else "Aucun",
    }


def generate_fiscal_dashboard_html() -> str:
    """
    Génère un tableau de bord HTML moderne, interactif et autonome
    dans compta_impots/tableau_de_bord_fiscal.html.
    """
    entries = load_recettes()
    metrics = compute_fiscal_metrics(entries)

    # Génération des lignes du tableau HTML
    rows_html = []
    for r in reversed(entries):
        rows_html.append(f"""
        <tr>
            <td><strong>{r['date']}</strong></td>
            <td><code>{r['piece']}</code></td>
            <td><span class="badge client">{r['client']}</span></td>
            <td>{r['nature']}</td>
            <td>{r['montant_devise']} {r['devise']}</td>
            <td class="montant-eur"><strong>{r['montant_eur']:.2f} €</strong></td>
            <td><span class="badge mode">{r['mode_reglement']}</span></td>
            <td><small>{r['regime_tva']}</small></td>
        </tr>
        """)

    client_breakdown_html = []
    for client, total in metrics["by_client"].items():
        pct = (total / metrics["total_ca_eur"] * 100) if metrics["total_ca_eur"] > 0 else 0
        client_breakdown_html.append(f"""
        <div class="stat-progress-item">
            <div class="progress-labels">
                <span>{client}</span>
                <strong>{total:.2f} € ({pct:.1f}%)</strong>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: {pct}%;"></div>
            </div>
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tableau de Bord Fiscal & Comptable - Micro-Entreprise BNC</title>
    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-hover: #334155;
            --primary: #38bdf8;
            --success: #10b981;
            --warning: #f59e0b;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            padding: 2rem 1.5rem;
            line-height: 1.5;
        }}
        .container {{ max-width: 1300px; margin: 0 auto; }}
        header {{
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        h1 {{ font-size: 1.8rem; font-weight: 700; color: #fff; }}
        .subtitle {{ color: var(--text-muted); font-size: 0.95rem; margin-top: 0.25rem; }}
        .tag-status {{
            background: rgba(16, 185, 129, 0.2);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.4);
            padding: 0.35rem 0.8rem;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.85rem;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}
        .kpi-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1.25rem;
        }}
        .kpi-title {{ font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }}
        .kpi-value {{ font-size: 1.8rem; font-weight: 800; margin: 0.5rem 0; color: #fff; }}
        .kpi-hint {{ font-size: 0.8rem; color: var(--text-muted); }}
        .kpi-value.green {{ color: var(--success); }}
        .kpi-value.blue {{ color: var(--primary); }}
        .kpi-value.orange {{ color: var(--warning); }}

        .box-declaration {{
            background: #172554;
            border: 1px solid #1e40af;
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        .box-title {{ font-size: 1.1rem; font-weight: 700; color: #93c5fd; margin-bottom: 0.75rem; }}
        .cases-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
        }}
        .case-item {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid #1e3a8a;
            border-radius: 0.5rem;
            padding: 1rem;
        }}
        .case-code {{
            display: inline-block;
            background: #2563eb;
            color: #fff;
            font-weight: 800;
            padding: 0.2rem 0.6rem;
            border-radius: 0.35rem;
            font-size: 0.95rem;
            margin-bottom: 0.5rem;
        }}
        .case-amount {{ font-size: 1.5rem; font-weight: 800; color: #fff; margin: 0.4rem 0; }}
        .case-desc {{ font-size: 0.85rem; color: #cbd5e1; }}

        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        .card h2 {{ font-size: 1.25rem; font-weight: 700; margin-bottom: 1.25rem; }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
            text-align: left;
        }}
        th, td {{ padding: 0.85rem 1rem; border-bottom: 1px solid var(--border); }}
        th {{ background: rgba(15, 23, 42, 0.5); color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; }}
        tr:hover td {{ background: var(--surface-hover); }}
        .montant-eur {{ color: var(--success); font-family: monospace; font-size: 1rem; }}
        .badge {{
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 0.35rem;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge.client {{ background: rgba(56, 189, 248, 0.15); color: var(--primary); }}
        .badge.mode {{ background: rgba(148, 163, 184, 0.2); color: var(--text-muted); }}

        .stat-progress-item {{ margin-bottom: 1rem; }}
        .progress-labels {{ display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.35rem; }}
        .progress-bar-bg {{ background: #0f172a; height: 8px; border-radius: 9999px; overflow: hidden; }}
        .progress-bar-fill {{ background: var(--primary); height: 100%; border-radius: 9999px; }}

        .rules-note {{
            background: rgba(30, 41, 59, 0.7);
            border-left: 4px solid var(--warning);
            padding: 1rem;
            border-radius: 0.35rem;
            font-size: 0.85rem;
            color: #cbd5e1;
            margin-top: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Tableau de Bord Fiscal & Comptable</h1>
                <div class="subtitle">Micro-Entreprise BNC (Prestations de Services) — Affiliation Amazon Multi-Stores</div>
            </div>
            <div>
                <span class="tag-status">✓ Conforme URSSAF & Formulaire 2042-C-PRO</span>
            </div>
        </header>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-title">CA Brut Total Encaissé</div>
                <div class="kpi-value green">{metrics['total_ca_eur']:.2f} €</div>
                <div class="kpi-hint">Montant exact crédité sur le compte bancaire</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Cotisations URSSAF ({metrics['taux_urssaf_pct']})</div>
                <div class="kpi-value orange">{metrics['cotisations_urssaf']:.2f} €</div>
                <div class="kpi-hint">Prestations de services BNC (Base + CFP)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Revenu Net Estimé</div>
                <div class="kpi-value blue">{metrics['revenu_net_apres_urssaf']:.2f} €</div>
                <div class="kpi-hint">Après paiement des charges sociales</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Virements Enregistrés</div>
                <div class="kpi-value">{metrics['nb_operations']}</div>
                <div class="kpi-hint">Dernier versement : {metrics['dernier_virement']}</div>
            </div>
        </div>

        <div class="box-declaration">
            <div class="box-title">📋 Prêt à déclarer sur Impots.gouv.fr (Formulaire 2042-C-PRO)</div>
            <div class="cases-grid">
                <div class="case-item">
                    <span class="case-code">CASE 5HQ</span> <strong>(Régime classique sans versement libératoire)</strong>
                    <div class="case-amount">{metrics['case_5hq_montant']:.2f} €</div>
                    <div class="case-desc">
                        Reportez ce montant brut. L'administration appliquera automatiquement
                        <strong>l'abattement forfaitaire BNC de 34%</strong> (-{metrics['case_5hq_abattement_estime']:.2f} €).
                        Base nette imposable retenue : <strong>{metrics['case_5hq_base_imposable']:.2f} €</strong>.
                    </div>
                </div>
                <div class="case-item">
                    <span class="case-code">CASE 5TE</span> <strong>(Si option Versement Libératoire souscrite)</strong>
                    <div class="case-amount">{metrics['case_5te_montant']:.2f} €</div>
                    <div class="case-desc">
                        Reportez ce montant si vous avez opté pour le versement libératoire de l'IR.
                        Impôt payé au fil de l'eau (2.2%) : <strong>{metrics['case_5te_impot_paye']:.2f} €</strong>.
                    </div>
                </div>
            </div>
            <div class="rules-note">
                <strong>Règle d'or fiscale :</strong> Choisissez la Case <strong>5HQ</strong> OU la Case <strong>5TE</strong> selon votre option fiscale à l'URSSAF.
                Ne déclarez JAMAIS les deux simultaneously. Les virements en devises étrangères (USD, GBP, JPY) sont déclarés pour leur valeur exacte créditée en Euros sur votre relevé bancaire.
            </div>
        </div>

        <div class="card">
            <h2>Répartition des Encaissements par Boutique Amazon</h2>
            { "".join(client_breakdown_html) }
        </div>

        <div class="card">
            <h2>Livre des Recettes Chronologique Officiel</h2>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>N° Pièce</th>
                            <th>Boutique / Débiteur</th>
                            <th>Nature</th>
                            <th>Devise Origine</th>
                            <th>Crédité EUR</th>
                            <th>Règlement</th>
                            <th>Régime TVA</th>
                        </tr>
                    </thead>
                    <tbody>
                        { "".join(rows_html) }
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""
    ensure_compta_dir()
    with open(HTML_DASHBOARD, mode="w", encoding="utf-8") as f:
        f.write(html_content)

    return str(HTML_DASHBOARD)


if __name__ == "__main__":
    dashboard_path = generate_fiscal_dashboard_html()
    metrics = compute_fiscal_metrics()
    print("==================================================================")
    print("COMPTA & FISCALITE MICRO-ENTREPRISE BNC (AMAZON PARTENAIRES)")
    print("==================================================================")
    print(f"Total CA Brut Encaissé : {metrics['total_ca_eur']:.2f} €")
    print(f"Cotisations URSSAF estimées ({metrics['taux_urssaf_pct']}) : {metrics['cotisations_urssaf']:.2f} €")
    print(f"Revenu Net : {metrics['revenu_net_apres_urssaf']:.2f} €")
    print(f"-> Case 2042-C-PRO 5HQ : {metrics['case_5hq_montant']:.2f} € (Abattement 34% automatique)")
    print(f"-> Case 2042-C-PRO 5TE : {metrics['case_5te_montant']:.2f} € (Si option versement libératoire)")
    print(f"Tableau de bord généré avec succès : {dashboard_path}")
