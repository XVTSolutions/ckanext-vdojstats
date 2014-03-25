from ckan.lib.base import BaseController, render, config
import ckan.plugins.toolkit as tk
import helpers as h

class VDojStatsController(BaseController):


    def overall(self):
        #TODO
        tk.c.sub_title = 'All sites overall'

        #overall information
        private_num = h.count_private_assets()
        published_num = h.count_published_assets()
        active_num = h.count_active_assets()
        dormant_num = h.count_dormant_assets()
        pending_approval_num = h.count_pending_approval_assets()
        tk.c.overall = {
            'Private':private_num,
            'Published':published_num,
            'Active':active_num,
            'Not Active':dormant_num,
            'Pending Approval':pending_approval_num,
        }
        return render('vdojstats-overall.html')

    def all_assets(self):
        #TODO
        tk.c.sub_title = 'All Packages'
        tk.c.allassets = h.count_assets_by_date()
        return render('vdojstats-all-assets.html')

    def organizations(self):
        #TODO
        tk.c.sub_title = 'Organizations'

        #search parameter
        org_ids = []
        private = None
        suspended = None
        pending_approval = None

        tk.c.selected_org_names = []
        tk.c.selected_package_states = []
        if tk.request.method == 'GET':
            data = tk.request.GET
            if data.has_key('search'):
                tk.c.search = data.get('search')
            if data.has_key('organization'):
                for key, value in data.iteritems():
                    if key == 'organization' and len(value):
                        tk.c.selected_org_names.append(value)
                        org_id = h.get_organization_id(value)
                        org_ids.append(org_id)
            if data.has_key('package_state'):
                for key, value in data.iteritems():
                    if key == 'package_state' and len(value):
                        tk.c.selected_package_states.append(value)
            if data.has_key('private[]'):
                tk.c.private = data.get('private[]')
                if tk.c.private =='private':
                    private = True
                if tk.c.private =='published':
                    private = False

            if data.has_key('suspended[]'):
                tk.c.suspended = data.get('suspended[]')
                if tk.c.suspended =='suspended':
                    suspended = True
                if tk.c.suspended =='not_suspended':
                    suspended = False

            if data.has_key('pending_approval[]'):
                tk.c.pending_approval = data.get('pending_approval[]')
                if tk.c.pending_approval =='pending_approval':
                    pending_approval = True
                if tk.c.pending_approval =='not_pending_approval':
                    pending_approval = False

        tk.c.option_org_names = h.get_org_names()
        tk.c.option_package_states = h.get_package_states()
        tk.c.org_assets = h.list_assets(org_ids=org_ids, package_states=tk.c.selected_package_states, private=private, suspended=suspended, pending_approval=pending_approval)
        return render('vdojstats-organizations.html')

    def all_users(self):
        #TODO
        tk.c.sub_title = 'All users'
        tk.c.active_users_num = h.count_active_users()
        tk.c.dormant_users_num = h.count_dormant_users()
        tk.c.user_list = h.list_users()
        return render('vdojstats-all-users.html')

    def user(self, id):
        #TODO
        tk.c.sub_title = 'User Activities'
        print '**********************************id**************'
        print id
        print '**********************************id**************'
        tk.c.user_info = h.get_user(id)
        tk.c.user_activity_list = h.list_activities_for_user(user_id=id)
        #print '*************user_activity_list**************'
        #print [activity for activity in tk.c.user_activity_list]

        return render('vdojstats-user.html')


