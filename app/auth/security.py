from flask import current_app, session, g
from flask_login import current_user
from flask_principal import Permission, identity_loaded, Need, UserNeed, RoleNeed

from functools import partial
from ..models import User, Role, AppPermission

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


@identity_loaded.connect
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Update the identity with the roles that the user provides
    if hasattr(current_user, 'role_id'):
        role = Role.query.filter_by(id=current_user.role_id).first()
        identity.provides.add(RoleNeed(role.name))

        app_permissions = role.app_permissions.all()
        for app_permission_name in app_permissions:
            identity.provides.add(AppPermissionNeed(str(app_permission_name)))


def current_privileges():
    return (('{method} : {value}').format(method=n.method, value=n.value)
            for n in g.identity.provides)
