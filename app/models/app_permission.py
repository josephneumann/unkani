from app import db

##################################################################################################
# ROLE -> APP PERMISSION ASSOCIATION TABLE
##################################################################################################

role_app_permission = db.Table('role_app_permission',
                               db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
                               db.Column('app_permission_id', db.Integer, db.ForeignKey('app_permission.id'),
                                         primary_key=True))


###################################################################################################
# APP PERMISSION SQL ALCHEMY MODEL DEFINITION
###################################################################################################

class AppPermission(db.Model):
    __tablename__ = 'app_permission'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    roles = db.relationship('Role', secondary=role_app_permission, back_populates='app_permissions')

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
                db.session.add(app_permission)
        db.session.commit()
