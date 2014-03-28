import ckan
from ckan.model.types import make_uuid
from sqlalchemy import orm, Table, Column, types, ForeignKey
from ckan.model.meta import metadata
import ckan.plugins.toolkit as tk

vdojstats_report_table = Table('vdojstats_report', metadata,
        Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
        Column('name', types.UnicodeText, nullable = False),
        Column('org_id', types.UnicodeText, nullable = True),
        Column('permission', types.UnicodeText, nullable = True),
        Column('report_on', types.UnicodeText, nullable = True),
        Column('custodian', types.Boolean, default = False),
    )

class VDojStatsReport(ckan.model.domain_object.DomainObject):
    def validate(self):
        data = self.as_dict()
        errors = { 'name' : [] }
        context = {}
        is_valid = True
        
        validator = tk.get_validator('not_empty')
        try:
            validator('name', data, errors, context)
        except ckan.lib.navl.dictization_functions.StopOnError:
            is_valid = False
        
        return is_valid, errors

#orm.mapper(PackageSuspend, package_suspend_table, properties={
#    'package': orm.relationship(ckan.model.Package, uselist=False)
#})
#m = orm.class_mapper(ckan.model.Package)
#m.add_property('package_suspend', orm.relationship(PackageSuspend, uselist=False))

orm.mapper(VDojStatsReport, vdojstats_report_table)

def create_table():
    vdojstats_report_table.create(checkfirst=True)