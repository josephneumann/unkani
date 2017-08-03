from app import sa

##################################################################################################
# ROLE -> APP PERMISSION ASSOCIATION TABLE
##################################################################################################

role_app_permission = sa.Table('role_app_permission',
                               sa.Column('role_id', sa.Integer, sa.ForeignKey('role.id'), primary_key=True),
                               sa.Column('app_permission_id', sa.Integer, sa.ForeignKey('app_permission.id'),
                                         primary_key=True))


###################################################################################################
# APP PERMISSION SQL ALCHEMY MODEL DEFINITION
###################################################################################################

class AppPermission(sa.Model):
    __tablename__ = 'app_permission'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text, unique=True)
    roles = sa.relationship('Role', secondary=role_app_permission, back_populates='app_permissions')

    def __repr__(self):
        return str(self.name)

    @staticmethod
    def initialize_app_permissions():
        __doc__ = """
        AppPermission Staticmethod:  Initializes the set of AppPermission records as
        defined in the app security module.  Reads from a dict to assign names to permission.
        If app_permission already exists, it is ignored.  This method is used during deployment
        and on database creation / upgrades."""
        from app.security import app_permissions_dict
        for p in app_permissions_dict:
            app_permission = AppPermission.query.filter_by(name=p).first()
            if app_permission is None:  # pragma: no cover
                app_permission = AppPermission(name=p)
                app_permission.id = app_permissions_dict[p]
                sa.session.add(app_permission)
        sa.session.commit()
