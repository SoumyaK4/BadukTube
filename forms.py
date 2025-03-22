from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectMultipleField, SelectField, SubmitField
from wtforms.validators import DataRequired, URL

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class LectureForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    youtube_url = StringField('YouTube URL', validators=[DataRequired(), URL()])
    topics = SelectField('Topic', coerce=int)
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
    is_paid = SelectField('Is Paid', choices=[(0, 'Free'), (1, 'Paid')], coerce=int)
    submit = SubmitField('Save Collection')

