# -#-coding: utf-8 -#-
import datetime
import ckan.plugins.toolkit as tk
import ckan
import pylons
from ckanext.vdojstats.model import VDojStatsReport
from ckan.common import _
from ckan import model
from ckan.model.meta import metadata
from ckan.model import Session
from ckan.lib.navl.dictization_functions import StopOnError
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
package_state_draft = 'draft'
package_state_active = 'active'
package_state_deleted = 'deleted'
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
    print rows
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
    print rows
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
    print rows
    for row in rows:
        if row['state']==state:
            return row['NUM']
    return 0

def _count_assets_by_date(activity_types=None):
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
    sql = select(cols, from_obj=[package, activity.outerjoin(detail)]).where(package.c.id == activity.c.object_id).where( detail.c.object_type == 'Package')
    if len(types):
        sql = sql.where(detail.c.activity_type.in_(types))
    sql = sql.group_by(func.date_trunc('day', activity.c.timestamp)).group_by(activity.c.activity_type).group_by(detail.c.object_type).group_by(detail.c.activity_type).order_by(func.date_trunc('day', activity.c.timestamp).desc())
    rows = model.Session.execute(sql).fetchall()
    activity_list = []
    for row in rows:
        activity_list.append({
            'num':row['num'],
            'day':row['day'].strftime(DATE_FORMAT),
            'detail_type':row['detail_type'],
            })

    return activity_list

def count_pending_approval_assets(org_id=None):
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
    rows = model.Session.execute(sql).fetchall()
    print rows
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
    print rows
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
    print rows
    for row in rows:
        return row['NUM']
    return 0

def count_assets_by_date():

    records = []
    record = None
    current_day = None
    rows = _count_assets_by_date()
    for row in rows:
        if row['day'] != current_day:
            if record is not None:
                records.append(record)

            current_day = row['day']
            record = {
                'day': row['day'],
                activity_type_new: 0L,
                activity_type_changed: 0L,
                activity_type_deleted: 0L,
            }
        record.update({row['detail_type']:row['num']})
    #finalize
    if record is not None:
        records.append(record)
    return records

def count_created_assets_by_date():
    return _count_assets_by_date([activity_type_new])

def count_modified_assets_by_date():
    return _count_assets_by_date([activity_type_changed])

def count_deleted_assets_by_date():
    return _count_assets_by_date([activity_type_deleted])

def list_users():
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
    cols = [activity.c.activity_type.label('activity_type'), detail.c.activity_type.label('detail_type'), detail.c.object_type, activity.c.timestamp]
    sql = select(cols, from_obj=[user, activity.outerjoin(detail) ]).where(user.c.id == activity.c.user_id).where( user.c.id == user_id).order_by(activity.c.timestamp.desc())
    rows = model.Session.execute(sql).fetchall()
    activity_list = []
    for row in rows:
        activity_list.append({
            'activity_type':row['activity_type'],
            'detail_type':row['detail_type'] or '',
            'object_type':row['object_type'] or '',
            'timestamp':row['timestamp'].strftime(DATETIME_FORMAT),
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

def list_assets(org_ids=None, package_states=None, private=None, suspended=None, pending_approval=None):
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

    sql = "SELECT P.id AS package_id, P.title AS package_title, P.name AS package_name, P.state AS package_state, P.private, P.type AS package_type, P.owner_org, G.title AS group_title, G.name AS group_name, review.next_review_date, (CASE WHEN suspend.package_id IS NOT NULL THEN True ELSE False END) as suspended, suspend.reason AS suspend_reason "
    sql = sql + "FROM \"group\" G, package P " 
    sql = sql + "LEFT OUTER JOIN package_review review ON review.package_id = P.id "
    sql = sql + "LEFT OUTER JOIN package_suspend suspend ON suspend.package_id = P.id "
    sql = sql + "WHERE G.id = P.owner_org "
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
    sql = sql + "ORDER BY G.name ASC "
    rows = model.Session.execute(sql).fetchall()
    activity_list = []
    for row in rows:
        next_review_date = None
        if row['next_review_date']:
            next_review_date = row['next_review_date'].strftime(DATE_FORMAT)

        activity_list.append({
            'package_id':row['package_id'],
            'package_title':row['package_title'],
            'package_name':row['package_name'],
            'package_state':row['package_state'].capitalize(),
            'is_private':'Yes' if row['private'] else 'No',
            'is_suspended':'Yes' if row['suspended'] else 'No',
            'suspend_reason': row['suspend_reason'] or '',
            'owner_org':row['owner_org'] or '',
            'group_title':row['group_title'],
            'group_name':row['group_name'],
            'next_review_date':next_review_date or '',
            })
    return activity_list

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
        {'text': package_state_draft.capitalize(), 'value': package_state_draft},
        {'text': package_state_active.capitalize(), 'value': package_state_active},
        {'text': package_state_deleted.capitalize(), 'value': package_state_deleted},
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
    response.headers['Content-disposition']='attachment; filename=%s'%(outputFilename)
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
    response.headers['Content-disposition']='attachment; filename=%s'%(inputFilename)
    response.headers['Content-Length']=os.path.getsize(inputFilename)
    response.body = "\n".join(content)
    return response

def createResponseWithXML(tree, filename, response):
    #write xml to disk
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    #root = tree.parse(filename)
    response.headers['Content-Type']='text/xml'
    response.headers['Content-disposition']='attachment; filename=%s'%(filename)
    response.headers['Content-Length']=os.path.getsize(filename)
    response.body = ET.tostring(tree.getroot())
    return response

def current_time():
    return datetime.datetime.utcnow().strftime(DATETIME_FORMAT)

def get_export_dir():
    directory = config.get('vdojstats.export_dir', '/tmp/')
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def get_export_header_title():
    return config.get('vdojstats.export_header', 'Victoria DoJ')

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


