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
                url += '?zone=' + this.zone;
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
            <td>{{ nest.address }}</td>
            <td>{{ managementAction }}</td>
            <td>
                    <a v-if="nest.originates_in_vespawatch" v-bind:href="nest.updateUrl">{{ editStr }}</a>
                    <span v-if="!nest.originates_in_vespawatch" v-bind:title="cannotEditTitle">{{ cannotEditLabel }}</span>
            </td>
        </tr>
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
        addressStr: function () {
            return gettext('address');
        },
        managementStr: function () {
            return gettext('management');
        },
        nestClass: function () {
            return "table-danger";
        }
    },
    data: function () {
        return {
            _nests: []
        }
    },
    mounted: function () {
        if (this.zone != null) {
            this.$root.loadNests(this.zone);
        } else {
            this.$root.loadNests();
        }
    },
    props: ['nests', 'zone'],
    watch: {
        nests: function (n, o) {
            this._nests = n;
        }
    },
    template: `
        <div class="row">
        <table class="table">
            <thead>
                <tr>
                    <th>{{ dateStr }}</th>
                    <th>{{ addressStr }}</th>
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


var VwLocationSelectorLocationInput = {
    data: function () {
        return {
            location: this.initAddress ? '' + this.initAddress : ''
        }
    },
    computed: {
        positionLabel: function() {
            return gettext('Position');
        },
        searchLabel: function() {
            return gettext('Search');
        },
        detectPositionLabel: function() {
            return gettext('Detect current position');
        },
        orLabel: function() {
            return gettext('or')
        },
        typeALocationLabel: function () {
            return gettext('type a location here and click "Search"...')
        }
    },
    methods: {
        search: function () {
            this.$emit('search', this.location);
        }
    },
    props: ['initAddress'],
    template: `
        <div class="form-group">
            <label for="id_position">{{positionLabel}}</label>
            <div class="input-group">
                <button class="btn btn-secondary" v-on:click.stop.prevent="$emit('autodetect-btn')">{{ detectPositionLabel }}</button>
                <label>{{ orLabel }}</label>
                <input type="text" class="form-control" id="id_position" name="position" v-model="location" :placeholder="typeALocationLabel">
                <div class="input-group-append">
                    <button type="button" class="btn btn-secondary" v-on:click="search" >{{ searchLabel }}</button>
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
        long: {
            get: function () {return this.longitude},
            set: function (v) {this.$emit("lon-updated", v);}
        },
        latitudeLabel: function() {
            return gettext('Latitude');
        },
        longitudeLabel: function() {
            return gettext('Longitude');
        },
        addressLabel: function() {
            return gettext('Address');
        },
        _address: {
            get: function () {
                return this.address;
            },
            set: function () {
                // do nothing
            }
        }

    },
    props: ['longitude', 'latitude', 'address'],
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
                <label for="id_address">{{addressLabel}}</label>
                <input type="text" class="form-control numberinput" id="id_address" name="address" v-model="_address">
            </div>
        </div>
        `
};

var VwTaxonSelectorEntry = {
    delimiters: ['[[', ']]'],
    props: {
        'taxon': Object,
        'radioName': String,
        'pictureAttribute': String,
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
            
                <img class="card-img-top" :src="taxon[pictureAttribute]" style="width: 100px;">
            
                <input class="form-check-input" type="radio" :name="radioName" :id="getRadioId(taxon)" :value="taxon.id" :checked="selected">
                        
                <label class="form-check-label" :for="getRadioId(taxon)">
                    [[ taxon.name ]]
                </label>
            </div>
        </div>`

};

var VwTaxonSelector = {
    components : {
        'vw-taxon-selector-entry': VwTaxonSelectorEntry
    },
    delimiters: ['[[', ']]'],
    props: {
        'taxonApiUrl': String,
        'radioName': String,
        'taxonSelected': Number,
        'mode': String // nest | individual
    },
    computed: {
        buttonLabel: function () {
            return gettext('Show more species');
        },
        pictureAttrName: function () {
            switch(this.mode) {
                case 'nest': return 'identification_picture_nest_url';
                case 'individual': return 'identification_picture_individual_url';
            }
        }
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
                        <vw-taxon-selector-entry :taxon="taxon" :picture-attribute="pictureAttrName" :radio-name="radioName" :selected="taxon.id == taxonSelected"></vw-taxon-selector-entry>
                    </div> 
                    
                    <div>
                        <button class="btn btn-outline-primary btn-sm" v-if="!showAll" v-on:click.stop.prevent="showAll = true">[[ buttonLabel ]]</button>
                    </div>
                    
                    <div v-if="showAll">
                        <div v-for="taxon in taxaData" v-if="!taxon.identification_priority" class="form-check-inline">
                            <vw-taxon-selector-entry :taxon="taxon" :picture-attribute="pictureAttrName" :radio-name="radioName" :selected="taxon.id == taxonSelected"></vw-taxon-selector-entry>
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
            return gettext('Observation date');
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
            modelAddress: this.address ? '' + this.address : '',
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
        autodetectPosition: function () {
            var that = this;
            navigator.geolocation.getCurrentPosition(function(position) {
                that.setCoordinates([position.coords.longitude, position.coords.latitude]);
                that.markerCoordinates = [position.coords.longitude, position.coords.latitude];
            });
        },
        getCoordinates: function (address) {
            console.log('Address input changed to ' + address + '+\n -> get coordinates and update locationCoordinates and markerCoordinates');
            this.provider.search({query: address})
            .then(result => {
                var firstResult = result[0];
                console.log(result);
                this.locationCoordinates = [firstResult.x, firstResult.y];
                this.markerCoordinates = [firstResult.x, firstResult.y];
                this.modelAddress = firstResult.label;
            })
        },
        reverseGeocode: function() {
            // Updates this.modelAddress based on this.locationCoordinates

            var that = this;
            axios.get("https://nominatim.openstreetmap.org/reverse", {params: {
                format: 'jsonv2', 'lat': that.locationCoordinates[1], 'lon': that.locationCoordinates[0]}})
            .then(response => {
                that.modelAddress = response.data.display_name;
            });
        },

        setCoordinates: function (coordinates) {
            console.log('Marker moved. Set locationCoordinates and update address.');
            this.locationCoordinates = coordinates;
            this.reverseGeocode();
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

    props: ['initCoordinates', 'initMarker', 'address'],

    template: `
        <section>
            <vw-location-selector-location-input v-bind:init-address="address" v-on:autodetect-btn="autodetectPosition" v-on:search="getCoordinates"></vw-location-selector-location-input>
            <vw-location-selector-map v-bind:init-marker="initMarker" v-bind:position="markerCoordinates" v-on:marker-move="setCoordinates"></vw-location-selector-map>
            <vw-location-selector-coordinates v-bind:longitude="locationLng" v-bind:latitude="locationLat" v-bind:address="modelAddress" v-on:lon-updated="updateLongitude" v-on:lat-updated="updateLatitude"></vw-location-selector-coordinates>
        </section>
        `
};

var app = new Vue({
    components: {
        'vw-observations-viz': VwObservationsViz,
        'vw-location-selector': VwLocationSelector,
        'vw-datetime-selector': VwDatetimeSelector,
        'vw-management-table': VwManagementTable,
        'vw-taxon-selector': VwTaxonSelector,
    },
    data: {
        individuals: null,
        nests: null
    },
    delimiters: ['[[', ']]'],
    el: '#vw-main-app',
    methods: {
        loadNests: function (zone) {
            let url = '/api/observations?type=nest';
            if (zone != null) {
                url = url + '&zone=' + zone;
            }
            axios.get(url)
            .then(response => {
                if (response.data.nests) {
                    this.nests = response.data.nests;
                }
            })
            .catch(function (error) {
                // handle error
                console.log(error);
            });

        }
    }
});