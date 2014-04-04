from ckan.lib.base import BaseController, render, config
import ckan.plugins.toolkit as tk
import helpers as h
import model
import json
import csv
import re
import xml.etree.ElementTree as ET
from ckan.model import Group, Session, Member, User, Activity
from sqlalchemy import distinct, desc, not_
from sqlalchemy.orm import joinedload
from ckan.lib.activity_streams import activity_stream_string_functions
from ckan.lib.base import abort
from ckan.common import _


class VDojStatsController(BaseController):

    def __before__(self, action, **params):
        super(VDojStatsController, self).__before__(action, **params)
        if not tk.c.userobj:
            print '**************invador***************'
            abort(401, _('You are not authorized to display statistics pages.') )

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
        file_path = h.get_export_dir() + 'vdojstats-overall.pdf'
        response = h.convertHtmlToPdf(tk.render('vdojstats-overall-pdf.html'), file_path, tk.response)
        return response

    def overall_csv(self):
        self._overall()
        file_path = h.get_export_dir() + 'vdojstats-overall.csv'
        with open(file_path, 'wb') as csvfile:
            writer = csv.writer(csvfile, lineterminator = '\n')
            record = ['State', 'Count']
            writer.writerow(record)
            for key, value in tk.c.overall.items():
                record = [key, str(value)]
                writer.writerow(record)
        response = h.convertHtmlToCsv(file_path, tk.response)
        return response

    def overall_xml(self):
        #TODO
        self._overall()
        root = ET.Element('root')
        for key, value in tk.c.overall.items():
            record = ET.SubElement(root, 'record')
            state = ET.SubElement(record, 'State')
            state.text = key
            count = ET.SubElement(record, 'Count')
            count.text = str(value)
        file_path = h.get_export_dir() + 'vdojstats-overall.xml'
        tree = ET.ElementTree(root)
        response = h.createResponseWithXML(tree, file_path, tk.response)
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
        file_path = h.get_export_dir() + 'vdojstats-all-assets.pdf'
        response = h.convertHtmlToPdf(tk.render('vdojstats-all-assets-pdf.html'), file_path, tk.response)
        return response

    def all_assets_csv(self):
        self._all_assets()
        file_path = h.get_export_dir() + 'vdojstats-all-assets.csv'
        with open(file_path, 'wb') as csvfile:
            writer = csv.writer(csvfile, lineterminator = '\n')
            record = ['Date', 'New', 'Modified', 'Deleted']
            writer.writerow(record)
            for row in tk.c.allassets:
                record = [row['day'], row['new'], row['changed'], row['deleted']]
                writer.writerow(record)
        response = h.convertHtmlToCsv(file_path, tk.response)
        return response

    def all_assets_xml(self):
        self._all_assets()
        root = ET.Element('root')
        for row in tk.c.allassets:
            record = ET.SubElement(root, 'record')
            day = ET.SubElement(record, 'Date')
            day.text = row['day']
            new = ET.SubElement(record, 'New')
            new.text = str(row['new'])
            changed = ET.SubElement(record, 'Modified')
            changed.text = str(row['changed'])
            deleted = ET.SubElement(record, 'Deleted')
            deleted.text = str(row['deleted'])
        file_path = h.get_export_dir() + 'vdojstats-all-assets.xml'
        tree = ET.ElementTree(root)
        response = h.createResponseWithXML(tree, file_path, tk.response)
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
        file_path = h.get_export_dir() + 'vdojstats-organizations.pdf'
        response = h.convertHtmlToPdf(tk.render('vdojstats-organizations-pdf.html'), file_path, tk.response)
        return response

    def organizations_csv(self):
        self._organizations()
        file_path = h.get_export_dir() + 'vdojstats-organizations.csv'
        with open(file_path, 'wb') as csvfile:
            writer = csv.writer(csvfile, lineterminator = '\n')
            record = ['Organisation', 'Packasge', 'status', 'Private', 'Suspend', 'Suspend Reason', 'Review Date']
            writer.writerow(record)
            for row in tk.c.org_assets:
                record = [row['group_title'] or row['group_name'], row['package_title'] or row['package_name'], row['package_state'], row['is_private'], row['is_suspended'], row['suspend_reason'], row['next_review_date']]
                writer.writerow(record)
        response = h.convertHtmlToCsv(file_path, tk.response)
        return response

    def organizations_xml(self):
        self._organizations()
        root = ET.Element('root')
        for row in tk.c.org_assets:
            record = ET.SubElement(root, 'record')
            group = ET.SubElement(record, 'Organisation')
            group.text = row['group_title'] or row['group_name']
            package = ET.SubElement(record, 'Packasge')
            package.text = row['package_title'] or row['package_name']
            status = ET.SubElement(record, 'status')
            status.text = row['package_state']
            is_private = ET.SubElement(record, 'Private')
            is_private.text = row['is_private']
            is_suspended = ET.SubElement(record, 'Suspend')
            is_suspended.text = row['is_suspended']
            suspend_reason = ET.SubElement(record, 'Suspend_Reason')
            suspend_reason.text = row['suspend_reason']
            next_review_date = ET.SubElement(record, 'Review_Date')
            next_review_date.text = row['next_review_date']
        file_path = h.get_export_dir() + 'vdojstats-organizations.xml'
        tree = ET.ElementTree(root)
        response = h.createResponseWithXML(tree, file_path, tk.response)
        return response

    '''
    all users
    '''
    def _all_users(self):
        tk.c.sub_title = 'All users'
        candidate = None
        is_active = None
        is_sysadmin = None
        if tk.request.method == 'GET':
            data = tk.request.GET
            if data.has_key('search'):
                tk.c.search = data.get('search')
            if data.has_key('candidate'):
                tk.c.candidate = candidate = data.get('candidate', '')
            if data.has_key('state[]'):
                tk.c.state = data.get('state[]')
                if tk.c.state =='active':
                    is_active = True
                if tk.c.state =='not_active':
                    is_active = False
            if data.has_key('sysadmin[]'):
                tk.c.sysadmin = data.get('sysadmin[]')
                if tk.c.sysadmin =='sysadmin':
                    is_sysadmin = True
                if tk.c.sysadmin =='not_sysadmin':
                    is_sysadmin = False
        tk.c.active_users_num = h.count_active_users()
        tk.c.dormant_users_num = h.count_dormant_users()
        tk.c.user_list = h.list_users(candidate=candidate, is_active=is_active, is_sysadmin=is_sysadmin)

    def all_users(self):
        self._all_users()
        return render('vdojstats-all-users.html')

    def all_users_pdf(self):
        self._all_users()
        file_path = h.get_export_dir() + 'vdojstats-all-users.pdf'
        response = h.convertHtmlToPdf(tk.render('vdojstats-all-users-pdf.html'), file_path, tk.response)
        return response

    def all_users_csv(self):
        self._all_users()
        file_path = h.get_export_dir() + 'vdojstats-all-users.csv'
        with open(file_path, 'wb') as csvfile:
            writer = csv.writer(csvfile, lineterminator = '\n')
            record = ['User Name', 'Is Active', 'Is Administrator']
            writer.writerow(record)
            for row in tk.c.user_list:
                record = [row['name'], row['state'], row['sysadmin']]
                writer.writerow(record)
        response = h.convertHtmlToCsv(file_path, tk.response)
        return response

    def all_users_xml(self):
        self._all_users()
        root = ET.Element('root')
        for row in tk.c.user_list:
            record = ET.SubElement(root, 'record')
            name = ET.SubElement(record, 'User_Name')
            name.text = row['name']
            state = ET.SubElement(record, 'Is_Active')
            state.text = row['state']
            sysadmin = ET.SubElement(record, 'Is_Administrator')
            sysadmin.text = row['sysadmin']
        file_path = h.get_export_dir() + 'vdojstats-all-users.xml'
        tree = ET.ElementTree(root)
        response = h.createResponseWithXML(tree, file_path, tk.response)
        return response

    def autocomplete_user(self):
        if tk.request.method == 'GET':
            tk.response.headers['Content-Type']='application/json'
            data = tk.request.GET
            if data.has_key('candidate'):
                candidate = data.get('candidate')
                return json.dumps(h.list_users(candidate))
        return []

    '''
    user activitiy
    '''
    def _user(self, username):
        tk.c.username = username
        user = User.get(username)
        tk.c.user_info = h.get_user(user.id)
        tk.c.sub_title = 'User Activities: %s'%(user.fullname or user.name) 
        tk.c.user_activity_list = h.list_activities_for_user(user_id=user.id)

    def user(self, username):
        self._user(username)
        return render('vdojstats-user.html')
    
    def user_pdf(self, username):
        self._user(username)
        file_path = h.get_export_dir() + 'vdojstats-user.pdf'
        response = h.convertHtmlToPdf(tk.render('vdojstats-user-pdf.html'), file_path, tk.response)
        return response

    def user_csv(self, username):
        self._user(username)
        file_path = h.get_export_dir() + 'vdojstats-user.csv'
        with open(file_path, 'wb') as csvfile:
            writer = csv.writer(csvfile, lineterminator = '\n')
            record = ['Date Time', 'Activity', 'Object (Detail)', 'Activity (Detail)']
            writer.writerow(record)
            for row in tk.c.user_activity_list:
                record = [row['timestamp'], row['activity_type'], row['object_type'], row['detail_type']]
                writer.writerow(record)
        response = h.convertHtmlToCsv(file_path, tk.response)
        return response
    
    def user_xml(self, username):
        self._user(username)
        root = ET.Element('root')
        for row in tk.c.user_activity_list:
            record = ET.SubElement(root, 'record')
            timestamp = ET.SubElement(record, 'Date_Time')
            timestamp.text = row['timestamp']
            activity_type = ET.SubElement(record, 'Activity')
            activity_type.text = row['activity_type']
            object_type = ET.SubElement(record, 'Object_Detail')
            object_type.text = row['object_type']
            detail_type = ET.SubElement(record, 'Activity_Detail')
            detail_type.text = row['detail_type']
        file_path = h.get_export_dir() + 'vdojstats-user.xml'
        tree = ET.ElementTree(root)
        response = h.createResponseWithXML(tree, file_path, tk.response)
        return response

    def report_add(self):
        """
        """        
        tk.c.sub_title = 'Add Report'
        
        if tk.request.method == 'POST':
            
            report = model.VDojStatsReport()
            report.name = tk.request.params.getone('name')
            report.org_id = tk.request.params.getone('organization')
            report.permission = tk.request.params.getone('permission')
            report.report_on = tk.request.params.getone('report_on')
            report.custodian = 'custodian' in tk.request.params
            
            #todo - validate
            is_valid, errors = report.validate()
            
            if is_valid:
                report.save()
                        
                tk.redirect_to(controller="ckanext.vdojstats.controller:VDojStatsController", action="report_view", id=report.id)
            else :
                data = report.as_dict()
                data["organizations"] = [ { 'id': org.id, 'title' : org.title } for org in Session.query(Group.title, Group.id).filter(Group.is_organization == True).order_by(Group.title)]
                
                vars = {
                    'errors': errors,
                    'data': data
                }
            
                return render('vdojstats-report-add.html', extra_vars = vars)
        else:
        
            vars = {
                'errors': {},
                'data': {
                         'organizations' : [ { 'id': org.id, 'title' : org.title } for org in Session.query(Group.title, Group.id).filter(Group.is_organization == True).order_by(Group.title)]
                }
            }
        
            return render('vdojstats-report-add.html', extra_vars = vars)
        
    def _report_view(self, id):
        report = Session.query(model.VDojStatsReport).filter(model.VDojStatsReport.id == id).first()
        
        if not report:
            tk.abort(404, tk._('Report not found'))
            
        tk.c.sub_title = report.name
        tk.c.action = "report/view"
        
        show_org = report.org_id is None or len(report.org_id) == 0
            
        #get results
        if report.report_on == "activities":
                        
            activity_query = Session.query(Activity, User).filter(Activity.user_id == User.id).order_by(desc(Activity.timestamp))
                       
            member_query = Session.query(Member.table_id).filter(Member.table_name == 'user').filter(Member.state == 'active')
                       
            if report.org_id is not None and len(report.org_id) > 0:
                member_query = member_query.filter(Member.group_id == report.org_id)
                
            if report.permission != 'all':
                member_query = member_query.filter(Member.capacity == report.permission)

            #todo -something with custodian
            
            activity_query = activity_query.filter(Activity.user_id.in_(member_query))

            activities = [{
                        'activity': a.as_dict(),
                        'user': u.as_dict()
                        } for a,u in activity_query]
            
            return report.as_dict(), activities, show_org
            
        elif report.report_on == "details":
            
            user_query = Session.query(User.id, User.name, User.fullname, User.email, User.state, User.sysadmin, Group.title.label("organization"), Member.capacity).join(Member, Member.table_id == User.id).join(Group, Group.id == Member.group_id).filter(Member.table_name == 'user').filter(Member.state == 'active').filter(Group.is_organization == True).order_by(User.name)
                       
            if report.org_id is not None and len(report.org_id) > 0:
                user_query = user_query.filter(Member.group_id == report.org_id)
                
            if report.permission != 'all':
                user_query = user_query.filter(Member.capacity == report.permission)
                
            #todo -something with custodian
                
            users = [{
                        'id' : u.id,
                        'name': u.name,
                        'fullname': u.fullname,
                        'email': u.email,
                        'state': u.state,
                        'sysadmin' : u.sysadmin,
                        'organization': u.organization,
                        'capacity': u.capacity
                        } for u in user_query]
            
            return report.as_dict(), users, show_org
        else:
            tk.abort(404, tk._('Report not found'))
        
        
    def report_view(self, id):
        """
        """                    
        report, results, show_org = self._report_view(id)
        
        tk.c.sub_title = report['name']
            
        if report['report_on'] == "activities":          
            tk.c.activities = results
            tk.c.report = report
        elif report['report_on'] == "details":
            tk.c.users = results
            tk.c.report = report
            tk.c.show_org = show_org
        else:
            tk.abort(404, tk._('Report not found'))
            
        return render('vdojstats-report-view.html')
    
    def report_view_pdf(self, id):
        report, results, show_org = self._report_view(id)
        
        if report['report_on'] == "activities":         
            tk.c.activities = results
            tk.c.report = report
        elif report['report_on'] == "details":
            tk.c.users = results
            tk.c.report = report
            tk.c.show_org = show_org
        else:
            tk.abort(404, tk._('Report not found'))
        
        file_path = '%s/%s.pdf' % (h.get_export_dir(), re.sub('[^a-zA-Z0-9_-]+', '_', report['name'].encode('ascii','ignore')))
        response = h.convertHtmlToPdf(tk.render('vdojstats-report-pdf.html'), file_path, tk.response)
        return response

    def report_view_csv(self, id):
        report, results, show_org = self._report_view(id)
        file_path = '%s/%s.csv' % (h.get_export_dir(), re.sub('[^a-zA-Z0-9_-]+', '_', report['name'].encode('ascii','ignore')))
        
        if report['report_on'] == "activities": 
            with open(file_path, 'wb') as csvfile:
                writer = csv.writer(csvfile, lineterminator = '\n')
                record = ['time', 'user', 'activity type']
                writer.writerow(record)
                for row in results:
                    record = [row['activity']['timestamp'], row['user']['fullname'], row['activity']['activity_type']]
                    writer.writerow(record)    
        elif report['report_on'] == "details":
            with open(file_path, 'wb') as csvfile:
                writer = csv.writer(csvfile, lineterminator = '\n')
                record = ['name', 'email', 'state', 'organization', 'role', 'system administrator']
                writer.writerow(record)
                for row in results:
                    record = [row['fullname'], row['email'], row['state'], row['organization'], row['capacity'], row['sysadmin']]
                    writer.writerow(record)
            
        response = h.convertHtmlToCsv(file_path, tk.response)
        return response

    def report_view_xml(self, id):
        report, results, show_org = self._report_view(id)
        file_path = '%s/%s.xml' % (h.get_export_dir(), re.sub('[^a-zA-Z0-9_-]+', '_', report['name'].encode('ascii','ignore')))
                
        if report['report_on'] == "activities":                    
            tree = h.dict_to_etree({ 'activities' : {'activity' : [ {
                                                                '@time': row['activity']['timestamp'],
                                                                '@user': row['user']['fullname'],
                                                                '@activity_type': row['activity']['activity_type']
                                                                } for row in results]}})
            
            response = h.createResponseWithXML(tree, file_path, tk.response)
                    
                    
        elif report['report_on'] == "details":
            tree = h.dict_to_etree({ 'users' : {'user' : [ {
                                                            '@name': row['fullname'],
                                                            '@email': row['email'],
                                                            '@state': row['state'],
                                                            '@organization': row['organization'],
                                                            '@role': row['capacity'],
                                                            '@system_administrator': str(row['sysadmin'])
                                                            } for row in results]}})
            response = h.createResponseWithXML(tree, file_path, tk.response)      
        
        return response
    
    def report_edit(self, id):
        """
        """
        tk.c.sub_title = 'Edit Report'
        
        report = Session.query(model.VDojStatsReport).filter(model.VDojStatsReport.id == id).first()
        
        if not report:
            tk.abort(404, tk._('Report not found'))
    
        if tk.request.method == 'POST':
            
            report.name = tk.request.params.getone('name')
            report.org_id = tk.request.params.getone('organization')
            report.permission = tk.request.params.getone('permission')
            report.report_on = tk.request.params.getone('report_on')
            report.custodian = 'custodian' in tk.request.params
            
            #todo - validate
            is_valid, errors = report.validate()
            
            if is_valid:
                report.commit()
                        
                tk.redirect_to(controller="ckanext.vdojstats.controller:VDojStatsController", action="report_view", id=report.id)
            else :
                data = report.as_dict()
                data["organizations"] = [ { 'id': org.id, 'title' : org.title } for org in Session.query(Group.title, Group.id).filter(Group.is_organization == True).order_by(Group.title)]
                
                vars = {
                    'errors': errors,
                    'data': data
                }
            
                return render('vdojstats-report-add.html', extra_vars = vars)
        else:
            
            data = report.as_dict()
            data["organizations"] = [ { 'id': org.id, 'title' : org.title } for org in Session.query(Group.title, Group.id).filter(Group.is_organization == True).order_by(Group.title)]
        
            vars = {
                'errors': {},
                'data': data
            }
        
            return render('vdojstats-report-add.html', extra_vars = vars)
    
    def report_delete(self, id):
        """
        """
        if tk.request.method == 'POST':
            
            report = Session.query(model.VDojStatsReport).filter(model.VDojStatsReport.id == id).first()
        
            if not report:
                tk.abort(404, tk._('Report not found'))
                
            report.delete()
            report.commit()
                
            tk.redirect_to(controller="ckanext.vdojstats.controller:VDojStatsController", action="overall")
        else: 
            tk.abort(404, tk._('Report not found'))  
        
    


