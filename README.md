# flask web app template

TODO: Finish user auth design
User Registration:
1) Define a registration form in models.py
    a) Fields should include
        -first_name
        -last_name
        -email
        -username
        -password
        -password verification
        -phone_number
    b) Update user model accordingly as needed

2) Define a new route for /register
    a) Should not have @login_required decorator
    b) Should import and initialize the register form
    c) Should allow post, get
    d) Should redirect for register template

3) Update login template to show link for register url

4) Update /login route to redirect to index if login session exists

TODO: Enable HTTPS on domain
TODO: Genericafy the schema
TODO: Role based security
TODO: Facelift on bootstrap (Creative Tim)