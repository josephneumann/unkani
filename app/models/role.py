from app import db
from .role_app_permission import role_app_permission
from .app_permission import AppPermission


###################################################################################################
# USER ROLE SQL ALCHEMY MODEL DEFINITION
###################################################################################################
class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
    default = db.Column(db.Boolean, default=False)
    level = db.Column(db.Integer)
    app_permissions = db.relationship('AppPermission',
                                      secondary=role_app_permission,
                                      backref=db.backref('app_permissions', lazy='dynamic'),
                                      lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

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
                    role_ap_list = role.app_permissions.all()
                    if ap not in role_ap_list:
                        role.app_permissions.append(ap)
            db.session.add(role)
            db.session.commit()

        db.session.commit()
