from datetime import datetime
from app import db
from app.models.extensions import BaseExtension


class Organization(db.Model):
    """A formally or informally recognized grouping of people or organizations formed for the purpose of achieving
    some form of collective action. Includes companies, institutions, corporations, departments, community groups,
    healthcare practice groups, etc."""
    __tablename__ = 'organization'
    __mapper_args__ = {'extension': BaseExtension()}

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('organization.id'), index=True)
    name = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text, index=True)
    default = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime)

    children = db.relationship('Organization',
                               backref=db.backref('parent', remote_side=[id])
                               )

    def __repr__(self):  # pragma: no cover
        return '<Organization {}:{}>'.format(self.id, self.name)

    def before_insert(self):
        pass

    def before_update(self):
        pass

# class OrganizationType(db.Model):
#     """SQLAlchemy model to classify types of healthcare organizations"""
#     __tablename__ = 'organization_type'
#     __mapper_args__ = {'extension': BaseExtension()}
#
#     id = db.Column(db.Integer, primary_key=True)
#     display = db.Column(db.Text)
#     default = db.Column(db.Boolean, default=False)
#     code = db.Column(db.Text)
#     definition = db.Column(db.Text)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow())
#     updated_at = db.Column(db.DateTime)
#
#     organizations = db.relationship('Organization', backref='type', lazy='dynamic')
#
#     def __repr__(self):  # pragma: no cover
#         return '<OrganizationType {}:{}>'.format(self.id, self.name)
#
#     def before_insert(self):
#         pass
#
#     def before_update(self):
#         pass
#
#     @staticmethod
#     def initialize_organization_types():
#         """Initialize organization types to HL7 FHIR R3 standards"""
#         # Organization Type Initialization
#         url = "http://hl7.org/fhir/organization-type"
#
#         headers = {
#             'content-type': "application/json",
#             'accept': "application/json",
#         }
#
#         response = requests.request("GET", url, headers=headers)
#         if response.ok:
#             data = response.json()
#
#             for i in data['concept']:
#                 x = OrganizationType.query.filter(OrganizationType.code == i['code']).first()
#                 change_list = []
#                 if not x:  # pragma: no cover
#                     x = OrganizationType(display=i['display'], code=i['code'], definition=i['definition'])
#                     change_list.append(x)
#                 if change_list:
#                     db.session.add_all(change_list)
#                     db.session.commit()
