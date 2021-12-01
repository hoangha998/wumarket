from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, EmailField, DecimalField
from wtforms.validators import DataRequired, Email


class LoginForm(FlaskForm):
	email = EmailField(validators=[DataRequired()])
	password = PasswordField(validators=[DataRequired()])
	submit = SubmitField()

class SignUpForm(FlaskForm):
	firstName = StringField(validators=[DataRequired()], label='firstName')
	lastName = StringField(validators=[DataRequired()], label='lastName')
	password = PasswordField(validators=[DataRequired()])
	email = EmailField(validators=[DataRequired()])
	submit = SubmitField()

class NewProductForm(FlaskForm):
    title = StringField(validators=[DataRequired()])
    price = DecimalField(validators=[DataRequired()])
    image_link = StringField(validators=[DataRequired()])
    description = TextAreaField(validators=[DataRequired()])
    submit = SubmitField(label="Add Project")
    
class ValidateForm(FlaskForm):
		email = EmailField(validators=[DataRequired()])
		token = StringField(validators=[DataRequired()])
		submit = SubmitField(label="Validate")