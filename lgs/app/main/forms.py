from flask_wtf import FlaskForm
from wtforms import StringField,IntegerField,SelectField,SubmitField,TextAreaField
from wtforms.validators import Required,Length,Regexp,NumberRange
from wtforms import ValidationError
from ..models import Role,User
from flask_pagedown.fields import PageDownField

class EditProfileForm(FlaskForm):
	name = StringField('名字',validators=[Length(0,64)])
	about_me = TextAreaField("自我介绍")
	number = IntegerField('电话号码',validators=[NumberRange(11)])
	submit = SubmitField('提交')

class EditProfileAdminForm(FlaskForm):
	username = StringField('用户名',validators=[Length(1,64),
 		Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
 		'用户名只能是英文字母 ，字母和下划线')])
	role = SelectField('用户组',coerce=int)
	name = StringField('名字',validators=[Length(0,64)])
	about_me = TextAreaField("自我介绍")
	submit = SubmitField("提交")

	def __init__(self,user,*args,**kwargs):
		super(EditProfileAdminForm,self).__init__(*args,**kwargs)
		self.role.choices = [(role.id,role.name)
		for role in Role.query.order_by(Role.name).all()]
		self.user = user 


	def validate_username(self,field):
		if field.data != self.user.username and User.query.filter_by(username=field.data).first():
			raise ValidationError('用户名已经存在')


class PostForm(FlaskForm):
	body = PageDownField('想说点啥？',validators=[Required()])
	submit = SubmitField('提交')

class CommentForm(FlaskForm):
	body = PageDownField('评论',validators=[Required()])
	submit = SubmitField('提交')