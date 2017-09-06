from app import db, ma
from .app_permission import AppPermission, role_app_permission
from marshmallow import fields


###################################################################################################
# USER ROLE SQL ALCHEMY MODEL DEFINITION
###################################################################################################
class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, index=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
    default = db.Column(db.Boolean, default=False)
    level = db.Column(db.Integer, index=True)
    app_permissions = db.relationship('AppPermission',
                                      secondary=role_app_permission,
                                      back_populates='roles')

    def __repr__(self):  # pragma: no cover
        return '<Role {}:{}>'.format(self.id, self.name)

    @staticmethod
    def initialize_roles():
        __doc__ = """
        Role Staticmethod:  Creates and stores a default set of Roles as defined
        by the application security module.  Populates Role attributes including: 'id', 'name',
        'level'.  Also populates app_permissions in the role_app_permission association table
        to initialize the permissions for the given role."""
        from app.security import role_dict
        for r in role_dict:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r, id=role_dict[r]['id'], level=role_dict[r]['level'])
                if role.name == 'User':
                    role.default = True
                db.session.add(role)
                db.session.commit()
            role = Role.query.filter_by(name=r).first()
            for p in role_dict[r]['permissions']:
                ap = AppPermission.query.filter_by(name=p).first()
                if ap:
                    role_ap_list = role.app_permissions
                    if ap not in role_ap_list:
                        role.app_permissions.append(ap)
            db.session.add(role)
            db.session.commit()

        db.session.commit()

    def dump(self):
        schema = RoleSchema()
        data, x = schema.dump(self)
        return data

##################################################################################################
# MARSHMALLOW USER SCHEMA DEFINITION FOR OBJECT SERIALIZATION
##################################################################################################

class RoleSchema(ma.Schema):
    """Marshmallow schema, associated with SQLAlchemy Role model.  Used as a base object for
    serialization ."""

    class Meta:
        # exclude = ()
        ordered = False

    id = fields.Int(dump_only=True)
    name = fields.String(attribute='name', dump_only=True)
    level = fields.Int(attribute='level', dump_only=True)