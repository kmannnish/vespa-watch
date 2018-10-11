var dateslider = function (el, start, end, callback) {
    noUiSlider.create(el, {
    // Create two timestamps to define a range.
        range: {
            min: start,
            max: end
        },

    // Steps of one week
        step: 7 * 24 * 60 * 60 * 1000,

    // Two more timestamps indicate the handle starting positions.
        start: [start, end],

    // No decimals
        format: wNumb({
            decimals: 0
        })
    });

    var dateValues = [
        document.getElementById('range-start'),
        document.getElementById('range-end')
    ];

    dateValues[0].innerHTML = moment(start).format('lll');
    dateValues[1].innerHTML = moment(end).format('lll');

    el.noUiSlider.on('set', function (values, handle) {
        dateValues[handle].innerHTML = moment(+values[handle]).format('lll');
        callback(values[0], values[1]);
    });

};





