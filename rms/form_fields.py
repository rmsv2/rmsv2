from django.forms import ModelMultipleChoiceField
from .form_widgets import TagInputWidget
from django.core.exceptions import ValidationError
from .models import Tag


class TagField(ModelMultipleChoiceField):
    widget = TagInputWidget

    def _check_values(self, value):
        while True:
            try:
                return super()._check_values(value)
            except ValidationError as err:
                if err.code == 'invalid_choice':
                    tag = Tag.objects.create(name=err.params.get('value'))
                    tag.save()
