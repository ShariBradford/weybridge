from django import template
from django.template.defaultfilters import stringfilter
from shop.views import get_categories

register = template.Library()

@register.inclusion_tag('shop/sidebar.html', takes_context=True)
def sidebar(context):
    return {'categories': get_categories(None),'test':'Testing 123'}

@register.filter(name='strip_characters')
@stringfilter
def strip_characters(input_string):
    return input_string.replace('\\','').replace(' ','_').replace('\'','').replace('\"','')

@register.filter(name='lower', is_safe=True)
@stringfilter
def lower(value):
    """Converts a string into all lowercase"""
    return value.lower()

