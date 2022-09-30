# -*- coding: utf-8 -*-
{
    'name': "XKS_CRM",

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
        'base',
        'account',
        'product',
        'mail',
        'crm',
        'sale',
        'sale_crm',
        'sales_team'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/templates.xml',
        'security/crm_clue_xks_security.xml',
        'views/crm_lead_inherit_xks_menu_views.xml',
        'security/res_partner_xks_security.xml',
        'views/crm_lead_inherit_xks_view.xml',
        'views/res_partner_inherit_xks.view.xml',
        'views/sale_inherit_xks_view.xml',
        'views/ir_attachment_inherit_xks.xml',
        'views/purchase_inherit_xks_view.xml',
        'views/product_template_xks_view.xml',
        'views/product_product_xks_view.xml',
        'views/product_inspection_xks_view.xml',
        'views/product_produce_xks_view.xml',
        'views/purchase_order_pay_xks_view.xml',
        'views/crm_team_member_inherit_view.xml',
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
