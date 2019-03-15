$('.theme-card-deck div.card').each(function (index, value) {
    var card = $(this);
    var id = card.attr('id').split('-')[2];
    var obj = card.find('.card-text span.badge').text().toLowerCase();
    $.getJSON('/api/' + obj + 's/' + id)
        .done(function (r) {
            if (r.thumbnails && r.thumbnails.length > 0 && r.thumbnails[0]) {
                card.find('img.card-img-top').attr('src', r.thumbnails[0]);
            }
        });
    }
);