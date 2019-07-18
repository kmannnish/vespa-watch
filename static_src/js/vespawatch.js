// This file contains all our custom Javascript code, including VueJS components .

// TODO: Remove all constants/config from here and move to the VWConfig object (defined in custom_tags.py)
// TODO: Some gettext calls/computed properties are duplicated in multiple Vue components: factorize?

// 1. Global stuff

// Enable the language selector (navbar)
$(document).ready(function () {
    $('#lang').on('change', function () {
        document.forms['lang-form'].submit();
    });
});

// Load obs_card images
$(document).ready(function () {
    $('#obs-cards div.card').each(function (index, value) {
        var card = $(this);
        var split_id = card.attr('id').split('-');
        var subject = split_id[1].toLowerCase();
        var id = split_id[2];
        $.getJSON('/api/' + subject + 's/' + id)
            .done(function (r) {
                if (r.thumbnails && r.thumbnails.length > 0 && r.thumbnails[0]) {
                    card.find('img').attr('src', r.thumbnails[0]);
                }
            });
        }
    );
});

// Disable console.log() et al. if settings.JS_DEBUG != True
if (!VWConfig.debug) {
    if (!window.console) window.console = {};
    var methods = ['log', 'debug', 'warn', 'info'];
    for (var i = 0; i < methods.length; i++) {
        console[methods[i]] = function () {
        };
    }
}

// Declare global variable that can be filled in by a Django view
var formErrorMessagesRaw;

// 2. Vue.JS components

// The map of the visualization.
// This contains an observations prop. When this property is updated, (when data is retrieved
// from the API or when the user filters the data) the map is cleared and new circles are drawn.
var VwObservationsVizMap = {
    computed: {
        'managementMap': function () {
            return this.zoneId != null
        }
    },
    data: function () {
        return {
            initialZoomed: false,  // only allow the map to zoom and center on the data when the data is loaded for the first time.
            map: undefined,
            mapCircles: [],
            observationsLayer: undefined,
            selectedObservation: undefined
        }
    },

    methods: {
        addObservationsToMap: function () {
            var conf = VWConfig.map.circle;

            var getColor = d => {
                if (this.type === 'management') {
                    return d.subject === 'individual' ? conf.individualColor :
                        d.subject === 'nest' ?
                            d.actionFinished ? conf.nestColor.finished :
                                conf.nestColor.unfinished
                            : conf.unknownColor;  // if the subject is not 'Individual' or 'Nest'

                } else {
                    return d.subject === 'individual' ? conf.individualColor :
                        d.subject === 'nest' ? conf.nestColor.DEFAULT
                            : conf.unknownColor;  // if the subject is not 'Individual' or 'Nest'
                }
            };

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
                    className: 'circle',
                    subject: obs.subject,
                    id: obs.id
                });

                circle.on('click', () => {
                    var popup = new L.Popup();
                    popup.setLatLng([obs.latitude, obs.longitude]);
                    popup.setContent('loading...');    // Set the popup content to "loading" while the observation data is requested from the API
                    this.map.openPopup(popup);
                    this.fillPopupWithObsData(obs, popup);
                });
                this.mapCircles.push(circle);
            });
            this.observationsLayer = L.featureGroup(this.mapCircles);
            this.observationsLayer.addTo(this.map);
            this.observationsLayer.bringToFront();
            if (!this.initialZoomed) {
                //this.map.fitBounds(this.observationsLayer.getBounds());
            }
            this.initialZoomed = true;
            this.map.spin(false);
        },

        fillPopupWithObsData: function (obs, popup) {

            // Get observation data from the API
            var url = obs.subject === 'individual' ? VWConfig.apis.individualsUrl : VWConfig.apis.nestsUrl;
            var sep = url[url.length - 1] === '/' ? '' : '/';
            axios.get(url + sep + obs.id)
                .then(response => {
                    console.log('Fetched individual data');
                    console.log(response);
                    var obsData = response.data;
                    var url = new URL(obsData.detailsUrl, VWConfig.baseUrl);
                    var sep = VWConfig.staticRoot[VWConfig.staticRoot.length - 1] === '/' ? '' : '/';
                    var no_image_url = VWConfig.staticRoot + sep + 'vespawatch/img/no_image_rectangular.png';

                    if (this.editRedirect) {
                        url.searchParams.append('redirect_to', this.editRedirect);
                    }
                    var str = `
                        <div id="`+ "map-popup-" + obs.id + `" class="card">
                            <img class="card-img-top" src="` + (obsData.thumbnails[0] ? obsData.thumbnails[0] : no_image_url) + `">
                            <div class="card-body">
                                <h5 class="card-title">` + obsData.display_vernacular_name + `</h5>
                                <h6 class="card-subtitle text-muted mb-2"><em>` + obsData.display_scientific_name + `</em></h6>
                                <p class="card-text">
                                    <span class="badge badge-secondary text-lowercase">` + obsData.subject + `</span>` +
                                    (obsData.inat_vv_confirmed ? ` <span class="badge badge-success text-lowercase">` + gettext('Confirmed') + `</span>` : "") + `
                                </p>` + (obsData.inaturalist_id ? `<a class="card-link stretched-link" href="http://www.inaturalist.org/observations/` + obsData.inaturalist_id + `" target="_blank">iNaturalist</a>` : "") + `
                            </div>
                            <div class="card-footer text-muted">
                                <small>` + moment(obsData.observation_time).format('D MMMM YYYY') + `</small>
                            </div>
                        </div>
                    `;
                    popup.setContent(str);

                })
                .catch(function (error) {
                    console.log(error);
                });

        },

        clearMap: function () {
            if (this.observationsLayer) {
                this.observationsLayer.clearLayers();
                this.mapCircles = [];
            }
        },

        init: function () {
            var conf = VWConfig.map;

            // Init map
            var mapPosition = conf.initialPosition;
            var mapZoom = conf.initialZoom;
            this.map = L.map('vw-map-map').setView(mapPosition, mapZoom);

            // Add spinner
            this.map.spin(true);

            // Add legend
            var legend = L.control({ position: 'topright' });
            var nest_size = (conf.circle.nestRadius + conf.circle.strokeWidth) * 2;
            var indiv_size = (conf.circle.individualRadius + conf.circle.strokeWidth) * 2;          
            legend.onAdd = function(map) {
                var div = L.DomUtil.create('div', 'legend');
                div.innerHTML +=
                    '<svg ' +
                        'width="' + nest_size + '" ' +
                        'height="' + nest_size + '">' +
                    '<circle ' +
                        'cx="' + nest_size / 2 + '" ' +
                        'cy="' + nest_size / 2 + '" ' +
                        'r="' + conf.circle.nestRadius + '" ' +
                        'stroke="' + conf.circle.nestColor.DEFAULT + '" ' +
                        'stroke-width="' + conf.circle.strokeWidth + '" ' +
                        'stroke-opacity="' + conf.circle.strokeOpacity + '" ' +
                        'fill="' + conf.circle.nestColor.DEFAULT + '" ' +
                        'fill-opacity="' + conf.circle.fillOpacity + '"/>' +
                    '</svg> ' + gettext('Nest') + ' ';
                    
                div.innerHTML +=
                    '<svg ' +
                        'width="' + indiv_size + '" ' +
                        'height="' + indiv_size + '">' +
                    '<circle ' +
                        'cx="' + indiv_size / 2 + '" ' +
                        'cy="' + indiv_size / 2 + '" ' +
                        'r="' + conf.circle.individualRadius + '" ' +
                        'stroke="' + conf.circle.individualColor + '" ' +
                        'stroke-width="' + conf.circle.strokeWidth + '" ' +
                        'stroke-opacity="' + conf.circle.strokeOpacity + '" ' +
                        'fill="' + conf.circle.individualColor + '" ' +
                        'fill-opacity="' + conf.circle.fillOpacity + '"/>' +
                    '</svg> ' + gettext('Individual');

                return div;
            };
            legend.addTo(this.map);

            // Add base layer
            L.tileLayer(conf.tileLayerBaseUrl, conf.tileLayerOptions).addTo(this.map);

            if (this.zoneId) {
                axios.get(VWConfig.apis.zoneUrl, {params: {zone_id: this.zoneId}})
                    .then(response => {
                        var geoJSONLayer = L.geoJSON(response.data);
                        geoJSONLayer.addTo(this.map);
                        geoJSONLayer.bringToBack();
                        this.map.fitBounds(geoJSONLayer.getBounds());
                    })
                    .catch(function (error) {
                        console.log(error);
                    });
            }
        }
    },

    mounted: function () {
        this.init();
    },

    props: ['autozoom', 'editRedirect', 'observations', 'type', 'zoneId'],
    watch: {
        observations: function (newObservations, oldObservations) {
            this.clearMap();
            Vue.nextTick(() => { // !! The popups should be in the DOM before we reference them !!
                this.addObservationsToMap();
            });
        }
    },

    computed: {
        nestLabel: function () {
            return gettext('Nest');
        },

        individualLabel: function () {
            return gettext('Individual');
        },

    },

    template: `<div>
        <div class="mb-2" id="vw-map-map" style="height: 450px;"></div>
    </div>`
};


var VwObservationsVizTimeSlider = {
    props: {
        observationsTimeRange: Object,
        autoPlay: {
            type: Boolean,
            default: true
        },
        animationSpeed: {
            type: Number,
            default: 70 // milliseconds between steps
        },
        loop: {
            type: Boolean,
            default: true
        }
    },

    data: function () {
        return {
            selectedTimeRange: {
                'start': 0,
                'stop': 0
            },
            oneWeek: 7 * 24 * 60 * 60 * 1000,
            dataReady: false,
            playing: false,

            intervalId: 0, // Don't touch, managed by playAnimation() / stopAnimation()
        }
    },

    methods: {
        nextIncrementWillOverrun: function (duration) {
            if (this.selectedTimeRange.stop + duration >= this.observationsTimeRange.stop) {
                return true;
            } else {
                return false;
            }
        },

        incrementRangeEnd: function (duration) {
            if (this.selectedTimeRange.stop >= this.observationsTimeRange.stop) {
                this.selectedTimeRange.stop = this.selectedTimeRange.start;
            }

            this.selectedTimeRange.stop = this.selectedTimeRange.stop + duration;
        },

        stopAnimationIfRunning: function() {
            if (this.playing) {
                this.stopAnimation();
            }
        },

        toggleAnimation: function () {
            this.playing ? this.stopAnimation() : this.startAnimation();
        },

        startAnimation: function () {
            this.intervalId = window.setInterval(this.animation, this.animationSpeed);
        },

        animation: function () {
            if (this.dataReady) {
                this.playing = true;

                if (this.nextIncrementWillOverrun(this.oneWeek)) {
                    // We've reached the last observation...
                    if (!this.loop) {
                         this.stopAnimation()
                    }
                }
                this.incrementRangeEnd(this.oneWeek);
            }
        },

        stopAnimation: function () {
            window.clearInterval(this.intervalId);
            this.playing = false;
        }
    },

    watch: {
        observationsTimeRange: function (newRange, oldRange) {
            // Only when data is loaded from the API, the range of the slider can be set. Therefore,
            // watch the 'observationsTimeRange' prop to set the data initial value.
            console.log('New time range received');
            console.log(newRange);
            this.selectedTimeRange.start = this.observationsTimeRange.start;
            this.selectedTimeRange.stop = this.observationsTimeRange.start;

            this.dataReady = true;
        },
        selectedTimeRange: {
            handler: function () {
                this.$emit('time-updated', [this.selectedTimeRange.start, this.selectedTimeRange.stop]);
            },
            deep: true
        }
    },

    computed: {
        stopStr: function () {
            return moment(this.selectedTimeRange.stop).format('YYYY MMM');
        },
        buttonLabel: function () {
            return (this.playing ? gettext('Pause') : gettext('Play'));
        }
    },

    mounted: function () {
        this.$nextTick(function () {
            if (this.autoPlay) {
                this.startAnimation();
            }
        })
    },

    template: `
        <div id="vw-time-slider" class="d-flex align-items-center">
            <button style="width:120px;" class="btn btn-sm btn-secondary" type="button" @click="toggleAnimation">{{ buttonLabel }}</button>
            <input class="form-control-range mx-4" type="range" v-model.number="selectedTimeRange.stop" v-on:input="stopAnimationIfRunning" v-on:change="stopAnimationIfRunning" :min="observationsTimeRange.start" :max="observationsTimeRange.stop + oneWeek" :step="oneWeek">
            <div v-if="dataReady" style="width:120px;">{{ stopStr }}</div>
        </div>
        `
}

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
            individualsUrl: VWConfig.apis.individualsUrl,
            nestsUrl: VWConfig.apis.nestsUrl,
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
            var urls = [];

            if (this.zone != null) {
                console.log('Only requesting observations for zone ' + this.zone);
                urls.push(axios.get(this.observationsUrl + '&zone=' + this.zone + '&type=nest'));
            } else {
                urls.push(axios.get(this.individualsUrl + '?light=true&vvOnly=true'));
                urls.push(axios.get(this.nestsUrl + '?light=true&vvOnly=true'));
                console.log('No zone set');
            }
            axios.all(urls)
              .then(axios.spread((indivRes, nestRes) => {
                    console.log(indivRes.data);
                    console.log(nestRes.data);
                    this.setSubject(indivRes.data.individuals, 'individual');
                    this.setSubject(nestRes.data.nests, 'nest');
                    var allObservations = indivRes.data.individuals.concat(nestRes.data.nests);
                    this.parseDates(allObservations);
                    this.setCrossFilter(allObservations);
                    this.totalObsCount = allObservations.length;
                    this.initTimerangeSlider();
                    this.setObservations();

              }))
                .catch(function (error) {
                    console.log(error);
                });
        },

        setSubject: function (observations, subj) {
            observations.forEach(obs => obs.subject = subj);
        },

        initTimerangeSlider: function () {
            var earliestObs = this.cfDimensions.timeDim.bottom(1);
            console.log(earliestObs);
            var start = earliestObs[0].observation_time;
            var stop = new Date().valueOf();
            if (start === stop) {
                stop++;
            }
            this.timeRange = {start: start, stop: stop};
        },

        parseDates: function (observations) {
            observations.forEach(obs => obs.observation_time = moment(obs.observation_time).valueOf())
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
        if (this.loadData === '1') {
            this.getData();
        }
    },

    props: ['zone', 'loadData', 'editRedirect', 'type'],
    watch: {
        loadData: function (n, o) {
            if (n === '1') {
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
        <div>
            <vw-observations-viz-map :observations="observations" :edit-redirect="editRedirect" :zone-id="zone" :type="type"></vw-observations-viz-map>
            <vw-observations-viz-time-slider v-on:time-updated="filterOnTimeRange" :observations-time-range="timeRange"></vw-observations-viz-time-slider>
        </div>
        `
};

/// Component for the create/edit/delete Management Action modal
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
            duration: '',  // In seconds

            deleteConfirmation: false  // The user has asked to delete, we're asking confirmation (instead of the usual form)
        }
    },
    props: {
        mode: String, // 'add' or 'edit'
        nestId: Number, //the Nest ID for this action (!! also needed when editing)
        actionId: Number // If mode === 'edit': the ManagementAction ID
    },
    computed: {
        durationInMinutes: {
            get: function () {
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
            return this.mode === 'add' ? gettext('New management action') : gettext('Edit management action')
        },
        outcomeLabel: function () {
            return gettext('Outcome')
        },
        saveLabel: function () {
            return gettext('Save')
        },
        cancelLabel: function () {
            return gettext('Cancel')
        },
        deleteLabel: function () {
            return gettext('Delete')
        },
        yesDeleteLabel: function () {
            return gettext('Yes, delete')
        },
        nameLabel: function () {
            return gettext('Person name')
        },
        actionTimeLabel: function () {
            return gettext('Action time')
        },
        durationLabel: function () {
            return gettext('Duration')
        },
        inMinutesLabel: function () {
            return gettext('in minutes')
        },
        errorsLabel: function () {
            return gettext('Errors')
        },
        areYouSureStr: function () {
            return gettext('Are you sure you want to delete this action?')
        }
    },
    methods: {
        populateFromServer: function () {
            axios.get(this.loadActionUrl, {params: {'action_id': this.actionId}})
                .then(response => {
                    console.log('Received response', response);
                    this.actionTime = response.data.action_time;
                    this.outcome = response.data.outcome;
                    this.duration = response.data.duration;
                    this.personName = response.data.person_name;
                })
        },
        deleteAction: function () {
            var vm = this;
            axios.delete(this.deleteActionUrl, {params: {'action_id': this.actionId}})
                .then(response => {
                    if (response.data.result === 'OK') {
                        vm.$emit('close', true);
                    }
                }, error => {
                    console.log('Error');
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
                    console.log(error);
                });
        }
    },
    mounted: function () {
        // We load the "outcomes" list, and we're in edit mode, we populate the form from the server
        this.loadOutcomes().then(() => {
            if (this.mode === 'edit') {
                this.populateFromServer()
            }
        });
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
                
                <div v-if="deleteConfirmation">
                    <div class="modal-body">{{ areYouSureStr }}</div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-dark" @click="deleteConfirmation=false">{{ cancelLabel }}</button>
                        <button type="button" @click="deleteAction()" class="btn btn-danger">{{ yesDeleteLabel }}</button>
                    </div>
                </div>
                <div v-else>
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
                                <label for="outcome">{{ outcomeLabel }}*</label>
                                <select v-model="outcome" class="form-control" id="outcome">
                                    <option :value="outcome.value" v-for="outcome in availabeOutcomes">{{ outcome.label }}</option>
                                </select>
                                <label for="personName">{{ nameLabel }}</label>
                                <input v-model="personName" class="form-control" type="text" id="personName">
                                
                                <datetime v-model="actionTime" type="datetime" 
                                    input-class="datetimeinput form-control">
                                    <label for="startDate" slot="before">{{ actionTimeLabel }}*</label>          
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
                        <button v-if="mode === 'edit'" type="button" @click="deleteConfirmation=true" class="btn btn-danger">{{ deleteLabel }}</button>
                    </div>
                </div>
            </div>
        </div>

        </div>
      </div>
    </transition>`
};

// A row in the management table that displays the
// information of a single nest.
var VwManagementTableNestRow = {
    components: {
        'vw-management-action-modal': VwManagementActionModal
    },
    computed: {
        hasManagementAction: function () {
            // Does this Nest has a management action?
            return (this.nest.action !== '')
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
        editDeleteStr: function () {
            return gettext('edit / delete');
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
                    <button v-on:click="showEditActionModal()" class="btn btn-outline-info btn-sm">{{ editDeleteStr }}</button>
                </span>
                
                <button v-else v-on:click="showNewActionModal()" class="btn btn-outline-info btn-sm">{{ addStr }}</button>
                
                <vw-management-action-modal v-if="editActionModalOpened" v-on:close="hideEditActionModal" mode="edit" :nest-id="nest.id" :action-id="nest.actionId"></vw-management-action-modal>
                <vw-management-action-modal v-if="addActionModalOpened" v-on:close="hideNewActionModal" mode="add" :nest-id="nest.id"></vw-management-action-modal>
            </td>
            
            <td>
                    <span v-if="!nest.originates_in_vespawatch" v-bind:title="cannotEditTitle">{{ cannotEditLabel }}</span>
            </td>
        </tr>
        `
};


// The table on the management page that lists the nests
var VwManagementTable = {
    components: {
        'vw-management-table-nest-row': VwManagementTableNestRow
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
        loadingStr: function () {
            return gettext('Loading...')
        },
        noNestsStr: function () {
            return gettext('No nests yet!')
        },
        nestClass: function () {
            return 'table-danger';
        }
    },
    data: function () {
        return {
            _nests: []
        }
    },
    methods: {
        loadData: function () {
            if (this.zone != null) {
                this.$root.loadNests(this.zone);
            } else {
                this.$root.loadNests();
            }
            this.$emit('data-changed');
        }
    },
    mounted: function () {
        this.loadData();
    },
    props: ['nests', 'zone', 'currentlyLoading'],
    watch: {
        nests: function (n, o) {
            this._nests = n;
        }
    },
    template: `
        <div class="row">
            <span v-if="currentlyLoading">{{ loadingStr }}</span>
            <template v-else>
                <table v-if="nests && nests.length > 0" class="table">
                    <thead>
                        <tr>
                            <th>{{ dateStr }}</th><th>{{ addressStr }}</th><th>{{ managementStr }}</th><th></th>
                        </tr>
                    </thead>

                    <vw-management-table-nest-row v-for="nest in nests" :nest="nest" :key="nest.id" v-on:data-changed="loadData"></vw-management-table-nest-row>
                </table>
                <div v-else>{{ noNestsStr }}</div>
            </template>
    </div>
    `
};


// A row from the "Recent observations" table
var VwRecentObsTableRow = {
    props: ['observation'],
    computed: {
        observationTimeStr: function () {
            return moment(this.observation.observation_time).format('lll');
        },
        observationDetailsUrl: function () {
            return new URL(this.observation.detailsUrl, VWConfig.baseUrl);
        }
    },
    template: `<tr> 
                    <td><a :href="observationDetailsUrl">{{ observation.id }}</a></td>
                    <td>{{ observationTimeStr}}</td>
                    <td>{{ observation.subject }}</td>
                    <td>{{ observation.address }}</td>
               </tr>`
};

// The table of the recent observations on the home page
var VwRecentObsTable = {
    components: {
        'vw-recent-obs-table-row': VwRecentObsTableRow
    },
    data: function () {
        return {
            'currentlyLoading': false,
            'limit': 10,
            'observations': []
        }
    },
    computed: {
        dateStr: function () {
            return gettext('date');
        },
        addressStr: function () {
            return gettext('address');
        },
        recentObsStr: function () {
            return gettext('Recent observations')
        },
        loadingStr: function () {
            return gettext('Loading...')
        },
        subjectStr: function () {
            return gettext('subject')
        }
    },
    methods: {
        loadObs: function () {
            this.currentlyLoading = true;
            let url = VWConfig.apis.observationsUrl;

            axios.get(url + '?limit=' + this.limit)
                .then(response => {
                    if (response.data.observations) {
                        this.observations = response.data.observations;
                    }
                    this.currentlyLoading = false;
                })
                .catch(function (error) {
                    console.log(error);
                });
        }
    },
    mounted: function () {
        this.loadObs();
    },
    template: `
        <div class="row">
            <div class="col">
                <h2>{{ recentObsStr}}</h2>
                <span v-if="currentlyLoading">{{ loadingStr }}</span>
                <table v-else class="table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>{{ dateStr }}</th>
                            <th>{{ subjectStr}}</th>
                            <th>{{ addressStr }}</th>
                        </tr>
                    </thead>

                    <vw-recent-obs-table-row v-for="observation in observations" :observation="observation" :key="observation.key"></vw-recent-obs-table-row>
                </table>
            </div>
        </div>`
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
            this.$emit('marker-move', [this.marker.getLatLng().lng, this.marker.getLatLng().lat]);
        },
        setMarker: function (lat, lng) {
            console.log('Setting marker');
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
        this.map = L.map('vw-location-selector-map-map').setView(this.leafletPosition, this.mapZoom);
        L.tileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png').addTo(this.map);
        if (this.initMarker === 'true') {
            console.log('Init with a marker');
            this.setMarker(this.position[0], this.position[1]);
            this.map.setZoom(16);
            this.map.panTo(new L.LatLng(this.position[1], this.position[0]));
        } else {
            console.log('Don\'t add a marker');
        }
    },
    props: ['position', 'initMarker'],
    template: '<div class="mb-2" id="vw-location-selector-map-map" style="height: 300px;"></div>',
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

var VwLocationSelectorInput = {
    data: function () {
        return {
            input_location: null
        };
    },
    computed: {
        lat: function () {
            return this.latitude
        },
        long: function () {
            return this.longitude
        },
        searchLabel: function () {
            return gettext('Search');
        },
        addressHelpLabel: function () {
            return gettext('Type the address and move the maker on the map to where you observed the nest/individual');
        },
        addressIsInvalid: function () {
            return this.latitudeIsInvalid || this.longitudeIsInvalid;
        },
        addressErrorMessage: function () {
            if (this.addressIsInvalid) {
                return gettext('This field is required.');
            }
        },
        searchPositionLabel: function () {
            return gettext('type a location...')
        },
        _location: {
            get: function () {
                return this.input_location || this.location;
            },
            set: function (x) {
                this.input_location = x;
            }
        }

    },
    methods: {
        blockLocationDetection: function () {
            if (!this.detectionBlocked) {
                this.detectionBlocked = true;
                this.$emit('block-location-detection');
            }
        },
        commonInputClasses: function () {
            return ['form-control'];
        },
        addressInputClasses: function() {
            var cssClasses =  this.commonInputClasses();
            if (this.addressIsInvalid === true) {
                cssClasses.push('is-invalid');
            }
            return cssClasses.join(' ');
        },
        search: function () {
            this.$emit('search', this._location);
        },
    },
    props: ['detectionBlocked', 'longitude', 'latitude', 'location', 'latitudeIsInvalid', 'longitudeIsInvalid'],
    watch: {
        location: function (n, o) {
            this._location = n;
        }
    },
    template: `
        <div>
            <div class="form-row">
                <input type="hidden" id="id_latitude" name="latitude" v-model="lat">
                <input type="hidden" id="id_longitude" name="longitude" v-model="long">
                <div class="form-group col-12">
                    <div class="input-group">
                        <input type="text" :class="addressInputClasses()" id="id_location" name="location" v-model="_location" :placeholder="searchPositionLabel" v-on:input="blockLocationDetection">
                        <div class="input-group-append">
                            <button class="btn btn-secondary" v-on:click.stop.prevent="search" >{{ searchLabel }}</button>
                        </div>
                        <p v-if="addressIsInvalid" class="invalid-feedback"><strong>{{addressErrorMessage}}</strong></p>
                    </div>
                    <small class="form-text text-muted">{{addressHelpLabel}}</small>
                </div>
            </div>
        </div>
        `
};

var VwLocationSelectorCoordinates = {
    computed: {
        latitudeLabel: function () {
            return gettext('Latitude');
        },
        longitudeLabel: function () {
            return gettext('Longitude');
        },
    },
    methods: {
        roundCoordinate: function (nr) {
            if (nr) {
                return Math.round(nr * 100000) / 100000;
            }
            return 0;
        }
    },
    props: ['longitude', 'latitude'],
    template: `
        <small>{{longitudeLabel}}: {{roundCoordinate(longitude)}} \ {{latitudeLabel}}: {{roundCoordinate(latitude)}}</small>
`
};

var VwDatetimeSelector = {
    props: {
        'initDateTime': String,
        'isRequired': Boolean,
        'hiddenFieldName': String,
        'validationError': Boolean
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
        nowIsoFormat: function () {
            return new Date().toISOString();
        },
        errorMessages: function () {
            return (this.$root.formErrorMessages && this.$root.formErrorMessages.hasOwnProperty('observation_time')) ? this.$root.formErrorMessages.observation_time.map(x => gettext(x.message)) : [];
        },
        errorClasses: function () {
            var cssClasses =  ['datetimeinput', 'form-control'];
            if (this.validationError) {
                cssClasses.push('is-invalid');
            }
            return cssClasses.join(' ');
        }
    },

    mounted: function () {
        if (this.initDateTime) {
            this.observationTime = this.initDateTime;
        }
    },
    template: `<div class="form-group">
                    <datetime v-model="observationTime" type="datetime" :max-datetime="nowIsoFormat" :input-class="errorClasses">
                        <label for="startDate" slot="before">{{ observationTimeLabel }}<span v-if="isRequired">*</span></label>
                        <p slot="after" v-for="error in errorMessages" class="invalid-feedback">
                            <strong>{{ error }}</strong>
                        </p>
                    </datetime>
                    <input type="hidden" :name="hiddenFieldName" :value="observationTime"/>
               </div>`
};

var VwImageDropZone = {
    components: {
        vueDropzone: vue2Dropzone
      },
    computed: {
        url: function () {
            return this.urls[this.type];
        },
        dropzoneOptions: function () {
            // See https://www.dropzonejs.com/#configuration-options
            return {
                addRemoveLinks: true,
                params: {'csrfmiddlewaretoken': this.csrfToken},
                url: this.url,
                paramName: 'image',
                thumbnailWidth: 150,
                maxFiles: 3,
                maxFilesize: 5, // MB
                dictDefaultMessage: gettext('Drop up to 3 photos here to upload')
            }
        },
        errorMessage: function () {
            return gettext('This field is required.');
        },
        errorClasses: function () {
            if (this.validationError) {
                return 'form-control is-invalid';
            }
        }
    },
    data: function () {
        return {
            imageFieldElement: null,
            uploadedImages: {},
            urls: {'nest': '/api/nest_pictures/', 'individual': '/api/individual_pictures/'},
        }
    },
    props: ['csrfToken', 'type', 'validationError'],
    methods: {
        addToForm: function (file, response) {
            var imgId = response.imageId;
            this.uploadedImages[response.name] = imgId;
            var oldVal = this.imageFieldElement.val();  // pity: I have to fall back to jQuery here, otherwise the entire form should go into a Vue component
            this.imageFieldElement.val(oldVal + "," + imgId);

        },
        removeFromForm: function (file, error, xhr) {
            // Make sure to remove the image from the form when the user deletes it from the dropzone
            var imgId = this.uploadedImages[file.name];
            var oldVal = this.imageFieldElement.val();
            var newIdList = oldVal.split(',').filter(x => x !== "").filter(x => parseInt(x) !== imgId);
            this.imageFieldElement.val(newIdList.join(","));
            delete this.uploadedImages[file.name];

        },
        showError: function (file, message, xhr) {
            if (message.hasOwnProperty('errors')) {
                if (message.errors.hasOwnProperty('image')) {
                    $(file.previewElement).find(".dz-error-message span").text( message.errors.image[0] )
                }
            }
        }
    },
    mounted: function () {
        this.imageFieldElement = $('#id_image_ids');
        var el = this;
        var preloadImageObj = this.imageFieldElement.val();  // pity: I have to fall back to jQuery here, otherwise the entire form should go into a Vue component
        if (preloadImageObj != null) {
            var preloadImageIds = preloadImageObj.split(',').filter(x => x !== '').map(x => parseInt(x));  // remove empty elements from the list and parse integers
            console.log(preloadImageIds);
            preloadImageIds.forEach(function (x) {
                // For every image url, get the image (meta)data from the API
                axios.get(el.url + x)
                    .then(response => {
                        var file = {size: 123, name: response.data.name, type: 'image/png'};
                        var sep = VWConfig.staticRoot[VWConfig.staticRoot.length - 1] === '/' ? '' : '/';
                        var path;
                        if (response.data.url[0] === '/') {
                            path = response.data.url.slice(1, response.data.url.length - 1);
                        } else {
                            path = response.data.url;
                        }
                        var url = VWConfig.staticRoot + sep + path;
                        // Use the image data to preload images in the dropzone element
                        el.$refs.myVueDropzone.manuallyAddFile(file, url);
                        el.uploadedImages[file.name] = x;
                    });
            });
        }
    },
    template: `
        <div>
            <vue-dropzone :class="errorClasses" ref="myVueDropzone" id="dropzone" :options="dropzoneOptions" v-on:vdropzone-success="addToForm" v-on:vdropzone-removed-file="removeFromForm" v-on:vdropzone-error="showError"></vue-dropzone>
            <p v-if="validationError" class="invalid-feedback">
                <strong>{{ errorMessage }}</strong>
            </p>
        </div>`

};

var VwLocationSelector = {
    data: function () {
        return {
            locationCoordinates: [this.initCoordinates[0], this.initCoordinates[1]],  // the coordinates that will be passed to the long lat fields
            locationDetectionBlocked: false,
            geolocationFailed: false,
            geolocationRunning: true,
            markerCoordinates: this.initCoordinates[0] ? [this.initCoordinates[0], this.initCoordinates[1]] : [4.5, 50.7],  // the coordinates that will be passed to the map
            modelAddress: this.location ? '' + this.location : '',
            provider: new GeoSearch.OpenStreetMapProvider({
                params: {
                    countrycodes: 'BE'
                }
            })
        }
    },
    computed: {
        locationLng: function () {
            return this.locationCoordinates ? this.locationCoordinates[0] : null;
        },
        locationLat: function () {
            return this.locationCoordinates ? this.locationCoordinates[1] : null;
        }
    },
    components: {
        'vw-location-selector-map': VwLocationSelectorMap,
        'vw-location-selector-coordinates': VwLocationSelectorCoordinates,
        'vw-location-selector-input': VwLocationSelectorInput
    },

    methods: {
        autodetectPosition: function () {
            var that = this;
            if ("geolocation" in navigator) {
                /* geolocation is available */
                navigator.geolocation.getCurrentPosition(function (position) {
                    if (that.locationDetectionBlocked) {
                        return;
                    }
                    that.geolocationRunning = false;
                    that.setCoordinates([position.coords.longitude, position.coords.latitude]);
                    that.markerCoordinates = [position.coords.longitude, position.coords.latitude];
                    that.reverseGeocode();
                },
                    function () {
                    that.geolocationFailed = true;
                    that.geolocationRunning = false;
                });
            } else {
                /* geolocation IS NOT available */
                that.geolocationFailed = true;
            }

        },
        blockLocationDetection: function () {
            this.locationDetectionBlocked = true;
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
            axios.get('https://nominatim.openstreetmap.org/reverse', {
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
        },
    },
    mounted: function () {
        if (this.locationLng !== "") {
            this.locationDetectionBlocked = true;
        } else {
            this.autodetectPosition();

        }
    },

    props: ['location', 'initCoordinates', 'initMarker', 'latitudeIsInvalid', 'longitudeIsInvalid'],

    template: `
        <div class="row">
            <div class="col-lg-12">
                <vw-location-selector-input 
                v-on:search="getCoordinates"
                v-on:block-location-detection="blockLocationDetection"
                detection-blocked="true"
                v-bind:longitude="locationLng" v-bind:latitude="locationLat" v-bind:location="modelAddress"
                v-bind:latitude-is-invalid="latitudeIsInvalid" v-bind:longitude-is-invalid="longitudeIsInvalid">
                </vw-location-selector-input>
                <vw-location-selector-map v-bind:init-marker="initMarker" v-bind:position="markerCoordinates" v-on:marker-move="setCoordinates"></vw-location-selector-map>
                <vw-location-selector-coordinates :longitude="locationLng" :latitude="locationLat"></vw-location-selector-coordinates>
            </div>
        </div>
        `
};

var app = new Vue({
    components: {
        'vw-observations-viz': VwObservationsViz,
        'vw-location-selector': VwLocationSelector,
        'vw-datetime-selector': VwDatetimeSelector,
        'vw-management-table': VwManagementTable,
        'vw-recent-obs-table': VwRecentObsTable,
        'vw-image-dropzone': VwImageDropZone
    },
    computed: {
        formErrorMessages: function () {
            return formErrorMessagesRaw ? JSON.parse(this.htmlDecode(formErrorMessagesRaw)) : null;
        }
    },
    data: function () {
        return {
            individuals: null,
            nests: null,
            currentlyLoading: false
        };
    },
    delimiters: ['[[', ']]'],
    el: '#vw-main-app',
    methods: {
        htmlDecode: function (input) {
            // from https://stackoverflow.com/a/34064434/1805725
            var doc = new DOMParser().parseFromString(input, 'text/html');
            return doc.documentElement.textContent;
        },
        loadNests: function (zone) {
            this.$refs.viz.getData();  // call getData on the ObservationViz component
            this.currentlyLoading = true;
            this.nests = [];
            let url = VWConfig.apis.observationsUrl + '?type=nest';
            if (zone != null) {
                url = url + '&zone=' + zone;
            }
            axios.get(url)
                .then(response => {
                    if (response.data.observations) {
                        this.nests = response.data.observations;
                        this.$emit('nests updated', 1);
                    }
                    this.currentlyLoading = false;
                })
                .catch(function (error) {
                    console.log(error);
                });

        }
    }
});
