from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,TextAreaField
from wtforms.validators import Required,Length

class EditProfileForm(FlaskForm):
	name = StringField('名字',validators=[Length(0,64)])
	about_me = TextAreaField("自我介绍")
	submit = SubmitField('提交')

#class EditProfileAdminForm(FlaskForm):
	