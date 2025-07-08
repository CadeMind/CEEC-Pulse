console.log('CEEC Pulse Dashboard loaded');

function fetchFiltered() {
    if (typeof window.parsedFile === 'undefined') {
        return;
    }
    const params = {
        artist: $('#artist-filter').val(),
        outlet: $('#outlet-filter').val(),
        start_date: $('#start-date').val(),
        end_date: $('#end-date').val(),
        units_min: $('#units-min').val(),
        units_max: $('#units-max').val(),
        royalty_min: $('#royalty-min').val(),
        royalty_max: $('#royalty-max').val()
    };
    $.getJSON(`/filter_data/${window.parsedFile}`, params, function(res) {
        const tbody = $('#data-table tbody');
        tbody.empty();
        res.data.forEach(row => {
            const tr = $('<tr>');
            Object.values(row).forEach(v => {
                tr.append($('<td>').text(v));
            });
            tbody.append(tr);
        });
        $('#summary').text(res.summary);
    });
}

$(function() {
    $('#artist-filter, #outlet-filter, #start-date, #end-date, #units-min, #units-max, #royalty-min, #royalty-max').on('change', fetchFiltered);

    $('#reset-filters').on('click', function() {
        $('#artist-filter').val('all');
        $('#outlet-filter').val('all');
        $('#start-date').val('');
        $('#end-date').val('');
        if ($('#units-min').length) {
            $('#units-min').val($('#units-min').attr('min'));
            $('#units-max').val($('#units-max').attr('max'));
        }
        if ($('#royalty-min').length) {
            $('#royalty-min').val($('#royalty-min').attr('min'));
            $('#royalty-max').val($('#royalty-max').attr('max'));
        }
        fetchFiltered();
    });
});
