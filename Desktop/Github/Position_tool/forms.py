from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, SelectField, PasswordField, IntegerField
from wtforms.validators import DataRequired, Optional

class OrderForm(FlaskForm):
    product = SelectField('Product', choices=[], validators=[DataRequired()])
    mwh_value = SelectField('MWh/Unit', choices=[], coerce=int, validators=[DataRequired()])
    buy_sell = SelectField('Buy/Sell', choices=[('Buy', 'Buy'), ('Sell', 'Sell')], validators=[DataRequired()])
    volume = FloatField('Volume', validators=[DataRequired()])
    entry_price = FloatField('Entry Price', validators=[DataRequired()])
    strategy = SelectField('Strategy', choices=[], validators=[DataRequired()])
    comment = StringField('Comment')
    submit = SubmitField('Submit')

class EditOrderForm(FlaskForm):
    product = SelectField('Product', choices=[], validators=[Optional()])
    buy_sell = SelectField('Buy/Sell', choices=[('Buy', 'Buy'), ('Sell', 'Sell')], validators=[Optional()])
    volume = FloatField('Volume', validators=[Optional()])
    entry_price = FloatField('Entry Price', validators=[Optional()])
    exit_price = FloatField('Exit Price', validators=[Optional()])  # ← už není povinné
    strategy = SelectField('Strategy', choices=[], validators=[Optional()])
    comment = StringField('Comment')
    submit = SubmitField('Save Changes')

class EditResultForm(FlaskForm):
    product = SelectField('Product', choices=[], validators=[Optional()])
    mwh_value = SelectField('MWh/Unit', choices=[], coerce=int, validators=[DataRequired()])
    buy_sell = SelectField('Buy/Sell', choices=[('Buy', 'Buy'), ('Sell', 'Sell')], validators=[Optional()])
    volume = FloatField('Volume', validators=[Optional()])
    entry_price = FloatField('Entry Price', validators=[Optional()])
    exit_price = FloatField('Exit Price', validators=[Optional()])  # ← už není povinné
    strategy = SelectField('Strategy', choices=[], validators=[Optional()])
    comment = StringField('Comment')
    submit = SubmitField('Save Changes')

class DictionaryForm(FlaskForm):
    type = SelectField('Type', choices=[], validators=[DataRequired()])
    value = IntegerField('Value', validators=[DataRequired()])
    submit = SubmitField('Add')

class PasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Confirm')
