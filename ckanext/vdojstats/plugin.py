import os
from logging import getLogger

from ckan.plugins import implements, SingletonPlugin
from ckan.lib.navl.dictization_functions import StopOnError
from model import create_table
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import helpers as h

log = getLogger(__name__)

class VDojStatsPlugin(SingletonPlugin):
    '''Stats plugin.'''
    
    create_table()

    implements(plugins.IRoutes, inherit=True)
    implements(plugins.IConfigurer, inherit=True)
    implements(plugins.ITemplateHelpers)

    def before_map(self, map):

        map.connect('stats', '/stats',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='overall')

        map.connect('stats', '/stats/overall',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='overall')

        map.connect('stats', '/stats/all_assets',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='all_assets')

        map.connect('stats', '/stats/organizations',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='organizations')

        map.connect('stats', '/stats/all_users',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='all_users')

        map.connect('stats', '/stats/user/{id}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='user')
        
        map.connect('report', '/report/add',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='report_add')
        
        map.connect('report', '/report/view/{id}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='report_view')
        
        map.connect('report', '/report/pdf/{id}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='report_view_pdf')
        
        map.connect('report', '/report/csv/{id}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='report_view_csv')
        
        map.connect('report', '/report/xml/{id}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='report_view_xml')
        
        map.connect('report', '/report/edit/{id}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='report_edit')
        
        map.connect('report', '/report/delete/{id}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='report_delete')

        map.connect('stats', '/stats/overall_pdf',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='overall_pdf')

        map.connect('stats', '/stats/all_assets_pdf',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='all_assets_pdf')

        map.connect('stats', '/stats/organizations_pdf',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='organizations_pdf')

        map.connect('stats', '/stats/all_users_pdf',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='all_users_pdf')

        map.connect('stats', '/stats/user_pdf/{id}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='user_pdf')

        map.connect('stats', '/stats/overall_csv',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='overall_csv')

        map.connect('stats', '/stats/all_assets_csv',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='all_assets_csv')

        map.connect('stats', '/stats/organizations_csv',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='organizations_csv')

        map.connect('stats', '/stats/all_users_csv',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='all_users_csv')

        map.connect('stats', '/stats/user_csv/{id}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='user_csv')

        map.connect('stats', '/stats/overall_xml',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='overall_xml')

        map.connect('stats', '/stats/all_assets_xml',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='all_assets_xml')

        map.connect('stats', '/stats/organizations_xml',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='organizations_xml')

        map.connect('stats', '/stats/all_users_xml',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='all_users_xml')

        map.connect('stats', '/stats/user_xml/{id}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='user_xml')

        return map

    def update_config(self, config):
        here = os.path.dirname(__file__)
        tk.add_template_directory(config, 'templates')
        tk.add_public_directory(config, 'public')
        tk.add_resource('public', 'ckanext-vdojstats')
        #tk.add_resource('jquery.uix.multiselect', 'multiselect')
        #tk.add_resource('jspdf', 'jspdf')
        #tk.add_resource('jquery-ui-1.10.3.custom', 'jqueryui')
        #tk.add_resource('public/jquery.uix.multiselect/css', 'multiselect-css')
        #tk.add_resource('public/jquery.uix.multiselect/js', 'multiselect-js')

    def get_helpers(self):
        # ITemplateHelpers
        # TODO
        return {
            'get_reports'   : h.get_reports,
            'current_time'  : h.current_time,
            'get_export_header_title' : h.get_export_header_title,
                }

