# -#-coding: utf-8 -#-
import datetime
import ckan.plugins.toolkit as tk
import sys
import ckan
import pylons
import copy
from ckanext.vdojstats.model import VDojStatsReport
from ckan.common import _
from ckan import model
from ckan.model.meta import metadata
from ckan.model import Session, Activity, ActivityDetail
from ckan.lib.navl.dictization_functions import StopOnError
from ckan.lib.helpers import full_current_url, url_for, link_to, dataset_display_name, markdown_extract
from urlparse import urlparse
from ckan.logic.converters import convert_group_name_or_id_to_id
from sqlalchemy import *
import ckan.logic as logic
from xhtml2pdf import pisa             # import python module
import os
import csv
import xml.etree.ElementTree as ET
import pylons.config as config

check_access = logic.check_access
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized

activity_type_new = 'new'
activity_type_changed = 'changed'
activity_type_deleted = 'deleted'
activity_type_suspended = 'suspended'
activity_type_unsuspended = 'unsuspended'
activity_type_reviewed = 'reviewed'

object_type_package = 'package'
object_type_resource = 'resource'
object_type_metadata = 'metadata'

dataset_activity_type_new = 'new package'
dataset_activity_type_changed = 'changed package'
dataset_activity_type_deleted = 'deleted package'
dataset_activity_type_reviewed = 'package reviewed'

total_per_date = 'total_per_date'
package_state_draft = 'draft'
package_state_draft_complete = 'draft-complete'
package_state_active = 'active'
package_state_deleted = 'deleted'
package_state_suspended = 'suspended'
package_state_unsuspended = 'unsuspended'
user_state_active = 'active'


DATE_FORMAT = '%d-%m-%Y'
DATETIME_FORMAT = '%d-%m-%Y %H:%M:%S'

def table(name):
    return Table(name, metadata, autoload=True)

def datetime2date(datetime_):
    return datetime.date(datetime_.year, datetime_.month, datetime_.day)

def _count_public_or_private_assets(is_private, org_id=None):
    """
     get count of the private/public package
     parameter: is_private (boolean)
     parameter: organization_id
    """
    package = table('package')
    sql = select([func.count(package.c.id).label('NUM'), package.c.private]).group_by(package.c.private)
    if org_id is not None:
        sql = sql.where(package.c.owner_org == org_id)
    rows = model.Session.execute(sql).fetchall()
    for row in rows:
        if row['private']==is_private:
            return row['NUM']
    return 0

def _count_state_assets(state, org_id=None):
    """
     get count of the package with the parameter
     parameter: state (string)
     parameter: organization_id
    """
    package = table('package')
    sql = select([func.count(package.c.id).label('NUM'), package.c.state]).group_by(package.c.state)
    if org_id is not None:
        sql = sql.where(package.c.owner_org == org_id)
    rows = model.Session.execute(sql).fetchall()
    for row in rows:
        if row['state']==state:
            return row['NUM']
    return 0

def _count_state_users(state):
    """
     get count of the package with the parameter
     parameter: state (string)
     parameter: organization_id
    """
    user = table('user')
    sql = select([func.count(user.c.id).label('NUM'), user.c.state]).group_by(user.c.state)
    rows = model.Session.execute(sql).fetchall()
    for row in rows:
        if row['state']==state:
            return row['NUM']
    return 0

def _count_assets_by_date_and_activity(activity_types=None):
    """
     get count of assets by date
     parameter: activity_types (list)
    """
    types = []
    if activity_types is not None:
        if isinstance(activity_types, list):
            types = activity_types
        else:
            types.append(activity_types)

    package = table('package')
    activity = table('activity')
    detail = table('activity_detail')
    cols = [func.count(activity.c.activity_type).label('num'), activity.c.activity_type.label('activity_type'), detail.c.object_type, detail.c.activity_type.label('detail_type'), func.date_trunc('day', activity.c.timestamp).label('day')]
    sql = select(cols, from_obj=[package, activity.outerjoin(detail)]).where(package.c.id == activity.c.object_id).where ( detail.c.object_type == object_type_package) #only package level
    if len(types):
        sql = sql.where(detail.c.activity_type.in_(types))
    sql = sql.group_by(func.date_trunc('day', activity.c.timestamp)).group_by(activity.c.activity_type).group_by(detail.c.object_type).group_by(detail.c.activity_type).order_by(func.date_trunc('day', activity.c.timestamp).desc())
    rows = model.Session.execute(sql).fetchall()
    activity_list = []
    for row in rows:
        activity_list.append({
            'num':row['num'],
            'day':row['day'].strftime(DATE_FORMAT),
            'activity_type':row['activity_type'],
            'object_type':row['object_type'],
            'detail_type':row['detail_type'],
            })

    return activity_list

def count_assets_by_date_and_activity():

    records = []
    record = None
    current_day = None
    rows = _count_assets_by_date_and_activity()
    for row in rows:
        if row['day'] != current_day:
            if record is not None:
                record.update({total_per_date:record[activity_type_new]+record[activity_type_changed]+record[activity_type_deleted]+record[activity_type_suspended]+record[activity_type_unsuspended]+record[activity_type_reviewed]})
                records.append(record)

            current_day = row['day']
            record = {
                'day': row['day'],
                activity_type_new: 0L,
                activity_type_changed: 0L,
                activity_type_deleted: 0L,
                activity_type_suspended: 0L,
                activity_type_unsuspended: 0L,
                activity_type_reviewed: 0L,
                total_per_date: 0L,
            }
        record.update({row['detail_type']:row['num']})
    #finalize
    if record is not None:
        record.update({total_per_date:record[activity_type_new]+record[activity_type_changed]+record[activity_type_deleted]+record[activity_type_suspended]+record[activity_type_unsuspended]+record[activity_type_reviewed]})
        records.append(record)
    return records

def _count_assets_by_date_and_state_without_timezone(states_types=None):
    """
     get count of assets by date
     parameter: activity_types (list)
    """
    types = []
    if states_types is not None:
        if isinstance(states_types, list):
            types = states_types
        else:
            types.append(states_types)

    revision = table('package_revision')
    package = table('package')
    cols = [func.count(revision.c.state).label('num'), revision.c.state.label('state'), func.date_trunc('day', revision.c.revision_timestamp).label('day')]
    sql = select(cols, from_obj=[revision.outerjoin(package)]).where(package.c.id == revision.c.id)
    if len(types):
        sql = sql.where(revision.c.state.in_(types))
    sql = sql.group_by(func.date_trunc('day', revision.c.revision_timestamp)).group_by(revision.c.state).order_by(func.date_trunc('day', revision.c.revision_timestamp).desc())
    rows = model.Session.execute(sql).fetchall()
    state_list = []
    for row in rows:
        state_list.append({
            'num':row['num'],
            'day':row['day'].strftime(DATE_FORMAT),
            'state':row['state'],
            })

    return state_list

def _count_assets_by_date_and_state():
    """
     get count of assets by date
     parameter: activity_types (list)
    """

    tz_code = config.get('ckan.timezone', 'Australia/Melbourne')

    sql = "SELECT COUNT(revision.state) as num, revision.state as revision_state, date_trunc('day', (revision.metadata_modified + interval '1' hour * EXTRACT(timezone_hour from timezone('%s', revision.metadata_modified)) + interval '1' minute * EXTRACT(timezone_minute from timezone('%s', revision.metadata_modified)))) AS day "%(tz_code, tz_code)
    sql = sql + " FROM package_revision revision "
    sql = sql + " INNER JOIN package ON revision.id = package.id "
    sql = sql + " GROUP BY day, revision_state "
    sql = sql + " ORDER BY day DESC "

    rows = model.Session.execute(sql).fetchall()
    state_list = []
    for row in rows:
        state_list.append({
            'num':row['num'],
            'day':row['day'].strftime(DATE_FORMAT),
            'state':row['revision_state'],
            })

    return state_list


def count_today_review_assets(org_id=None):

    return _count_delay_review_assets(org_id, only_today=True)

def count_delay_review_assets(org_id=None):

    return _count_delay_review_assets(org_id, only_today=False)

def _count_delay_review_assets(org_id=None, only_today=True):
    """
     get count of the review-scheduled package
     parameter: organization_id
    """
    package_review = table('package_review')
    cols = [func.count(package_review.c.package_id).label('NUM')]
    if org_id is None:
        sql = select(cols)
    else:
        package = table('package')
        sql = select(cols, from_obj=[package_review.join(package)]).where(package.c.owner_org == org_id)
    if only_today:
        sql = sql.where(package_review.c.next_review_date == datetime.date.today())
    else:   #delay
        sql = sql.where(package_review.c.next_review_date < datetime.date.today())
    rows = model.Session.execute(sql).fetchall()
    for row in rows:
        return row['NUM']
    return 0
def count_published_assets(org_id=None):
    return _count_public_or_private_assets(False, org_id)

def count_private_assets(org_id=None):
    return _count_public_or_private_assets(True, org_id)

def count_active_assets(org_id=None):
    return _count_state_assets(package_state_active, org_id)

def count_dormant_assets(org_id=None):
    """
     get count of the package with the parameter
     parameter: organization_id
    """
    package = table('package')
    sql = select([func.count(package.c.id).label('NUM')]).where(package.c.state != package_state_active)
    if org_id is not None:
        sql = sql.where(package.c.owner_org == org_id)
    rows = model.Session.execute(sql).fetchall()
    for row in rows:
        return row['NUM']
    return 0

def count_active_users():
    return _count_state_users('active')

def count_dormant_users():
    """
     get count of the package with the parameter
     parameter: state (string)
     parameter: organization_id
    """
    user = table('user')
    sql = select([func.count(user.c.id).label('NUM')]).where(user.c.state != 'active')
    rows = model.Session.execute(sql).fetchall()
    for row in rows:
        return row['NUM']
    return 0

def count_assets_by_date_and_state():

    records = []
    record = None
    current_day = None
    rows = _count_assets_by_date_and_state()
    for row in rows:
        if row['day'] != current_day:
            if record is not None:
                record.update({total_per_date:record[package_state_draft]+record[package_state_draft_complete]+record[package_state_active]+record[package_state_deleted]+record[package_state_suspended]})
                records.append(record)

            current_day = row['day']
            record = {
                'day': row['day'],
                package_state_draft: 0L,
                package_state_draft_complete: 0L,
                package_state_active: 0L,
                package_state_deleted: 0L,
                package_state_suspended: 0L,
                total_per_date: 0L,
            }
        record.update({row['state']:row['num']})
    #finalize
    if record is not None:
        record.update({total_per_date:record[package_state_draft]+record[package_state_draft_complete]+record[package_state_active]+record[package_state_deleted]+record[package_state_suspended]})
        records.append(record)
    return records

def list_users(candidate=None, is_active=None, is_sysadmin=None):
    #TODO
    #page = int(request.params.get('page', 1))
    order_by = ('name')

    context = {'return_query': True, 'user': tk.c.user or tk.c.author,
               'auth_user_obj': tk.c.userobj}

    data_dict = {'order_by': order_by}
    try:
        check_access('user_list', context, data_dict)
    except NotAuthorized:
        abort(401, _('Not authorized to see this page'))

    user = table('user')
    sql = select([user.c.id, user.c.fullname, user.c.name, user.c.state, user.c.sysadmin])
    if candidate is not None:
        sql = sql.where(or_(user.c.fullname.like("%"+"%s"%(candidate)+"%"), user.c.name.like("%"+"%s"%(candidate)+"%")))
    if is_active is not None:
        if is_active:
            sql = sql.where(user.c.state==user_state_active)
        else:
            sql = sql.where(user.c.state!=user_state_active)
    if is_sysadmin is not None:
        sql = sql.where(user.c.sysadmin == is_sysadmin)
    rows = model.Session.execute(sql).fetchall()
    users_list = []
    for row in rows:
        users_list.append({
            'id':row['id'],
            'name':row['name'] ,
            'fullname':row['fullname'],
            'state':'Yes' if row['state'] == user_state_active else 'No',
            'sysadmin':'Yes' if row['sysadmin'] else 'No',
            })

    #return get_action('user_list')(context, data_dict) #this gets only active user
    return users_list

def get_user(user_id):
    context = {'model': model,
               'user': tk.c.user}
    data_dict = {'id': user_id}
    return get_action('user_show')(context, data_dict)

def list_activities_for_user(user_id, offset=0, limit=1000):
    context = {'return_query': True, 'user': tk.c.user or tk.c.author,
               'auth_user_obj': tk.c.userobj}

    data_dict = {'id': user_id, 'offset' : offset, 'limit' : limit}
    try:
        check_access('user_list', context, data_dict)

    except NotAuthorized:
        abort(401, _('Not authorized to see this page'))

    #return get_action('user_activity_list')(context, data_dict)
    #TODO
    user = table('user')
    activity = table('activity')
    detail = table('activity_detail')
    cols = [activity.c.activity_type.label('activity_type'), activity.c.data.label('activity_data'), detail.c.activity_type.label('detail_type'), detail.c.object_type, activity.c.timestamp]
    sql = select(cols, from_obj=[user, activity.outerjoin(detail) ]).where(user.c.id == activity.c.user_id).where( user.c.id == user_id).order_by(activity.c.timestamp.desc())
    rows = model.Session.execute(sql).fetchall()
    activity_list = []
    for row in rows:
        activity_list.append({
            'activity_type':(row['activity_type'] or '').title(),#capitalize
            'detail_type':(row['detail_type'] or '').title(),#capitalize
            'object_type':(row['object_type'] or '').title(),#capitalize
            'timestamp':row['timestamp'].strftime(DATETIME_FORMAT),
            'activity_data':row['activity_data'],
            })

    return activity_list

def get_organization_id(name):
    context = {'model': model,
               'session': model.Session,
               'user': tk.c.user or tk.c.author}
    try:
        return convert_group_name_or_id_to_id(name, context)
    except Exception:
        print 'cannot convert org name to org id'

def list_assets(org_ids=None, package_states=None, private=None, suspended=None, pending_approval=None, package=None):
    """
     get list of assets
     parameter: org_ids (list)
     parameter: package_states (list)
     parameter: private (boolean)
     parameter: suspended (boolean)
     parameter: pending_approval (boolean)
    """
    #parameter check
    organizations = []
    if org_ids is not None:
        if isinstance(org_ids, list):
            organizations = ["'%s'"%(org_id) for org_id in org_ids]
        else:
            organizations.append("'%s'"%(org_ids))

    pstats = []
    if package_states is not None:
        if isinstance(package_states, list):
            pstats = ["'%s'"%(package_state) for package_state in package_states]
        else:
            pstats.append("'%s'"%(package_states))

    sql = "SELECT P.id AS package_id, P.title AS package_title, P.name AS package_name, P.state AS package_state, P.private, P.type AS package_type, P.owner_org, G.title AS group_title, G.name AS group_name, review.next_review_date, (CASE WHEN suspend.package_id IS NOT NULL THEN True ELSE False END) AS suspended, suspend.reason AS suspend_reason, activity.timestamp AS activity_timestamp "
    sql = sql + "FROM package P " 
    sql = sql + "LEFT OUTER JOIN \"group\" G ON P.owner_org = G.id AND G.is_organization IS TRUE "  #only organization
    sql = sql + "LEFT OUTER JOIN package_review review ON review.package_id = P.id "
    sql = sql + "LEFT OUTER JOIN package_suspend suspend ON suspend.package_id = P.id "
    sql = sql + "LEFT OUTER JOIN (SELECT object_id, activity_type, MAX(timestamp) AS timestamp FROM activity WHERE activity_type = '%s' GROUP BY object_id, activity_type) activity ON activity.object_id = P.id "%(dataset_activity_type_reviewed)
    sql = sql + "WHERE P.id IS NOT NULL "   #dummy statement
    if len(organizations):
        sql = sql + "AND P.owner_org IN (%s) "%(",".join(organizations))
    if len(pstats):
        sql = sql + "AND P.state IN (%s) "%(",".join(pstats))
    if private is not None:
        sql = sql + "AND P.private = %r "%(private)
    if suspended is not None:
        if suspended:
            sql = sql + "AND suspend.package_id IS NOT NULL "
        else:
            sql = sql + "AND suspend.package_id IS NULL  "
    if pending_approval is not None:
        if pending_approval:
            sql = sql + "AND review.package_id IS NOT NULL "
        else:
            sql = sql + "AND review.package_id IS NULL "
    if package is not None:
        sql = sql + "AND (P.title LIKE '%" + package + "%' OR P.name LIKE '%" + package + "%') " 
    sql = sql + "ORDER BY G.name ASC "
    rows = model.Session.execute(sql).fetchall()
    activity_list = []
    for row in rows:
        next_review_date = ''
        last_review_date = ''
        if row['next_review_date']:
            next_review_date = row['next_review_date'].strftime(DATE_FORMAT)
        if row['activity_timestamp']:
            last_review_date = row['activity_timestamp'].strftime(DATE_FORMAT)

        activity_list.append({
            'package_id':row['package_id'],
            'package_title':row['package_title'],
            'package_name':row['package_name'],
            'package_state':row['package_state'].title(),
            'is_private':'Yes' if row['private'] else 'No',
            'is_suspended':'Yes' if row['suspended'] else 'No',
            'suspend_reason': row['suspend_reason'] or '',
            'owner_org':row['owner_org'] or '',
            'group_title':row['group_title'] or '',
            'group_name':row['group_name'] or '',
            'last_review_date':last_review_date,
            'next_review_date':next_review_date,
            })
    return activity_list

def autocomplete_package(search_key=None):
    #TODO
    #page = int(request.params.get('page', 1))

    package = table('package')
    sql = select([package.c.id, package.c.name, package.c.title])
    if search_key is not None:
        sql = sql.where(or_(package.c.name.like("%"+"%s"%(search_key)+"%"), package.c.title.like("%"+"%s"%(search_key)+"%")))
    sql.order_by(package.c.name.asc()).order_by(package.c.title.asc())
    rows = model.Session.execute(sql).fetchall()
    package_list = []
    for row in rows:
        package_list.append({
            'id':row['id'],
            'name':row['name'] ,
            'title':row['title'],
            })

    return package_list


def get_org_names():
    context = {'model': model,
               'user': tk.c.user}
    data_dict = {}
    names = get_action('organization_list')(context, data_dict)
    organization_options = []
    for name in names:
        organization_options.append({
            'text': name,
            'value': name,
        })
    return organization_options

def get_package_states():
    return [
        {'text': package_state_draft.title(), 'value': package_state_draft},
        {'text': package_state_draft_complete.title(), 'value': package_state_draft_complete},
        {'text': package_state_active.title(), 'value': package_state_active},
        {'text': package_state_deleted.title(), 'value': package_state_deleted},
        {'text': package_state_suspended.title(), 'value': package_state_suspended},
    ]
    
def get_reports():
    reports = [r.as_dict() for r in Session.query(VDojStatsReport).order_by(VDojStatsReport.name).all()]
    return reports

# Utility function
def convertHtmlToPdf(sourceHtml, outputFilename, response):
    # open output file for writing (truncated binary)
    resultFile = open(outputFilename, "w+b")

    # convert HTML to PDF
    pisaStatus = pisa.CreatePDF(
            sourceHtml,                # the HTML to convert
            dest=resultFile)           # file handle to recieve result

    resultFile.seek(0)
    pdf = resultFile.read()

    # close output file
    resultFile.close()                 # close output file

    response.headers['Content-Type']='application/pdf'
    response.headers['Content-disposition']='attachment; filename=%s'%(os.path.basename(outputFilename.encode('ascii','ignore')))
    response.headers['Content-Length']=len(pdf)
    response.body = pdf

    return response

def convertHtmlToCsv(inputFilename, response):
    content = []        
    with open(inputFilename, 'rb') as csvfile:
        reader = csv.reader(csvfile, lineterminator = '\n')
        for row in reader:
            content.append(','.join(row))
    response.headers['Content-Type']='application/csv'
    response.headers['Content-disposition']='attachment; filename=%s'%(os.path.basename(inputFilename.encode('ascii','ignore')))
    response.headers['Content-Length']=os.path.getsize(inputFilename)
    response.body = "\n".join(content)
    return response

def createResponseWithXML(tree, filename, response):
    #write xml to disk
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    #root = tree.parse(filename)
    response.headers['Content-Type']='text/xml'
    response.headers['Content-disposition']='attachment; filename=%s'%(os.path.basename(filename.encode('ascii','ignore')))
    response.headers['Content-Length']=os.path.getsize(filename)
    response.body = ET.tostring(tree.getroot())
    return response

def current_time():
    return datetime.datetime.utcnow().strftime(DATETIME_FORMAT)

def get_export_dir():
    site_id = config.get('ckan.site_id', 'default')
    directory = config.get('vdojstats.export_dir', '/tmp/export/%s/'%(site_id))
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def get_export_header_title():
    return config.get('vdojstats.export_header', 'Victoria DoJ')

def get_site_logo_url():
    parsed_uri = urlparse(full_current_url())
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    return "%s%s"%(domain, config.get('ckan.site_logo', 'vdoj-logo-white-transparent.png'))


def get_activity_dict():
    return {
        #package
        u'new': {'activity_type': dataset_activity_type_new, 'object_type': object_type_package, 'detail_type': activity_type_new},
        u'edit': {'activity_type': dataset_activity_type_changed, 'object_type': object_type_package, 'detail_type': activity_type_changed},
        u'delete': {'activity_type': dataset_activity_type_deleted, 'object_type': object_type_package, 'detail_type': activity_type_deleted},
        #metadata => the same as edit
        u'new_metadata': {'activity_type': dataset_activity_type_changed, 'object_type': object_type_package, 'detail_type': activity_type_changed},
        #suspend
        u'index': {'activity_type': dataset_activity_type_changed, 'object_type': object_type_package, 'detail_type': package_state_suspended},
        u'unsuspend': {'activity_type': dataset_activity_type_changed, 'object_type': object_type_package, 'detail_type': package_state_unsuspended},
        #resource
        u'new_resource': {'activity_type': dataset_activity_type_changed, 'object_type': object_type_resource, 'detail_type': activity_type_new},
        u'resource_edit': {'activity_type': dataset_activity_type_changed, 'object_type': object_type_resource, 'detail_type': activity_type_changed},
        u'resource_delete': {'activity_type': dataset_activity_type_changed, 'object_type': object_type_resource, 'detail_type': activity_type_deleted},
    }

def get_activity_info(action):
    return get_activity_dict()[action]

def create_activity(context, pkg_dict):

    model = context['model']
    session = context['session']
    user = context['user']
    userobj = model.User.get(user)

    dataset_context = {'model': model, 'session': session,
           'api_version': 3, 'for_edit': True,
           'user': tk.c.user or tk.c.author, 'auth_user_obj': userobj}
    action = tk.c.action
    if action not in get_activity_dict():
        return

    activity_info = get_activity_info(action)
    activity_object_id = None
    activity_data = {}
    detail_data = {}
    activity_object_id = pkg_dict.get('id')
    if not activity_object_id:
        return

    #retrieve package data as activity_data
    try:
        activity_data =  tk.get_action('package_show')(dataset_context, {'id': activity_object_id})
    except NotFound:
        #at new creation of the package, the data has not been existing in the DB, so retrieve the data from pkg_dict and sanitize it
        activity_data = copy.deepcopy(pkg_dict)
        _sanitize_dict(activity_data) #sanitize

    #retrieve package/resource data as detail_data
    if activity_info.get('object_type') == object_type_package:
        detail_data = activity_data
    elif activity_info.get('object_type') == object_type_resource:
        if tk.c.resource_id:
            detail_object_id = tk.c.resource_id
            try:
                detail_data =  tk.get_action('resource_show')(dataset_context, {'id': detail_object_id})
            except NotFound:
                print '************no id=%s**************'%(detail_object_id)
                pass
        elif 'resources' in pkg_dict:
            #retrieve non-id resource
            activity_data = copy.deepcopy(pkg_dict)
            _sanitize_dict(activity_data) #sanitize
            for resource in activity_data.get('resources'):
                if not 'id' in resource:
                    #new resource data
                    detail_data = copy.deepcopy(resource)
                    _sanitize_dict(detail_data) #sanitize
                    detail_data.update({'id':''})#to avoid server error at displaying on the user activity
    else:
        return  #ignore unexpected

    if len(activity_data)==0:
        return

    detail_type = activity_info.get('detail_type')

    #create activity record
    activity = Activity(user_id=userobj.id, object_id=activity_object_id, revision_id=pkg_dict.get('revision_id'), activity_type=activity_info.get('activity_type'), data={object_type_package: activity_data,})#always package
    activity.save()

    #create detail record
    if len(detail_data):
        activity_detail = ActivityDetail(activity_id=activity.id, object_id=activity.object_id, object_type=activity_info.get('object_type'), activity_type=detail_type, data={activity_info.get('object_type'): detail_data,})
        activity_detail.save()

def _sanitize_dict(dictionary):
    for k,v in dictionary.items():
        if isinstance(v, dict):
            _sanitize_dict(v)
        elif isinstance(v, list):
            for i in v:
                _sanitize_dict(i)
        if type(v) is datetime.datetime:
            del dictionary[k] #delete this since this contains unserialized datetime object

def dict_to_etree(d):
    def _to_etree(d, root):
        if not d:
            pass
        elif isinstance(d, basestring):
            root.text = d
        elif isinstance(d, dict):
            for k,v in d.items():
                assert isinstance(k, basestring)
                if k.startswith('#'):
                    assert k == '#text' and isinstance(v, basestring)
                    root.text = v
                elif k.startswith('@'):
                    assert isinstance(v, basestring)
                    root.set(k[1:], v)
                elif isinstance(v, list):
                    for e in v:
                        _to_etree(e, ET.SubElement(root, k))
                else:
                    _to_etree(v, ET.SubElement(root, k))
        else: assert d == 'invalid type'
    assert isinstance(d, dict) and len(d) == 1
    tag, body = next(iter(d.items()))
    node = ET.Element(tag)
    _to_etree(body, node)
    return ET.ElementTree(node)



def vdoj_group_link(group, wordcount=None):
    url = url_for(controller='group', action='read', id=group['name'])
    display_text = group['title']
    if wordcount:
        display_text = markdown_extract(group['title'], extract_length=wordcount)
    return link_to(display_text, url)

def vdoj_organization_link(organization, wordcount=None):
    url = url_for(controller='organization', action='read', id=organization['name'])
    display_text = organization['name']
    if wordcount:
        display_text = markdown_extract(organization['name'], extract_length=wordcount)
    return link_to(display_text, url)

def vdoj_dataset_link(package_or_package_dict, wordcount=None):
    if isinstance(package_or_package_dict, dict):
        name = package_or_package_dict['name']
    else:
        name = package_or_package_dict.name
    display_text = dataset_display_name(package_or_package_dict)
    if wordcount:
        display_text = markdown_extract(display_text, extract_length=wordcount)
    return link_to(
        display_text,
        url_for(controller='package', action='read', id=name)
    )

def get_dispaly_name_for_object_data(data):
    display_name = ''
    if 'activity_data' in data:
        activity_data = data.get('activity_data')
        if 'package' in activity_data:
            pkg = activity_data.get('package')
            display_name = pkg.get('name')
       	elif 'dataset' in activity_data:
            ds = activity_data.get('dataset')
            display_name = ds.get('name')
       	elif 'group' in activity_data and activity_data.get('group'):
            group = activity_data.get('group')
            if group.get('is_organization'):
                display_name = group.get('name')
            else:
                display_name = group.get('title')
    return display_name

