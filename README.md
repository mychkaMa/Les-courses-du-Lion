# Les courses du Lyon

Cette application est le projet de fin d'études d'un groupe d'étudiants du Master GeoNum.

« Les courses du Lion » est une application faite pour celles et ceux qui souhaitent s’inscrire dans une démarche éco-responsable. Elle leur propose de les accompagner en proposant :
Une carte des lieux de l’économie circulaire, là, à côté !
Des rencontres avec artisans et commerçants sympas (présentation, prix, coups de cœur).
Un itinéraire personnalisé et optimisé pour faire ses courses rapidement en mode doux. Des indicateurs éco-responsables pour voir son impact carbone, social, porte-monnal et déchêtal…

Auteurs : Larry Kiener, Mathilde Marchand, Pierre Jacquemond et Rayan Majeri  
Master Géographies Numériques - Géomatique @2022
 
## Fonctionnalités interessantes
- Architecture de l'application avec Flask
- Connexion à postgres et exécution de script SQL à partir du code python avec psycopg2
- Affichage de données geographiques avec leaflet avec légende/sélection de couche
- Utilisation des géoservices de l'IGN (isochrone et calcul de trajet)
- Géotraitement à la volée avec GeoPandas
- Algo de choix du maximum de diversité dans les commerces

## Prérequis :
- Avoir installé python, flask et postgreSQL/GIS sur sa machine

## Pour lancer le projet
1. Executer le script SQL dans Postgres
2. Executer app.py dans visual studio code. un serveur python doit se mettre en marche et lancer l'application

Have Fun!
