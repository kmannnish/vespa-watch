var observationsUrl = '/api/observations';
var mapId = 'map';
var mapPosition = [50.5, 4.5];
var mapZoom = 8;
var map;
var mapCircles = [];
var observationsCF;
var cfDimensions = {};


// Generate a HTML string that represents the observation
function observationToHtml(obs) {
    var html = '';

    if (obs.species != null) {
        html += '<h1>' + obs.species + '</h1><br>';
    }

    if (obs.observation_time != null) {
        html += obs.observation_time + '<br>';
    }

    if (obs.subject != null) {
        html += '<b>subject:</b> '+ obs.subject + '<br>';
    }

    if (obs.comments != null) {
        html += '<p>' + obs.comments + '</p>';
    }

    if (obs.inaturalist_id != null) {
        html += '<a target="_blank" href="http://www.inaturalist.org/observations/' + obs.inaturalist_id + '">iNaturalist observation</a><br>';
    }

    html += '<a href="/observations/' + obs.id + '/">Edit</a>';

    return html;
}


// Get all obsevations from the observations global and add a circle to the map for each observation
function addObservationsToMap() {
    mapCircles = [];

    cfDimensions.timeDim.top(200).forEach(function (obs) {
        var color = 'orange';
        var circle = L.circleMarker([obs.longitude, obs.latitude], {
            stroke: true,  // whether to draw a stroke
            weight: 1, // stroke width in pixels
            color: color,  // stroke color
            opacity: 0.8,  // stroke opacity
            fillColor: color,
            fillOpacity: 0.5,
            radius: 10,
            className: "circle"
        }).addTo(map);
        circle.bindPopup(observationToHtml(obs));
        mapCircles.push(circle);
    });
}

function logObservations(obs) {
    console.log(obs);
}

function setCrossFilter(observations) {
    observationsCF = crossfilter(observations);
    cfDimensions.timeDim = observationsCF.dimension(function (d) {return d.observation_time;});
}

function getObservations() {
    axios.get(observationsUrl)
        .then(function (response) {
            logObservations(response.data);
            setCrossFilter(response.data.observations);
            initTimerangeSlider();
            addObservationsToMap();
        })
        .catch(function (error) {
            // handle error
            console.log(error);
        });
}

function clearMap() {
    mapCircles.forEach(function (mapCircle) {
        map.removeLayer(mapCircle);
    });
}

function initTimerangeSlider() {
    var range = document.getElementById('range');
    var latestObs = cfDimensions.timeDim.top(1);
    var earliestObs = cfDimensions.timeDim.bottom(1);
    var slider = dateslider(range, earliestObs[0].observation_time, latestObs[0].observation_time, function(start, end) {
        console.log('start: ' + start);
        console.log('end: ' + end);
        cfDimensions.timeDim.filterRange([start, end]);
        clearMap();
        addObservationsToMap();
    });
}

function initMap() {
    map = L.map(mapId).setView(mapPosition, mapZoom);
    // For basemaps, check: https://leaflet-extras.github.io/leaflet-providers/preview/
    var CartoDB_Positron = L.tileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);
}

function init() {
    initMap();
    getObservations();
}

init();