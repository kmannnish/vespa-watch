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
            this.observations.forEach(obs => {
                var color = 'orange';
                var circle = L.circleMarker([obs.latitude, obs.longitude], {
                    stroke: true,  // whether to draw a stroke
                    weight: 1, // stroke width in pixels
                    color: color,  // stroke color
                    opacity: 0.8,  // stroke opacity
                    fillColor: color,
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
            var mapPosition = [50.5, 4.5];
            var mapZoom = 8;
            this.map = L.map("vw-map-map")
                .setView(mapPosition, mapZoom);
            var CartoDB_Positron = L.tileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
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

    template: '<div id="vw-map-map" style="height: 750px"></div>'
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
            return moment(this.selectedTimeRange.start).format('lll');
        },
        stopStr: function () {
            return moment(this.selectedTimeRange.stop).format('lll');
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
    template: '<div> <div id="vw-time-slider"></div> <span id="vw-time-start">{{ startStr }}</span> - <span id="vw-time-stop">{{ stopStr }}</span></div>'
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
            this.timeRange = {start: earliestObs[0].observation_time, stop: latestObs[0].observation_time};
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

    template: '<div> <vw-observations-viz-time-slider v-on:time-updated="filterOnTimeRange" v-model="timeRange"></vw-observations-viz-time-slider> <vw-observations-viz-map v-bind:observations="observations"></vw-observations-viz-map> </div>'

};

var app = new Vue({
    components: {
        'vw-observations-viz': VwObservationsViz
    },
    delimiters: ['[[', ']]'],
    el: '#vw-main-app'
});