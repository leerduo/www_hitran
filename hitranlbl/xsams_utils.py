# -*- coding: utf-8 -*-
# xsams_utils.py
# Christian Hill
# Department of Physics and Astronomy, University College London
# christian.hill@ucl.ac.uk
#
# v0.1 3/9/12
# Helper methods for writing XML tags for an XSAMS document.

def make_mandatory_tag(tag_name, contents, default):
    """
    Make and return a mandatory tag (element) for the XML document, falling
    back to default if contents is None.

    """

    if contents is None:
        contents = default
    return '<%s>%s</%s>' % (tag_name, contents, tag_name)

def make_optional_tag(tag_name, contents, attrs={}):
    """
    Make and return an optional tag (element) for the XML document if
    contents is not None; otherwise return an empty string.

    """

    if contents is None:
        return ''
    s_attrs = ''
    for attr_name, attr_value in attrs.items():
        s_attrs = '%s %s="%s"' % (s_attrs, attr_name, attr_value)
    return '<%s%s>%s</%s>' % (tag_name, s_attrs, contents, tag_name)

def make_referenced_text_tag(name, value_text, comment=None, src_list=[]):
    """
    Make and return a ReferencedTextType element, containing the element Value
    and (optionally) the elements Comments and (one or more) SourceRefs.

    Attributes:
    name: the name of the ReferencedTextType element
    value_text: a string to be placed within this element's Value tag.
    comment: a string to be placed inside its Comments tag
    src_list: a list of source IDs to be output as SourceRef tags

    """

    tag_parts = ['<%s>' % name,]
    if comment:
        tag_parts.append(make_optional_tag('Comments', comment))
    for source_id in src_list:
        tag_parts.append('<SourceRef>B%s-%d</SourceRef>' (NODEID, source_id))
    tag_parts.append('<Value>%s</Value>' % value_text)
    tag_parts.append('</%s>' % name)
    return '\n'.join(tag_parts)

def make_datatype_tag(name, value, error=None, comment=None, src_list=[]):
    tag_parts = ['<%s>' % name,]
    if comment:
        tag_parts.append(make_optional_tag('Comments', comment))
    for source_id in src_list:
        tag_parts.append('<SourceRef>B%s-%d</SourceRef>' (NODEID, source_id))
    tag_parts.append(make_mandatory_tag('Value', value, '[Missing Value]'))
    tag_parts.append(make_optional_tag('Accuracy', error,
                     {'type': 'statistical'}))
    tag_parts.append('</%s>' % name)
    return '\n'.join(tag_parts)

