# Schéma MEM

Chaque fiche doit utiliser un frontmatter YAML en tête du fichier.

## Champs obligatoires

- id
- type
- title
- tags
- universe
- summary
- status
- version
- updated_at

## Types autorisés

- character
- location
- theme
- timeline
- glossary

## Convention

- `id` doit être unique
- `tags` doit être une liste
- `version` commence à `1.0.0`
- `updated_at` format `YYYY-MM-DD`
- le contenu détaillé vient sous le frontmatter

## Exemple de structure

```yaml
***
id: char-001
type: character
title: Nom du personnage
tags: [hero, warrior]
universe: nom-univers
summary: Résumé court
status: active
version: 1.0.0
updated_at: 2026-06-10
***
Contenu détaillé ici.
