from django.forms.widgets import SelectMultiple


class TagInputWidget(SelectMultiple):
    template_name = 'django/forms/widgets/tag_input.html'

    def _render(self, template_name, context, renderer=None):
        return super()._render(template_name, context, renderer)




