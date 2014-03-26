from ckan.lib.base import BaseController, render, config
import ckan.plugins.toolkit as tk
import helpers as h
import os

class VDojStatsController(BaseController):


    '''
    overall
    '''
    def _overall(self):
        tk.c.sub_title = 'All sites overall'

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

    def overall(self):
        self._overall()
        return render('vdojstats-overall.html')

    def overall_pdf(self):
        self._overall()
        file_path = '/tmp/vdojstats-overall.pdf'
        response = h.convertHtmlToPdf(tk.render('vdojstats-overall-pdf.html'), file_path, tk.response)
        return response

    '''
    all assets
    '''
    def _all_assets(self):
        tk.c.sub_title = 'All Packages'
        tk.c.allassets = h.count_assets_by_date()
        return render('vdojstats-all-assets.html')

    def all_assets(self):
        self._all_assets()
        return render('vdojstats-all-assets.html')

    def all_assets_pdf(self):
        self._all_assets()
        file_path = '/tmp/vdojstats-all-assets.pdf'
        response = h.convertHtmlToPdf(tk.render_snippet('snippets/vdojstats-all-assets-content.html', data={'allassets':tk.c.allassets} ), file_path, tk.response)
        return response

    '''
    Organizations
    '''
    def _organizations(self):
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

    def organizations(self):
        self._organizations()
        return render('vdojstats-organizations.html')

    def organizations_pdf(self):
        self._organizations()
        file_path = '/tmp/vdojstats-organizations.pdf'
        response = h.convertHtmlToPdf(tk.render_snippet('snippets/vdojstats-organizations-content.html', data={'org_assets':tk.c.org_assets} ), file_path, tk.response)
        return response

    '''
    all users
    '''
    def _all_users(self):
        tk.c.sub_title = 'All users'
        tk.c.active_users_num = h.count_active_users()
        tk.c.dormant_users_num = h.count_dormant_users()
        tk.c.user_list = h.list_users()

    def all_users(self):
        self._all_users()
        return render('vdojstats-all-users.html')

    def all_users_pdf(self):
        self._all_users()
        file_path = '/tmp/vdojstats-all-users.pdf'
        response = h.convertHtmlToPdf(tk.render_snippet('snippets/vdojstats-all-users-content.html', data={'user_list':tk.c.user_list} ), file_path, tk.response)
        return response

    '''
    user activitiy
    '''
    def _user(self, id):
        tk.c.sub_title = 'User Activities'
        tk.c.id = id
        tk.c.user_info = h.get_user(id)
        tk.c.user_activity_list = h.list_activities_for_user(user_id=id)

    def user(self, id):
        self._user(id)
        return render('vdojstats-user.html')

    def user_pdf(self, id):
        self._user(id)
        file_path = '/tmp/vdojstats-user.pdf'
        response = h.convertHtmlToPdf(tk.render_snippet('snippets/vdojstats-user-content.html', data={'user_activity_list':tk.c.user_activity_list} ), file_path, tk.response)
        return response



