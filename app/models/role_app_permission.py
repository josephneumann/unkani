from app import db

##################################################################################################
# ROLE -> APP PERMISSION ASSOCIATION TABLE
##################################################################################################

role_app_permission = db.Table('role_app_permission',
                               db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                               db.Column('app_permission_id', db.Integer, db.ForeignKey('app_permission.id')))
