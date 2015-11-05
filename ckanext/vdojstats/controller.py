from ckan.lib.base import BaseController, render, config
import ckan.plugins.toolkit as tk
import helpers as h
import model
import json
import csv
import re
import math
import xml.etree.ElementTree as ET
from ckan.model import Group, Session, Member, User, Activity, Package
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
        
        context = {'user': tk.c.user or tk.c.author}
        try:
            tk.check_access('statistics_show', context, {})
        except tk.NotAuthorized:
            abort(401, tk._('You are not authorized to display statistics pages.'))
        
    '''
    overall
    '''
    def _overall(self):
        tk.c.sub_title = _('All sites overall')

        private_num = h.count_private_assets()
        public_num = h.count_public_assets()
        active_num = h.count_active_assets()
        dormant_num = h.count_dormant_assets()
        today_review_num = h.count_today_review_assets()
        delay_review_num = h.count_delay_review_assets()
        tk.c.overall = [
            {'header': 'Visibility',
            'content':
                [
                    {'label':'Private', 'num':private_num},
                    {'label':'Public', 'num':public_num},
                ]
            },
            ]

        oh = h.get_open_status_helper()
        if oh:
            #TODO
            options = h.count_open_status_assets()
            print options
            tk.c.overall.append({
                'header': 'Datavic Datasets',
                'content': options
                })

        tk.c.overall.append(
            {'header': 'Activeness',
            'content':
                [
                    {'label':'Active', 'num':active_num},
                    {'label':'Not Active', 'num':dormant_num},
                ]
            })

        tk.c.overall.append(
            {'header': 'Review Status',
            'content':
                [
                    {'label':'Pending Review for Today', 'num':today_review_num},
                    {'label':'Pending Review (Delay)', 'num':delay_review_num},
                ]
            })

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
            for table in tk.c.overall:
                header = table.get('header')
                writer.writerow([header])
                record = ['State', 'Count']
                writer.writerow(record)
                for row in table.get('content', []):
                    record = [row.get('label'), str(row.get('num'))]
                    writer.writerow(record)
                writer.writerow([])
        response = h.convertHtmlToCsv(file_path, tk.response)
        return response

    def overall_xml(self):
        #TODO
        self._overall()
        root = ET.Element('root')
        for table in tk.c.overall:
            tbl = ET.SubElement(root, 'table')
            header = ET.SubElement(tbl, 'header')
            header.text = table.get('header')
            for row in table.get('content', []):
                record = ET.SubElement(tbl, 'record')
                state = ET.SubElement(record, 'State')
                state.text = row.get('label')
                count = ET.SubElement(record, 'Count')
                count.text = str(row.get('num'))
        file_path = h.get_export_dir() + 'vdojstats-overall.xml'
        tree = ET.ElementTree(root)
        response = h.createResponseWithXML(tree, file_path, tk.response)
        return response

    '''
    all assets by activity
    '''
    def _all_assets_by_activity(self):
        tk.c.sub_title = _('All Assets By Activity')
        tk.c.allassets = h.count_assets_by_date_and_activity()

    def all_assets_by_activity(self):
        self._all_assets_by_activity()
        return render('vdojstats-all-assets-by-activity.html')

    def all_assets_by_activity_pdf(self):
        self._all_assets_by_activity()
        file_path = h.get_export_dir() + 'vdojstats-all-assets-by-activity.pdf'
        response = h.convertHtmlToPdf(tk.render('vdojstats-all-assets-by-activity-pdf.html'), file_path, tk.response)
        return response

    def all_assets_by_activity_csv(self):
        self._all_assets_by_activity()
        file_path = h.get_export_dir() + 'vdojstats-all-assets-by-activity.csv'
        with open(file_path, 'wb') as csvfile:
            writer = csv.writer(csvfile, lineterminator = '\n')
            record = ['Date', 'New', 'Modified', 'Deleted', 'Suspended', 'Unsuspended', 'Reviewed', 'Total']
            writer.writerow(record)
            for row in tk.c.allassets:
                record = [row['day'], row[h.activity_type_new], row[h.activity_type_changed], row[h.activity_type_deleted], row[h.activity_type_suspended], row[h.activity_type_unsuspended], row[h.activity_type_reviewed], row[h.total_per_date]]
                writer.writerow(record)
        response = h.convertHtmlToCsv(file_path, tk.response)
        return response

    def all_assets_by_activity_xml(self):
        self._all_assets_by_activity()
        root = ET.Element('root')
        for row in tk.c.allassets:
            record = ET.SubElement(root, 'record')
            day = ET.SubElement(record, 'Date')
            day.text = row['day']
            new = ET.SubElement(record, 'New')
            new.text = str(row[h.activity_type_new])
            changed = ET.SubElement(record, 'Modified')
            changed.text = str(row[h.activity_type_changed])
            deleted = ET.SubElement(record, 'Deleted')
            deleted.text = str(row[h.activity_type_deleted])
            suspended = ET.SubElement(record, 'Suspended')
            suspended.text = str(row[h.activity_type_suspended])
            unsuspended = ET.SubElement(record, 'Unsuspended')
            unsuspended.text = str(row[h.activity_type_unsuspended])
            reviewed = ET.SubElement(record, 'Reviewed')
            reviewed.text = str(row[h.activity_type_reviewed])
            total = ET.SubElement(record, 'Total')
            total.text = str(row[h.total_per_date])
        file_path = h.get_export_dir() + 'vdojstats-all-assets-by-activity.xml'
        tree = ET.ElementTree(root)
        response = h.createResponseWithXML(tree, file_path, tk.response)
        return response

    '''
    all assets by state
    '''
    def _all_assets_by_state(self):
        tk.c.sub_title = _('All Assets By State')
        #tk.c.allassets = h.count_assets_by_date()
        tk.c.allassets = h.count_assets_by_date_and_state()

    def all_assets_by_state(self):
        self._all_assets_by_state()
        return render('vdojstats-all-assets-by-state.html')

    def all_assets_by_state_pdf(self):
        self._all_assets_by_state()
        file_path = h.get_export_dir() + 'vdojstats-all-assets-by-state.pdf'
        response = h.convertHtmlToPdf(tk.render('vdojstats-all-assets-by-state-pdf.html'), file_path, tk.response)
        return response

    def all_assets_by_state_csv(self):
        self._all_assets_by_state()
        file_path = h.get_export_dir() + 'vdojstats-all-assets-by-state.csv'
        with open(file_path, 'wb') as csvfile:
            writer = csv.writer(csvfile, lineterminator = '\n')
            record = ['Date', 'Draft', 'Draft-Complete', 'Active', 'Deleted', 'Suspended', 'Total']
            writer.writerow(record)
            for row in tk.c.allassets:
                record = [row['day'], row[h.package_state_draft], row[h.package_state_draft_complete], row[h.package_state_active], row[h.package_state_deleted], row[h.package_state_suspended], row[h.total_per_date]]
                writer.writerow(record)
        response = h.convertHtmlToCsv(file_path, tk.response)
        return response

    def all_assets_by_state_xml(self):
        self._all_assets_by_state()
        root = ET.Element('root')
        for row in tk.c.allassets:
            record = ET.SubElement(root, 'record')
            day = ET.SubElement(record, 'Date')
            day.text = row['day']
            draft = ET.SubElement(record, 'Draft')
            draft.text = str(row[h.package_state_draft])
            draft_complete = ET.SubElement(record, 'Draft_Complete')
            draft_complete.text = str(row[h.package_state_draft_complete])
            active = ET.SubElement(record, 'Active')
            active.text = str(row[h.package_state_active])
            deleted = ET.SubElement(record, 'Deleted')
            deleted.text = str(row[h.package_state_deleted])
            suspended = ET.SubElement(record, 'Suspended')
            suspended.text = str(row[h.package_state_suspended])
            total = ET.SubElement(record, 'Total')
            total.text = str(row[h.total_per_date])
        file_path = h.get_export_dir() + 'vdojstats-all-assets-by-state.xml'
        tree = ET.ElementTree(root)
        response = h.createResponseWithXML(tree, file_path, tk.response)
        return response

    '''
    all assets by open dataset
    '''
    def _all_assets_by_open_dataset(self):
        tk.c.sub_title = _('All Assets By Datavic Datasets')
        tk.c.allassets = h.count_extra_revision_by_date_and_open_datasets()

    def all_assets_by_open_dataset(self):
        self._all_assets_by_open_dataset()
        return render('vdojstats-all-assets-by-open-dataset.html')

    def all_assets_by_open_dataset_pdf(self):
        self._all_assets_by_open_dataset()
        file_path = h.get_export_dir() + 'vdojstats-all-assets-by-open-dataset.pdf'
        response = h.convertHtmlToPdf(tk.render('vdojstats-all-assets-by-open-dataset-pdf.html'), file_path, tk.response)
        return response

    def all_assets_by_open_dataset_csv(self):
        self._all_assets_by_open_dataset()
        file_path = h.get_export_dir() + 'vdojstats-all-assets-by-open-dataset.csv'
        options = h.get_open_status_options()
        with open(file_path, 'wb') as csvfile:
            writer = csv.writer(csvfile, lineterminator = '\n')
            record = [u'Date']
            record.extend(options)
            record.append('Total')
            writer.writerow(record)
            for row in tk.c.allassets:
                record = [row['day']]
                for option in options:
                    record.append(row[option])
                record.append(row[h.total_per_date])
                writer.writerow(record)
        response = h.convertHtmlToCsv(file_path, tk.response)
        return response

    def all_assets_by_open_dataset_xml(self):
        self._all_assets_by_open_dataset()
        root = ET.Element('root')
        options = h.get_open_status_options()
        for row in tk.c.allassets:
            record = ET.SubElement(root, 'record')
            day = ET.SubElement(record, 'Date')
            day.text = row['day']

            for option in options:
                option_element = ET.SubElement(record, re.sub('[^a-zA-Z0-9_-]+', '_', option.encode('ascii','ignore')))
                option_element.text = str(row[option])

            total = ET.SubElement(record, 'Total')
            total.text = str(row[h.total_per_date])
        file_path = h.get_export_dir() + 'vdojstats-all-assets-by-open-dataset.xml'
        tree = ET.ElementTree(root)
        response = h.createResponseWithXML(tree, file_path, tk.response)
        return response

    '''
    Organizations
    '''
    def _assets(self):
        tk.c.sub_title = _('Assets')

        #search parameter
        org_ids = []
        private = None
        suspended = None
        package = None

        tk.c.selected_org_names = []
        tk.c.selected_package_states = []
        tk.c.selected_open_datasets = []
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
            if data.has_key('package'):
                tk.c.package = package = data.get('package', '')
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

            if data.has_key('pending_review[]'):
                tk.c.pending_review = data.get('pending_review[]')

            if data.has_key('open_datasets'):
                for key, value in data.iteritems():
                    if key == 'open_datasets' and len(value):
                        tk.c.selected_open_datasets.append(value)

        tk.c.option_org_names = h.get_org_names()
        tk.c.option_package_states = h.get_package_states()
        tk.c.option_open_datasets = h.get_open_status_options()
        tk.c.org_assets = h.list_assets(org_ids=org_ids, package_states=tk.c.selected_package_states, private=private, suspended=suspended, pending_review=tk.c.pending_review, opendata_sets=tk.c.selected_open_datasets, package=package)

    def assets(self):
        self._assets()
        return render('vdojstats-assets.html')

    def assets_pdf(self):
        self._assets()
        file_path = h.get_export_dir() + 'vdojstats-assets.pdf'
        response = h.convertHtmlToPdf(tk.render('vdojstats-assets-pdf.html'), file_path, tk.response)
        return response

    def assets_csv(self):
        self._assets()
        file_path = h.get_export_dir() + 'vdojstats-assets.csv'
        with open(file_path, 'wb') as csvfile:
            writer = csv.writer(csvfile, lineterminator = '\n')
            record = ['Organisation', 'Packasge', 'status', 'Private']
            if h.has_opendata_set(tk.c.selected_org_names):
                record.append('Datavic Datasets');
            record.extend(['Suspend', 'Suspend Reason', 'Last Review Date', 'Next Review Date'])
            writer.writerow(record)
            for row in tk.c.org_assets:
                record = [row['group_title'] or row['group_name'], row['package_title'] or row['package_name'], row['package_state'], row['is_private']]
                if h.has_opendata_set(tk.c.selected_org_names):
                    record.append(row['opendata_set']);
                record.extend([row['is_suspended'], row['suspend_reason'], row['last_review_date'], row['next_review_date']])
                writer.writerow(record)
        response = h.convertHtmlToCsv(file_path, tk.response)
        return response

    def assets_xml(self):
        self._assets()
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
            if h.has_opendata_set(tk.c.selected_org_names):
                opendata_set = ET.SubElement(record, 'Datavic_Datasets')
                opendata_set.text = row['opendata_set']
            is_suspended = ET.SubElement(record, 'Suspend')
            is_suspended.text = row['is_suspended']
            suspend_reason = ET.SubElement(record, 'Suspend_Reason')
            suspend_reason.text = row['suspend_reason']
            last_review_date = ET.SubElement(record, 'Last_Review_Date')
            last_review_date.text = row['last_review_date']
            next_review_date = ET.SubElement(record, 'Next_Review_Date')
            next_review_date.text = row['next_review_date']
        file_path = h.get_export_dir() + 'vdojstats-organizations.xml'
        tree = ET.ElementTree(root)
        response = h.createResponseWithXML(tree, file_path, tk.response)
        return response

    def autocomplete_package(self):
        if tk.request.method == 'GET':
            tk.response.headers['Content-Type']='application/json'
            data = tk.request.GET
            if data.has_key('search_key'):
                search_key = data.get('search_key')
                return json.dumps(h.autocomplete_package(search_key))
        return []

    '''
    all users
    '''
    def _all_users(self):
        tk.c.sub_title = _('All users')
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
                record = [row['fullname'] or row['name'], row['state'], row['sysadmin']]
                writer.writerow(record)
        response = h.convertHtmlToCsv(file_path, tk.response)
        return response

    def all_users_xml(self):
        self._all_users()
        root = ET.Element('root')
        for row in tk.c.user_list:
            record = ET.SubElement(root, 'record')
            name = ET.SubElement(record, 'User_Name')
            name.text = row['fullname'] or row['name']
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
        tk.c.sub_title = _('User Activities: %s'%(user.fullname or user.name) )
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
            record = ['Date Time', 'Activity', 'Object (Detail)', 'Activity (Detail)', 'Data']
            writer.writerow(record)
            for row in tk.c.user_activity_list:
                record = [row['timestamp'], row['activity_type'], row['object_type'], row['detail_type'], h.get_dispaly_name_for_object_data(row)]
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
            data = ET.SubElement(record, 'Data')
            data.text = h.get_dispaly_name_for_object_data(row)
        file_path = h.get_export_dir() + 'vdojstats-user.xml'
        tree = ET.ElementTree(root)
        response = h.createResponseWithXML(tree, file_path, tk.response)
        return response

    def report_add(self):
        """
        """        
        tk.c.sub_title = _('Add Report')
        
        if tk.request.method == 'POST':
            print 'POST'
            report = model.VDojStatsReport()
            report.name = tk.request.params.getone('name') if tk.request.params.getone('name') else None
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
                         'organizations' : [ { 'id': org.id, 'title' : org.title } for org in Session.query(Group.title, Group.id).filter(Group.is_organization == True).order_by(Group.title)],
                         'report_on' : 'activities'
                }
            }
        
            return render('vdojstats-report-add.html', extra_vars = vars)
        
    def _report_view(self, id, page, perpage):
        report = Session.query(model.VDojStatsReport).filter(model.VDojStatsReport.id == id).first()
        
        if not report:
            tk.abort(404, tk._('Report not found'))
            
        tk.c.sub_title = _(report.name)
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

            if report.custodian:
                package_query = Session.query(Package.maintainer)
                activity_query = activity_query.filter(User.name.in_(package_query))
            
            activity_query = activity_query.filter(Activity.user_id.in_(member_query))
            
            total = activity_query.count()
            
            if page is not None and perpage is not None:
                activity_query = activity_query.offset(page * perpage).limit(perpage)
                                
            activities = [{
                        'activity': a.as_dict(),
                        'user': u.as_dict()
                        } for a,u in activity_query]
            
            return report.as_dict(), activities, total, show_org
            
        elif report.report_on == "details":
            
            user_query = Session.query(User.id, User.name, User.fullname, User.email, User.state, User.sysadmin, Group.title.label("organization"), Member.capacity).join(Member, Member.table_id == User.id).join(Group, Group.id == Member.group_id).filter(Member.table_name == 'user').filter(Member.state == 'active').filter(Group.is_organization == True).order_by(User.name)
                       
            if report.org_id is not None and len(report.org_id) > 0:
                user_query = user_query.filter(Member.group_id == report.org_id)
                
            if report.permission != 'all':
                user_query = user_query.filter(Member.capacity == report.permission)
                
            if report.custodian:
                package_query = Session.query(Package.maintainer)
                user_query = user_query.filter(User.name.in_(package_query))
                
            total = user_query.count()
            
            if page is not None and perpage is not None:
                user_query = user_query.offset(page * perpage).limit(perpage)
                
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
            
            return report.as_dict(), users, total, show_org
        else:
            tk.abort(404, tk._('Report not found'))
        
        
    def report_view(self, id):
        """
        """    
        page = int(tk.request.params.get('page', 0))
        perpage = int(tk.request.params.get('perpage', 10))
            
        report, results, total, show_org = self._report_view(id, page, perpage)
        
        tk.c.sub_title = _(report['name'])
        
        tk.c.total = total
        tk.c.page = page
        tk.c.perpage = perpage
        tk.c.start_record = (page * perpage) + 1
        tk.c.end_record = min((page * perpage) + perpage, total)
        tk.c.lastpage = int(math.ceil(total / perpage))
        tk.c.report = report
            
        if report['report_on'] == "activities":          
            tk.c.activities = results
        elif report['report_on'] == "details":
            tk.c.users = results
            tk.c.show_org = show_org
        else:
            tk.abort(404, tk._('Report not found'))
            
        return render('vdojstats-report-view.html')
    
    def report_view_pdf(self, id):
        report, results, total, show_org = self._report_view(id, None, None)
        
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
        report, results, total, show_org = self._report_view(id, None, None)
        file_path = '%s/%s.csv' % (h.get_export_dir(), re.sub('[^a-zA-Z0-9_-]+', '_', report['name'].encode('ascii','ignore')))
        
        if report['report_on'] == "activities": 
            with open(file_path, 'wb') as csvfile:
                writer = csv.writer(csvfile, lineterminator = '\n')
                record = ['Time', 'User', 'Activity Type', 'Data']
                writer.writerow(record)
                for row in results:
                    activity_data = {}
                    data_name = ''
                    if 'activity' in row and 'data' in row['activity']:
                        activity = row['activity']['data']
                        if 'package' in activity:
                            activity_data = activity.get('package')
                        elif 'dataset' in activity:
                            activity_data = activity.get('dataset')
                        elif 'group' in activity:
                            activity_data = activity.get('group')
                        data_name = activity_data.get('name', '')
                    record = [row['activity']['timestamp'], row['user']['fullname'] or row['user']['name'], row['activity']['activity_type'], data_name]
                    writer.writerow(record)    
        elif report['report_on'] == "details":
            with open(file_path, 'wb') as csvfile:
                writer = csv.writer(csvfile, lineterminator = '\n')
                record = ['name', 'email', 'state', 'organization', 'role', 'system administrator']
                writer.writerow(record)
                for row in results:
                    record = [row['fullname'] or row['name'], row['email'], row['state'], row['organization'], row['capacity'], row['sysadmin']]
                    writer.writerow(record)
            
        response = h.convertHtmlToCsv(file_path, tk.response)
        return response

    def report_view_xml(self, id):
        report, results, total, show_org = self._report_view(id, None, None)
        file_path = '%s/%s.xml' % (h.get_export_dir(), re.sub('[^a-zA-Z0-9_-]+', '_', report['name'].encode('ascii','ignore')))
                
        if report['report_on'] == "activities":
            activity_list = []
            for row in results:
                data_name = ''
                activity_data = {}
                if 'activity' in row and 'data' in row['activity']:
                    activity = row['activity']['data']
                    if 'package' in activity:
                        activity_data = activity.get('package')
                    elif 'dataset' in activity:
                        activity_data = activity.get('dataset')
                    elif 'group' in activity:
                        activity_data = activity.get('group')
                    data_name = activity_data.get('name', '')
                activity_list.append({
                    '@time': row['activity']['timestamp'],
                    '@user': row['user']['fullname'] or row['user']['name'],
                    '@activity_type': row['activity']['activity_type'],
                    '@data_name': data_name
                    })
            tree = h.dict_to_etree({ 'activities' : {'activity' : activity_list }})
            response = h.createResponseWithXML(tree, file_path, tk.response)
                    
                    
        elif report['report_on'] == "details":
            tree = h.dict_to_etree({ 'users' : {'user' : [ {
                                                            '@name': row['fullname'] or row['name'],
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
        tk.c.sub_title = _('Edit Report')
        
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
        
    


