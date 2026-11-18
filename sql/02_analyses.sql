-- =====================================================================
-- 02. Requêtes d'analyse (chaque requête répond à une question métier)
-- =====================================================================

-- Q1. Quel est le poids de chaque magasin, en CA et en panier moyen ?
SELECT magasin, ville,
       ROUND(SUM(montant_ttc), 0)                          AS ca,
       COUNT(*)                                            AS tickets,
       ROUND(AVG(montant_ttc), 1)                          AS panier_moyen,
       ROUND(100 * SUM(montant_ttc) / SUM(SUM(montant_ttc)) OVER (), 1) AS part_ca_pct
FROM ventes
GROUP BY magasin, ville
ORDER BY ca DESC;

-- Q2. Quels rayons portent le chiffre d'affaires, et dans quel magasin ?
SELECT rayon, magasin, ROUND(SUM(montant_ttc), 0) AS ca,
       RANK() OVER (PARTITION BY magasin ORDER BY SUM(montant_ttc) DESC) AS rang_dans_magasin
FROM ventes
GROUP BY rayon, magasin
ORDER BY magasin, rang_dans_magasin;

-- Q3. Le recul de février est-il réel, une fois ramené au nombre de jours ouverts ?
SELECT strftime(date_vente, '%Y-%m')           AS mois,
       COUNT(DISTINCT date_vente)              AS jours_avec_ventes,
       ROUND(SUM(montant_ttc), 0)              AS ca,
       ROUND(SUM(montant_ttc) / COUNT(DISTINCT date_vente), 0) AS ca_par_jour
FROM ventes
GROUP BY mois
ORDER BY mois;

-- Q4. À quelles heures et quels jours faut-il renforcer les caisses ?
SELECT dayname(date_vente) AS jour, heure,
       COUNT(*) AS tickets, ROUND(SUM(montant_ttc), 0) AS ca
FROM ventes
GROUP BY jour, heure
ORDER BY ca DESC
LIMIT 10;

-- Q5. Les membres de la carte de fidélité dépensent-ils plus ?
SELECT type_client,
       COUNT(*)                     AS tickets,
       ROUND(AVG(montant_ttc), 1)   AS panier_moyen,
       ROUND(AVG(quantite), 2)      AS articles_par_ticket,
       ROUND(AVG(note_client), 2)   AS note_moyenne
FROM ventes
GROUP BY type_client;

-- Q6. Quel mode de paiement domine selon le magasin ?
SELECT magasin, paiement, COUNT(*) AS tickets,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY magasin), 1) AS part_pct
FROM ventes
GROUP BY magasin, paiement
ORDER BY magasin, tickets DESC;

-- Q7. Évolution hebdomadaire et moyenne mobile sur 4 semaines
WITH hebdo AS (
    SELECT date_trunc('week', date_vente) AS semaine, SUM(montant_ttc) AS ca
    FROM ventes GROUP BY semaine
)
SELECT semaine, ROUND(ca, 0) AS ca,
       ROUND(AVG(ca) OVER (ORDER BY semaine ROWS BETWEEN 3 PRECEDING AND CURRENT ROW), 0) AS moyenne_mobile_4s
FROM hebdo
ORDER BY semaine;

-- Q8. Satisfaction : quels rayons sont les moins bien notés ?
SELECT rayon, ROUND(AVG(note_client), 2) AS note_moyenne,
       ROUND(100.0 * AVG(CASE WHEN note_client < 6 THEN 1 ELSE 0 END), 1) AS part_notes_faibles_pct
FROM ventes
GROUP BY rayon
ORDER BY note_moyenne;
