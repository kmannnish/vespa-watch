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
            initialZoomed: false,  // only allow the map to zoom and center on the data when the data is loaded for the first time.
            map: undefined,
            mapCircles: [],
            observationsLayer: undefined,
        }
    },

    methods: {
        addObservationsToMap: function () {

            function getColor(d) {
                return d.subject === 'individual' ? '#FD9126' :
                    d.subject === 'nest' ?
                        d.actionCode === 'FD' ? '#3678ff' :
                        d.actionCode === 'PD' ? '#3678ff' :
                        d.actionCode === 'ND' ? '#3678ff' :
                            '#3678ff'
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
            this.observationsLayer.addTo(this.map);
            if (!this.initialZoomed) {
                this.map.fitBounds(this.observationsLayer.getBounds());
            }
            this.initialZoomed = true;
        },

        // Generate a HTML string that represents the observation
        observationToHtml: function (obs) {
            var html = '';

            html += '<h1>' + obs.taxon + '</h1>';

            if (obs.observation_time != null) {
                html += moment(obs.observation_time).format('lll') + '';
            }

            if (obs.subject != null) {
                html += '<b>subject:</b> '+ obs.subject + '';
            }

            if (obs.comments != null) {
                html += '<p>' + obs.comments + '</p>';
            }

            if (obs.inaturalist_id != null) {
                html += '<a target="_blank" href="http://www.inaturalist.org/observations/' + obs.inaturalist_id + '">iNaturalist observation</a>';
            }

            if (obs.imageUrls.length > 0 ) {
                obs.imageUrls.forEach(function (img) {
                    html += '<img class="theme-img-thumb" src="' + img + '">'
                });
            }

            html += '<a href="/' + obs.subject + 's/' + obs.id + '/' + (this.editRedirect ? '?redirect_to=' + this.editRedirect : '') + '">View details</a>';

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

    props: ['autozoom', 'editRedirect', 'observations'],
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
            if (el.noUiSlider != null) {
                // Destroying the UI time slider if it already exists.
                // This can happen when the observations viz is used and
                // the observations loaded are updated (for instance in
                // the management page, when the admin selects a zone.
                el.noUiSlider.destroy();
            }
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
            el.noUiSlider.on('slide', (values, handle) => {
                this.selectedTimeRange.start = parseInt(values[0]);
                this.selectedTimeRange.stop = parseInt(values[1]);
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
            var url = this.observationsUrl;
            if (this.zone != null) {
                // console.log("Only requesting observations for zone " + this.zone);
                url += '?zone=' + this.zone.id;
            } else {
                // console.log("No zone set");
            }
            axios.get(url)
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
        if (this.loadData === "1") {
            this.getData();
        }
    },

    props: ['zone', 'loadData', 'editRedirect'],
    watch: {
        loadData: function (n, o) {
            if (n === "1") {
                this.getData();
            }
        },
        zone: function (n, o) {
            console.log('new zone passed in: ');
            console.log(n);
            this.getData();
        }
    },

    template: `
        <section>
            <vw-observations-viz-map v-bind:observations="observations" v-bind:edit-redirect="editRedirect"></vw-observations-viz-map>
            <vw-observations-viz-time-slider v-on:time-updated="filterOnTimeRange" v-model="timeRange"></vw-observations-viz-time-slider>
        </section>
        `
};


// A row in the management table that displays the
// information of a single nest.
var VwManagmentTableNestRow = {
    computed: {
        cannotEditLabel: function () {
            return gettext('You cannot edit this observation');
        },
        cannotEditTitle: function () {
            return gettext('This observation was created on iNaturalist. You cannot edit it here');
        },
        editStr: function () {
            return gettext('edit');
        },
        managementAction: function () {
            return gettext(this.nest.action);
        },
        nestClass: function () {
            if (this.nest.action) {
                return '';
            }
            return 'table-danger';
        },
        observationTimeStr: function () {
            return moment(this.nest.observation_time).format('lll');
        }
    },
    props: ['nest'],
    template: `
        <tr :class="nestClass">
            <td>{{ observationTimeStr }}</td>
            <td>{{ nest.location }}</td>
            <td>{{ managementAction }}</td>
            <td>
                    <a v-if="nest.originates_in_vespawatch" v-bind:href="nest.updateUrl">{{ editStr }}</a>
                    <span v-if="!nest.originates_in_vespawatch" v-bind:title="cannotEditTitle">{{ cannotEditLabel }}</span>
            </td>
        </tr>
        `
};

// The selector element that allows the admin user to
// select a zone. Using a custom element here that emits
// an event when a zone is selected.
var VwManagementZoneSelector = {
    computed: {
        selectZoneLabel: function () {
            return gettext('Select a zone');
        }
    },
    props: ['zones'],
    template: `
        <div class="form-row">
        <label for="id-zone-select">{{ selectZoneLabel }}</label>
            <select class="form-control" id="id-zone-select" name="zone-select" v-on:change="$emit('zone-selected', $event.target.value)">
                <option v-for="zone in zones" v-bind:value="zone.id">{{ zone.name }}</option>
            </select>
        </div>
        `
};

// The table on the management page that lists the nests
var VwManagementTable = {
    components: {
        'vw-management-table-nest-row': VwManagmentTableNestRow
    },
    computed: {
        dateStr: function () {
            return gettext('date');
        },
        locationStr: function () {
            return gettext('location');
        },
        managementStr: function () {
            return gettext('management');
        },
        nestClass: function () {
            return "table-danger";
        }
    },
    props: ['nests'],
    template: `
        <div class="row">
        <table class="table">
            <thead>
                <tr>
                    <th>{{ dateStr }}</th>
                    <th>{{ locationStr }}</th>
                    <th>{{ managementStr }}</th>
                    <th></th>
                </tr>
            </thead>

            <vw-management-table-nest-row v-for="nest in nests" v-bind:nest="nest" :key="nest.id">
            </vw-management-table-nest-row>
        </table>
    </div>
    `
};

// The management page is largely a component
// Note the following props:
//  - admin: if the user is an admin user, the zone selector will be rendered
//  - initZone: if the user has a zone, this zone will be set as the initial zone and hence
//      only observations from this zone will be loaded on the map and in the table.
//
// The logic in this component allows us to do the following:
// When the page loads, load the map and table based on the
// initial zone. If no zone is set initially (for an admin user
// for instance), load all observations.
// When a zone is selected, update the observations on the map
// and in the nest table.
var VwManagementPage = {
    components: {
        'vw-management-table': VwManagementTable,
        'vw-management-zone-selector': VwManagementZoneSelector,
        'vw-observations-viz': VwObservationsViz
    },
    data: function () {
        return {
            // The map has a load-data prop to which it listens. Initially, the management page
            // sets this prop to "0". If we would not do this and a user with a zone would load
            // the page, the zone would be set causing the map to update which can cause a race
            // condition with the `mounted` function from the map that loads the map without a
            // zone filter.
            // Therefore, we set the load-data prop to 0 by default, but we check in the `mounted`
            // method from this component whether the user has a zone. If not, we set madLoadData
            // to "1" tirggering the map to load data without zone filter.
            mapLoadData: "0",
            nests: [],
            observationsUrl: '/api/observations',
            zone: null,
            allZones: [],
            zonesUrl: '/api/zones'
        }
    },
    computed: {
        myNestsLabel: function () {
            return gettext('My nests');
        },
        userIsAdmin: function () {
            return this.admin === '1';
        },
        zoneLabel: function () {
            return gettext('Zone');
        },
        zoneLookup: function () {
            var lookup = {};
            this.allZones.forEach(function (zone) {
                lookup[zone.id] = zone.name;
            });
            return lookup;
        }
    },
    methods: {
        getNests: function (zone) {
            var url = this.observationsUrl;
            if (zone != null) {
                url += "?zone=" + zone.id;
            }
            axios.get(url)
                .then(response => {
                    console.log(response.data);
                    this.nests = response.data.nests;
                })
                .catch(function (error) {
                    // handle error
                    console.log(error);
                });

        },
        getZones: function () {
            axios.get(this.zonesUrl)
                .then(response => {
                    this.allZones = ['---'].concat(response.data.zones);
                })
                .catch(function (error) {
                    console.log(error);
                });
        },
        selectZone: function (zoneId) {
            this.zone = {'id': zoneId, 'name': this.zoneLookup[zoneId]};
            this.getNests(this.zone);
        }
    },
    mounted: function () {
        if (this.userIsAdmin) {
            this.getZones();
        }
        if (this.initZone) {
            // this.initZone is a JSON string that needs to be parsed.
            // This may not be a best practice, but it works.
            this.zone = JSON.parse(this.initZone);
        } else {
            this.mapLoadData = "1";
        }
        this.getNests(this.zone);
    },
    props: ['admin', 'initZone'],
    template: `
        <section>
            <vw-management-zone-selector v-if="userIsAdmin" v-bind:zones="allZones" v-on:zone-selected="selectZone"></vw-management-zone-selector>
            <h1 v-if="zone">{{ zoneLabel }} {{ zone.name }}</h1>

            <vw-observations-viz v-bind:zone="zone" v-bind:load-data="mapLoadData" edit-redirect="management"></vw-observations-viz>
            <h1>{{ myNestsLabel }}</h1>
            <vw-management-table v-bind:nests="nests"></vw-management-table>
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
            <div class="form-group col-md-6" id="div_id_location">
                <label for="id_location">{{locationLabel}}</label>
                <input type="text" class="form-control numberinput" id="id_location" name="location" v-model="_location">
            </div>
        </div>
        `
};

var VWTaxonSelectorEntry = {
    delimiters: ['[[', ']]'],
    props: {
        'taxon': Object,
        'radioName': String,
        'selected': {
            'type': Boolean,
            'default': false
        }
    },
    methods: {
        getRadioId : function(taxon) {
            return 'taxonRadios' + taxon.id;
        },
    },
    template: `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">[[ taxon.name ]]</h5>
            
                <img class="card-img-top" :src="taxon.identification_picture_url" style="width: 100px;">
            
                <input class="form-check-input" type="radio" :name="radioName" :id="getRadioId(taxon)" :value="taxon.id" :checked="selected">
                        
                <label class="form-check-label" :for="getRadioId(taxon)">
                    [[ taxon.name ]]
                </label>
            </div>
        </div>`

};

var VwTaxonSelector = {
    components : {
        'vw-taxon-selector-entry': VWTaxonSelectorEntry
    },
    delimiters: ['[[', ']]'],
    props: {
        'taxonApiUrl': String,
        'radioName': String,
        'taxonSelected': Number,
    },
    computed: {
        buttonLabel: function () {
            return gettext('Show more species');
        },
    },
    data: function() {
        return {
            'taxaData': [],
            'showAll': false
        }
    },
    methods: {
        showAllIfNeeded: function() {
            if (this.taxonSelected) {
                var that = this;
                var found = this.taxaData.find(function(taxon) {
                    return taxon.id === that.taxonSelected;
                });

                if (!found.identification_priority) {
                    this.showAll = true;
                }
            }
        },
        getData: function(){
            axios.get(this.taxonApiUrl)
            .then(response => {
                this.taxaData = response.data;
                this.showAllIfNeeded();
            })
            .catch(function (error) {
                // handle error
                console.log(error);
            });
        }
    },
    mounted: function () {
        this.getData();
    },
    template: `<div class="form-group">
                    <div v-for="taxon in taxaData" v-if="taxon.identification_priority" class="form-check-inline">
                        <vw-taxon-selector-entry :taxon="taxon" :radio-name="radioName" :selected="taxon.id == taxonSelected"></vw-taxon-selector-entry>
                    </div> 
                    
                    <div>
                        <button class="btn btn-outline-primary btn-sm" v-if="!showAll" v-on:click.stop.prevent="showAll = true">[[ buttonLabel ]]</button>
                    </div>
                    
                    <div v-if="showAll">
                        <div v-for="taxon in taxaData" v-if="!taxon.identification_priority" class="form-check-inline">
                            <vw-taxon-selector-entry :taxon="taxon" :radio-name="radioName" :selected="taxon.id == taxonSelected"></vw-taxon-selector-entry>
                        </div>
                    </div>          
               </div>`
};

var VwDatetimeSelector = {
    delimiters: ['[[', ']]'],
    props: {
        'initDateTime': String,
        'isRequired': Boolean,
        'hiddenFieldName': String,
    },
    data: function() {
        return {
            observationTime: undefined, // As ISO3166
        }
    },
    computed: {
        observationTimeLabel: function () {
            return gettext('Observation time');
        },
    },

    mounted: function () {
        if (this.initDateTime) {
            this.observationTime = this.initDateTime;
        }
    },
    template: `<div class="form-group">
                    <datetime v-model="observationTime" type="datetime" 
                              input-class="datetimeinput form-control">
                        <label for="startDate" slot="before">
                            [[ observationTimeLabel ]]
                            <span v-if="isRequired">*</span>
                        </label>          
                    </datetime>
                    <input type="hidden" :name="hiddenFieldName" :value="observationTime"/>
               </div>`
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
        'vw-location-selector': VwLocationSelector,
        'vw-datetime-selector': VwDatetimeSelector,
        'vw-management-page': VwManagementPage,
        'vw-taxon-selector': VwTaxonSelector,
    },
    delimiters: ['[[', ']]'],
    el: '#vw-main-app'
});