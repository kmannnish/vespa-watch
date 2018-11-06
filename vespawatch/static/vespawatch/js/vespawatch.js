// This file contains vuejs components that are used in our application.
//  * VwObservationsViz: This is the main visualization displayed on the home page. It consists
//    of a time slider and a map, both of which are also components defined here.
//  * VwObservationsVizMap: The map of the VwObservationsViz component
//  * VwObservationsVizTimeSlider: The time slider of the VwObservationsViz.



// The map of the visualization.
// This contains an observations prop. When this property is updated, (when data is retrieved
// from the API or when the user filters the data) the map is cleared and new circles are drawn.
var VwObservationsVizMap = {
    data: function() {
        return {
            map: undefined,
            mapCircles: []
        }
    },

    methods: {
        addObservationsToMap: function () {

            function getColor(d) {
                return d.subject === 'Individual' ? '#FF0000' :
                    d.subject === 'Nest' ?
                        d.action === 'FD' ? '#0000FF' :
                        d.action === 'PD' ? '#00FF00' :
                        d.action === 'ND' ? '#0FaF00' :
                            '#1FCFaF'
                    : '#000';  // if the subject is not 'Individual' or 'Nest'
            }

            this.observations.forEach(obs => {
                var color = 'orange';
                var circle = L.circleMarker([obs.latitude, obs.longitude], {
                    stroke: true,  // whether to draw a stroke
                    weight: 1, // stroke width in pixels
                    color: getColor(obs),  // stroke color
                    opacity: 0.8,  // stroke opacity
                    fillColor: getColor(obs),
                    fillOpacity: 0.5,
                    radius: 10,
                    className: "circle"
                }).addTo(this.map);
                circle.bindPopup(this.observationToHtml(obs));
                this.mapCircles.push(circle);
            });
        },

        // Generate a HTML string that represents the observation
        observationToHtml: function (obs) {
            var html = '';

            if (obs.species != null) {
                html += '<h1>' + obs.species + '</h1><br>';
            }

            if (obs.observation_time != null) {
                html += moment(obs.observation_time).format('lll') + '<br>';
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

            if (obs.imageUrls.length > 0 ) {
                obs.imageUrls.forEach(function (img) {
                    html += '<img class="theme-img-thumb" src="' + img + '"><br>'
                });
            }

            html += '<a href="/observations/' + obs.id + '/">View details</a>';

            return html;
        },
        clearMap: function() {
            this.mapCircles.forEach(mapCircle => {
                this.map.removeLayer(mapCircle);
            });
        },
        init: function () {
            var mapPosition = [50.85, 4.35];
            var mapZoom = 8;
            this.map = L.map("vw-map-map")
                .setView(mapPosition, mapZoom);
            var CartoDB_Positron = L.tileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://carto.com/attributions">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 20
            })
                .addTo(this.map);
        }
    },

    mounted: function () {
        this.init();
    },

    props: ['observations'],
    watch: {
        observations: function (newObservations, oldObservations) {
            console.log('vw-observations-viz-map: Observations got updated!');
            this.clearMap();
            this.addObservationsToMap();
        }
    },

    template: '<div class="mb-2" id="vw-map-map" style="height: 450px;"></div>'
};


// Time slider
// Has a prop 'value' which is used for binding data with the v-model directive.
// This should be an object with properties 'start' and 'stop' to indicate the total
// range of the slider.
// The time slider will also emit an 'time-updated' event when the user changes the
// selected range.
var VwObservationsVizTimeSlider = {
    data: function () {
        return {
            selectedTimeRange: {}
        }
    },
    props: ['value'],
    computed: {
        startStr: function () {
            return moment(this.selectedTimeRange.start).format('D MMM YYYY');
        },
        stopStr: function () {
            return moment(this.selectedTimeRange.stop).format('D MMM YYYY');
        }
    },
    methods: {
        init: function () {
            var el = document.getElementById('vw-time-slider');
            this.selectedTimeRange = {
                start: this.value.start,
                stop: this.value.stop
            };
            noUiSlider.create(el, {
            // Create two timestamps to define a range.
                range: {
                    min: this.value.start,
                    max: this.value.stop
                },

            // Steps of one week
                step: 7 * 24 * 60 * 60 * 1000,

            // Two more timestamps indicate the handle starting positions.
                start: [this.value.start, this.value.stop],

            // No decimals
                format: wNumb({
                    decimals: 0
                })
            });
            el.noUiSlider.on('set', (values, handle) => {
                this.selectedTimeRange.start = parseInt(values[0]);
                this.selectedTimeRange.stop = parseInt(values[1]);
                this.$emit('time-updated', values.map(x => parseInt(x)));
            });
        }
    },
    watch: {
        value: function (newRange, oldRange) {
            // when data is loaded from the API, the range of the slider can be set. Therefore,
            // watch the 'value' prop and call init() when that prop is changed.
            this.init();
        }
    },
    template: `
        <div class="row align-items-center py-2 mb-2">
            <div class="col-2">{{ startStr }}</div>
            <div class="col"><div id="vw-time-slider"></div></div>
            <div class="col-2 text-right">{{ stopStr }}</div>
        </div>
        `
};

// The VwObservationsViz consists of 2 child components: the time slider (VwObservationsVizTimeSlider)
// and the map (VwObservationsVizMap).
// Data is retrieved from the API and subsequently the time slider and the map are updated
// accordingly. When the time slider is updated, the observations are filtered and the remaining
// observations are passed to the map which will then redraw all circles.
var VwObservationsViz = {
    components: {
        'vw-observations-viz-time-slider': VwObservationsVizTimeSlider,
        'vw-observations-viz-map': VwObservationsVizMap
    },

    data: function () {return {
        observationsUrl: '/api/observations',
        observations: [],
        observationsCF: undefined,
        cfDimensions: {},
        timeRange: {start: undefined, stop: undefined},
        totalObsCount: 0
    }},

    methods: {
        getData: function () {
            // Call the API to get observations
            axios.get(this.observationsUrl)
            .then(response => {
                console.log(response.data);
                this.setCrossFilter(response.data.observations);
                this.totalObsCount = response.data.observations.length;
                this.initTimerangeSlider();
                this.setObservations();
            })
            .catch(function (error) {
                // handle error
                console.log(error);
            });
        },

        initTimerangeSlider: function () {
            var latestObs = this.cfDimensions.timeDim.top(1);
            var earliestObs = this.cfDimensions.timeDim.bottom(1);
            var start = earliestObs[0].observation_time;
            var stop = latestObs[0].observation_time;
            if (start === stop) {
                stop++;
            }
            this.timeRange = {start: start, stop: stop};
        },

        setCrossFilter: function (observations) {
            this.observationsCF = crossfilter(observations);
            this.cfDimensions.timeDim = this.observationsCF.dimension(function (d) {return d.observation_time;});
        },

        setObservations: function () {
            this.observations = this.cfDimensions.timeDim.top(this.totalObsCount);
        },

        filterOnTimeRange: function (timeRange) {
            this.cfDimensions.timeDim.filterRange(timeRange);
            this.setObservations();
        }
    },

    mounted: function () {
        // This function gets called when the component is completely loaded on the page
        this.getData();
    },

    template: `
        <section>
            <vw-observations-viz-map v-bind:observations="observations"></vw-observations-viz-map>
            <vw-observations-viz-time-slider v-on:time-updated="filterOnTimeRange" v-model="timeRange"></vw-observations-viz-time-slider>
        </section>
        `
};

var VwLocationSelectorLocationInput = {
    data: function () {
        return {
            location: this.initLocation ? '' + this.initLocation : ''
        }
    },
    methods: {
        search: function () {
            this.$emit('search', this.location);
        }
    },
    props: ['initLocation'],
    template: `
        <div id="div_id_location" class="form-group">
            <label for="id_location" class="col-form-label ">{% trans "Location" %}</label>
            <div>
                <input type="text" name="location" class="textinput form-control" id="id_location" v-model="location">
                <button type="button" v-on:click="search" class="btn btn-success">{% trans "Get position" %}</button>
            </div>
        </div>
        `
};

var VwLocationSelectorMap = {
    computed: {
        leafletPosition: function () {
            return [this.position[1], this.position[0]]; // leaflet expects a position array to be [lat, long] instead of [long, lat]
        }
    },
    data: function () {
        return {
            map: null,
            mapZoom: 8,
            marker: null
        };
    },
    methods: {
        emitLongLat: function () {
            this.$emit("marker-move", [this.marker.getLatLng().lng, this.marker.getLatLng().lat]);
        },
        setMarker: function(lat, lng) {
            console.log("setting marker");
            if (this.marker != undefined) { this.map.removeLayer(this.marker); }; // Only one!

            // Create the marker
            this.marker = L.marker([lng, lat], {
                draggable: true
            }).addTo(this.map);


            // ... Then make them follow the marker.
            this.marker.on('dragend', e => {
                this.emitLongLat();
            });
        }
    },
    mounted: function () {
        this.map = L.map("vw-location-selector-map-map").setView(this.leafletPosition, this.mapZoom);
        L.tileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png').addTo(this.map);
        if (this.initMarker === "true") {
            console.log("init with a marker");
            this.setMarker(this.position[0], this.position[1]);
            this.map.setZoom(16);
            this.map.panTo(new L.LatLng(this.position[1], this.position[0]));
        } else {
            console.log("don't add a marker");
        }
    },
    props: ['position', 'initMarker'],
    template: `
        <div class="row">
            <div class="col">
                <div id="vw-location-selector-map-map" style="width: 640px; height: 480px;"></div>
            </div>
        </div>
        `,
    watch: {
        position: function (n, o) {
            console.log('Map: position updated');
            console.log(n);
            this.setMarker(n[0], n[1]);
            this.map.setZoom(16);
            this.map.panTo(new L.LatLng(n[1], n[0]));
        }
    }
};

var VwLocationSelectorCoordinates = {
    computed: {
        lat: {
            get: function () {return this.latitude},
            set: function (v) {this.$emit("lat-updated", v);}
        },
        long: {
            get:
                function () {
                    return this.longitude
                },
            set: function (v) {this.$emit("lon-updated", v);}
        }
    },
    props: ['longitude', 'latitude'],
    template: `
        <div>
            <div id="div_id_longitude" class="form-group">
                <label for="id_longitude" class="col-form-label ">{% trans "Longitude" %}</label>
                <div>
                    <input type="text" name="longitude" class="numberinput form-control" id="id_longitude" v-model="long">
                </div>
            </div>
            
            <div id="div_id_latitude" class="form-group">
                <label for="id_latitude" class="col-form-label ">{% trans "Latitude" %}</label>
                <div>
                    <input type="text" name="latitude" class="numberinput form-control" id="id_latitude" v-model="lat">
                </div>
            </div>
        </div>
        `
};

var VwLocationSelector = {
    data: function () {
        return {
            bbox: [[50.2, 4.4], [50.9, 4.9]],
            locationCoordinates: [this.initCoordinates[0], this.initCoordinates[1]],  // the coordinates that will be passed to the long lat fields
            markerCoordinates: [this.initCoordinates[0], this.initCoordinates[1]],  // the coordinates that will be passed to the map
            provider: new GeoSearch.OpenStreetMapProvider({
                params: {
                    countrycodes: 'BE'
                }
            })
        }
        },
    computed: {
        locationLng: function () {
            return this.locationCoordinates ? this.locationCoordinates[0] : this.initCoordinates[0];  // TODO or use startCoordinates?
        },
        locationLat: function () {
            return this.locationCoordinates ? this.locationCoordinates[1] : this.initCoordinates[1];  // TODO or use startCoordinates?
        }
    },
    components: {
        'vw-location-selector-location-input': VwLocationSelectorLocationInput,
        'vw-location-selector-map': VwLocationSelectorMap,
        'vw-location-selector-coordinates': VwLocationSelectorCoordinates
    },

    methods: {
        getCoordinates: function (location) {
            console.log('Location input changed to ' + location + '+\n -> get coordinates and update locationCoordinates and markerCoordinates');
            this.provider.search({query: location})
            .then(result => {
                var firstResult = result[0];
                console.log(result);
                this.locationCoordinates = [firstResult.x, firstResult.y];
                this.markerCoordinates = [firstResult.x, firstResult.y];
            })
        },
        setCoordinates: function (coordinates) {
            console.log('Marker moved. Set locationCoordinates');
            this.locationCoordinates = coordinates;
        },
        updateLatitude: function (lat) {
            console.log('latitude was updated');
            this.markerCoordinates = [this.markerCoordinates[0], lat];
        },
        updateLongitude: function (long) {
            console.log('longitude was updated');
            this.markerCoordinates = [long, this.markerCoordinates[1]];
        },
    },

    props: ['initCoordinates', 'initMarker', 'location'],

    template: `<div>
        <vw-location-selector-location-input v-bind:init-location="location" v-on:search="getCoordinates"></vw-location-selector-location-input>
        <vw-location-selector-map v-bind:init-marker="initMarker" v-bind:position="markerCoordinates" v-on:marker-move="setCoordinates"></vw-location-selector-map>
        <vw-location-selector-coordinates v-bind:longitude="locationLng" v-bind:latitude="locationLat" v-on:lon-updated="updateLongitude" v-on:lat-updated="updateLatitude"></vw-location-selector-coordinates>
        </div>`

};

var app = new Vue({
    components: {
        'vw-observations-viz': VwObservationsViz,
        'vw-location-selector': VwLocationSelector
    },
    delimiters: ['[[', ']]'],
    el: '#vw-main-app'
});
