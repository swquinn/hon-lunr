"""
    hon_lunr
    ~~~~~

    A plugin for the Hon utility. It extends the Hon HTML output by adding
    search indexing using Lunr to the book's website.

    :license: MIT, see LICENSE for more details.
"""


class Lunr(Plugin):
    """A Hon plugin that adds Lunr search indexing.

    Lunr has issues with indexing more than 100k documents.

    :type document_store: dict
    :type search_index: object
    """
    _name = 'Lunr'
