from app import db

###################################################################################################
# APP PERMISSION SQL ALCHEMY MODEL DEFINITION
###################################################################################################

class AppPermission(db.Model):
    __tablename__ = 'app_permission'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

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
                db.session.add(app_permission)
        db.session.commit()
