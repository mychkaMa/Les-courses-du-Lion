/**
 * Variables globales
 */
var userLocation; // = { lat: 45.756681, lng: 4.831715 };
var userLocationMarker;

var liste_course = []; // 'Activite,Alimentaire,Bien,Dechet,Don,Equipement,Reparation,Restauration'
var categories;

const isochroneColor = '#80b1d3';

var isFirstLoad = true;



window.onload = function () {
    resetCheckboxes();



};

getCategoriesColors()
    .then(res => {
        categories = res

    })
    .catch(error => {
        console.error('Une erreur s\'est produite :', error);
    });



function setUserLocation(lat, lng) {
    // MAJ des coordonnées
    userLocation = {
        lat: lat,
        lng: lng
    };

    // Mettre à jour le contenu de la balise HTML avec les nouvelles coordonnées
    document.getElementById('userCoords').innerHTML = `Latitude: ${lat} <br /> Longitude: ${lng}`;

    // MAJ du marker
    if (userLocationMarker) {
        map.removeLayer(userLocationMarker);
    }
    // Créer un nouveau marqueur et l'ajouter à la carte
    userLocationMarker = L.marker([userLocation.lat, userLocation.lng]).addTo(map);

    map.setView([userLocation.lat, userLocation.lng], 15);
}



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
    try {
        let response = await fetch(url);
        let data = await response.json();
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
var drawnLayer = new L.layerGroup();

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

    // categories.forEach(category => {
    //     if (nom_categ === category.nom_categ) {
    //         return {
    //             fillColor: category.colors,
    //         };
    //     } else {
    //         return {
    //             fillColor: "#0099CC"
    //         };
    //     }
    // });

    if (nom_categ === "Déchet") {
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
    } else if (nom_categ === "Bien-être") {
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
    } else if (nom_categ === "Réparation") {
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

// Ajout d'évènements : zoom + buffer + couleur
function addMouseEvents(feature, leaflet_object) {
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

function showMarkets(data) {
    // Récupération des catégories de commerces
    const categories = getCategories();

    // Ajout des points pour chaque catégorie de commerce
    categories.forEach(function (categorie) {
        var markets = L.geoJson(data, {
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
                    '<styleTitre><p style="font-weight:bold">' + feature.properties.name + '</p></styleTitre><styleColonne><p style="font-weight:bold">Catégorie</styleColonne><br><styleText>' + feature.properties.nom_categ + '</styleText><styleColonne><p style="font-weight:bold">Offre</styleColonne><br><styleText>' + feature.properties.offre_stru + '</styleText><styleColonne><p style="font-weight:bold">Adresse</styleColonne><br><styleText>' + feature.properties.numvoie + ' ' + feature.properties.voie + ' ' + feature.properties.code_posta + ' ' + feature.properties.commune + '</styleText>',
                    { className: feature.properties.nom_categ_esp + "_popup" });
                marker.on('click', function (ev) { marker.openPopup(marker.getLatLng()) })
                return marker
            },
            onEachFeature: addMouseEvents,
            filter: function (feature, layer) {
                return feature.properties.nom_categ == categorie;
            },
        }).addTo(map);

        // Ajout de la légende uniquement lors du premier chargement
        if (isFirstLoad) {
            const color = getColors(categorie).fillColor;
            const customLegend = customizeLayerControl(color, categorie);
            layerControl.addOverlay(markets, customLegend);
        }
    });

    // Mettre isFirstLoad à false après le premier chargement
    isFirstLoad = false;
}

function customizeLayerControl(color, name) {
    return '<i style="background-color:' + color + '; padding:1px; border:1px solid black; border-radius:4px; width:1px; position:relative;">&nbsp;&nbsp;&nbsp;&nbsp;</i>' + name;
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

    drawnLayer.addLayer(bulle)
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
    drawnLayer.addLayer(itineraire)
}


function affiche_itineraire2(itineraire) {
    // Ajout du geoJSON
    var isochrone = L.geoJson(itineraire, {
        style: lineStyle,
        onEachFeature: function (feature, layer) {
            var txt = layer.setText(data_iti.duration.toString().substring(0, 2) + ' min', { center: true, offset: 15, attributes: { fill: 'black' } })
        }

    }).addTo(map);
    itineraire.setZIndex(1400)
    drawnLayer.addLayer(itineraire)
}


/////////////////////////////////////////////////////////////////////////////////
/////////////////////// Afficher l isochrone sur la carte //////////////////////////
/////////////////////////////////////////////////////////////////////////////////

function isochroneStyle(feature) {
    return {
        fillColor: 'white',
        weight: 3,
        opacity: 1,
        color: isochroneColor,
        fillOpacity: 0,
        dashArray: '5, 10',
        dashOffset: '10'
    }
};

function showIsochrone(isochrone) {
    // Ajout du geoJSON à la carte
    var isochrone = L.geoJson(isochrone, {
        style: isochroneStyle,
        onEachFeature: function (feature, layer) {
            var txt = layer.setText('10 min', { offset: 15, attributes: { fill: isochroneColor, font: 'bold 50px' } })
        }
    }).addTo(map);

    isochrone.setZIndex(1100);
    drawnLayer.addLayer(isochrone)

    legendName = "Isochrone 15m"
    const customLegend = customizeLayerControl(isochroneColor, legendName)
    layerControl.addOverlay(isochrone, customLegend);
}


function addLegend(layer, legend, name) {
    layerControl.addOverlay(layer, name);
}


/////////////////////////////////////////////////////////////////////////////////
///////////// chopix du type de courses ////////////////
/////////////////////////////////////////////////////////////////////////////////

var checkboxes = document.querySelectorAll("[id^='choix_commerce_']");

function getCategories() {
    const categories = new Set();
    checkboxes.forEach(function (checkbox) {
        //categories.push(checkbox.value);
        categories.add(checkbox.value);
    })
    return categories
}


// Use Array.forEach to add an event listener to each checkbox.
checkboxes.forEach(function (checkbox) {
    checkbox.addEventListener('change', (event) => {
        liste_course =
            Array.from(checkboxes) // Convert checkboxes to an array to use filter and map.
                .filter(i => i.checked) // Use Array.filter to remove unchecked checkboxes.
                .map(i => i.value) // Use Array.map to extract only the checkbox values from the array of objects.
    })
});

/**
 * Décocher toutes les checkboxes au chargement de la page
 */
function resetCheckboxes() {
    checkboxes.forEach(function (checkbox) {
        checkbox.checked = false;
    });

}



/////////////////////////////////////////////////////////////////////////////////
////////////////////////////// creation de la bulle ///////////////////////////
/////////////////////////////////////////////////////////////////////////////////

async function recherche_bulle(userLocation) {

    // calcul de la bulle
    //suppression des anciennes bulles
    drawnLayer.eachLayer(function (layer) {
        map.removeLayer(layer)
    });

    var data_fetch = await fetchAsync("/itineraire/" + JSON.stringify(userLocation) + "&" + liste_course.toString())

    if (data_fetch['message'] == 'pas de bulle') {
        alert("Notre service ne trouve pas de bulle pour votre recherche...");
    }
    if (data_fetch['message'] == 'fund') {
        // supprime les couches existantes
        map.eachLayer(function (layer) {
            //console.log('layer', layer)
            map.removeLayer(layer);
        });

        osm.addTo(map);
        showIsochrone(JSON.parse(data_fetch['isochrone']));
        //affiche_bulle(JSON.parse(data_fetch['bulle']));
        //affiche_itineraire2(JSON.parse(data_fetch['itineraire']));
        showMarkets(data_fetch['markers'][0][0]);
    }
}


document.getElementById('find_bulle').addEventListener("click", function () {
    if (!userLocation) {
        alert("Veuillez choisir une localisation");
    }
    var isUserLocation = checkUserLocation(userLocation.lat, userLocation.lng);
    var isCategories = checkCategories(liste_course);

    if (isUserLocation && isCategories) {
        recherche_bulle(userLocation, bounds_gd_lyon)
    }
}, false);

/////////////////////////////////////////////////////////////////////////////////
///////////// Chargement des tous les commerces au 1er chargement////////////////
/////////////////////////////////////////////////////////////////////////////////
data = JSON.parse(document.getElementById("getdata").dataset.markers);
data = data[0][0]
showMarkets(data)






/////////////////////////////////////////////////////////////////////////////////
////////////////// Récupération de la localisation utilisateur //////////////////
/////////////////////////////////////////////////////////////////////////////////

/**
 * Créer une localisation aléatoire dans Lyon
 */
document.getElementById('randomLocation').addEventListener("click", function () {
    var minLat = 45.71;
    var maxLat = 45.80;
    var minLng = 4.8;
    var maxLng = 4.88;

    // Générer un nombre décimal aléatoire compris entre min (inclus) et max (exclus)
    var lat = Math.random() * (maxLat - minLat) + minLat;
    var lng = Math.random() * (maxLng - minLng) + minLng;

    setUserLocation(lat, lng);
}, false);


/**
 * Créer une localisation à partir d'un clic sur la carte
 */
function onMapClick(e) {
    setUserLocation(e.latlng.lat, e.latlng.lng);
}
map.on('click', onMapClick);


/**
 * Géocoder l'adresse de l'utilisateur
 */
var geocoderBAN = L.geocoderBAN({
    collapsed: false,
    style: 'searchBar',
    resultsNumber: 5,
    placeholder: 'Entrez votre adresse'
}).addTo(map)

geocoderBAN.markGeocode = function (feature) {
    setUserLocation(feature.geometry.coordinates[1], feature.geometry.coordinates[0]);
    // var popup = L.popup()
    //     .setLatLng(latlng)
    //     .setContent(feature.properties.label)
    //     .openOn(map)
}


/**
 * Récupérer la position de l'utilisateur
 */
document.getElementById('webLocation').addEventListener("click", function () {
    // recupere la position de l'utilisateur
    map.locate({ setView: true, watch: false, maxZoom: 14 })
        .on('locationfound', async function (e) {
            await setUserLocation(e.latlng.lat, e.latlng.lng);
        })
        .on('locationerror', function (e) {
            alert("Où êtes vous?? Le service ne connait pas votre point de départ. Renseigner une adresse ou autoriser la geolocalisation dans votre navigateur ");
        })
})

/**
 * Vérifier si l'utilisateur est localisé dans le GL
 * @param {*} lat 
 * @param {*} lng 
 * @returns 
 */
function checkUserLocation(lat, lng) {
    if (!bounds_gd_lyon.contains([[lat, lng]])) {
        alert("Vous êtes trop loin des commerces...");
        return false
    }
    return true;
}


/**
 * Vérifier si l'utilisateur à cocher des catégories
 * @param {*} listCategories 
 * @returns 
 */
function checkCategories(listCategories) {
    if (listCategories.length > 0) {
        return true;
    }
    else {
        alert("Vous devez choisir un type de courses avant de calculer un itinéraire ...");
        return false;
    }
}




async function getCategoriesColors() {
    var categories = await fetchAsync("/categories/")
    return categories
}