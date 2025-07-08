console.log('CEEC Pulse Dashboard loaded');

let artistsChart;
let tracksChart;
let outletChart;
let salesChart;

function createOrUpdateChart(chart, ctx, type, data, options) {
    if (chart) {
        chart.data = data;
        chart.options = options;
        chart.update();
        return chart;
    }
    return new Chart(ctx, { type, data, options });
}

function updateCharts(rows) {
    if (!rows || rows.length === 0) {
        return;
    }

    function aggregate(key) {
        const result = {};
        rows.forEach(r => {
            const k = r[key] || 'N/A';
            const u = parseFloat(r['Units']) || 0;
            result[k] = (result[k] || 0) + u;
        });
        return result;
    }

    function topEntries(obj, limit) {
        return Object.entries(obj)
            .sort((a, b) => b[1] - a[1])
            .slice(0, limit);
    }

    const artistData = topEntries(aggregate('Artist'), 10);
    const trackData = topEntries(aggregate('Tracktitle'), 10);
    const outletData = topEntries(aggregate('Outletname'), Object.keys(aggregate('Outletname')).length);

    const dateMap = {};
    rows.forEach(r => {
        const d = (r['Sales Period'] || '').substring(0, 10);
        const u = parseFloat(r['Units']) || 0;
        if (d) {
            dateMap[d] = (dateMap[d] || 0) + u;
        }
    });
    const dateData = Object.entries(dateMap).sort((a, b) => new Date(a[0]) - new Date(b[0]));

    artistsChart = createOrUpdateChart(
        artistsChart,
        document.getElementById('artists-chart').getContext('2d'),
        'bar',
        {
            labels: artistData.map(a => a[0]),
            datasets: [{ label: 'Units', data: artistData.map(a => a[1]), backgroundColor: 'rgba(75,192,192,0.6)' }]
        },
        { plugins: { legend: { display: false } }, responsive: true }
    );

    tracksChart = createOrUpdateChart(
        tracksChart,
        document.getElementById('tracks-chart').getContext('2d'),
        'bar',
        {
            labels: trackData.map(a => a[0]),
            datasets: [{ label: 'Units', data: trackData.map(a => a[1]), backgroundColor: 'rgba(54,162,235,0.6)' }]
        },
        { plugins: { legend: { display: false } }, responsive: true }
    );

    const pieColors = outletData.map((_, i) => `hsl(${i * 30}, 70%, 60%)`);
    outletChart = createOrUpdateChart(
        outletChart,
        document.getElementById('outlet-chart').getContext('2d'),
        'pie',
        {
            labels: outletData.map(a => a[0]),
            datasets: [{ data: outletData.map(a => a[1]), backgroundColor: pieColors }]
        },
        { responsive: true }
    );

    salesChart = createOrUpdateChart(
        salesChart,
        document.getElementById('sales-chart').getContext('2d'),
        'line',
        {
            labels: dateData.map(d => d[0]),
            datasets: [{
                label: 'Units',
                data: dateData.map(d => d[1]),
                borderColor: 'rgba(255,99,132,0.8)',
                backgroundColor: 'rgba(255,99,132,0.4)',
                fill: false
            }]
        },
        { responsive: true }
    );
}

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
        updateCharts(res.data);
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

    if (typeof window.parsedFile !== 'undefined') {
        fetchFiltered();
    }

    $('#lang-select').on('change', function() {
        const url = new URL(window.location.href);
        url.searchParams.set('lang', $(this).val());
        window.location.href = url.toString();
    });

    $('#theme-toggle').on('click', function() {
        $('body').toggleClass('dark');
        localStorage.setItem('theme', $('body').hasClass('dark') ? 'dark' : 'light');
    });

    if (localStorage.getItem('theme') === 'dark') {
        $('body').addClass('dark');
    }
});
