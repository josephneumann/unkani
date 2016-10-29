#!/usr/bin/env python3
import os
from datetime import datetime, date
from app import db
from app.models import User, Role
from names import get_first_name, get_last_name
from random import randint, choice


#######################################################################################
#                                User Model Utilities                                 #
#######################################################################################
def create_random_user(users=1, gender=None, **kwargs):
    try:
        users = int(users)
    except ValueError:
        print('Exception: Please enter an integer value for the users parameter')
    else:
        allowed_genders = ['male', 'female']
        if gender:
            if gender not in allowed_genders:
                gender = None

        username_list = []
        email_domains = ['@gmail.com', '@icloud.com', '@yahoo.com', '@microsoft.com'
            , '@aol.com', '@comcast.com', '@mail.com', '@inbox.com', '@outlook.com']
        email_domains_number = len(email_domains)
        password = os.environ.get('TEST_USER_PASSWORD')
        while len(username_list) < users:
            random_number = str(randint(0, 1000))
            rand_email_index = randint(0, (email_domains_number - 1))
            first_name = get_first_name(gender)
            last_name = get_last_name()
            username = first_name + '.' + last_name + random_number
            rand_domain = email_domains[rand_email_index]
            email = username + rand_domain
            dob = random_dob()
            phone = random_phone()
            user = User(first_name=first_name, last_name=last_name, email=email
                        , username=username, phone=phone, dob=dob)
            if password:
                user.password = password
                user.password = password
            db.session.add(user)
            db.session.commit()
            username_list.append(user.username)
        return username_list


def random_dob():
    current_datetime = datetime.now()
    year = choice(range(current_datetime.year - 100, current_datetime.year - 10))
    month = choice(range(1, 13))
    day = choice(range(1, 29))
    dob = date(year, month, day)
    return dob


def random_phone():
    p = list('0000000000')
    p[0] = str(randint(1, 9))
    for i in [1, 2, 6, 7, 8]:
        p[i] = str(randint(0, 9))
    for i in [3, 4]:
        p[i] = str(randint(0, 8))
    if p[3] == p[4] == 0:
        p[5] = str(randint(1, 8))
    else:
        p[5] = str(randint(0, 8))
    n = range(10)
    if p[6] == p[7] == p[8]:
        n = [i for i in n if i != p[6]]
    p[9] = str(choice(n))
    p = ''.join(p)
    return str(p[:3] + '-' + p[3:6] + '-' + p[6:])


#######################################################################################
#                                Database Utilities                                   #
#######################################################################################

def reset_db():
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
        initialize_user_roles()

        # initialize user
        if input_yes("Would you like to configure an admin user?"):
            print("Creating admin user...")
            initialize_user_admin()
        else:
            print("No admin user was created...")

        if input_yes("Would you like to create randomly generated users?"):
            user_create_number = input("How many random users do you want to create? [10]: ")
            if not user_create_number:
                user_create_number = 10
            print("Creating " + str(user_create_number) + " random user(s)...")
            username_list = create_random_user(user_create_number)
            print("Created the following users:")
            for username in username_list:
                print(username)
            total_users = str(len(username_list))
            print("Total random users created: " + total_users)

        print("Process completed without errors")
    else:
        print("Oh thank god............")
        print("That was a close call!")


def initialize_user_roles():
    admin_role = Role(name='Admin', id=0)
    user_role = Role(name='User', id=1)
    db.session.add_all([admin_role, user_role])
    db.session.commit()


def initialize_user_admin():
    admin_email = input(
        "Enter in the email for your admin [joseph.r.neumann@icloud.com]: ") or "joseph.r.neumann@icloud.com"
    admin_password = input("Enter in admin's password [admin]: ") or "admin"
    user = User(email=admin_email, role_id=0, password=admin_password, first_name='Joseph',
                last_name='Neumann', dob='1990-01-01', phone='262-555-8899'
                , username='jneumann', confirmed=True)
    db.session.add(user)
    db.session.commit()


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
