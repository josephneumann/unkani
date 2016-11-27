from app import db
from .models import User, Role


#######################################################################################
#                               Command Line Utilities                                #
#######################################################################################

def input_yes(question_prompt='Please enter [y/n]', default_answer='yes', **kwargs):
    def check_yes(input):
        if input == 1:
            return True
        elif input[0] in ['y', 'Y']:
            return True
        else:
            return False

    def check_no(input):
        if input == 0:
            return True
        elif input[0] in ['n', 'N']:
            return True
        else:
            return False

    if default_answer:
        if check_yes(default_answer) or check_no(default_answer):
            default_display = ' [Default is ' + default_answer + ']: '
        else:
            default_display = None
    else:
        default_display = None

    ans = input(question_prompt + default_display)
    if ans:
        if check_yes(ans):
            return True
        else:
            return False
    elif check_yes(default_answer):
        return True
    else:
        return False


def reset_db_command_line():
    print(""""
    __________________________________________________________________________
    |                        !!!-----WARNING-----!!!                          |
    |This command drops all tables, re-creates them and initializes some data |
    |As a result ALL data will be lost from the target environment            |
    --------------------------------------------------------------------------

    """)
    if input_yes("Are you sure you wan to proceed?", "No"):
        print('Database is refreshing...')
        print('Dropping and recreating tables...')
        db.drop_all()
        db.create_all()

        print("Initializing user roles...")
        Role.initialize_roles()

        # # initialize user
        # if input_yes("Would you like to configure an admin user?"):
        #     print("Creating admin user...")
        #     initialize_user_admin()
        # else:
        #     print("No admin user was created...")

        if input_yes("Would you like to create randomly generated users?"):
            user_create_number = input("How many random users do you want to create? [10]: ")
            if not user_create_number:
                user_create_number = 10
            print("Creating " + str(user_create_number) + " random user(s)...")
            user_list = []
            while len(user_list) < int(user_create_number):
                user = User()
                user.create_random_user()
                user_list.append(user)
            db.session.add_all(user_list)
            db.session.commit()
            print("Created the following users:")
            for user in user_list:
                print(user.username)
            total_users = str(len(user_list))
            print("Total random users created: " + total_users)

        print("Process completed without errors")
    else:
        print("Oh thank god............")
        print("That was a close call!")
