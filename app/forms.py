from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp
try:
    from app.models import User
except ImportError:
    from models import User


class LoginForm(FlaskForm):
    email = StringField('Email or Username', validators=[
        DataRequired(message='Email or username is required')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=20, message='Username must be between 3 and 20 characters'),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address')
    ])
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required'),
        Length(min=2, max=30, message='First name must be between 2 and 30 characters'),
        Regexp(r'^[a-zA-Z\s]+$', message='First name can only contain letters and spaces')
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required'),
        Length(min=2, max=30, message='Last name must be between 2 and 30 characters'),
        Regexp(r'^[a-zA-Z\s]+$', message='Last name can only contain letters and spaces')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, max=128, message='Password must be between 8 and 128 characters long'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])', 
               message='Password must contain at least one lowercase letter, one uppercase letter, one number, and one special character (@$!%*?&)')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email address.')


class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address')
    ])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('No account found with this email address.')


class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, max=128, message='Password must be between 8 and 128 characters long'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])', 
               message='Password must contain at least one lowercase letter, one uppercase letter, one number, and one special character (@$!%*?&)')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password'),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required')
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required'),
        Length(min=8, max=128, message='Password must be between 8 and 128 characters long'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])', 
               message='Password must contain at least one lowercase letter, one uppercase letter, one number, and one special character (@$!%*?&)')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password'),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')

    def validate_current_password(self, current_password):
        from flask_login import current_user
        if not current_user.check_password(current_password.data):
            raise ValidationError('Current password is incorrect.')


class DeleteAccountForm(FlaskForm):
    password = PasswordField('Enter your password to confirm', validators=[
        DataRequired(message='Password is required to delete account')
    ])
    confirm_delete = BooleanField('I understand that this action cannot be undone', validators=[
        DataRequired(message='You must confirm that you understand this action cannot be undone')
    ])
    submit = SubmitField('Delete My Account')

    def validate_password(self, password):
        from flask_login import current_user
        if not current_user.check_password(password.data):
            raise ValidationError('Password is incorrect.')


class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=20, message='Username must be between 3 and 20 characters'),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address')
    ])
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required'),
        Length(min=2, max=30, message='First name must be between 2 and 30 characters'),
        Regexp(r'^[a-zA-Z\s]+$', message='First name can only contain letters and spaces')
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required'),
        Length(min=2, max=30, message='Last name must be between 2 and 30 characters'),
        Regexp(r'^[a-zA-Z\s]+$', message='Last name can only contain letters and spaces')
    ])
    submit = SubmitField('Update Profile')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UpdateProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already exists. Please choose a different one.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already registered. Please use a different email address.')
