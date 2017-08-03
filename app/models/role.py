from app import sa
from .app_permission import AppPermission, role_app_permission


###################################################################################################
# USER ROLE SQL ALCHEMY MODEL DEFINITION
###################################################################################################
class Role(sa.Model):
    __tablename__ = 'role'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text, unique=True, index=True)
    users = sa.relationship('User', backref='role', lazy='dynamic')
    default = sa.Column(sa.Boolean, default=False)
    level = sa.Column(sa.Integer, index=True)
    app_permissions = sa.relationship('AppPermission',
                                      secondary=role_app_permission,
                                      back_populates='roles')

    def __repr__(self):  # pragma: no cover
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
                sa.session.add(role)
                sa.session.commit()
            role = Role.query.filter_by(name=r).first()
            for p in role_dict[r]['permissions']:
                ap = AppPermission.query.filter_by(name=p).first()
                if ap:
                    role_ap_list = role.app_permissions
                    if ap not in role_ap_list:
                        role.app_permissions.append(ap)
            sa.session.add(role)
            sa.session.commit()

        sa.session.commit()
