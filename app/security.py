from flask_principal import Permission, Need, UserNeed, RoleNeed
from functools import partial, wraps

# Define Custom Need Types
AppPermissionNeed = partial(Need, 'AppPermission')
AppPermissionNeed.__doc__ = """A need with the method preset to `"action"`."""

# Role Permission Definition
role_permission_admin = Permission(RoleNeed('Admin'))
role_permission_user = Permission(RoleNeed('User'))

# AppPermission Permission Definition
app_permission_admin = Permission(AppPermissionNeed('Admin'))
app_permission_usercreate = Permission(AppPermissionNeed('User Create'))
app_permission_userdelete = Permission(AppPermissionNeed('User Delete'))
app_permission_userupdate = Permission(AppPermissionNeed('User Update'))
app_permission_userview = Permission(AppPermissionNeed('User View'))
app_permission_rolecreate = Permission(AppPermissionNeed('Role Create'))
app_permission_roledelete = Permission(AppPermissionNeed('Role Delete'))
app_permission_roleupdate = Permission(AppPermissionNeed('Role Update'))
app_permission_roleview = Permission(AppPermissionNeed('Role View'))
app_permission_apppermissioncreate = Permission(AppPermissionNeed('App Permission Create'))
app_permission_apppermissiondelete = Permission(AppPermissionNeed('App Permission Delete'))
app_permission_apppermissionupdate = Permission(AppPermissionNeed('App Permission Update'))
app_permission_apppermissionview = Permission(AppPermissionNeed('App Permission View'))


# Generate user permission object from userid
def create_user_permission(userid):
    user_permission = Permission(UserNeed(int(userid)))
    return user_permission
