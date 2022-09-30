odoo.define('crm_dashboard.custom', function (require) {
    'use strict';

    var rpc = require('web.rpc');
    var manager = false;
    rpc.query({
        model: "crm.lead",
        method: "check_user_group",
    })
    .then(function (res) {
        manager = res;
    });

    $(document).on("mouseenter", ".dashboard_main_section", function(event){
        var percentage_crm_month = $('#percentage_crm-month').val();
        var gauge_month = new Gauge(document.getElementById("gauge-month"));
        gauge_month.value(percentage_crm_month);

        var percentage_crm_quarter = $('#percentage_crm-quarter').val();
        var gauge_quarter = new Gauge(document.getElementById("gauge-quarter"));
        gauge_quarter.value(percentage_crm_quarter);

        var percentage_crm_year = $('#percentage_crm-year').val();
        var gauge_year = new Gauge(document.getElementById("gauge-year"));
        gauge_year.value(percentage_crm_year);

        $('#country_revenue_table').columnHeatmap({
            columns: [1],
            inverse:true,
        });
        $('#country_count_table').columnHeatmap({
            columns: [1],
            inverse:true,
        });
        // if (manager) {
        //     $('#salesperson_revenue_table').columnHeatmap({
        //         columns: [1],
        //         inverse:true,
        //     });
        // }
    });
});