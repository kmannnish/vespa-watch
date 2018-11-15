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
            mapCircles: [],
            observationsLayer: undefined,
        }
    },

    methods: {
        addObservationsToMap: function () {

            function getColor(d) {
                return d.subject === 'individual' ? '#FF0000' :
                    d.subject === 'nest' ?
                        d.actionCode === 'FD' ? '#0000FF' :
                        d.actionCode === 'PD' ? '#00FF00' :
                        d.actionCode === 'ND' ? '#0FaF00' :
                            '#1FCFaF'
                    : '#000';  // if the subject is not 'Individual' or 'Nest'
            }

            function getRadius(d) {
                return d.subject === 'individual' ? 5 : 12;
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
                    radius: getRadius(obs),
                    className: "circle"
                });
                circle.bindPopup(this.observationToHtml(obs));
                this.mapCircles.push(circle);
            });
            this.observationsLayer = L.featureGroup(this.mapCircles);
            console.log(this.observationsLayer);
            this.observationsLayer.addTo(this.map);
            this.map.fitBounds(this.observationsLayer.getBounds());
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

            html += '<a href="/' + obs.subject + 's/' + obs.id + '/">View details</a>';

            return html;
        },
        clearMap: function() {
            if (this.observationsLayer) {
                this.observationsLayer.clearLayers();
                this.mapCircles = [];
            }
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
            if (this.zone) {
                console.log("Only requesting observations for zone " + this.zone);
                this.observationsUrl = this.observationsUrl + '?zone=' + this.zone;
            } else {
                console.log("No zone set");
            }
            axios.get(this.observationsUrl)
            .then(response => {
                console.log(response.data);
                var allObservations = [];
                if (response.data.individuals) {
                    allObservations = allObservations.concat(response.data.individuals);
                }
                if (response.data.nests) {
                    allObservations = allObservations.concat(response.data.nests);
                }
                this.setCrossFilter(allObservations);
                this.totalObsCount = allObservations.length;
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

    props: ['zone'],

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
    computed: {
        positionLabel: function() {
            return gettext('Position');
        },
        searchLabel: function() {
            return gettext('Search');
        }
    },
    methods: {
        search: function () {
            this.$emit('search', this.location);
        }
    },
    props: ['initLocation'],
    template: `
        <div class="form-group">
            <label for="id_position">{{positionLabel}}</label>
            <div class="input-group">
                <input type="text" class="form-control" id="id_position" name="position" v-model="location">
                <div class="input-group-append">
                    <button type="button" class="btn btn-secondary" v-on:click="search" >{{searchLabel}}</button>
                </div>
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
    template: '<div class="mb-2" id="vw-location-selector-map-map" style="height: 200px;"></div>',
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
        latitudeLabel: function() {
            return gettext('Latitude');
        },
        locationLabel: function() {
            return gettext('Location');
        },
        long: {
            get:
                function () {
                    return this.longitude
                },
            set: function (v) {this.$emit("lon-updated", v);}
        },
        longitudeLabel: function() {
            return gettext('Longitude');
        },
        _location: {
            get: function () {
                return this.location;
            },
            set: function () {
                // do nothing
            }
        }

    },
    props: ['longitude', 'latitude', 'location'],
    template: `
        <div class="form-row">
            <div class="form-group col-md-3" id="div_id_latitude">
                <label for="id_latitude">{{latitudeLabel}}</label>
                <input type="text" class="form-control numberinput" id="id_latitude" name="latitude" v-model="lat">
            </div>
            <div class="form-group col-md-3" id="div_id_longitude">
                <label for="id_longitude">{{longitudeLabel}}</label>
                <input type="text" class="form-control numberinput" id="id_longitude" name="longitude" v-model="long">
            </div>
            <div class="form-group col-md-6" id="div_id_address">
                <label for="id_address">{{locationLabel}}</label>
                <input type="text" class="form-control numberinput" id="id_address" name="address" v-model="_location">
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
            modelLocation: this.location ? '' + this.location : '',
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
                this.modelLocation = location;
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

    template: `
        <section>
            <vw-location-selector-location-input v-bind:init-location="location" v-on:search="getCoordinates"></vw-location-selector-location-input>
            <vw-location-selector-map v-bind:init-marker="initMarker" v-bind:position="markerCoordinates" v-on:marker-move="setCoordinates"></vw-location-selector-map>
            <vw-location-selector-coordinates v-bind:longitude="locationLng" v-bind:latitude="locationLat" v-bind:location="modelLocation" v-on:lon-updated="updateLongitude" v-on:lat-updated="updateLatitude"></vw-location-selector-coordinates>
        </section>
        `
};

var app = new Vue({
    components: {
        'vw-observations-viz': VwObservationsViz,
        'vw-location-selector': VwLocationSelector
    },
    delimiters: ['[[', ']]'],
    el: '#vw-main-app'
});
