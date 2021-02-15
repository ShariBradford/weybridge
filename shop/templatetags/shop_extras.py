from django import template
from django.template.defaultfilters import stringfilter
from shop.views import get_categories

register = template.Library()

@register.inclusion_tag('shop/sidebar.html', takes_context=True)
def sidebar(context):
    # print(f"{context['user'].first_name}")
    return {
        'categories': get_categories(None),
        'user': context['user'], 
        'test':'Testing 123'
    }

@register.filter(name='strip_characters')
@stringfilter
def strip_characters(input_string):
    return input_string.replace('\\','').replace(' ','_').replace('\'','').replace('\"','')

@register.filter(name='lower', is_safe=True)
@stringfilter
def lower(value):
    """Converts a string into all lowercase"""
    return value.lower()

@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    """
    Creates a URL (containing only the querystring [including "?"]) derived
    from the current URL's querystring, by updating it with the provided
    keyword arguments.

    Example (imagine URL is ``/abc/?gender=male&name=Tim``)::

        {% querystring name="Diego" age=20 %}
        ?name=Diego&gender=male&age=20
    """
    request = context['request']
    updated = request.GET.copy()
    for k, v in kwargs.items():  # have to iterate over and not use .update as it's a QueryDict not a dict
        if v is not None:
            updated[k] = v
        else:
            updated.pop(k, 0)  # Remove or return 0 - aka, delete safely this key

    return '?{}'.format(updated.urlencode()) if updated else '/'
