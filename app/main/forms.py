from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

# Deprecated NameForm from initial iteration
# class NameForm(Form):
#     name = StringField('What is your name?', validators=[DataRequired()])
#     submit = SubmitField('Submit')
