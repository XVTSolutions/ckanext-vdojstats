# -#-coding: utf-8 -#-
import datetime
import ckan.plugins.toolkit as tk
import ckan
import pylons
from ckan.common import _
from ckan import model
from ckan.model.meta import metadata
from ckan.model import Session
from ckan.lib.navl.dictization_functions import StopOnError
from sqlalchemy import *
import ckan.logic as logic

check_access = logic.check_access
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized

activity_type_new = 'new'
activity_type_changed = 'changed'
activity_type_deleted = 'deleted'
package_state_active = 'active'
package_state_draft = 'draft'
user_state_active = 'active'
package_type_dataset_suspended = 'dataset-suspended'


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
    sql = select([func.count(package.c.id).label('NUM')]).where(package.c.state != 'active')
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
        record.update({row['activity_type']:row['num']})
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
            'name':row['fullname'] or row['name'] ,
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

def list_assets(org_ids=None, package_states=None, private=None, suspend=None, pending_approval=None):
    """
     get list of assets
     parameter: org_ids (list)
     parameter: package_states (list)
     parameter: private (boolean)
     parameter: suspend (boolean)
     parameter: pending_approval (boolean)
    """
    #parameter check
    organizations = []
    if org_ids is not None:
        if isinstance(org_ids, list):
            organizations = org_ids
        else:
            organizations.append(org_ids)

    pstats = []
    if package_states is not None:
        if isinstance(package_states, list):
            pstats = package_states
        else:
            pstats.append(package_states)

    package = table('package')
    group = table('group')
    review = table('package_review')
    cols = [package.c.id.label('package_id'), package.c.title.label('package_title'), package.c.name.label('package_name'), package.c.state.label('package_state'), package.c.private, package.c.type.label('package_type'), package.c.owner_org, group.c.title.label('group_title'), group.c.name.label('group_name'), review.c.next_review_date]
    sql = select(cols, from_obj=[package.outerjoin(review), group]).where(group.c.id == package.c.owner_org)
    if len(organizations):
        sql = sql.where(package.c.owner_org.in_(organizations))
    if len(pstats):
        sql = sql.where(package.c.state.in_(pstats))
    if private is not None:
        sql = sql.where(package.c.private == private)
    if suspend is not None:
        if suspend:
            sql = sql.where(package.c.type == 'dataset-suspended')
        else:
            sql = sql.where(package.c.type != 'dataset-suspended')
    if pending_approval is not None:
        if pending_approval:
            sql = sql.where(review.c.package_id != None)
        else:
            sql = sql.where(review.c.package_id == None)
    sql = sql.order_by(group.c.name)
    rows = model.Session.execute(sql).fetchall()
    activity_list = []
    for row in rows:
        next_review_date = None
        if row['next_review_date']:
            next_review_date = row['next_review_date'].strftime(DATE_FORMAT)

        activity_list.append({
            'package_id':row['package_id'],
            'package_name':row['package_title'] or row['package_name'],
            'package_state':row['package_state'],
            'is_private':'Yes' if row['private'] else 'No',
            'is_suspended':'Yes' if row['package_type'] == package_type_dataset_suspended else 'No',
            'owner_org':row['owner_org'] or '',
            'group_name':row['group_title'] or row['group_name'],
            'next_review_date':next_review_date or '',
            })
    return activity_list

