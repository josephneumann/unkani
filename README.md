# flask web app template

TODO: Finish user auth design
User Registration:
1) Define a registration form in /auth/forms.py
    a) Fields should include
        -first_name
        -last_name
        -email
        -username
        -password
        -password verification
        -phone_number TODO Validator for phone number
        -DOB TODO display date in useful format
    b) Update user model accordingly
        -DONE: Define new attributes
        -DONE: migrate and upgrade local database
        -TODO:  Push migration script, drop_all(), create_all() for staging
        -TODO:  Push migration script, drop_all(), create_all() for production
    c) Define validaton methods for Form to verify that username and email are not already in use by another user


--2) Define a new route for /register
   -- a) Should not have @login_required decorator
   -- b) Should import and initialize the register form
   --c) Should allow post, get
   --d) Should redirect for register template

--3) Update login template to show link for register url

4) Update /login route to redirect to index if login session exists

--5) Set default Role in user model (1=USER)

6) Implement account verification via cryptographically secure token generation (itsdangerous)
    --a) Add boolean column for verified with default=False
    --b) Add method for generating Token with SECRETKEY
    --c) Add mehtod for verifying secure token and updating verified column for user
    d)TODO: Add unit tests for secure token generation and validation (see GitHub)
    --e) Update register route to send email validation with secure token before redirecting to index
    f) TODO: Validate html email template for confirm
    g) TODO: Migrate auth user changes and upgrade for each db
    h) TODO: protect all pages but auth, confirm and status assets by checking confirmed boolean
    i) TODO: enable resending token
    j) TODO: enable password reset and account management





TODO:
Enable HTTPS on domain
Genericafy the schema
Role based security
Facelift on bootstrap (Creative Tim)