from flask import Flask, jsonify
from flask import render_template
from flask import request, redirect
import numpy as np
import psycopg2
import json
import requests
import geojson
import shapely.wkt
import pandas as pd
import sys
import geopandas as gpd
#import folium
#from IPython.display import display
from shapely.geometry import Point
#import pygeos
from tabulate import tabulate
import logging
from shapely.geometry import shape, mapping


app = Flask(__name__)

# Configuring logging
logging.basicConfig(filename='app.log', level=logging.DEBUG)
f = open("app.log", "a")
f.truncate()
f.close()



def get_all_data():
    connection = psycopg2.connect(database="mychka", user="postgres", password="mychka", host="localhost", port=5432)
    cursor = connection.cursor()
    cursor.execute("""select json_build_object('type', 'FeatureCollection','features', json_agg(ST_AsGeoJSON( t.*)::json )) as geojson 
    from (eco_circulaire
    inner JOIN association
        ON eco_circulaire.id=association.gid
    inner JOIN sous_categ
        ON association.id_sous_categ=sous_categ.id_sous_categ
    inner JOIN categ
        ON sous_categ.id_categ=categ.id_categ ) as t""")
    
    return cursor

    
@app.route('/')
def index():
    cursor = get_all_data()
    markers=cursor.fetchall()

    #cursor.execute("""select distinct classe from eco_circulaire order by classe asc""")
    #classes=[c for c, in cursor.fetchall()]

    cursor.execute("""select distinct nom_categ from categ order by nom_categ asc""")
    categs=[c for c, in cursor.fetchall()]

    return render_template("Accueil.html", markers=markers,categs=categs)


# Récupération des paramètres de la requête
def getParams(path):
    args=path.split("&")
    
    # Récupération de la position de l'utilisateur    
    dict_position=json.loads(args[0])
    user_position=str(dict_position["lng"])+","+str(dict_position["lat"])
    
    # Récupération des categories de courses
    cat_course=args[1].split(',')

    return user_position, cat_course


# Récupère l'isochrone de 10 min à pied à partir de la position de l'utilisateur
def isochrone_service(user_position):
    service_ign = """https://wxs.ign.fr/essentiels/geoportail/isochrone/rest/1.0.0/isochrone?"""
    resource = "bdtopo-iso"
    costValue = "300"
    costType = "time"
    timeUnit = "second"
    profile = "pedestrian"
    crs = "EPSG:4326" 

    url = service_ign + "point=" + user_position + "&resource=" + resource + "&costValue=" + costValue + "&costType=" + costType + "&profile=" + profile
    response = requests.get(url)
    return response


def format_geojson(geom):
    # Create a GeoJSON Polygon
    polygon = geojson.Polygon(geom['coordinates'])

    # Create a Feature
    feature = geojson.Feature(geometry=polygon, properties={"name": "isochrone"})

    # Conversion en string GeoJSON
    isochrone_geojson = geojson.dumps(feature)

    # Conversion en WKT
    shapely_polygon = shape(polygon)
    isochrone_wkt = shapely_polygon.wkt

    return isochrone_geojson, isochrone_wkt


# Récupération des commerces dans l'isochrone filtré par catégorie
def build_request(cat_course, isochrone_wkt, radius):
    request="""SELECT json_build_object('type', 'FeatureCollection','features', json_agg(ST_AsGeoJSON( t.*)::json )) as geojson 
    from (eco_circulaire
    inner JOIN association
        ON eco_circulaire.id=association.gid
    inner JOIN sous_categ
        ON association.id_sous_categ=sous_categ.id_sous_categ
    inner JOIN categ
        ON sous_categ.id_categ=categ.id_categ ) as t   
        WHERE ST_Intersects(ST_Buffer(ST_ForceRHR(ST_Boundary(ST_GeomFromText('"""+ isochrone_wkt +"""',4326))),"""+ str(radius) +""", 'side=left'), t.geom)=TRUE 
    AND ST_IsValid(t.geom) AND (
    """
    # Ajouter des categories de commerces demandées par l'utilisateur
    i = 0
    for cat in cat_course:
        # uniquement pour la 1ere categorie
        if i == 0 :
            request=request + "t.nom_categ='" + cat + "'"
        else:
            request=request + " OR t.nom_categ='" + cat + "'" 
        i=i+1

    request = request + ');'
    
    #logging.debug(f' build_request sisi : {request}')
    return request


#Récupérer données de la page html indiquée apres le /
@app.route('/itineraire/<path:path>', methods=['GET'])
def send_file(path):

    user_position, cat_course = getParams(path)
    logging.debug(f'user position : {user_position}, catégories : {cat_course}, ')

    response = isochrone_service(user_position)
    if response.status_code != 200:
        logging.debug(f'La requête IGN isochrone a échoué : {response}')
        sys.exit(1)
   
    response_json = response.json()
    geom = response_json['geometry']
    isochrone_geojson, isochrone_wkt = format_geojson(geom)

    # Récupération du geojson des commerces
    cursor = get_all_data()
    poi_eco_circ=[c for c, in cursor.fetchall()]
    gdf_eco_circ= gpd.GeoDataFrame.from_features(poi_eco_circ[0]["features"])
    gdf_eco_circ.crs = "epsg:4326"




    ################## recupere les commerces dans l isochrone filtré par catégorie #########################

    # Taille du buffer. Augmente si 0 commerces dans l'isochrone de base
    radius = 0
    # Nombre de commerces dans l'isochrone
    nb_com = 0
    request = build_request(cat_course, isochrone_wkt, radius)
    score_max = 0
    iteration = 0
    
    # calcul du score minimum
    # le score minimum doit augmenter avec le nb de catégories cochées
    categs=gdf_eco_circ.groupby('nom_categ').nom_sous_categ.nunique()

    score_minimum=0
    bulle_trouvee=False

    for cat in cat_course:
        #score_minimum=score_minimum+categs.loc[cat]
        score_minimum=7


    # il faut au moins que 75% des sous_categories des catgéroies choisies soient prése,tent dans la bulle
    score_minimum= int(score_minimum * 0.75)
    print("le score de diversité min est de : "+str(score_minimum))

    # agrandi l'isochrone par un buffer tant qu'il n'y a pas au moins 4 commerces dedans 
    while bulle_trouvee==False and iteration <11:
    
        #Augmentation du beffer
        cursor.execute(build_request(cat_course, isochrone_wkt, radius))
        radius=radius+0.0049
        #récupération du json
        poi_eco_circ=[c for c, in cursor.fetchall()]

        # astuce car len(None) fait planter
        try:
            nb_com=len(poi_eco_circ[0]['features'])
        except:
            nb_com=0

        if(nb_com>0):    
            gdf_com_dans_iso = gpd.GeoDataFrame.from_features(poi_eco_circ[0]["features"])

            ############### creation des bulles ##################
            gdf_com_dans_iso.crs = "epsg:4326"

            gdf_com_dans_iso_buff=gdf_com_dans_iso.copy()
            gdf_com_dans_iso_buff.geometry=gdf_com_dans_iso.to_crs(2154).buffer(300).geometry
            # Numerotation des bulles
            gdf_com_dans_iso_buff.insert(0, 'num_bulle', range(0, len(gdf_com_dans_iso_buff)))


            ############### recupérationn des commerces dans les bulles #############################
            com_in_200m = gpd.overlay(gdf_com_dans_iso_buff,gdf_com_dans_iso.to_crs(2154), how='intersection',keep_geom_type=False)

            com_in_200m.rename(columns={ 'nom_categ_2' : 'nom_categ'}, inplace=True)
            
            


        
            ############## Calcul du score de diversité pour chaque bulle  #########################

            score_ss_categ=com_in_200m.groupby('num_bulle').nom_sous_categ_2.nunique()
            


            # vérifie que le score_minimum de sous_catégories est atteint
            if(score_ss_categ[score_ss_categ.idxmax()] >= score_minimum):
                
                # place true pour toutes les bulles qui ont le score max
                #print("bulles avec le max de diversité")
                #print(score_ss_categ.eq(score_ss_categ.max()))       
                
                # vérifie si les bulles ont les commerces des catégories demandées.
                score_categ=com_in_200m.groupby('num_bulle').nom_categ.nunique() 
                #print("bulles avec toutes les categories demandées")
                #print(score_categ.eq(len(cat_course)))  
                
                print("jointure score max et toutes categ")
                cumul_score = pd.concat([score_ss_categ.eq(score_ss_categ.max()), score_categ.eq(len(cat_course))], axis=1)
                
                # Recherche si une bulle ayant toutes les categories de commerce et au moins 75% des sous_categories est trouvé 
                if cumul_score.loc[cumul_score.nom_sous_categ_2 & cumul_score.nom_categ == True].empty == False:
                    print("!!! bulle trouvé !!! ")
                    
                    # Recupère les numero de bulles qui respecte les 2 conditions
                    liste_bulles_ok=cumul_score.loc[cumul_score.nom_sous_categ_2 & cumul_score.nom_categ == True].index
                    print(cumul_score.loc[cumul_score.nom_sous_categ_2 & cumul_score.nom_categ == True])         

                    # Recupere toutes les geométries des bulles ok
                    bulles_ok = gdf_com_dans_iso_buff.to_crs(4326).loc[gdf_com_dans_iso_buff.num_bulle.isin(liste_bulles_ok)]


                    #choisi la bulle la plus proche de la position de l'utilisateur
                    id_best_bulle=bulles_ok.iloc[bulles_ok.to_crs(4326).centroid.sindex.nearest(Point(path_dict["lng"],path_dict["lat"]))[1]]['num_bulle'].values[0]
                    print(id_best_bulle)


                    #id_best_bulle=score_nb_com.loc[score_nb_com.index.isin(cumul_score.loc[cumul_score.nom_sous_categ_2 & cumul_score.nom_categ == True].index)].idxmax()
                    bulle_trouvee=True


            iteration = iteration +1



    if iteration >= 10:
        response ={'message': 'pas de bulle'}
        return response




    ############## extraction de la meilleure des bulles ##################################

    best_bulle=com_in_200m.to_crs(4326).loc[com_in_200m.num_bulle == id_best_bulle]

    commerces_bulle=best_bulle.to_json()

    ############## polygone de la meilleure des bulles ##################################

    best_bulle_buff = gdf_com_dans_iso_buff.to_crs(4326).loc[gdf_com_dans_iso_buff.num_bulle == id_best_bulle]

    bulle=best_bulle_buff.to_json() 

    centre_bulle=best_bulle_buff.to_crs(4326).centroid


    #########  itineraire vers le meilleur commerce ##############
    url = """https://wxs.ign.fr/calcul/geoportail/itineraire/rest/1.0.0/route?resource=bdtopo-pgr&profile=pedestrian&optimization=fastest&start="""+user_position+"&end="+str(centre_bulle.x.values[0])+","+str(centre_bulle.y.values[0])+"""&intermediates=&constraints={"constraintType": "banned","key":"wayType","operator":"=","value":"tunnel"}&geometryFormat=geojson&getSteps=true&getBbox=true&waysAttributes=cleabs&timeUnit=minute"""

    response = requests.get(url)    

    # conversion bytes vers dict     
    response_json = response.json()
    # conversion en string
    itineraire = json.dumps(response_json)

    response={'itineraire':itineraire, 'isochrone': isochrone_geojson, 'bulle': bulle, 'commerces_bulle':commerces_bulle, 'message': 'fund'} 
     
    return response




@app.route('/Qui-sommes-nous')
def qui_sommes_nous():
    return render_template("Qui-sommes-nous.html")

@app.route('/A-propos')
def a_propos():
    return render_template("A-propos.html")

@app.route('/Tutoriel')
def tuto():
    return render_template("Tutoriel.html")

@app.route('/Login')
def login():
    return render_template("Login.html")


if __name__ == '__main__':
    app.run(debug=True)