import markdown2
from django import template

register = template.Library()


@register.filter(name='markdown')
def markdown_filter(value):
    return markdown2.markdown(value)
