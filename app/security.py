from flask_principal import Permission, Need, UserNeed, RoleNeed
from functools import partial, wraps

# Define Custom Need Types
AppPermissionNeed = partial(Need, 'AppPermission')
AppPermissionNeed.__doc__ = """A need with the method preset to `"AppPermission"`."""

# Role Permission Definition
role_permission_superadmin = Permission(RoleNeed('Super Admin'))
role_permission_admin = Permission(RoleNeed('Admin'))
role_permission_user = Permission(RoleNeed('User'))

# AppPermission Permission Definition
app_permission_usercreate = Permission(AppPermissionNeed('User Create'))
app_permission_userprofileupdate = Permission(AppPermissionNeed('User Profile Update'))
app_permission_userdelete = Permission(AppPermissionNeed('User Delete'))
app_permission_userdeactivate = Permission(AppPermissionNeed('User Deactivate'))
app_permission_userpasswordreset = Permission(AppPermissionNeed('User Reset Password'))
app_permission_userpasswordchange = Permission(AppPermissionNeed('User Change Password'))
app_permission_userresendconfirmation = Permission(AppPermissionNeed('User Resend Confirmation'))
app_permission_userforceconfirmation = Permission(AppPermissionNeed('User Force Confirmation'))
app_permission_userrolechange = Permission(AppPermissionNeed('User Role Change'))
app_permission_patientadmin = Permission(AppPermissionNeed('Patient Admin'))
app_permission_useradmin = Permission(AppPermissionNeed('User Admin'))


def return_template_context_permissions():
    template_context_permissions = {
        "role_permission_superadmin": role_permission_superadmin,
        "role_permission_admin": role_permission_admin,
        "role_permission_user": role_permission_user,
        "app_permission_usercreate": app_permission_usercreate,
        "app_permission_userdelete": app_permission_userdelete,
        "app_permission_userdeactivate": app_permission_userdeactivate,
        "app_permission_userpasswordreset": app_permission_userpasswordreset,
        "app_permission_userpasswordchange": app_permission_userpasswordchange,
        "app_permission_userresendconfirmation": app_permission_userresendconfirmation,
        "app_permission_userforceconfirmation": app_permission_userforceconfirmation,
        "app_permission_userrolechange": app_permission_userrolechange,
        "app_permission_userprofileupdate": app_permission_userprofileupdate,
        "app_permission_patientadmin": app_permission_patientadmin,
        "app_permission_useradmin": app_permission_useradmin,
        "test_user_permission": test_user_permission
    }
    return template_context_permissions


# Generate user permission object from userid
def create_user_permission(userid):
    user_permission = Permission(UserNeed(int(userid)))
    return user_permission


def test_user_permission(userid):
    user_permission = create_user_permission(userid)
    if user_permission.can():
        return True
    else:
        return False


# Dict of app_permission records used for initialization
app_permissions_dict = {
    'User Create': (1),
    'User Profile Update': (2),
    'User Delete': (3),
    'User Deactivate': (4),
    'User Reset Password': (5),
    'User Change Password': (6),
    'User Resend Confirmation': (7),
    'User Force Confirmation': (8),
    'User Role Change': (9),
    'Patient Admin': (10),
    'User Admin': (11)
}

role_dict = {
    'Super Admin': {'id': 1,
                    'permissions':
                        ['User Create',
                         'User Profile Update',
                         'User Deactivate',
                         'User Reset Password',
                         'User Resend Confirmation',
                         'User Role Change',
                         'User Delete',
                         'User Change Password',
                         'User Force Confirmation',
                         'Patient Admin',
                         'User Admin'],
                    'level': 1000},
    'User': {'id': 2,
             'permissions':
                 ['User Profile Update',
                  'User Deactivate',
                  'User Reset Password',
                  'User Resend Confirmation',
                  'User Change Password'],
             'level': 100},
    'Admin': {'id': 3,
              'permissions':
                  ['User Create',
                   'User Profile Update',
                   'User Deactivate',
                   'User Reset Password',
                   'User Resend Confirmation',
                   'User Role Change',
                   'User Admin'],
              'level': 500
              }
}
