from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, SelectMultipleField, StringField, SubmitField
from wtforms.validators import URL, DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class LectureForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    youtube_url = StringField('YouTube URL', validators=[DataRequired(), URL()])
    topics = SelectMultipleField('Topics', coerce=int)
    tags = SelectMultipleField('Tags', coerce=int)
    rank = SelectField('Rank', coerce=int)
    collections = SelectMultipleField('Collections', coerce=int)
    submit = SubmitField('Save Lecture')

class MetadataForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Save')


class CollectionForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField('Save Collection')

