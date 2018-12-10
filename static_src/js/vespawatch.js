// This file contains all our custom Javascript code, including VueJS components .

// TODO: Remove all constants/config from here and move to the VWConfig object (defined in custom_tags.py)

// TODO: Update comment
//  * VwObservationsViz: This is the main visualization displayed on the home page. It consists
//    of a time slider and a map, both of which are also components defined here.
//  * VwObservationsVizMap: The map of the VwObservationsViz component
//  * VwObservationsVizTimeSlider: The time slider of the VwObservationsViz.

// Language selector (Navbar)
$(document).ready(function () {
    $('#lang').on('change', function () {
        document.forms['lang-form'].submit();
    });
});

// Disable console.log() et al. if settings.JS_DEBUG = True
if(!VWConfig.debug){
    if(!window.console) window.console = {};
    var methods = ["log", "debug", "warn", "info"];
    for(var i=0;i<methods.length;i++){
        console[methods[i]] = function(){};
    }
}

// The map of the visualization.
// This contains an observations prop. When this property is updated, (when data is retrieved
// from the API or when the user filters the data) the map is cleared and new circles are drawn.
var VwObservationsVizMap = {
    data: function () {
        return {
            initialZoomed: false,  // only allow the map to zoom and center on the data when the data is loaded for the first time.
            map: undefined,
            mapCircles: [],
            observationsLayer: undefined,
        }
    },

    methods: {
        addObservationsToMap: function () {
            var conf = VWConfig.map.circle;

            function getColor(d) {
                return d.subject === 'individual' ? conf.individualColor :
                    d.subject === 'nest' ?
                        d.actionCode === 'FD' ? conf.nestColor.FD :
                            d.actionCode === 'PD' ? conf.nestColor.PD :
                                d.actionCode === 'ND' ? conf.nestColor.ND :
                                    conf.nestColor.DEFAULT
                        : conf.unknownColor;  // if the subject is not 'Individual' or 'Nest'
            }

            function getRadius(d) {
                return d.subject === 'individual' ? conf.individualRadius : conf.nestRadius;
            }

            this.observations.forEach(obs => {
                var circle = L.circleMarker([obs.latitude, obs.longitude], {
                    stroke: true,  // whether to draw a stroke
                    weight: conf.strokeWidth, // stroke width in pixels
                    color: getColor(obs),  // stroke color
                    opacity: conf.strokeOpacity,  // stroke opacity
                    fillColor: getColor(obs),
                    fillOpacity: conf.fillOpacity,
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
            // TODO: Use some template system to avoid this method
            var html = '';

            html += '<h1>' + obs.taxon + '</h1>';

            if (obs.observation_time != null) {
                html += moment(obs.observation_time).format('lll') + '';
            }

            if (obs.subject != null) {
                html += '<b>subject:</b> ' + obs.subject + '';
            }

            if (obs.comments != null) {
                html += '<p>' + obs.comments + '</p>';
            }

            if (obs.inaturalist_id != null) {
                html += '<a target="_blank" href="http://www.inaturalist.org/observations/' + obs.inaturalist_id + '">iNaturalist observation</a>';
            }

            if (obs.imageUrls.length > 0) {
                obs.imageUrls.forEach(function (img) {
                    html += '<img class="theme-img-thumb" src="' + img + '">'
                });
            }

            html += '<a href="/' + obs.subject + 's/' + obs.id + '/' + (this.editRedirect ? '?redirect_to=' + this.editRedirect : '') + '">View details</a>';

            return html;
        },
        clearMap: function () {
            if (this.observationsLayer) {
                this.observationsLayer.clearLayers();
                this.mapCircles = [];
            }
        },
        init: function () {
            var conf = VWConfig.map;

            var mapPosition = conf.initialPosition;
            var mapZoom = conf.initialZoom;
            this.map = L.map("vw-map-map").setView(mapPosition, mapZoom);

            L.tileLayer(conf.tileLayerBaseUrl, conf.tileLayerOptions).addTo(this.map);
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

    data: function () {
        return {
            observationsUrl: VWConfig.apis.observationsUrl,
            observations: [],
            observationsCF: undefined,
            cfDimensions: {},
            timeRange: {start: undefined, stop: undefined},
            totalObsCount: 0
        }
    },

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
            this.cfDimensions.timeDim = this.observationsCF.dimension(function (d) {
                return d.observation_time;
            });
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

var VwManagementActionModal = {
    data: function () {
        return {
            actionOutcomesUrl: VWConfig.apis.actionOutcomesUrl,
            saveActionUrl: VWConfig.apis.actionSaveUrl,
            loadActionUrl: VWConfig.apis.actionLoadUrl,
            deleteActionUrl: VWConfig.apis.actionDeleteUrl,
            availabeOutcomes: [],

            errors: [],

            actionTime: '',  // As ISO3166
            outcome: '',
            personName: '',
            duration: ''  //in Seconds
        }
    },
    props: {
        mode: String, // 'add' or 'edit'
        nestId: Number, //the Nest ID for this action (!! also needed when editing)
        actionId: Number // If mode === 'edit': the ManagementAction ID
    },
    computed: {
        durationInMinutes: {
            get: function() {
                if (this.duration !== '') {
                    return this.duration / 60;
                }
            },
            set: function (newValue) {
                if (newValue !== '') {
                    this.duration = newValue * 60;
                } else {
                    this.duration = '';
                }
            }
        },

        modalTitle: function () {
            return this.mode === 'add' ? gettext("New management action") : gettext("Edit management action")
        },
        outcomeLabel: function () {
            return gettext("Outcome")
        },
        saveLabel: function () {
            return gettext("Save")
        },
        cancelLabel: function () {
            return gettext("Cancel")
        },
        deleteLabel: function () {
            return gettext("Delete")
        },
        nameLabel: function () {
            return gettext("Person name")
        },
        actionTimeLabel: function () {
            return gettext("Action time")
        },
        durationLabel: function () {
            return gettext("Duration")
        },
        inMinutesLabel: function () {
            return gettext("in minutes")
        },
        errorsLabel: function () {
            return gettext("Errors")
        }
    },
    methods: {
        populateFromServer: function () {
            axios.get(this.loadActionUrl, {params: {'action_id': this.actionId}})
                .then(response => {
                    console.log("received response", response);
                    this.actionTime = response.data.action_time;
                    this.outcome = response.data.outcome;
                    this.duration = response.data.duration;
                    this.personName = response.data.person_name;
                })
        },
        deleteAction : function () {
            var vm = this;
            axios.delete(this.deleteActionUrl, {params: {'action_id': this.actionId}})
                .then(response => {
                    if (response.data.result === 'OK') {
                        vm.$emit('close', true);
                    }
                }, error => {
                    console.log("Error");
                });
        },
        save: function () {
            const params = new URLSearchParams();
            params.append('nest', this.nestId);
            params.append('action_time', this.actionTime);
            params.append('outcome', this.outcome);
            params.append('person_name', this.personName);
            params.append('duration', this.duration);

            if (this.mode === 'edit') {
                // We give the actionId to the server so it can perform an update
                params.append('action_id', this.actionId);
            }

            var vm = this;
            axios.post(this.saveActionUrl, params)
                .then(function (response) {
                    if (response.data.result === 'OK') {
                        vm.$emit('close', true);
                    }
                })
                .catch(function (error) {
                    vm.errors = error.response.data.errors;
                });
        },
        loadOutcomes: function () {
            return axios.get(this.actionOutcomesUrl)
                .then(response => {
                    this.availabeOutcomes = response.data;
                })
                .catch(function (error) {
                    // handle error
                    console.log(error);
                });
        }
    },
    mounted: function () {
        // We load the "outcomes" list, and we're in edit mode, we populate the form from the server
        this.loadOutcomes().then(() => { if(this.mode === 'edit'){this.populateFromServer()} });
    },

    template: `
<transition name="modal">
      <div class="modal-mask">
        <div class="modal-wrapper">

        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">{{ modalTitle }}</h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true" @click="$emit('close', false)">&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                    <div v-if="Object.keys(errors).length !== 0">
                        <h6>{{ errorsLabel }}</h6>
                        <ul > 
                            <li v-for="(errorList, fieldName) in errors">
                                {{ fieldName }}:
                                <span v-for="(err, index) in errorList">{{ err }} <span v-if="errorList.length-1<index">, </span> </span>
                            </li>
                        </ul>
                    </div>
                    <form>
                        <div class="form-group">
                            <label for="outcome">{{ outcomeLabel }} *</label>
                            <select v-model="outcome" class="form-control" id="outcome">
                                <option :value="outcome.value" v-for="outcome in availabeOutcomes">{{ outcome.label }}</option>
                            </select>
                            <label for="personName">{{ nameLabel }}</label>
                            <input v-model="personName" class="form-control" type="text" id="personName">
                            
                            <datetime v-model="actionTime" type="datetime" 
                                input-class="datetimeinput form-control">
                                <label for="startDate" slot="before">{{ actionTimeLabel }} *</label>          
                            </datetime>
               
                            <label for="duration">{{ durationLabel }}</label>
                            <input v-model="durationInMinutes" class="form-control" type="number" id="duration">
                            <small class="form-text text-muted">({{ inMinutesLabel }})</small>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-dark" @click="$emit('close', false)">{{ cancelLabel }}</button>
                    <button type="button" class="btn btn-primary" @click="save()">{{ saveLabel }}</button>
                    <button v-if="mode === 'edit'" type="button" @click="deleteAction()" class="btn btn-danger">{{ deleteLabel }}</button>
                </div>
            </div>
        </div>

        </div>
      </div>
    </transition>`
};

// A row in the management table that displays the
// information of a single nest.
var VwManagmentTableNestRow = {
    components: {
        'vw-management-action-modal': VwManagementActionModal
    },
    computed: {
        hasManagementAction: function () {
            // Does this Nest has a management action?
            return (this.nest.action !== "")
        },
        managementActionID: function () {
            // If this nest has a management action, return its ID
            return this.nest.actionId;
        },
        cannotEditLabel: function () {
            return gettext('You cannot edit this observation');
        },
        cannotEditTitle: function () {
            return gettext('This observation was created on iNaturalist. You cannot edit it here');
        },
        editStr: function () {
            return gettext('edit');
        },
        addStr: function () {
            return gettext('add');
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
    data: function () {
        return {
            addActionModalOpened: false,
            editActionModalOpened: false
        }
    },
    methods: {
        showNewActionModal: function () {
            this.addActionModalOpened = true;
        },
        hideNewActionModal: function (dataChanged) {
            this.addActionModalOpened = false;
            if (dataChanged) {
                // Data has been changed by the modal, ask the parent for refreshed data
                this.$emit('data-changed');
            }
        },
        showEditActionModal: function () {
            this.editActionModalOpened = true;
        },
        hideEditActionModal: function (dataChanged) {
            this.editActionModalOpened = false;
            if (dataChanged) {
                // Data has been changed by the modal, ask the parent for refreshed data
                this.$emit('data-changed');
            }
        }

    },
    template: `
        <tr :class="nestClass">
            <td>{{ observationTimeStr }}</td>
            
            <td>{{ nest.address }}</td>
            
            <td>
                <span v-if="hasManagementAction">
                    {{ managementAction }}
                    <button v-on:click="showEditActionModal()" class="btn btn-outline-info btn-sm">{{ editStr }}</button>
                </span>
                
                <button v-else v-on:click="showNewActionModal()" class="btn btn-outline-info btn-sm">{{ addStr }}</button>
                
                <vw-management-action-modal v-if="editActionModalOpened" v-on:close="hideEditActionModal" mode="edit" :nest-id="nest.id" :action-id="nest.actionId"></vw-management-action-modal>
                <vw-management-action-modal v-if="addActionModalOpened" v-on:close="hideNewActionModal" mode="add" :nest-id="nest.id"></vw-management-action-modal>
            </td>
            
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
    methods: {
        loadData: function() {
            if (this.zone != null) {
                this.$root.loadNests(this.zone);
            } else {
                this.$root.loadNests();
            }
        }
    },
    mounted: function () {
        this.loadData();
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

            <vw-management-table-nest-row v-for="nest in nests" :nest="nest" :key="nest.id" v-on:data-changed="loadData">
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
        positionLabel: function () {
            return gettext('Position');
        },
        searchLabel: function () {
            return gettext('Search');
        },
        detectPositionLabel: function () {
            return gettext('Detect current position');
        },
        orLabel: function () {
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
        setMarker: function (lat, lng) {
            console.log("setting marker");
            if (this.marker != undefined) {
                this.map.removeLayer(this.marker);
            }
            ; // Only one!

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
            get: function () {
                return this.latitude
            },
            set: function (v) {
                this.$emit("lat-updated", v);
            }
        },
        long: {
            get: function () {
                return this.longitude
            },
            set: function (v) {
                this.$emit("lon-updated", v);
            }
        },
        latitudeLabel: function () {
            return gettext('Latitude');
        },
        longitudeLabel: function () {
            return gettext('Longitude');
        },
        addressLabel: function () {
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
        getRadioId: function (taxon) {
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
    components: {
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
            switch (this.mode) {
                case 'nest':
                    return 'identification_picture_nest_url';
                case 'individual':
                    return 'identification_picture_individual_url';
            }
        }
    },
    data: function () {
        return {
            'taxaData': [],
            'showAll': false
        }
    },
    methods: {
        showAllIfNeeded: function () {
            if (this.taxonSelected) {
                var that = this;
                var found = this.taxaData.find(function (taxon) {
                    return taxon.id === that.taxonSelected;
                });

                if (!found.identification_priority) {
                    this.showAll = true;
                }
            }
        },
        getData: function () {
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
    data: function () {
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
            navigator.geolocation.getCurrentPosition(function (position) {
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
        reverseGeocode: function () {
            // Updates this.modelAddress based on this.locationCoordinates

            var that = this;
            axios.get("https://nominatim.openstreetmap.org/reverse", {
                params: {
                    format: 'jsonv2', 'lat': that.locationCoordinates[1], 'lon': that.locationCoordinates[0]
                }
            })
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
            let url = VWConfig.apis.observationsUrl + '?type=nest';
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