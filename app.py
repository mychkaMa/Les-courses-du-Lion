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
import geopandas as gpd
#import folium
#from IPython.display import display
from shapely.geometry import Point
#import pygeos
from tabulate import tabulate
import logging


app = Flask(__name__)

# Configuring logging
logging.basicConfig(filename='app.log', level=logging.DEBUG)
f = open("app.log", "a")
f.truncate()
f.close()

@app.route('/')
def index():

    connection = psycopg2.connect(database="mychka", user="postgres", password="mychka", host="localhost", port=5432) #todo variabilisé ?

    cursor = connection.cursor()

    cursor.execute("""select json_build_object('type', 'FeatureCollection','features', json_agg(ST_AsGeoJSON( t.*)::json )) as geojson 
    from (eco_circulaire
    inner JOIN association
        ON eco_circulaire.id=association.gid
    inner JOIN sous_categ
        ON association.id_sous_categ=sous_categ.id_sous_categ
    inner JOIN categ
        ON sous_categ.id_categ=categ.id_categ ) as t""")
    
    markers=cursor.fetchall()

    #cursor.execute("""select distinct classe from eco_circulaire order by classe asc""")
    #classes=[c for c, in cursor.fetchall()]

    cursor.execute("""select distinct nom_categ from categ order by nom_categ asc""")
    categs=[c for c, in cursor.fetchall()]

    return render_template("Accueil.html", markers=markers,categs=categs)



@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.get_json()  # Récupérer les données JSON envoyées depuis le client
    # Faire quelque chose avec les données (par exemple, les traiter)
    return jsonify({'message': 'Données reçues avec succès'})




@app.route('/your-endpoint', methods=['POST'])
def your_endpoint():
    # Logging incoming request data
    logging.debug('Request data: %s', request.json)

    # Process the request
    # Your code here

    # Logging outgoing response data
    response_data = {'message': 'Response received'}
    logging.debug('Response data: %s', response_data)

    return jsonify(response_data)


#Récupérer données de la page html indiquée apres le / # TODO
@app.route('/itineraire/<path:path>', methods=['GET'])
def send_file(path):

    logging.debug(f'def send_file : {path}')


    arg=path.split("&")
    # recuperation de la position de l'utilisateur    
    path_dict=json.loads(arg[0])


    toto = { "lat": 45.756681, "lng": 4.831715 }
    user_position = str(toto["lng"]) + "," + str(toto["lat"])

   # user_position=str(path_dict["lng"])+","+str(path_dict["lat"])
    
    # Recuperation des categories de courses
    cat_course=arg[1].split(',')


    logging.debug(f'user : {cat_course}, {user_position}')
    

################### Récupère l'isochrone de 10 min à pied auitour de la position de l'utilisateur  ##############
  #  service_capabilities = "https://wxs.ign.fr/essentiels/geoportail/getcapabilities"
   # response = requests.get(service_capabilities)    
    #logging.debug(f'response get cap : {response}')

    service_isochrone = "https://wxs.ign.fr/essentiels/geoportail/isochrone/rest/1.0.0/isochrone?"
    service_isochrone2 = """https://wxs.ign.fr/calcul/geoportail/itineraire/rest/1.0.0/isochrone?point=2.337306,48.849319&resource=bdtopo-iso&costValue=300&costType=time&profile=car&direction=departure&constraints={"constraintType":"banned","key":"wayType","operator":"=","value":"autoroute"}&distanceUnit=meter&timeUnit=second&crs=EPSG:4326"""
    service_isochrone3 = """https://wxs.ign.fr/essentiels/geoportail/isochrone/rest/1.0.0/isochrone?point=4.831715,45.756681&resource=bdtopo-iso&costValue=300&costType=time"""
    response = requests.get(service_isochrone3)    

    resource = "bdtopo-iso",
    costValue = "300",
    costType = "time"

    url = str(service_isochrone2) + "point=" + str(user_position) + "&resource=" + str(resource) + "&costValue=" + str(costValue) + "&costType=" + str(costType)
    logging.debug(f'url : {url}')
    


    #response = requests.get(url)    
    logging.debug(f'response IGN : {response}')
    dict = response.json()
    logging.debug(f'dict : {dict}')
    geomWKT=dict['geometry']


    geomWKT='POLYGON ((4.857825 45.766805, 4.857183 45.766805, 4.856541 45.766805, 4.852689 45.769942, 4.852689 45.77039, 4.851406 45.770839, 4.850122 45.771735, 4.850122 45.773975, 4.851406 45.774872, 4.852689 45.77532, 4.853331 45.77532, 4.853973 45.774872, 4.853973 45.775768, 4.853973 45.776216, 4.853973 45.776664, 4.855257 45.777112, 4.855257 45.778009, 4.855257 45.778457, 4.853973 45.779353, 4.853973 45.779801, 4.853973 45.780249, 4.854615 45.780249, 4.855257 45.781594, 4.857825 45.782042, 4.857825 45.78249, 4.857825 45.782938, 4.858467 45.782938, 4.859109 45.782938, 4.859751 45.783386, 4.860392 45.783386, 4.861034 45.783386, 4.861676 45.783386, 4.861676 45.782938, 4.861676 45.78249, 4.861676 45.782042, 4.861676 45.781594, 4.86296 45.781594, 4.86296 45.782042, 4.863602 45.782042, 4.863602 45.781594, 4.863602 45.781146, 4.864244 45.781594, 4.864886 45.781594, 4.865528 45.781594, 4.86617 45.780698, 4.86617 45.780249, 4.865528 45.779801, 4.866811 45.779353, 4.867453 45.778905, 4.868095 45.777561, 4.868095 45.777112, 4.870021 45.776664, 4.871305 45.776216, 4.871305 45.775768, 4.871305 45.774424, 4.871305 45.773975, 4.870663 45.773975, 4.871305 45.773527, 4.871305 45.773079, 4.870663 45.773079, 4.870021 45.771735, 4.869379 45.771735, 4.868737 45.77039, 4.867453 45.769494, 4.866811 45.769494, 4.866811 45.769942, 4.864886 45.768598, 4.864244 45.768598, 4.86296 45.767702, 4.862318 45.766357, 4.861034 45.766357, 4.860392 45.76815, 4.859751 45.766357, 4.858467 45.766357, 4.857825 45.766805))'
    #print(geomWKT)
    #geom = str(geomWKT['coordinates'])
    # Convert to a shapely.geometry.polygon.Polygon objects
    g1 = shapely.wkt.loads(geomWKT)

    g2 = geojson.Feature(geometry=g1, properties={})

    # conversion en string
    isochrone = geojson.dumps(g2)

    
    ################## recupere toutes les données #########################
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

    #récupération du json
    json_c_for_c=[c for c, in cursor.fetchall()]


    gdf_tout_com= gpd.GeoDataFrame.from_features(json_c_for_c[0]["features"])
    gdf_tout_com.crs = "epsg:4326"

    ################## recupere les commerces dans l isochrone filtré par catégorie #########################

    # taille du buffer. Augmente si 0 commerces dans l'isochrone de base
    radius=0

    # Nombre de commerces dans l'isochrone
    nb_com=0
    
    # construction de la requete sql
    def build_request(cat_course,geomWKT,radius):
        request="""SELECT json_build_object('type', 'FeatureCollection','features', json_agg(ST_AsGeoJSON( t.*)::json )) as geojson 
        from (eco_circulaire
        inner JOIN association
            ON eco_circulaire.id=association.gid
        inner JOIN sous_categ
            ON association.id_sous_categ=sous_categ.id_sous_categ
        inner JOIN categ
            ON sous_categ.id_categ=categ.id_categ ) as t   
        WHERE ST_Intersects(ST_Buffer(ST_ForceRHR(ST_Boundary(ST_GeomFromText('"""+geomWKT+"""',4326))),"""+str(radius)+""", 'side=left'), t.geom)=TRUE 
        AND ST_IsValid(t.geom) AND (
        """
        # Ajouter des categories de commerces delmandées par l'utilisateur
        i=0
        for cat in cat_course:
            # uniquement pour la 1ere categorie
            if i==0:
                request=request+"t.nom_categ='"+cat+"'" 
            else:
                request=request+" OR t.nom_categ='"+cat+"'" 
            i=i+1
    
        request=request+');'
        return request

    score_max = 0
    iteration = 0
    
    # calcul du score minimum
    # le score minimum doit augmenter avec le nb de catégories cochées
    categs=gdf_tout_com.groupby('nom_categ').nom_sous_categ.nunique()

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
        cursor.execute(build_request(cat_course,geomWKT,radius))
        radius=radius+0.0049
        #récupération du json
        json_c_for_c=[c for c, in cursor.fetchall()]

        # astuce car len(None) fait planter
        try:
            nb_com=len(json_c_for_c[0]['features'])
        except:
            nb_com=0

        if(nb_com>0):    
            gdf_com_dans_iso = gpd.GeoDataFrame.from_features(json_c_for_c[0]["features"])

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
    dict = response.json()
    # conversion en string
    itineraire = json.dumps(dict)

    response={'itineraire':itineraire, 'isochrone': isochrone, 'bulle': bulle, 'commerces_bulle':commerces_bulle, 'message': 'fund'} 
     
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