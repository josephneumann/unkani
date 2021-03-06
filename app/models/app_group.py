from app import db, ma
from app.models.extensions import BaseExtension
from datetime import datetime
from marshmallow import fields

##################################################################################################
# USER -> APP GROUP ASSOCIATION TABLE
##################################################################################################

user_app_group = db.Table('user_app_group',
                          db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                          db.Column('app_group_id', db.Integer, db.ForeignKey('app_group.id'), primary_key=True))


###################################################################################################
# APP PERMISSION SQL ALCHEMY MODEL DEFINITION
###################################################################################################
class AppGroup(db.Model):
    __mapper_args__ = {'extension': BaseExtension()}
    __versioned__ = {}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    active = db.Column(db.Boolean, default=True)
    default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime)

    users = db.relationship('User', secondary=user_app_group, back_populates='app_groups', lazy='dynamic')

    def __repr__(self):
        return '<AppGroup {}:{}>'.format(self.id, self.name)

    @staticmethod
    def initialize_app_groups():
        __doc__ = """
        AppGroup Staticmethod:  Initializes the set of AppGroup records as
        defined in the app security module.  Reads from a dict to assign names to an AppGroup.
        If the AppGroup already exists, it is ignored.  This method is used during deployment
        and on database creation / upgrades."""
        from app.security import app_group_dict
        for p in app_group_dict:
            ap = AppGroup.query.filter_by(name=p.upper().strip()).first()
            if ap is None:  # pragma: no cover
                ap = AppGroup(name=p.upper().strip())
                ap.id = app_group_dict[p]['id']
                ap.default = app_group_dict[p]['default']
                db.session.add(ap)
        db.session.commit()

    def before_insert(self):
        pass

    def before_update(self):
        pass

    def dump(self):
        schema = AppGroupSchema()
        data, x = schema.dump(self)
        return data


##################################################################################################
# MARSHMALLOW USER SCHEMA DEFINITION FOR OBJECT SERIALIZATION
##################################################################################################

class AppGroupSchema(ma.Schema):
    """Marshmallow schema, associated with SQLAlchemy AppGroup model.  Used as a base object for
    serialization ."""

    class Meta:
        # exclude = ()
        ordered = False

    id = fields.Int(dump_only=True)
    name = fields.String(attribute='name', dump_only=True)
    active = fields.Boolean(attribute='active', dump_only=True)
    created_at = fields.DateTime(attribute='created_at', dump_only=True)
    updated_at = fields.DateTime(attribute='updated_at', dump_only=True)