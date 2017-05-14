from app import sa

##################################################################################################
# ROLE -> APP PERMISSION ASSOCIATION TABLE
##################################################################################################

role_app_permission = sa.Table('role_app_permission',
                               sa.Column('role_id', sa.Integer, sa.ForeignKey('role.id')),
                               sa.Column('app_permission_id', sa.Integer, sa.ForeignKey('app_permission.id')))
