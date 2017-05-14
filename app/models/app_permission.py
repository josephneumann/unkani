from app import sa

###################################################################################################
# APP PERMISSION SQL ALCHEMY MODEL DEFINITION
###################################################################################################

class AppPermission(sa.Model):
    __tablename__ = 'app_permission'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text, unique=True)

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
            if app_permission is None:
                app_permission = AppPermission(name=p)
                app_permission.id = app_permissions_dict[p]
                sa.session.add(app_permission)
        sa.session.commit()
