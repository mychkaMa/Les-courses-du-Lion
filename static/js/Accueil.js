//var user_position ='';

var user_position = { lat: 45.756681, lng: 4.831715 };

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////// fonction pour debuguer: liste tous les arguments d'un objet javascript /////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function listerToutesLesProprietes(o) {
    let objectToInspect;
    let resultat = [];

    for (objectToInspect = o;
        objectToInspect !== null;
        objectToInspect = Object.getPrototypeOf(objectToInspect)) {
        resultat = resultat.concat(Object.getOwnPropertyNames(objectToInspect));
    }
    return resultat;
}


/////////////////////////////////////////////////////////////////////////////////
////////////////////// envoi des donné au server app.py /////////////////////////
/////////////////////////////////////////////////////////////////////////////////

async function fetchAsync(url) {
    console.log('fetchAsync1', url);
    try {
        let response = await fetch(url);
        console.log('fetchAsync2', response);
        let data = await response.json();
        console.log('fetchAsync3', data);
        return data;
    } catch (error) {
        console.error('Erreur lors de la récupération des données:', error);
        throw error; // Vous pouvez choisir de relancer l'erreur ou de la gérer différemment ici
    }
}


/////////////////////////////////////////////////////////////////////////////////
///////////////////////////////// Carte Leaflet /////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////

var map = L.map('map');
var osmUrl = 'https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png';
var osmAttrib = 'Map data © OpenStreetMap contributors';
var osm = new L.TileLayer(osmUrl, { attribution: osmAttrib }).addTo(map);
map.setView([45.7640, 4.8357], 12);

// FullScreen
map.addControl(new L.Control.Fullscreen());
var layerControl = L.control.layers().addTo(map);
layerControl.options = { collapsed: false }

// limitation de la navigation à Lyon
var p1 = L.point(45.913444276, 5.021678272), p2 = L.point(45.582896678, 4.703865076), bounds_gd_lyon = L.bounds(p1, p2);
map.setMaxBounds(bounds_gd_lyon);


//Gestion couche
var drawn_layer = new L.layerGroup();

/////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////// Echelle ////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////

var scale = L.control.scale(
    options = {
        position: 'bottomleft',
        maxWidth: 100,
        metric: true,
        imperial: false,
        updateWhenIdle: false
    },
).addTo(map);

/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////// style commerces /////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////

// Définition du style en fonction du type de commerce
function getColors(nom_categ) {
    if (nom_categ === "Dechet") {
        return {
            fillColor: "#b3de69",
        };
    } else if (nom_categ === "Alimentaire") {
        return {
            fillColor: "#fb8072",
        };
    } else if (nom_categ === "Textile") {
        return {
            fillColor: "#80b1d3",
        };
    } else if (nom_categ === "Activite") {
        return {
            fillColor: "#bebada",
        };
    } else if (nom_categ === "Bien etre") {
        return {
            fillColor: "#fccde5",
        };
    } else if (nom_categ === "Equipement Maison") {
        return {
            fillColor: "#8dd3c7",
        };
    } else if (nom_categ === "Restauration") {
        return {
            fillColor: "#fdb462",
        };
    } else if (nom_categ === "Don") {
        return {
            fillColor: "#ffffb3",
        };
    } else if (nom_categ === "Reparation") {
        return {
            fillColor: "#d9d9d9",
        };
    } else {
        return {
            fillColor: "#0099CC"
        };
    }
}


/////////////////////////////////////////////////////////////////////////////////
/////////////////////// Afficher les commerces sur la carte//////////////////////
/////////////////////////////////////////////////////////////////////////////////

function affiche_commerces(data) {

    // Ajout d'évènements : zoom + buffer + couleur
    function mouse_events(feature, leaflet_object) {
        leaflet_object.on('click', function (event) {
            map.setView(event.latlng, 16);
        });
        leaflet_object.on('mouseover', function (event) {
            var leaflet_object = event.target;
            leaflet_object.setRadius(12),
                leaflet_object.setStyle({
                    color: "white",
                    weight: 5
                })
        });
        leaflet_object.on('mouseout', function (event) {
            var leaflet_object = event.target;
            leaflet_object.setStyle({
                color: "white",
                weight: 1
            }),
                leaflet_object.setRadius(6)
        });
    }


    // Ajout du geoJSON

    var categs = ['Activite', 'Alimentaire', 'Bien etre', 'Dechet', 'Don', 'Equipement Maison', 'Reparation', 'Restauration', 'Textile'];


    // Ajout des points, une couche par categorie de commerce
    categs.forEach(function (categ) {
        var commerces = L.geoJson(data, {
            style: function (feature) {
                return {
                    radius: 6,
                    color: 'white',
                    weight: 1,
                    fillOpacity: 1
                }
            },

            pointToLayer: function (feature, latlng) {
                var marker = L.circleMarker(latlng, getColors(feature.properties.nom_categ)).bindPopup(
                    '<styleTitre><p style= "font-weight : bold">' + feature.properties.name + '</p></styleTitre><styleColonne><p style= "font-weight : bold">Catégorie</styleColonne><br><styleText>' + feature.properties.nom_categ + '</styleText><styleColonne><p style= "font-weight : bold">Offre</styleColonne><br><styleText>' + feature.properties.offre_stru + '</styleText><styleColonne><p style= "font-weight : bold">Adresse</styleColonne><br><styleText>' + feature.properties.numvoie + ' ' + feature.properties.voie + ' ' + feature.properties.code_posta + ' ' + feature.properties.commune + '</styleText>',
                    { className: feature.properties.nom_categ_esp + "_popup" });
                marker.on('click', function (ev) { marker.openPopup(marker.getLatLng()) })
                return marker
            },

            onEachFeature: mouse_events,

            filter: function (feature, layer) {
                return feature.properties.nom_categ == categ;
            },

        }).addTo(map);
        // crer un control layer avec titre

        layerControl.addOverlay(commerces, '<i style="background-color:' + getColors(categ).fillColor + '; padding:5px ; border:1px solid black ; border-radius:4px; width: 20px; position: relative;">&nbsp;&nbsp;&nbsp;&nbsp;</i> ' + categ);
        //console.log(layerControl.getContainer())
    });

}


/////////////////////////////////////////////////////////////////////////////////
/////////////////////// Afficher la bulle sur la carte //////////////////////////
/////////////////////////////////////////////////////////////////////////////////


function areaStyle(feature) {
    return {
        fillColor: '#ee6b12',
        weight: 2,
        opacity: 0.7,
        color: 'black',
        //dashArray: '3',
        fillOpacity: 0.3
    }
};

function affiche_bulle(data_bulle) {

    // Ajout du geoJSON
    var bulle = L.geoJson(data_bulle, { style: areaStyle }).addTo(map)
    bulle.bringToBack()
    map.fitBounds(bulle.getBounds());

    drawn_layer.addLayer(bulle)
}

/////////////////////////////////////////////////////////////////////////////////
/////////////////////// Afficher l itineraire sur la carte //////////////////////
/////////////////////////////////////////////////////////////////////////////////

function lineStyle(feature) {
    return {
        weight: 2,
        opacity: 0.7,
    }
};

function affiche_itineraire(data_iti) {
    // Ajout du geoJSON
    var itineraire = L.geoJson(data_iti.geometry, {
        style: lineStyle,
        onEachFeature: function (feature, layer) {

            var txt = layer.setText(data_iti.duration.toString().substring(0, 2) + ' min', { center: true, offset: 15, attributes: { fill: 'black' } })

        }

    }).addTo(map);
    itineraire.setZIndex(1400)
    drawn_layer.addLayer(itineraire)
}



/////////////////////////////////////////////////////////////////////////////////
/////////////////////// Afficher l isochrone sur la carte //////////////////////////
/////////////////////////////////////////////////////////////////////////////////


function IsoStyle(feature) {
    return {
        fillColor: 'white',
        weight: 2,
        opacity: 1,
        color: '#80b1d3',
        fillOpacity: 0,
        dashArray: '5, 10',
        dashOffset: '10'
    }
};




function affiche_isochrone(data_iso) {
    // Ajout du geoJSON
    var isochrone = L.geoJson(data_iso, {
        style: IsoStyle,
        onEachFeature: function (feature, layer) {

            var txt = layer.setText('10 min', { offset: 15, attributes: { fill: '#80b1d3', font: 'bold 30px' } })

        }

    }).addTo(map);
    isochrone.setZIndex(1100);
}



/////////////////////////////////////////////////////////////////////////////////
///////////////////////////// Connaitre votre adresse ///////////////////////////
/////////////////////////////////////////////////////////////////////////////////

var geocoderBAN = L.geocoderBAN({
    collapsed: false,
    style: 'searchBar',
    resultsNumber: 5,
    placeholder: 'Entrez votre adresse'
}).addTo(map)


geocoderBAN.markGeocode = function (feature) {
    var latlng = [feature.geometry.coordinates[1], feature.geometry.coordinates[0]]
    map.setView(latlng, 14)
    user_position = { lat: latlng[0], lng: latlng[1] };

    var popup = L.popup()
        .setLatLng(latlng)
        .setContent(feature.properties.label)
        .openOn(map)
}

/////////////////////////////////////////////////////////////////////////////////
///////////// chopix du type de courses ////////////////
/////////////////////////////////////////////////////////////////////////////////

var checkboxes = document.querySelectorAll("#choix_commerce");
//var liste_course = []

var liste_course = 'Activite,Alimentaire,Bien,Dechet,Don,Equipement,Reparation,Restauration'

// Use Array.forEach to add an event listener to each checkbox.
checkboxes.forEach(function (checkbox) {
    checkbox.addEventListener('change', (event) => {
        liste_course =
            Array.from(checkboxes) // Convert checkboxes to an array to use filter and map.
                .filter(i => i.checked) // Use Array.filter to remove unchecked checkboxes.
                .map(i => i.value) // Use Array.map to extract only the checkbox values from the array of objects.
        console.log(liste_course.toString())
    })
});

/////////////////////////////////////////////////////////////////////////////////
///////////// Chargement des tous les commerces au 1er chargement////////////////
/////////////////////////////////////////////////////////////////////////////////
data = JSON.parse(document.getElementById("getdata").dataset.markers);
data = data[0][0]

affiche_commerces(data)


/////////////////////////////////////////////////////////////////////////////////
////////////////////////////// creation de la bulle ///////////////////////////
/////////////////////////////////////////////////////////////////////////////////

async function recherche_bulle(user_position) {

    // Sending data to Flask server
    console.log("Sending data:", data);

    fetch('/your-endpoint', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
        .then(response => response.json())
        .then(data => {
            // Logging the response from Flask server
            console.log("Response from server:", data);
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

/*

    if (liste_course.length > 0) {
        if (bounds_gd_lyon.contains([[user_position.lat, user_position.lng]]) == true) {

            // calcul de la bulle
            //suppression des anciennes bulles
            drawn_layer.eachLayer(function (layer) {
                map.removeLayer(layer)
            });

            var data_fetch = await fetchAsync("/itineraire/" + JSON.stringify(user_position) + "&" + liste_course.toString())
            //console.log(data_fetch);

            if (data_fetch['message'] == 'pas de bulle') {
                alert("Notre service ne trouve pas de bulle pour votre recherche...");
            }
            if (data_fetch['message'] == 'fund') {
                // supprime les couches existantes

                osm.addTo(map);
                affiche_isochrone(JSON.parse(data_fetch['isochrone']));
                affiche_bulle(JSON.parse(data_fetch['bulle']));
                affiche_itineraire(JSON.parse(data_fetch['itineraire']));

            }
        }
        else {
            alert("vous êtes trop loin des commerces...");
        }
    }
    else {
        alert("vous devez choisir un type de courses avant de calculer un itinéraire ...");
    }
}

*/
document.getElementById('find_bulle').addEventListener("click", function () {
    if (user_position == '') {
        // recupere la position de l'utilisateur
        map.locate({ setView: true, watch: false, maxZoom: 14 })

            .on('locationfound', async function (e) {
                user_position = e.latlng
                var popupup = L.popup()
                    .setLatLng(e.latlng)
                    .setContent("Votre position")
                    .openOn(map)

                recherche_bulle(user_position, bounds_gd_lyon)
            })


            .on('locationerror', function (e) {
                alert("Où êtes vous?? Le service ne connait pas votre point de départ. Renseigner une adresse ou autoriser la geolocalisation dans votre navigateur ");
            })
    }
    else {
        recherche_bulle(user_position, bounds_gd_lyon)
    }
}, false);


