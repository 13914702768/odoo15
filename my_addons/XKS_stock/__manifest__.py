# -*- coding: utf-8 -*-
{
    'name': "XKS_stock",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "zhangxian",
    # 'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        # 'base',
        # 'account',
        # 'mail',
        # 'crm',
        # 'sale',
        # 'sale_crm',
        # 'sales_team'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/crm_produce_xks_view.xml',
        'views/crm_produce_menu_xks.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    # 'assets': {
    #     'web.assets_qweb': [
    #     ],
    #     'web.assets_backend': [
    #         'xks_crm/static/src/scss/leads.scss',
    #     ],
    #     'web.assets_tests': [
    #     ],
    #     'web.qunit_suite_tests': [
    #     ],
    # },
    'application': False,
    'license': 'LGPL-3',
}
