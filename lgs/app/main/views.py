from datetime import datetime
from flask import render_template,session,redirect,url_for,abort,request,flash
from ..decorators import permission_required
from . import main
from .forms import EditProfileForm,EditProfileAdminForm,PostForm,CommentForm
from .. import db
from ..models import User,Permission,Role,Post,Comment
from wtforms.validators import Required
from flask_login import current_user,login_required
from app.decorators import admin_required

@main.route('/',methods=['GET','POST'])
def index():
	form = PostForm()
	if current_user.can(Permission.WRITE_ARTICLES) and \
	form.validate_on_submit():
		post = Post(
			body=form.body.data,
			author = current_user._get_current_object())
		db.session.add(post)
		return redirect(url_for('main.index'))
	page = request.args.get('page',1,type=int)
	pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page,
		per_page=20,error_out=False)
	posts = pagination.items
	return render_template('index.html',form=form,posts=posts,pagination=pagination)

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
	posts = user.posts.order_by(Post.timestamp.desc()).all()
	for post in posts:
		for comment in post.comments:
			comment.unread = False 
	return render_template('user.html',user = user,posts=posts,Comment=Comment)

@main.route('/about')
def about():
	return render_template('about.html')

#修改个人信息
@main.route('/editprofile',methods=['GET','POST'])
@login_required
def editprofile():
	form = EditProfileForm()
	if form.validate_on_submit():
		current_user.name = form.name.data
		current_user.about_me = form.about_me.data
		current_user.number = form.number.data
		db.session.add(current_user)
		flash('成功修改')
		return redirect(url_for('main.user',
			username=current_user.username))
	form.name.data = current_user.name
	form.about_me.data= current_user.about_me
	form.number.data = current_user.number
	return render_template('editprofile.html',form=form)

@main.route('/edit_profile_admin/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
	user = User.query.get_or_404(id)
	form = EditProfileAdminForm(user=user)
	if form.validate_on_submit():
		user.username = form.username.data
		user.role= Role.query.get(form.role.data)
		user.about_me = form.about_me.data
		user.name = form.name.data
		db.session.add(user)
		flash('用户信息已经更新')
		return redirect(url_for('main.user',username=user.username))
	form.username.data = user.username
	form.role.data = user.role_id
	form.about_me.data = user.about_me
	form.name.data = user.name
	return render_template('editprofile.html',form=form,user=user)

#文章的固定连接
@main.route('/post/<int:id>',methods=['POST','GET'])
def post(id):
	post = Post.query.get_or_404(id)
	form = CommentForm()
	if form.validate_on_submit() and current_user.can(Permission.COMMENT):
		comment = Comment(body=form.body.data,post=post,author=current_user._get_current_object())
		db.session.add(comment)
		flash('评论成功')	
		return redirect(url_for('.post',id=post.id))
	comments=Comment.query.filter_by(post=post)
	return render_template('post.html',posts=[post],form=form,
		comments=comments)


@main.route("/edit/<int:id>",methods=['GET','POST'])
@login_required
def edit(id):
	post = Post.query.get_or_404(id)
	if current_user != post.author and\
	not current_user.can(Permission.ADMINISTER):
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.body = form.body.data
		db.session.add(post)
		flash('文章更新成功')
		return redirect(url_for('main.post',id=post.id))
	form.body.data = post.body
	return render_template('edit_post.html',form=form)

# #关注相关的路由
# @main.route('/followers/<username>')
# def followers(username):
# 	user = User.query.filter_by(username=username).first()
# 	if user is None:
# 		flash('用户不存在')
# 		return redirect(url_for('.index'))
# 	page=request.arts.get('page',1,type=int)
# 	pagination = user.followers.pagenate(
# 		page,per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
# 		error_out=False)
# 	follows = [{'user':item.follower,'timestamp':item.timestamp} 
# 	for item in pagination.items]
# 	return render_template('followers.html',user=user,
# 		pagination=pagination,follows=follows)

# @main.route('/followed'<username>)
# def followed(username):
# 	user = User.query.filter_by(username=username).first()
# 	if user is None:
# 		flash("用户不存在")
# 		return redirect(url_for('index'))	
# 	page = request.arts.get('page',1,type=int)
# 	pagination = user.followers.pagenate(
# 		page,per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
# 		error_out=False)
# 	follows = [{'user':item.follower,'timestamp':item.timestamp}
# 		for item in pagination.items]
# 	return render_template('follwed.html',user=user,
# 		pagination=pagination,follows=follows)

# @main.route('/follow/<username>')
# def follow(username):
# 	user =User.query.filter_by(username=username).first()
# 	if user is None:
# 		flash('用户不存在')
# 		return redirect(url_for('.index'))
# 	if current_user.is_following(user):
# 		flash('你已经关注这位用户')
# 		return redirect(url_for('.user',username=username))
# 	current_user.follow(user)
# 	flash('成功关注')
# 	return redict(url_for('.user',username=username))
