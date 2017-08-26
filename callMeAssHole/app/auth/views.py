from flask import render_template,redirect,request,url_for,flash
from flask_login import login_user,logout_user,login_required
from . import auth
from ..models import User ,Role
from .form import LoginForm,RegistrationForm,ResetPassword
from .. import db
from flask_login import current_user

#登入
@auth.route('/login',methods=['GET','POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user,form.remember_me.data)
			return redirect(request.args.get('next') or url_for('main.index'))
		flash('密码或用户名不正确')
	return render_template('auth/login.html',form=form)

#注销
@auth.route('/logout')
@login_required
def logout():
	logout_user()
	flash("成功登出")
	return redirect(url_for('main.index'))

#注册
@auth.route('/register',methods=['GET','POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(username=form.username.data,
			password=form.password.data,
			role=Role.query.filter_by(default=True).first())
		db.session.add(user)
		flash('注册成功')
		return redirect(url_for('auth.login'))
	return render_template('auth/register.html',form=form)

#刷新登陆时间
@auth.before_app_request
def before_request():
	if current_user.is_authenticated:
		current_user.ping()

#修改密码