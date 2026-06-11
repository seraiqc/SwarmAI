# SEC — Agent Sécurité

SEC est le premier agent de la phase 0 du Swarm.

## Mission
- Surveiller les exploits
- Prévenir le vol et le piratage
- Scanner les outputs des autres agents
- Empêcher toute fuite de mots de passe, clés API et private keys

## Fonction principale
SEC bloque tout contenu dangereux avant qu’il passe aux autres agents.

## Dossier
- config/ : règles et chemins Vault
- scanners/ : scripts de détection
- hooks/ : scripts pre-commit
- alerts/ : règles d’alerte
- tests/ : tests de sécurité

## Étapes
1. Scanner les secrets
2. Bloquer les commits dangereux
3. Générer des alertes
4. Préparer Vault
5. Tester la sécurité

## Règle
Aucun contenu ne doit avancer sans validation de SEC.
