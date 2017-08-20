from datetime import datetime
from flask import render_template,session,redirect,url_for,abort,flash
from ..decorators import permission_required
from . import main
from .forms import EditProfileForm
from .. import db
from ..models import User,Permission
from wtforms.validators import Required
from flask_login import current_user,login_required


@main.route('/',methods=['GET','POST'])
def index():
	return render_template('index.html')

@main.route('/test')
@permission_required(Permission.MODERATE_COMMENTS)
def test():
	print("what?")
	return "for comment moderators"

@main.route('/user/<username>')
def user(username):
	user=User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	return render_template('user.html',user = user)

#修改个人信息
@main.route('/editprofile',methods=['GET','POST'])
@login_required
def editprofile():
	form = EditProfileForm()
	if form.validate_on_submit():
		current_user.name = form.name.data
		current_user.about_me = form.about_me.data
		db.session.add(current_user)
		flash('成功修改')
		return redirect(url_for('main.user',
			username=current_user.username))
	form.name.data = current_user.name
	form.about_me.data= current_user.about_me
	return render_template('editprofile.html',form=form)