from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.security import check_password_hash, generate_password_hash
try:
    from ..app import limiter
except ImportError:
    from app import limiter
try:
    from app.models import User, db, Portfolio
    from app.forms import (LoginForm, RegisterForm, PasswordResetRequestForm, 
                          PasswordResetForm, ChangePasswordForm, DeleteAccountForm, 
                          UpdateProfileForm)
    from app.app import mail
except ImportError:
    from models import User, db, Portfolio
    from forms import (LoginForm, RegisterForm, PasswordResetRequestForm, 
                      PasswordResetForm, ChangePasswordForm, DeleteAccountForm, 
                      UpdateProfileForm)
    from app import mail

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter((User.email == form.email.data) | (User.username == form.email.data)).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        
        flash('Invalid email/username or password', 'error')
    elif form.errors:
        # Show form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return render_template('auth/login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def register():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            username=form.username.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Send welcome email
        try:
            from app.services.email_service import send_welcome_email
            send_welcome_email(user)
        except Exception as e:
            # Log error but don't break registration
            print(f"Error sending welcome email: {e}")
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth.route('/profile')
@login_required
def profile():
    """User profile page"""
    # Redirect admin users to admin dashboard
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    return render_template('auth/profile.html', user=current_user)


@auth.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    form = UpdateProfileForm(current_user.username, current_user.email)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        
        db.session.commit()
        flash('Your profile has been updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
    
    return render_template('auth/edit_profile.html', form=form)


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per hour")
def change_password():
    """Change user password"""
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('Your password has been changed successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html', form=form)


@auth.route('/delete-account', methods=['GET', 'POST'])
@login_required
@limiter.limit("3 per hour")
def delete_account():
    """Delete user account"""
    if current_user.is_admin:
        flash('Admin accounts cannot be deleted through this interface.', 'error')
        return redirect(url_for('admin.dashboard'))
    
    form = DeleteAccountForm()
    
    if form.validate_on_submit():
        user_email = current_user.email
        user_name = f"{current_user.first_name} {current_user.last_name}"
        
        # Delete user and all associated data (cascade delete handles this)
        db.session.delete(current_user)
        db.session.commit()
        
        # Send confirmation email
        try:
            send_account_deletion_email(user_email, user_name)
        except Exception as e:
            # Log error but don't break the deletion process
            print(f"Error sending account deletion email: {e}")
        
        logout_user()
        flash('Your account has been deleted successfully. We\'re sorry to see you go!', 'info')
        return redirect(url_for('main.index'))
    
    return render_template('auth/delete_account.html', form=form)


def send_reset_email(user):
    """Send password reset email to user"""
    token = user.get_reset_token()
    msg = Message(
        'Password Reset Request - FreelanceHub',
        sender='noreply@freelancehub.com',
        recipients=[user.email]
    )
    msg.body = f'''Hi {user.first_name},

You have requested to reset your password for your FreelanceHub account.

To reset your password, click the following link:
{url_for('auth.reset_password', token=token, _external=True)}

If you did not make this request, please ignore this email and no changes will be made to your account.

This link will expire in 30 minutes for security reasons.

Best regards,
The FreelanceHub Team
'''
    msg.html = f'''
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #333;">Password Reset Request</h2>
        <p>Hi {user.first_name},</p>
        <p>You have requested to reset your password for your FreelanceHub account.</p>
        <p>To reset your password, click the button below:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{url_for('auth.reset_password', token=token, _external=True)}" 
               style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Reset Password
            </a>
        </div>
        <p>If the button doesn't work, copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #666;">{url_for('auth.reset_password', token=token, _external=True)}</p>
        <p><strong>Important:</strong> This link will expire in 30 minutes for security reasons.</p>
        <p>If you did not make this request, please ignore this email and no changes will be made to your account.</p>
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 12px;">
            Best regards,<br>
            The FreelanceHub Team
        </p>
    </div>
    '''
    mail.send(msg)


def send_account_deletion_email(email, name):
    """Send account deletion confirmation email"""
    msg = Message(
        'Account Deletion Confirmation - FreelanceHub',
        sender='noreply@freelancehub.com',
        recipients=[email]
    )
    msg.body = f'''Hi {name},

This email confirms that your FreelanceHub account has been successfully deleted.

All your data, including your portfolio and projects, has been permanently removed from our system.

If you deleted your account by mistake or have any questions, please contact our support team as soon as possible.

We're sorry to see you go and hope you'll consider joining us again in the future.

Best regards,
The FreelanceHub Team
'''
    msg.html = f'''
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #333;">Account Deletion Confirmation</h2>
        <p>Hi {name},</p>
        <p>This email confirms that your FreelanceHub account has been successfully deleted.</p>
        <p><strong>What was deleted:</strong></p>
        <ul>
            <li>Your user account and profile information</li>
            <li>Your portfolio and all projects</li>
            <li>All associated data and files</li>
        </ul>
        <p>All your data has been permanently removed from our system.</p>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 0;"><strong>Need help?</strong> If you deleted your account by mistake or have any questions, please contact our support team as soon as possible.</p>
        </div>
        <p>We're sorry to see you go and hope you'll consider joining us again in the future.</p>
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 12px;">
            Best regards,<br>
            The FreelanceHub Team
        </p>
    </div>
    '''
    mail.send(msg)


@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.index'))
    
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
            flash('Check your email for instructions to reset your password', 'info')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', form=form)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.index'))
    
    user = User.verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('auth.reset_password_request'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset! You can now log in', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)
