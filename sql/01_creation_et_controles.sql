-- =====================================================================
-- 01. Chargement et contrôles qualité
-- Moteur : DuckDB (syntaxe SQL standard, transposable à PostgreSQL)
-- =====================================================================

CREATE OR REPLACE TABLE ventes AS
SELECT
    "Invoice ID"                         AS facture,
    Branch                               AS magasin,
    City                                 AS ville,
    "Customer type"                      AS type_client,
    Gender                               AS genre,
    "Product line"                       AS rayon,
    "Unit price"                         AS prix_unitaire,
    Quantity                             AS quantite,
    "Tax 5%"                             AS taxe,
    Total                                AS montant_ttc,
    CAST(Date AS DATE)                   AS date_vente,
    hour(CAST(Time AS TIME))             AS heure,
    Payment                              AS paiement,
    "Cost of goods sold"                 AS cout_marchandises,
    "Gross margin percentage"            AS taux_marge,
    "Gross income"                       AS marge_brute,
    "Customer stratification rating"     AS note_client
FROM read_csv('data/ventes_supermarche.csv', dateformat = '%m/%d/%Y', header = true);

-- Contrôle 1 : doublons de facture
SELECT COUNT(*) AS lignes, COUNT(DISTINCT facture) AS factures_uniques FROM ventes;

-- Contrôle 2 : valeurs manquantes sur les champs critiques
SELECT
    SUM(CASE WHEN montant_ttc IS NULL THEN 1 ELSE 0 END) AS montant_manquant,
    SUM(CASE WHEN date_vente  IS NULL THEN 1 ELSE 0 END) AS date_manquante,
    SUM(CASE WHEN rayon       IS NULL THEN 1 ELSE 0 END) AS rayon_manquant
FROM ventes;

-- Contrôle 3 : cohérence arithmétique (TTC = prix x quantité x 1,05)
SELECT COUNT(*) AS lignes_incoherentes
FROM ventes
WHERE ABS(montant_ttc - prix_unitaire * quantite * 1.05) > 0.01;

-- Contrôle 4 : le taux de marge varie-t-il ?
SELECT MIN(taux_marge) AS mini, MAX(taux_marge) AS maxi, COUNT(DISTINCT taux_marge) AS valeurs_distinctes
FROM ventes;
