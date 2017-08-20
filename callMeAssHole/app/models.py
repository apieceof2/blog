from . import db
from flask_login import UserMixin,AnonymousUserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from . import login_manager
from datetime import datetime

# 权限
class Permission:
	FOLLOW = 0x01
	COMMENT = 0x02
	WRITE_ARTICLES = 0x04
	MODERATE_COMMENTS = 0x08
	ADMINISTER = 0x80
#登入要求的
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))
#角色
class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer,primary_key=True)
	name = db.Column(db.String(64),unique=True)
	default = db.Column(db.Boolean,default=False,index=True)
	users = db.relationship('User',backref='role',lazy='dynamic')
	permissions = db.Column(db.Integer)

	#创建角色
	@staticmethod
	def insert_roles():
		roles={
		'User':(Permission.FOLLOW|
			Permission.COMMENT|
			Permission.WRITE_ARTICLES,True),
		'Moderator':(Permission.FOLLOW|
			Permission.COMMENT|
			Permission.WRITE_ARTICLES|
			Permission.MODERATE_COMMENTS,False),
		'Administrator':(0xff,False)
		}
		for r in roles:
			role = Role.query.filter_by(name=r).first()
			if role == None:
				role = Role(name=r)
				role.permissions = roles[r][0]
				role.default = roles[r][1]
				db.session.add(role)
		db.session.commit()

	def __repr__(self):
		return '<Role %r>' % self.name

#用户
class User(UserMixin,db.Model):
	__tablename__ = 'users'
	#基本信息
	email = db.Column(db.String(64),unique=True,index=True)
	id = db.Column(db.Integer,primary_key=True)
	username = db.Column(db.String(64),unique=True,index=True)
	role_id = db.Column(db.Integer,db.ForeignKey('roles.id'))
	password_hash = db.Column(db.String(128))

	#用户信息
	name = db.Column(db.String(64))
	about_me = db.Column(db.Text())
	memeber_since = db.Column(db.DateTime(),default=datetime.utcnow)
	last_seen = db.Column(db.DateTime(),default=datetime.utcnow)

	#刷新最后访问的时间
	def ping(self):
		self.last_seen = datetime.utcnow()
		db.session.add(self)

	#权限检测
	def can(self,permissions):
		return self.role is not None and\
		(self.role.permissions&permissions) == permissions
	#检测是否管理员
	def is_administrator(self):
		return self.can(Permission.ADMINISTER)
	#设定密码
	@property
	def password(self):
		raise AttributeError("password is not a readable attribute!")

	@password.setter
	def password(self,password):
		self.password_hash = generate_password_hash(password)
	#验证密码
	def verify_password(self,password):
		return check_password_hash(self.password_hash,password)

	def __repr__(self):
		return '<User %r>'%self.username
#游客
class AnonymousUser(AnonymousUserMixin):
	def can(self,permissions):
		return False
	def is_administrator(self):
		return False
		
login_manager.anonymous_user = AnonymousUser