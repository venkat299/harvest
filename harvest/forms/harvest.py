from dal import autocomplete

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML, Row, Div
from crispy_forms.bootstrap import InlineField, FormActions , StrictButton
from crispy_forms.bootstrap import Field, InlineRadios, TabHolder, Tab
from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.forms.widgets import SelectDateWidget
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import datetime

from harvest.models.strategy import Strategy, Stock, Watchlist, Order, Signal



class LedgerFormHelper(FormHelper):
    form_method = 'GET'
    layout = Layout(
            Div(
                # Div('e_status' , css_class='col-md-3'),
                # # Div('e_doj' , css_class='col-md-3'),
                # Div('e_join' , css_class='col-md-3'),
                Div('strategy__name' , css_class='col-md-3'),
                Div(Submit('submit', 'Apply Filter'), css_class='col-md-3'), css_class='row'
            ),
        )

class OrderFormHelper(FormHelper):
    form_method = 'GET'
    layout = Layout(
            Div(
                Div('signal__watchlist__strategy__name' , css_class='col-md-3'),
                Div(Submit('submit', 'Apply Filter'), css_class='col-md-3'), css_class='row'
            )
        )
class SignalFormHelper(FormHelper):
    form_method = 'GET'
    layout = Layout(
            Div(
                Div('watchlist__strategy__name' , css_class='col-md-3'),
                Div(Submit('submit', 'Apply Filter'), css_class='col-md-3'), css_class='row'
            )
        )
class MySelectDateWidget(SelectDateWidget):

    def create_select(self, *args, **kwargs):
        old_state = self.is_required
        self.is_required = False
        result = super(MySelectDateWidget, self).create_select(*args, **kwargs)
        self.is_required = old_state
        return result