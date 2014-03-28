import os
from logging import getLogger

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IRoutes, IConfigurer
from ckan.lib.navl.dictization_functions import StopOnError
from model import create_table
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import helpers as h

log = getLogger(__name__)

class VDojStatsPlugin(SingletonPlugin):
    '''Stats plugin.'''
    
    create_table()

    implements(IRoutes, inherit=True)
    implements(IConfigurer, inherit=True)
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
        
        map.connect('report', '/report/edit/{id}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='report_edit')
        
        map.connect('report', '/report/delete/{id}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='report_delete')

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
                }

