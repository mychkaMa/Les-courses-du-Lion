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


def send_request(query):
    connection = psycopg2.connect(database="mychka", user="postgres", password="mychka", host="localhost", port=5432)
    cursor = connection.cursor()
    cursor.execute(query)
    
    return cursor

def query_all_markets():
    query = """
    select json_build_object ('type', 'FeatureCollection','features', json_agg(ST_AsGeoJSON( t.*)::json )) as geojson 
    from (eco_circulaire
    inner JOIN association
        ON eco_circulaire.id=association.gid
    inner JOIN sous_categ
        ON association.id_sous_categ=sous_categ.id_sous_categ
    inner JOIN categ
        ON sous_categ.id_categ=categ.id_categ ) as t
    """
    # Retourner la requête SQL construite
    return query

def query_data(cat_course, isochrone, radius):
    query = query_all_markets()

    where_category = "WHERE t.nom_categ IN (" + ", ".join([f"'{cat}'" for cat in cat_course]) + ") "
    where_isochrone = f"""AND ST_Within(t.geom, ST_GeomFromGeoJSON('{isochrone}')) """
    where_isochrone1 = f"""AND ST_Intersects(
            ST_Buffer(ST_ForceRHR(ST_Boundary(ST_GeomFromText('{isochrone}', 4326))), {radius}, 'side=left'),
            t.geom) = TRUE """
    where_valid = "AND ST_IsValid(t.geom);"

    #print("query_________________________________", query + where_category + where_isochrone + where_valid)
    return query + where_category + where_isochrone + where_valid

    
@app.route('/')
def index():
    query = query_all_markets()
    cursor = send_request(query)
    markers = cursor.fetchall()

    #cursor.execute("""select distinct classe from eco_circulaire order by classe asc""")
    #classes=[c for c, in cursor.fetchall()]

    cursor.execute("""select distinct nom_categ from categ order by nom_categ asc""")
    categs=[c for c, in cursor.fetchall()]

    return render_template("Accueil.html", markers=markers,categs=categs)

def get_all_markets():
    query = query_all_markets()
    cursor = send_request(query)
    all_markets = cursor.fetchall()

    return all_markets


# Récupération des paramètres de la requête
def getParams(path):
    args=path.split("&")
    
    # Récupération de la position de l'utilisateur    
    dict_position=json.loads(args[0])
    user_position=str(dict_position["lng"])+","+str(dict_position["lat"])
    
    # Récupération des categories de courses
    cat_course=args[1].split(',')

    return user_position, cat_course

def build_isochrone_url(user_position):
    base_url = "https://wxs.ign.fr/essentiels/geoportail/isochrone/rest/1.0.0/isochrone?"
    params = {
        "point": user_position,
        "resource": "bdtopo-iso",
        "costValue": "900",
        "costType": "time",
        "timeUnit" : "second",
        "profile": "pedestrian",
        "crs" : "EPSG:4326" 
    }
    # Join parameters using '&'
    url_params = "&".join(f"{key}={value}" for key, value in params.items())
    return base_url + url_params

# Récupère l'isochrone de 10 min à pied à partir de la position de l'utilisateur
def isochrone_service(user_position):
    url = build_isochrone_url(user_position)
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError if request was not successful
        return response.json()
    except requests.RequestException as e:
        logging.error(f'La requête IGN isochrone a échoué : {e}')
        raise  # Propagate the exception to the caller


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
def build_request1(cat_course, isochrone_wkt, radius):
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


# Récupération des catégories
#@app.route('/categories/', methods=['GET'])
def get_categories():
    query = """select distinct nom_categ from categ order by nom_categ asc"""
    cursor = send_request(query)
    categories = cursor.fetchall()
    categories = [c for c, in categories]
    return categories


#Récupérer données de la page html indiquée apres le /
@app.route('/itineraire/<path:path>', methods=['GET'])
def send_file(path):

    # Récupération des paramètres de l'url
    user_position, cat_course = getParams(path)

    # Récupération de l'isochrone de 15 min à partir de la position de l'utilisateur
    response = isochrone_service(user_position)

    # Conversion en geojson de qualitey
    isochrone_geojson = response['geometry']
    isochrone_geojson_feature, isochrone_wkt = format_geojson(isochrone_geojson)
   
    isochrone = str(isochrone_geojson)
    isochrone = isochrone.replace("'", '"')

    # Récupération des commerces dans l'isochrone
    radius = 0
    query = query_data(cat_course, isochrone, radius)
    cursor = send_request(query)
    markers = cursor.fetchall() 



    if isochrone_geojson_feature:
        response = {
            'itineraire': '', 
            'isochrone': isochrone_geojson_feature, 
            'bulle': '', 
            'commerces_bulle': '', 
            'message': 'fund',
            'markers': markers
            }
        return response


    # Récupération du geojson des commerces ?
    cursor = query_all_markets()
    poi_eco_circ=[c for c, in cursor.fetchall()]
    gdf_eco_circ= gpd.GeoDataFrame.from_features(poi_eco_circ[0]["features"])
    gdf_eco_circ.crs = "epsg:4326"

    ################## recupere les commerces dans l isochrone filtré par catégorie #########################

    # Taille du buffer. Augmente si 0 commerces dans l'isochrone de base
    radius = 0
    # Nombre de commerces dans l'isochrone
    nb_com = 0
    request = query_data(cat_course, isochrone_wkt, radius)
    score_max = 0
    iteration = 0
    
    # calcul du score minimum
    # le score minimum doit augmenter avec le nb de catégories cochées
    categs=gdf_eco_circ.groupby('nom_categ').nom_sous_categ.nunique()
    #score_minimum=0
    bulle_trouvee=False
    score_minimum = len(cat_course)
    #for cat in cat_course:
        #score_minimum=score_minimum+categs.loc[cat]
        #score_minimum=7


    # il faut au moins que 75% des sous_categories des catgéroies choisies soient prése,tent dans la bulle
    score_minimum= int(score_minimum * 0.75)
    print("le score de diversité min est de : "+str(score_minimum))

    # agrandi l'isochrone par un buffer tant qu'il n'y a pas au moins 4 commerces dedans 
    while bulle_trouvee==False and iteration <11:
    
        #Augmentation du beffer
        cursor.execute(query_data(cat_course, isochrone_wkt, radius))
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

    response={'itineraire':itineraire, 'isochrone': isochrone_geojson_feature, 'bulle': bulle, 'commerces_bulle':commerces_bulle, 'message': 'fund'} 
     
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