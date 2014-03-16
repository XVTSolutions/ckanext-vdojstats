import os
from logging import getLogger

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IRoutes, IConfigurer
from ckan.lib.navl.dictization_functions import StopOnError
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

log = getLogger(__name__)

class VDojStatsPlugin(SingletonPlugin):
    '''Stats plugin.'''

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

        return map

    def update_config(self, config):
        here = os.path.dirname(__file__)
        tk.add_template_directory(config, 'templates')
        tk.add_public_directory(config, 'public')
        tk.add_resource('public', 'ckanext-vdojstats')
        tk.add_resource('public/dist', 'ckanext-vdojstats-dist')
        tk.add_resource('public/libs', 'ckanext-vdojstats-libs')

    def get_helpers(self):
        # ITemplateHelpers
        # TODO
        return {
            #Any   : function,
                }

