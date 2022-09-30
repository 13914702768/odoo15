odoo.define('crm_dashboard.CRMDashboard', function (require) {
    'use strict';

    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var web_client = require('web.web_client');
    var session = require('web.session');
    var _t = core._t;
    var QWeb = core.qweb;
    var self = this;
    var currency;

    var DashBoard = AbstractAction.extend({
        contentTemplate: 'CRMdashboard',
        events: {
            'change #search_city_ranking_user': 'render_search_city_ranking_user',
            'change #search_city_ranking_team': 'change_city_ranking_team',
            'change #search_sales_revenue_type': 'render_revenue_count_pie',
            'change #search_revenue_user': 'render_revenue_count_pie',
            'change #search_sales_revenue_team': 'render_sales_revenue_user',
            'change #search_sales_performance_type': 'render_sales_performance_chart_graph',
            'change #search_sales_performance_team': 'render_sales_performance_chart_graph',
            'change #monthly_goal_choose': 'change_monthly_goal',
            'change #quarter_goal_choose': 'change_quarter_goal',
            'change #year_goal_choose': 'change_year_goal',
            'click .activity': 'my_activity',
            'change #search_user': 'change_user',
            'click .customer': 'my_customer',
            'click .my_lead': 'my_lead',
            'click .opportunity': 'opportunity',
            'click .unassigned_leads': 'unassigned_leads',
            'click .exp_revenue': 'exp_revenue',
            'click .revenue_card': 'revenue_card',
            'change #income_expense_values': function (e) {
                e.stopPropagation();
                var $target = $(e.target);
                var value = $target.val();
                if (value == "this_year") {
                    this.onclick_this_year($target.val());
                } else if (value == "this_quarter") {
                    this.onclick_this_quarter($target.val());
                } else if (value == "this_month") {
                    this.onclick_this_month($target.val());
                } else if (value == "this_week") {
                    this.onclick_this_week($target.val());
                } else if (value == "this_all") {
                    this.onclick_this_all($target.val());
                }
            },
        },

        init: function (parent, context) {
            this._super(parent, context);
            this.upcoming_events = [];
            this.dashboards_templates = ['LoginUser', 'Managercrm', 'Admincrm'];
            this.login_employee = [];
        },

        willStart: function () {
            var self = this;
            this.login_employee = {};
            return this._super()
                .then(function () {

                    var def0 = self._rpc({
                        model: 'crm.lead',
                        method: 'check_user_group'
                    }).then(function (result) {
                        if (result == true) {
                            self.is_manager = 1;
                        } else {
                            self.is_manager = 3;
                            self._rpc({
                                model: 'crm.lead',
                                method: 'check_user_group_team'
                            }).then(function (result) {
                                if (result == true) {
                                    self.is_manager = 2;
                                }
                            });
                        }
                    });

                    var def1 = self._rpc({
                        model: "crm.lead",
                        method: "get_upcoming_events",
                    })
                        .then(function (res) {
                            self.upcoming_events = res['event'];
                        });

                    var def2 = self._rpc({
                        model: "crm.lead",
                        method: "get_top_deals",
                    })
                        .then(function (res) {
                            self.top_deals = res['deals'];
                        });

                    var def3 = self._rpc({
                        model: "crm.lead",
                        method: "get_monthly_goal",
                    })
                        .then(function (res) {
                            self.monthly_goals = res['goals'];
                        });

                    var def5 = self._rpc({
                        model: "crm.lead",
                        method: "get_country_revenue",
                    })
                        .then(function (res) {
                            self.top_country_revenue = res['country_revenue'];
                        });

                    var def6 = self._rpc({
                        model: "crm.lead",
                        method: "get_country_count",
                    })
                        .then(function (res) {
                            self.top_country_count = res['country_count'];
                        });

                    var def7 = self._rpc({
                        model: "crm.lead",
                        method: "get_city_revenue",
                        args: ['0', '0']
                    })
                    .then(function (res) {
                        self.top_city_revenue = res['city_revenue'];
                    });

                    var def8 = self._rpc({
                        model: "crm.lead",
                        method: "get_ratio_based_country",
                    })
                        .then(function (res) {
                            self.top_country_wise_ratio = res['country_wise_ratio'];
                        });

                    var def9 = self._rpc({
                        model: "crm.lead",
                        method: "get_ratio_based_sp",
                    })
                        .then(function (res) {
                            self.top_salesperson_wise_ratio = res['salesperson_wise_ratio'];
                        });

                    var def10 = self._rpc({
                        model: "crm.lead",
                        method: "get_ratio_based_sales_team",
                    })
                        .then(function (res) {
                            self.top_sales_team_wise_ratio = res['sales_team_wise_ratio'];
                        });

                    var def12 = self._rpc({
                        model: "crm.lead",
                        method: "get_count_unassigned",
                    })
                        .then(function (res) {
                            self.get_count_unassigned = res['count_unassigned'];
                        });

                    var def14 = self._rpc({
                        model: "crm.lead",
                        method: "get_user_list",
                        args: ["0"],
                    }).then(function (res) {
                        self.team_users = res['team_users'];
                        self.teams = res['teams'];
                        self.current_time = res['current_time'];
                    });

                    var def15 = self._rpc({
                        model: "crm.lead",
                        method: "get_goal_time_list",
                    })
                        .then(function (res) {
                            self.month_times = res['month_times'];
                            self.quarter_times = res['quarter_times'];
                            self.year_times = res['year_times'];
                        });

                    var def16 = self._rpc({
                        model: "crm.lead",
                        method: "get_quarter_goal",
                    })
                        .then(function (res) {
                            self.quarter_goals = res['quarter_goals'];
                        });

                    var def17 = self._rpc({
                        model: "crm.lead",
                        method: "get_year_goal",
                    })
                        .then(function (res) {
                            self.year_goals = res['quarter_goals'];
                        });

                    return $.when(def0, def1, def2, def3, def5, def6, def7, def8, def9, def10, def12, def14, def15, def16, def17);
                });
        },

        change_monthly_goal: function (ev) {
            var self = this;
            var month = $('#monthly_goal_choose').val();
            var user_id = $('#search_user').val()
            rpc.query({
                model: 'crm.lead',
                method: 'search_monthly_goal',
                args: [month, user_id],
            })
                .then(function (result) {
                    self.monthly_goals = result.goals
                    $("#percentage_crm-month").val(result.goals[3])
                    var html = "<span class='gauge__label--low'>"
                        + "<b>" + result.goals[2] + result.goals[0] + "</b></span>"
                        + "<span class='gauge__label--spacer'/>"
                        + "<span class='gauge__label--high'>"
                        + "<b>" + result.goals[2] + result.goals[1] + "</b></span>"
                    $(".mdl-typography__headline-month").html(html)

                })
        },

        change_quarter_goal: function (ev) {
            var self = this;
            var quarter = $("#quarter_goal_choose").val();
            var user_id = $('#search_user').val()
            rpc.query({
                model: 'crm.lead',
                method: 'search_quarter_goal',
                args: [quarter, user_id],
            })
                .then(function (result) {
                    self.quarter_goals = result.goals

                    $("#percentage_crm-quarter").val(result.goals[3])
                    var html = "<span class='gauge__label--low'>"
                        + "<b>" + result.goals[2] + result.goals[0] + "</b></span>"
                        + "<span class='gauge__label--spacer'/>"
                        + "<span class='gauge__label--high'>"
                        + "<b>" + result.goals[2] + result.goals[1] + "</b></span>"
                    $(".mdl-typography__headline-quarter").html(html)

                })
        },

        change_year_goal: function (ev) {
            var self = this;
            var year = $("#year_goal_choose").val();
            var user_id = $('#search_user').val()
            rpc.query({
                model: 'crm.lead',
                method: 'search_year_goal',
                args: [year, user_id],
            })
                .then(function (result) {
                    self.year_goals = result.goals
                    $("#percentage_crm-year").val(result.goals[3])
                    var html = "<span class='gauge__label--low'>"
                        + "<b>" + result.goals[2] + result.goals[0] + "</b></span>"
                        + "<span class='gauge__label--spacer'/>"
                        + "<span class='gauge__label--high'>"
                        + "<b>" + result.goals[2] + result.goals[1] + "</b></span>"
                    $(".mdl-typography__headline-year").html(html)

                })
        },

        change_user: function (ev) {
            var self = this;
            ev.stopPropagation();
            var $target = $(ev.target);
            var user_id = $target.val();
            var income_expense_values = $('#income_expense_values').val()
            if (income_expense_values == "this_year") {
                this.onclick_this_year(income_expense_values);
            } else if (income_expense_values == "this_quarter") {
                this.onclick_this_quarter(income_expense_values);
            } else if (income_expense_values == "this_month") {
                this.onclick_this_month(income_expense_values);
            } else if (income_expense_values == "this_week") {
                this.onclick_this_week(income_expense_values);
            } else if (income_expense_values == "this_all") {
                this.onclick_this_all(income_expense_values);
            }
            this.change_monthly_goal();
            this.change_quarter_goal();
            this.change_year_goal();
            this.render_graphs();
            this.search_upcoming_activity();
        },

        onclick_this_year: function (ev) {
            var self = this;
            var user_id = $('#search_user').val()
            rpc.query({
                model: 'crm.lead',
                method: 'crm_year',
                args: [user_id],
            })
                .then(function (result) {
                    $('#leads_this_all').hide();
                    $('#opp_this_all').hide();
                    $('#exp_rev_this_all').hide();
                    $('#rev_this_all').hide();
                    $('#ratio_this_all').hide();
                    $('#avg_time_this_all').hide();
                    $('#total_revenue_this_all').hide();
                    $('#leads_this_quarter').hide();
                    $('#opp_this_quarter').hide();
                    $('#exp_rev_this_quarter').hide();
                    $('#rev_this_quarter').hide();
                    $('#ratio_this_quarter').hide();
                    $('#avg_time_this_quarter').hide();
                    $('#total_revenue_this_quarter').hide();
                    $('#leads_this_month').hide();
                    $('#opp_this_month').hide();
                    $('#exp_rev_this_month').hide();
                    $('#rev_this_month').hide();
                    $('#ratio_this_month').hide();
                    $('#avg_time_this_month').hide();
                    $('#total_revenue_this_month').hide();
                    $('#leads_this_week').hide();
                    $('#opp_this_week').hide();
                    $('#exp_rev_this_week').hide();
                    $('#rev_this_week').hide();
                    $('#ratio_this_week').hide();
                    $('#avg_time_this_week').hide();
                    $('#total_revenue_this_week').hide();

                    $('#leads_this_year').show();
                    $('#opp_this_year').show();
                    $('#exp_rev_this_year').show();
                    $('#rev_this_year').show();
                    $('#ratio_this_year').show();
                    $('#avg_time_this_year').show();
                    $('#total_revenue_this_year').show();

                    $('#leads_this_year').empty();
                    $('#opp_this_year').empty();
                    $('#exp_rev_this_year').empty();
                    $('#rev_this_year').empty();
                    $('#ratio_this_year').empty();
                    $('#avg_time_this_year').empty();
                    $('#total_revenue_this_year').empty();
                    $('#customer_this_all').empty();

                    $('#leads_this_year').append('<span>' + result.record + '</span>');
                    $('#opp_this_year').append('<span>' + result.record_op + '</span>');
                    $('#exp_rev_this_year').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev_exp + '</span>');
                    $('#rev_this_year').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev + '</span>');
                    $('#ratio_this_year').append('<span>' + result.record_ratio + '</span>');
                    $('#avg_time_this_year').append('<span>' + result.avg_time + '&nbspsec' + '</span>');
                    $('#customer_this_all').append('<span>' + result.customer + '</span>');
                    $('#total_revenue_this_year').append('<span>' + result.opportunity_ratio_value + '</span>');
                })
            this.funnel_chart();
        },

        onclick_this_quarter: function (ev) {
            var self = this;
            var user_id = $('#search_user').val()
            rpc.query({
                model: 'crm.lead',
                method: 'crm_quarter',
                args: [user_id],
            })
                .then(function (result) {
                    $('#leads_this_all').hide();
                    $('#opp_this_all').hide();
                    $('#exp_rev_this_all').hide();
                    $('#rev_this_all').hide();
                    $('#ratio_this_all').hide();
                    $('#avg_time_this_all').hide();
                    $('#total_revenue_this_all').hide();
                    $('#leads_this_year').hide();
                    $('#opp_this_year').hide();
                    $('#exp_rev_this_year').hide();
                    $('#rev_this_year').hide();
                    $('#ratio_this_year').hide();
                    $('#avg_time_this_year').hide();
                    $('#total_revenue_this_year').hide();
                    $('#leads_this_month').hide();
                    $('#opp_this_month').hide();
                    $('#exp_rev_this_month').hide();
                    $('#rev_this_month').hide();
                    $('#ratio_this_month').hide();
                    $('#avg_time_this_month').hide();
                    $('#total_revenue_this_month').hide();
                    $('#leads_this_week').hide();
                    $('#opp_this_week').hide();
                    $('#exp_rev_this_week').hide();
                    $('#rev_this_week').hide();
                    $('#ratio_this_week').hide();
                    $('#avg_time_this_week').hide();
                    $('#total_revenue_this_week').hide();

                    $('#leads_this_quarter').show();
                    $('#opp_this_quarter').show();
                    $('#exp_rev_this_quarter').show();
                    $('#rev_this_quarter').show();
                    $('#ratio_this_quarter').show();
                    $('#avg_time_this_quarter').show();
                    $('#total_revenue_this_quarter').show();

                    $('#leads_this_quarter').empty();
                    $('#opp_this_quarter').empty();
                    $('#exp_rev_this_quarter').empty();
                    $('#rev_this_quarter').empty();
                    $('#ratio_this_quarter').empty();
                    $('#avg_time_this_quarter').empty();
                    $('#total_revenue_this_quarter').empty();
                    $('#customer_this_all').empty();

                    $('#leads_this_quarter').append('<span>' + result.record + '</span>');
                    $('#opp_this_quarter').append('<span>' + result.record_op + '</span>');
                    $('#exp_rev_this_quarter').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev_exp + '</span>');
                    $('#rev_this_quarter').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev + '</span>');
                    $('#ratio_this_quarter').append('<span>' + result.record_ratio + '</span>');
                    $('#avg_time_this_quarter').append('<span>' + result.avg_time + '&nbspsec' + '</span>');
                    $('#customer_this_all').append('<span>' + result.customer + '</span>');
                    $('#total_revenue_this_quarter').append('<span>' + result.opportunity_ratio_value + '</span>');
                })
        },

        onclick_this_month: function (ev) {
            var self = this;
            var user_id = $('#search_user').val()
            rpc.query({
                model: 'crm.lead',
                method: 'crm_month',
                args: [user_id],
            })
                .then(function (result) {
                    $('#leads_this_all').hide();
                    $('#opp_this_all').hide();
                    $('#exp_rev_this_all').hide();
                    $('#rev_this_all').hide();
                    $('#ratio_this_all').hide();
                    $('#avg_time_this_all').hide();
                    $('#total_revenue_this_all').hide();
                    $('#leads_this_year').hide();
                    $('#opp_this_year').hide();
                    $('#exp_rev_this_year').hide();
                    $('#rev_this_year').hide();
                    $('#ratio_this_year').hide();
                    $('#avg_time_this_year').hide();
                    $('#total_revenue_this_year').hide();
                    $('#leads_this_quarter').hide();
                    $('#opp_this_quarter').hide();
                    $('#exp_rev_this_quarter').hide();
                    $('#rev_this_quarter').hide();
                    $('#ratio_this_quarter').hide();
                    $('#avg_time_this_quarter').hide();
                    $('#total_revenue_this_quarter').hide();
                    $('#leads_this_week').hide();
                    $('#opp_this_week').hide();
                    $('#exp_rev_this_week').hide();
                    $('#rev_this_week').hide();
                    $('#ratio_this_week').hide();
                    $('#avg_time_this_week').hide();
                    $('#total_revenue_this_week').hide();

                    $('#leads_this_month').show();
                    $('#opp_this_month').show();
                    $('#exp_rev_this_month').show();
                    $('#rev_this_month').show();
                    $('#ratio_this_month').show();
                    $('#avg_time_this_month').show();
                    $('#total_revenue_this_month').show();

                    $('#leads_this_month').empty();
                    $('#opp_this_month').empty();
                    $('#exp_rev_this_month').empty();
                    $('#rev_this_month').empty();
                    $('#ratio_this_month').empty();
                    $('#avg_time_this_month').empty();
                    $('#total_revenue_this_month').empty();
                    $('#customer_this_all').empty();

                    $('#leads_this_month').append('<span>' + result.record + '</span>');
                    $('#opp_this_month').append('<span>' + result.record_op + '</span>');
                    $('#exp_rev_this_month').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev_exp + '</span>');
                    $('#rev_this_month').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev + '</span>');
                    $('#ratio_this_month').append('<span>' + result.record_ratio + '</span>');
                    $('#avg_time_this_month').append('<span>' + result.avg_time + '&nbspsec' + '</span>');
                    $('#customer_this_all').append('<span>' + result.customer + '</span>');
                    $('#total_revenue_this_month').append('<span>' + result.opportunity_ratio_value + '</span>');
                })
        },

        onclick_this_week: function (ev) {
            var self = this;
            var user_id = $('#search_user').val()
            rpc.query({
                model: 'crm.lead',
                method: 'crm_week',
                args: [user_id],
            })
                .then(function (result) {
                    $('#leads_this_all').hide();
                    $('#opp_this_all').hide();
                    $('#exp_rev_this_all').hide();
                    $('#rev_this_all').hide();
                    $('#ratio_this_all').hide();
                    $('#avg_time_this_all').hide();
                    $('#total_revenue_this_all').hide();
                    $('#leads_this_year').hide();
                    $('#opp_this_year').hide();
                    $('#exp_rev_this_year').hide();
                    $('#rev_this_year').hide();
                    $('#ratio_this_year').hide();
                    $('#avg_time_this_year').hide();
                    $('#total_revenue_this_year').hide();
                    $('#leads_this_quarter').hide();
                    $('#opp_this_quarter').hide();
                    $('#exp_rev_this_quarter').hide();
                    $('#rev_this_quarter').hide();
                    $('#ratio_this_quarter').hide();
                    $('#avg_time_this_quarter').hide();
                    $('#total_revenue_this_quarter').hide();
                    $('#leads_this_month').hide();
                    $('#opp_this_month').hide();
                    $('#exp_rev_this_month').hide();
                    $('#rev_this_month').hide();
                    $('#ratio_this_month').hide();
                    $('#avg_time_this_month').hide();
                    $('#total_revenue_this_month').hide();

                    $('#leads_this_week').show();
                    $('#opp_this_week').show();
                    $('#exp_rev_this_week').show();
                    $('#rev_this_week').show();
                    $('#ratio_this_week').show();
                    $('#avg_time_this_week').show();
                    $('#total_revenue_this_week').show();

                    $('#leads_this_week').empty();
                    $('#opp_this_week').empty();
                    $('#exp_rev_this_week').empty();
                    $('#rev_this_week').empty();
                    $('#ratio_this_week').empty();
                    $('#avg_time_this_week').empty();
                    $('#total_revenue_this_week').empty();
                    $('#customer_this_all').empty();

                    $('#leads_this_week').append('<span>' + result.record + '</span>');
                    $('#opp_this_week').append('<span>' + result.record_op + '</span>');
                    $('#exp_rev_this_week').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev_exp + '</span>');
                    $('#rev_this_week').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev + '</span>');
                    $('#ratio_this_week').append('<span>' + result.record_ratio + '</span>');
                    $('#avg_time_this_week').append('<span>' + result.avg_time + '&nbspsec' + '</span>');
                    $('#customer_this_all').append('<span>' + result.customer + '</span>');
                    $('#total_revenue_this_week').append('<span>' + result.opportunity_ratio_value + '</span>');
                })
        },

        onclick_this_all: function (ev) {
            var self = this;
            var user_id = $('#search_user').val()
            rpc.query({
                model: 'crm.lead',
                method: 'crm_all',
                args: [user_id],
            })
                .then(function (result) {
                    $('#leads_this_week').hide();
                    $('#opp_this_week').hide();
                    $('#exp_rev_this_week').hide();
                    $('#rev_this_week').hide();
                    $('#ratio_this_week').hide();
                    $('#avg_time_this_week').hide();
                    $('#total_revenue_this_week').hide();
                    $('#leads_this_year').hide();
                    $('#opp_this_year').hide();
                    $('#exp_rev_this_year').hide();
                    $('#rev_this_year').hide();
                    $('#ratio_this_year').hide();
                    $('#avg_time_this_year').hide();
                    $('#total_revenue_this_year').hide();
                    $('#leads_this_quarter').hide();
                    $('#opp_this_quarter').hide();
                    $('#exp_rev_this_quarter').hide();
                    $('#rev_this_quarter').hide();
                    $('#ratio_this_quarter').hide();
                    $('#avg_time_this_quarter').hide();
                    $('#total_revenue_this_quarter').hide();
                    $('#leads_this_month').hide();
                    $('#opp_this_month').hide();
                    $('#exp_rev_this_month').hide();
                    $('#rev_this_month').hide();
                    $('#ratio_this_month').hide();
                    $('#avg_time_this_month').hide();
                    $('#total_revenue_this_month').hide();

                    $('#leads_this_all').show();
                    $('#opp_this_all').show();
                    $('#exp_rev_this_all').show();
                    $('#rev_this_all').show();
                    $('#ratio_this_all').show();
                    $('#avg_time_this_all').show();
                    $('#total_revenue_this_all').show();

                    $('#leads_this_all').empty();
                    $('#opp_this_all').empty();
                    $('#exp_rev_this_all').empty();
                    $('#rev_this_all').empty();
                    $('#ratio_this_all').empty();
                    $('#avg_time_this_all').empty();
                    $('#total_revenue_this_all').empty();
                    $('#customer_this_all').empty();

                    $('#leads_this_all').append('<span>' + result.record + '</span>');
                    $('#opp_this_all').append('<span>' + result.record_op + '</span>');
                    $('#exp_rev_this_all').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev_exp + '</span>');
                    $('#rev_this_all').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev + '</span>');
                    $('#ratio_this_all').append('<span>' + result.record_ratio + '</span>');
                    $('#avg_time_this_all').append('<span>' + result.avg_time + '&nbspsec' + '</span>');
                    $('#customer_this_all').append('<span>' + result.customer + '</span>');
                    $('#total_revenue_this_all').append('<span>' + result.opportunity_ratio_value + '</span>');
                })
        },

        renderElement: function (ev) {
            var self = this;
            $.when(this._super())
                .then(function (ev) {
                    rpc.query({
                        model: "crm.lead",
                        method: "lead_details_user",
                        args: [],
                    })
                        .then(function (result) {
                            $('#leads_this_month').append('<span>' + result.record + '</span>');
                            $('#opp_this_month').append('<span>' + result.record_op + '</span>');
                            $('#exp_rev_this_month').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev_exp + '</span>');
                            $('#rev_this_month').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev + '</span>');
                            $('#ratio_this_month').append('<span>' + result.record_ratio + '</span>');
                            $('#avg_time_this_month').append('<span>' + result.avg_time + '&nbspsec' + '</span>');
                            $('#customer_this_all').append('<span>' + result.customer + '</span>');
                            $('#total_revenue_this_month').append('<span>' + result.opportunity_ratio_value + '</span>');
                            $('#target').append('<span>' + result.target + '</span>');
                            $('#ytd_target').append('<span>' + result.ytd_target + '</span>');
                            $('#difference').append('<span>' + result.difference + '</span>');
                            $('#won').append('<span>' + result.won + '</span>');
                        })
                });
        },

        my_activity: function (e) {
            var self = this;
            var $target = $(e.currentTarget);
            e.stopPropagation();
            e.preventDefault();
            var data_id = $target.attr('data-id')
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            // if(self.is_manager == 3){
            //     dmain = [['user_id', '=', session.uid]]
            // }
            this.do_action({
                name: _t("My Activity"),
                type: 'ir.actions.act_window',
                res_model: 'crm.lead',
                view_mode: 'tree',
                view_type: 'tree,form',
                // 499  crm.lead.list.activities  ir_ui_view.ID
                views: [[499, 'list'], [false, 'form']],
                domain: [['id', '=', data_id]],
                target: 'current',
            }, options)
        },

        my_customer: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            var user_id = $('#search_user').val()
            var domain = []
            if (user_id != '0') {
                domain = [['partner_share', '=', true], ['active', '=', true], ['user_id', '=', parseInt(user_id)], ['supplier_rank', '=', 0]]
            } else {
                if (self.is_manager == 1) {
                    domain = [['partner_share', '=', true], ['active', '=', true], ['supplier_rank', '=', 0]]
                } else {
                    domain = [['partner_share', '=', true], ['active', '=', true], ['user_id', '!=', null], ['supplier_rank', '=', 0]]
                }
            }
            this.do_action({
                name: _t("My Customer"),
                type: 'ir.actions.act_window',
                res_model: 'res.partner',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'], [false, 'form']],
                domain: domain,
                target: 'current',
            }, options)
        },

        my_lead: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var user_id = $('#search_user').val()
            var domain = []
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            if (user_id != '0') {
                domain = ['&', '&', ['type', '=', 'lead'], ['active', '=', true], '|', ['user_id', '=', parseInt(user_id)], ['user_id', '=', null]]
            } else {
                domain = [['type', '=', 'lead'], ['active', '=', true]]
            }
            this.do_action({
                name: _t("My Leads"),
                type: 'ir.actions.act_window',
                res_model: 'crm.lead',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'], [false, 'form']],
                domain: domain,
                target: 'current',
            }, options)
        },

        opportunity: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var user_id = $('#search_user').val()
            var domain = []
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            if (user_id != '0') {
                domain = [["type", "=", "opportunity"], ['active', '=', true], ['user_id', '=', parseInt(user_id)]
                    , ["x_lead_status", "in", ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31']]
                    ,["date_deadline", ">", self.current_time]
                ]
            } else {
                domain = [["type", "=", "opportunity"], ['active', '=', true] ,["date_deadline", ">", self.current_time]
                    , ["x_lead_status", "in", ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31']]]
            }
            this.do_action({
                name: _t("Opportunity"),
                type: 'ir.actions.act_window',
                res_model: 'crm.lead',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'], [false, 'form']],
                domain: domain,
                target: 'current',
            }, options)
        },

        exp_revenue: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var user_id = $('#search_user').val()
            var domain = []
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            if (user_id != '0') {
                domain = [["x_lead_status", "in", ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31']],
                    ['user_id', '=', parseInt(user_id)], ['type', '=', 'opportunity'], ['active', '=', true]
                    ,["date_deadline", ">", self.current_time]]
            } else {
                domain = [["x_lead_status", "in", ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31']],
                    ['type', '=', 'opportunity'], ['active', '=', true],["date_deadline", ">", self.current_time]]
            }
            this.do_action({
                name: _t("Expected Revenue"),
                type: 'ir.actions.act_window',
                res_model: 'crm.lead',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'], [false, 'form']],
                domain: domain,
                target: 'current',
            }, options)
        },

        revenue_card: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var user_id = $('#search_user').val()
            var domain = []
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            if (user_id != '0') {
                domain = [['user_id', '=', parseInt(user_id)], ['active', '=', true], ['type', '=', 'opportunity'],
                    ["x_lead_status", "not in", ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31']]]
            } else {
                domain = [['active', '=', true], ['type', '=', 'opportunity'],
                    ["x_lead_status", "not in", ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31']]]
            }
            this.do_action({
                name: _t("Revenue"),
                type: 'ir.actions.act_window',
                res_model: 'crm.lead',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'], [false, 'form']],
                domain: domain,
                target: 'current',
            }, options)
        },

        //unassigned_leads
        unassigned_leads: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Unassigned Leads"),
                type: 'ir.actions.act_window',
                res_model: 'crm.lead',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'], [false, 'form']],
                domain: [['user_id', '=', false], ['type', '=', 'lead']],
                context: {'group_by': 'team_id'},
                target: 'current',
            }, options)
        },

        start: function () {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function () {
                self.update_cp();
                self.render_dashboards();
                self.render_graphs();
                self.$el.parent().addClass('oe_background_grey');
            });
        },

        render_graphs: function () {
            var self = this;
            self.render_sales_activity_graph();
            self.render_leads_month_graph();
            self.funnel_chart();
            self.render_sales_performance_chart_graph();
            self.render_source_leads_graph();
            self.render_lost_leads_graph();
            self.render_lost_leads_by_stage_graph();
            self.render_revenue_count_pie();
        },

        funnel_chart: function () {
            var type = $('#income_expense_values').val()
            if (type == "this_year") {
                type = "2"
            } else if (type == "this_month") {
                type = "1"
            } else if (type == "this_all") {
                type = "0"
            } else {
                type = "0"
            }
            var user_id = $('#search_user').val()
            rpc.query({
                model: "crm.lead",
                method: "get_lead_stage_data",
                args: [user_id, type],
            }).then(function (callbacks) {
                Highcharts.chart("container", {
                    chart: {
                        type: "funnel",
                    },
                    title: false,
                    credits: {
                        enabled: false
                    },
                    plotOptions: {
                        series: {
                            dataLabels: {
                                enabled: true,
                                softConnector: true
                            },
                            center: ['45%', '50%'],
                            neckWidth: '50%',
                            neckHeight: '0%',
                            width: '90%',
                            height: '80%'
                        }
                    },
                    series: [{
                        name: "Number Of Leads",
                        data: callbacks,
                    }],
                });
            });
        },

        render_lost_leads_graph: function () {
            var self = this;
            var ctx = self.$(".lost_leads_graph");
            rpc.query({
                model: "crm.lead",
                method: "get_lost_lead_by_reason_pie",
            }).then(function (arrays) {
                var data = {
                    labels: arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16"
                        ],
                        borderColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16"
                        ],
                        borderWidth: 1
                    },]
                };

                //options
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "bottom",
                        labels: {
                            fontColor: "#333",
                            fontSize: 16
                        }
                    },
                    scales: {
                        yAxes: [{
                            gridLines: {
                                color: "rgba(0, 0, 0, 0)",
                                display: false,
                            },
                            ticks: {
                                min: 0,
                                display: false,
                            }
                        }]
                    }
                };

                //create Chart class object
                var chart = new Chart(ctx, {
                    type: "doughnut",
                    data: data,
                    options: options
                });
            });
        },

        render_lost_leads_by_stage_graph: function () {
            var self = this
            var ctx = self.$(".lost_leads_by_stage_graph");
            rpc.query({
                model: "crm.lead",
                method: "get_lost_lead_by_stage_pie",
            }).then(function (arrays) {
                var data = {
                    labels: arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16"
                        ],
                        borderColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16"
                        ],
                        borderWidth: 1
                    },]
                };

                //options
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "bottom",
                        labels: {
                            fontColor: "#333",
                            fontSize: 16
                        }
                    },
                    scales: {
                        yAxes: [{
                            gridLines: {
                                color: "rgba(0, 0, 0, 0)",
                                display: false,
                            },
                            ticks: {
                                min: 0,
                                display: false,
                            }
                        }]
                    }
                };

                //create Chart class object
                var chart = new Chart(ctx, {
                    type: "doughnut",
                    data: data,
                    options: options
                });
            });
        },

        render_sales_activity_graph: function () {
            var self = this
            var user_id = $('#search_user').val()
            rpc.query({
                model: "crm.lead",
                method: "get_the_sales_activity",
                args: [user_id]
            }).then(function (arrays) {
                var data = {
                    labels: arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16"
                        ],
                        borderColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16"
                        ],
                        borderWidth: 1
                    },]
                };

                //options
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "right",
                        labels: {
                            fontColor: "#333",
                            fontSize: 16
                        }
                    },
                    scales: {
                        yAxes: [{
                            gridLines: {
                                color: "rgba(0, 0, 0, 0)",
                                display: false,
                            },
                            ticks: {
                                min: 0,
                                display: false,
                            }
                        }]
                    }
                };
                var html = '<canvas class="sales_activity" width="200" height="120"/>';
                $("#crm_activity_div").html(html)
                //create Chart class object
                var chart = new Chart(self.$(".sales_activity"), {
                    type: "doughnut",
                    data: data,
                    options: options
                });
            });
        },

        search_upcoming_activity: function () {
            var self = this
            var user_id = $('#search_user').val()
            rpc.query({
                model: "crm.lead",
                method: "search_upcoming_events",
                args: [user_id]
            }).then(function (result) {
                self.upcoming_events = result.event
                var activitys = result.event
                var html = "";
                if (activitys != null && activitys.length > 0) {
                    for (var i = 0; i < activitys.length; i++) {
                        html += '<div class="item-header activity" data-id="' + activitys[i][7] + '">';
                        html += '<div class="count-container">' + activitys[i][1] + '</div>';
                        html += '<div class="item-title pl-3">';
                        html += '<div class="item-content"><ul>';
                        html += '<li>Activity:<span style="font-size: 16px;color: #4c4c4c;">' + activitys[i][4] + '</span></li>';
                        html += '<li>Name:<span style="font-size: 15px;color: #4c4c4c;">' + activitys[i][3] + '</span></li>';
                        html += '<li>Sale:<span style="font-size: 15px;color: #4c4c4c;">' + activitys[i][6] + '</span></li>';
                        if (activitys[i][2] != null) {
                            html += '<li>Summary:<span style="font-size: 13px;color: #4c4c4c;">' + activitys[i][2] + '</span></li>';
                        }
                        html += '</ul></div></div></div>';
                    }
                }
                $("#upcoming_activities_item_div").html(html)
            });
        },

        render_leads_month_graph: function () {
            var self = this
            var user_id = $('#search_user').val()
            rpc.query({
                model: "crm.lead",
                method: "get_lead_month_pie",
                args: [user_id],
            }).then(function (arrays) {
                var data = {
                    labels: arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16"
                        ],
                        borderColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16"
                        ],
                        borderWidth: 1
                    },]
                };

                //options
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "right",
                        labels: {
                            fontColor: "#333",
                            fontSize: 16
                        }
                    },
                    scales: {
                        yAxes: [{
                            gridLines: {
                                color: "rgba(0, 0, 0, 0)",
                                display: false,
                            },
                            ticks: {
                                min: 0,
                                display: false,
                            }
                        }]
                    }
                };

                var html = '<canvas class="lead_month" width="200" height="120"/>';
                $("#leads_by_month_div").html(html)
                //create Chart class object
                var chart = new Chart(self.$(".lead_month"), {
                    type: "doughnut",
                    data: data,
                    options: options
                });
            });
        },

        render_revenue_count_pie: function () {
            var self = this;
            var type = $('#search_sales_revenue_type').val()
            var team_id = $('#search_sales_revenue_team').val()
            var user_id = $('#search_revenue_user').val()
            rpc.query({
                model: "crm.lead",
                method: "revenue_count_pie",
                args: [user_id, type, team_id],
            }).then(function (arrays) {
                var data = {
                    labels: arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
                            "#ff7c43",
                            "#003f5c",
                            "#b22222"
                        ],
                        borderColor: [
                            "#ff7c43",
                            "#003f5c",
                            "#b22222"
                        ],
                        borderWidth: 1
                    },]
                };
                //options
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "bottom",
                        labels: {
                            fontColor: "#333",
                            fontSize: 16
                        }
                    },
                    scales: {
                        yAxes: [{
                            gridLines: {
                                color: "rgba(0, 0, 0, 0)",
                                display: false,
                            },
                            ticks: {
                                min: 0,
                                display: false,
                            }
                        }]
                    }
                };
                var html = '<canvas class="revenue_count_pie_canvas" width="200" height="120"/>'
                $("#total_revenue_by_salesperson_div").html(html)
                //create Chart class object
                var chart = new Chart(self.$(".revenue_count_pie_canvas"), {
                    type: "doughnut",
                    data: data,
                    options: options
                });
            });
        },

        render_sales_revenue_user: function () {
            var self = this;
            var team_id = $('#search_sales_revenue_team').val();
            rpc.query({
                model: 'crm.lead',
                method: 'get_user_list',
                args: [team_id],
            })
                .then(function (result) {
                    self.team_users = result.team_users
                    var html = '<option value="0">All</option>';
                    if (result.team_users != null && result.team_users.length > 0) {
                        for (var i = 0; i < result.team_users.length; i++) {
                            html += '<option value="' + result.team_users[i][0] + '">' + result.team_users[i][1] + '</option>'
                        }
                    }
                    $("#search_revenue_user").html(html)
                    if (team_id == "0") {
                        $("#search_revenue_user").hide()
                        $(".margin_top10_left50").hide()
                    } else {
                        $("#search_revenue_user").show()
                        $(".margin_top10_left50").show()
                    }
                    self.render_revenue_count_pie();
                })
        },

        change_city_ranking_team: function () {
            var self = this;
            var team_id = $('#search_city_ranking_team').val();
            rpc.query({
                model: 'crm.lead',
                method: 'get_user_list',
                args: [team_id],
            })
            .then(function (result) {
                    self.team_users = result.team_users
                    var html = '<option value="0">All</option>';
                    if (result.team_users != null && result.team_users.length > 0) {
                        for (var i = 0; i < result.team_users.length; i++) {
                            html += '<option value="' + result.team_users[i][0] + '">' + result.team_users[i][1] + '</option>'
                        }
                    }
                    $("#search_city_ranking_user").html(html)
                    if (team_id == "0") {
                        $("#search_city_ranking_user_form").hide()
                    } else {
                        $("#search_city_ranking_user_form").show()
                    }
                    self.render_search_city_ranking_user();
                })
        },

        render_search_city_ranking_user: function () {
            var self = this;
            var team_id = $('#search_city_ranking_team').val()
            var user_id = $('#search_city_ranking_user').val()
            rpc.query({
                model: "crm.lead",
                method: "get_city_revenue",
                args: [team_id, user_id],
            }).then(function (result) {
                var revenues = result.city_revenue;
                var html = "";
                if(revenues != null && revenues.length){
                    for(var i=0; i<revenues.length; i++){
                        html += '<tr><td>'+revenues[i][0]+'</td>';
                        html += '<td>'+revenues[i][2]+revenues[i][1]+'</td>';
                        html += '<td>'+revenues[i][3]+'</td>';
                        html += '<td>'+revenues[i][4]+'</td></tr>';
                    }
                }
                $("#city_ranking_tbody").html(html);
                $(".dashboard_main_section").trigger("mouseenter");
            });
        },

        render_sales_performance_chart_graph: function () {
            var self = this
            var team_id = $("#search_sales_performance_team").val()
            var type = $("#search_sales_performance_type").val()
            rpc.query({
                model: "crm.lead",
                method: "get_sales_performance",
                args: [team_id, type],
            }).then(function (arrays) {
                var data = {
                    labels: arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
                            "#003f5c",
                            "#f95d6a",
                            "#ff7c43",
                            "#6d5c16"
                        ],
                        borderColor: [
                            "#003f5c",
                            "#f95d6a",
                            "#ff7c43",
                            "#6d5c16"
                        ],
                        borderWidth: 1
                    },]
                };
                var html = '<canvas class="sales_performance" width="340px" height="400px"/>';
                $("#sales_performance_div").html(html)
                var chart = new Chart(self.$(".sales_performance"), {
                    type: "bar",
                    data: data,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: {
                            display: false //This will do the task
                        },
                    }
                });
            });
        },

        render_source_leads_graph: function () {
            var self = this
            var user_id = $("#search_user").val();
            rpc.query({
                model: "crm.lead",
                method: "get_the_source_pie",
                args: [user_id],
            }).then(function (arrays) {
                var data = {
                    labels: arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16"
                        ],
                        borderColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16"
                        ],
                        borderWidth: 1
                    },]
                };

                //options
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "right",
                        labels: {
                            fontColor: "#333",
                            fontSize: 14
                        }
                    },
                    scales: {
                        yAxes: [{
                            gridLines: {
                                color: "rgba(0, 0, 0, 0)",
                                display: false,
                            },
                            ticks: {
                                min: 0,
                                display: false,
                            }
                        }]
                    }
                };
                var html = '<canvas class="source_lead" width="200" height="120"/>';
                $("#leads_source").html(html)
                //create Chart class object
                var chart = new Chart(self.$(".source_lead"), {
                    type: "doughnut",
                    data: data,
                    options: options
                });
            });
        },

        render_source_leads_graph_new: function () {
            var self = this
            rpc.query({
                model: "crm.lead",
                method: "get_the_source_pie",
            }).then(function (arrays) {
                var colors = Highcharts.getOptions().colors,
                    categories = [
                        "Chrome",
                        "Safari",
                        "Opera"
                    ],
                    data = [
                        {
                            "y": 62.74,
                            "color": colors[2],
                            "drilldown": {
                                "name": "Chrome",
                                "categories": [
                                    "Chrome v65.0"
                                ],
                                "data": [
                                    33.02
                                ]
                            }
                        },
                        {
                            "y": 5.58,
                            "color": colors[3],
                            "drilldown": {
                                "name": "Safari",
                                "categories": [
                                    "Safari v11.0"
                                ],
                                "data": [
                                    13.39
                                ]
                            }
                        },
                        {
                            "y": 1.92,
                            "color": colors[4],
                            "drilldown": {
                                "name": "Opera",
                                "categories": [
                                    "Opera v50.0"
                                ],
                                "data": [
                                    10.96
                                ]
                            }
                        }
                    ],
                    browserData = [],
                    versionsData = [],
                    i,
                    j,
                    dataLen = data.length,
                    drillDataLen,
                    brightness;
                for (i = 0; i < dataLen; i += 1) {
                    // add browser data
                    browserData.push({
                        name: categories[i],
                        y: data[i].y,
                        color: data[i].color
                    });
                    // add version data
                    drillDataLen = data[i].drilldown.data.length;
                    for (j = 0; j < drillDataLen; j += 1) {
                        brightness = 0.2 - (j / drillDataLen) / 5;
                        versionsData.push({
                            name: data[i].drilldown.categories[j],
                            y: data[i].drilldown.data[j],
                            color: Highcharts.Color(data[i].color).brighten(brightness).get()
                        });
                    }
                }
                Highcharts.chart("city_ranking_div", {
                    chart: {
                        type: 'pie'
                    },
                    title: {
                        text: '2018'
                    },
                    subtitle: {
                        text: 'ok'
                    },
                    yAxis: {
                        title: {
                            text: 'Total percent market share'
                        }
                    },
                    plotOptions: {
                        pie: {
                            shadow: false,
                            center: ['50%', '50%']
                        }
                    },
                    tooltip: {
                        valueSuffix: '%'
                    },
                    series: [{
                        name: 'Browsers',
                        data: browserData,
                        size: '60%',
                        dataLabels: {
                            formatter: function () {
                                return this.y > 5 ? this.point.name : null;
                            },
                            color: '#ffffff',
                            distance: -30
                        }
                    }, {
                        name: 'Versions',
                        data: versionsData,
                        size: '80%',
                        innerSize: '60%',
                        dataLabels: {
                            formatter: function () {
                                // display only if larger than 1
                                return this.y > 1 ? '<b>' + this.point.name + ':</b> ' +
                                    this.y + '%' : null;
                            }
                        },
                        id: 'versions'
                    }],
                    responsive: {
                        rules: [{
                            condition: {
                                maxWidth: 400
                            },
                            chartOptions: {
                                series: [{
                                    id: 'versions',
                                    dataLabels: {
                                        enabled: false
                                    }
                                }]
                            }
                        }]
                    }
                });
            });
        },

        fetch_data: function () {
            var self = this;

            var def0 = self._rpc({
                model: 'crm.lead',
                method: 'check_user_group'
            }).then(function (result) {
                if (result == true) {
                    self.is_manager = 1;
                } else {
                    self.is_manager = 3;
                    self._rpc({
                        model: 'crm.lead',
                        method: 'check_user_group_team'
                    }).then(function (result) {
                        if (result == true) {
                            self.is_manager = 2;
                        }
                    });
                }
            });

            var def1 = self._rpc({
                model: "crm.lead",
                method: "get_upcoming_events",
            })
                .then(function (res) {
                    self.upcoming_events = res['event'];
                });

            var def2 = self._rpc({
                model: "crm.lead",
                method: "get_top_deals",
            })
                .then(function (res) {
                    self.top_deals = res['deals'];
                });

            var def3 = self._rpc({
                model: "crm.lead",
                method: "get_monthly_goal",
            })
                .then(function (res) {
                    self.monthly_goals = res['goals'];
                });

            var def5 = self._rpc({
                model: "crm.lead",
                method: "get_country_revenue",
            })
                .then(function (res) {
                    self.top_country_revenue = res['country_revenue'];
                });

            var def6 = self._rpc({
                model: "crm.lead",
                method: "get_country_count",
            })
                .then(function (res) {
                    self.top_country_count = res['country_count'];
                });

           var def7 = self._rpc({
               model: "crm.lead",
               method: "get_city_revenue",
               args: ['0', '0']
           })
           .then(function (res) {
               self.top_city_revenue = res['city_revenue'];
           });

            var def8 = self._rpc({
                model: "crm.lead",
                method: "get_ratio_based_country",
            })
                .then(function (res) {
                    self.top_country_wise_ratio = res['country_wise_ratio'];
                });

            var def9 = self._rpc({
                model: "crm.lead",
                method: "get_ratio_based_sp",
            })
                .then(function (res) {
                    self.top_salesperson_wise_ratio = res['salesperson_wise_ratio'];
                });

            var def10 = self._rpc({
                model: "crm.lead",
                method: "get_ratio_based_sales_team",
            })
                .then(function (res) {
                    self.top_sales_team_wise_ratio = res['sales_team_wise_ratio'];
                });

            var def12 = self._rpc({
                model: "crm.lead",
                method: "get_count_unassigned",
            })
                .then(function (res) {
                    self.get_count_unassigned = res['count_unassigned'];
                });

            var def14 = self._rpc({
                model: "crm.lead",
                method: "get_user_list",
                args: ["0"],
            })
                .then(function (res) {
                    self.team_users = res['team_users'];
                    self.teams = res['teams'];
                    self.current_time = res['current_time'];
                });

            var def15 = self._rpc({
                model: "crm.lead",
                method: "get_goal_time_list",
            })
                .then(function (res) {
                    self.month_times = res['month_times'];
                    self.current_month = res['current_month'];
                    self.quarter_times = res['quarter_times'];
                    self.current_quarter = res['current_quarter'];
                    self.year_times = res['year_times'];
                    self.current_year = res['current_year'];
                });

            var def16 = self._rpc({
                model: "crm.lead",
                method: "get_quarter_goal",
            })
                .then(function (res) {
                    self.quarter_goals = res['quarter_goals'];
                });

            var def17 = self._rpc({
                model: "crm.lead",
                method: "get_year_goal",
            })
                .then(function (res) {
                    self.year_goals = res['quarter_goals'];
                });

            return $.when(def0, def1, def2, def3, def5, def6, def7, def8, def9, def10, def12, def14, def15, def16, def17);
        },

        render_dashboards: function () {
            var self = this;
            if (this.login_employee) {
                var templates = []
                if (self.is_manager == 1) {
                    templates = ['LoginUser', 'Managercrm', 'Admincrm'];
                } else {
                    templates = ['LoginUser', 'Managercrm'];
                }
                _.each(templates, function (template) {
                    self.$('.o_hr_dashboard').append(QWeb.render(template, {widget: self}));
                });
            } else {
                self.$('.o_hr_dashboard').append(QWeb.render('EmployeeWarning', {widget: self}));
            }
        },

        on_reverse_breadcrumb: function () {
            var self = this;
            web_client.do_push_state({});
            this.update_cp();
            this.fetch_data().then(function () {
                self.$('.o_hr_dashboard').reload();
                self.render_dashboards();
            });
        },

        update_cp: function () {
            var self = this;
        },

    });

    core.action_registry.add('crm_dashboard', DashBoard);
    return DashBoard;
});