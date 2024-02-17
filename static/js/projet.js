var map = L.map('map');
var osmUrl = 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
var osmAttrib = 'Map data OpenstreetMap contributors';
var osm = new L.TileLayer(osmUrl, {attribution: osmAttrib}).addTo(map);
map.setView([45.733,4.832],15);




data=JSON.parse(document.getElementById("getdata").dataset.markers);
data=data[0][0]

var commerces = L.geoJSON(data)

commerces.addTo(map)
