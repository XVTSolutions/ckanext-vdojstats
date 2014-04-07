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

        map.connect('stats', '/stats/assets',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='assets')

        map.connect('stats', '/stats/all_users',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='all_users')

        map.connect('stats', '/stats/user/{username}',
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

        map.connect('stats', '/stats/assets_pdf',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='assets_pdf')

        map.connect('stats', '/stats/all_users_pdf',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='all_users_pdf')

        map.connect('stats', '/stats/user_pdf/{username}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='user_pdf')

        map.connect('stats', '/stats/overall_csv',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='overall_csv')

        map.connect('stats', '/stats/all_assets_csv',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='all_assets_csv')

        map.connect('stats', '/stats/assets_csv',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='assets_csv')

        map.connect('stats', '/stats/all_users_csv',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='all_users_csv')

        map.connect('stats', '/stats/user_csv/{username}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='user_csv')

        map.connect('stats', '/stats/overall_xml',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='overall_xml')

        map.connect('stats', '/stats/all_assets_xml',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='all_assets_xml')

        map.connect('stats', '/stats/assets_xml',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='assets_xml')

        map.connect('stats', '/stats/all_users_xml',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='all_users_xml')

        map.connect('stats', '/stats/user_xml/{username}',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='user_xml')

        map.connect('stats', '/stats/autocomplete_user',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='autocomplete_user')

        map.connect('stats', '/stats/autocomplete_package',
            controller='ckanext.vdojstats.controller:VDojStatsController',
            action='autocomplete_package')

        return map

    def update_config(self, config):
        here = os.path.dirname(__file__)
        tk.add_template_directory(config, 'templates')
        tk.add_public_directory(config, 'public')
        tk.add_resource('public', 'ckanext-vdojstats')

        #configure vicdoj export directory and header
        site_id = config.get('ckan.site_id', 'default')
        config.update({'vdojstats.export_dir': '/tmp/export/%s/'%(site_id)})
        config.update({'vdojstats.export_header': 'Victoria DoJ'})

    def get_helpers(self):
        # ITemplateHelpers
        # TODO
        return {
            'get_reports'   : h.get_reports,
            'current_time'  : h.current_time,
            'get_export_header_title' : h.get_export_header_title,
            'get_site_logo_url' : h.get_site_logo_url,
                }

