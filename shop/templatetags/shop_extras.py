from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.defaultfilters import stringfilter
from shop.services import get_categories

from decimal import Decimal
import math

register = template.Library()

@register.inclusion_tag('shop/sidebar.html', takes_context=True)
def sidebar(context):
    """
        Template tag that returns the category sidebar markup.
    """
    # print(f"{context['user'].first_name}")
    try:
        category = context['category']
    except KeyError:
        category = 0

    return {
        'categories': get_categories(None),
        'user': context['user'], 
        'test':'Testing 123',
        'category': category,
    }

# @register.filter
# def cart_item_count(request):
#     if user.is_authenticated:
#         qs = Order.objects.filter(user=user, ordered=False)
#         if qs.exists():
#             return qs[0].items.count()
#     return

@register.filter(name='strip_characters')
@stringfilter
def strip_characters(input_string):
    """
        Template tag that removes certain chracters from input_string param. 
    """
    return (
        input_string
        .replace('\\','')
        .replace(' ','_')
        .replace('\'','')
        .replace('\"','')
    )

@register.filter(name='lower', is_safe=True)
@stringfilter
def lower(value):
    """
        Converts a string into all lowercase
    """

    return value.lower()

@register.filter(name='negative', is_safe=True)
def negative(value):
    """Converts negative numbers into parentheses"""
    # print(f"Value: {value} (type={type(value)})")
    output = ''

    if value: 
        if isinstance(value, str):
            value=Decimal(value)
            
        output = '<span style="color:red">({})</span>'.format(intcomma(math.fabs(value))) if value < 0 else "{}".format(intcomma(value))

    return output 

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
