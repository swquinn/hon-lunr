"""
    hon_lunr
    ~~~~~

    A plugin for the Hon utility. It extends the Hon HTML output by adding
    search indexing using Lunr to the book's website.

    :license: MIT, see LICENSE for more details.
"""
import hon
import json
import os
import shutil
from hon.plugins import Plugin
from html.parser import HTMLParser
from jinja2 import (
    Environment,
    PackageLoader,
    Template,
    select_autoescape
)
from lunr import lunr


#: The Hon-Lunr plugin's path.
LUNR_PLUGIN_PATH = os.path.abspath(os.path.dirname(__file__))

#: The default maximum number of documents that Lunr can index.
DEFAULT_MAX_INDEX_SIZE = 1000000


def _on_finish_render(app, book=None, renderer=None, context=None):
    """Function connected to rendering finished signal.
    """
    lunr = app.get_plugin(Lunr)
    lunr.on_finish(book, renderer, context)


def _on_before_render(app, book=None, renderer=None, context=None):
    """Function connected to the before render signal.
    """
    lunr = app.get_plugin(Lunr)
    lunr.before_render(book, renderer, context)


def _on_generate_assets(app, book=None, renderer=None, context=None):
    """Function connected to the asset generation signal.
    """
    lunr = app.get_plugin(Lunr)
    lunr.generate_assets(book, renderer, context)


def _on_after_render_page(app, book=None, renderer=None, page=None, context=None):
    """Function connected to the after page render signal.
    """
    lunr = app.get_plugin(Lunr)
    lunr.after_render_page(book, renderer, page, context)


class PageTextParser(HTMLParser):
    """
    """

    def __init__(self, *args, **kwargs):
        super(PageTextParser, self).__init__(*args, **kwargs)
        self.text = ''

    def handle_data(self, data):
        text = str(data).strip()
        if text:
            self.text += text


class Lunr(Plugin):
    """A Hon plugin that adds Lunr search indexing.

    Lunr has issues with indexing more than 100k documents.

    :type document_store: dict
    :type search_index: object
    """
    _name = 'Lunr'

    default_config = {
        'enabled': True,
        'max_index_size': DEFAULT_MAX_INDEX_SIZE
    }

    @property
    def assets_dir(self):
        """
        """
        path = os.path.join(LUNR_PLUGIN_PATH, 'assets')
        return path

    @property
    def max_index_size(self):
        """
        """
        return self.config.get('max_index_size', DEFAULT_MAX_INDEX_SIZE)

    def __init__(self, app, config=None):
        super(Lunr, self).__init__(app, config=config)
        #: The document store that will
        self.document_store = {}

        #:
        self.search_index = None

        if app:
            self.init_app(app)

    def add_document(self, page_url, title, summary, keywords, body):
        document = {
            'url': page_url,
            'title': title,
            'summary': summary,
            'keywords': keywords,
            'body': body
        }
        self.document_store[page_url] = document
        return document

    def init_app(self, app):
        self.app.logger.debug('Initializing Lunr plugin for Hon...')
        self.environment = Environment(
            loader=PackageLoader('hon_lunr', 'templates')
        )

        #: Hook up the Lunr search plugin to relevant events...
        hon.after_render_page.connect(_on_after_render_page)
        hon.before_render.connect(_on_before_render)
        hon.finish_render.connect(_on_finish_render)
        hon.generate_assets.connect(_on_generate_assets)

    def after_render_page(self, book, renderer, page, context):
        """
        """
        if renderer.name != 'html' or not self.enabled or not page.search:
            return

        self.app.logger.debug('index page {}'.format(page.path))
        search_text = self.parse_search_text(page)
        self.add_document(page.link, page.title, page.summary,
            page.keywords, search_text)

    def before_render(self, book, renderer, context):
        """

        :param context: The rendering context for the book.
        :type context: hon.renderers.RenderingContext
        """
        if renderer.name != 'html' or not self.enabled:
            return

        print('*** context: {}'.format(context))
        context.add_plugin_resource({ 'path': 'js/lunr.js' }, 'js')
        context.add_plugin_resource({ 'path': 'js/hon-lunr.js' }, 'js')
        print('*** context: {}'.format(context))

    def generate_assets(self, book, renderer, context):
        if renderer.name != 'html' or not self.enabled:
            return

        js_output_dir = os.path.join(context.path, 'js')

        for asset_file in os.listdir(self.assets_dir):
            source = os.path.join(self.assets_dir, asset_file)
            if os.path.isfile(source):
                dest = os.path.join(js_output_dir, asset_file)
                shutil.copyfile(source, dest)

    def on_finish(self, book, renderer, context):
        if renderer.name != 'html' or not self.enabled:
            return

        js_output_dir = os.path.join(context.path, 'js')

        self.app.logger.debug('write search index')
        self.search_index = lunr(
            ref='url',
            fields=[
                dict(field_name='title', boost=10),
                dict(field_name='keywords', boost=15),
                'body'
            ],
            documents=self.document_store.values()
        )
        serialized_index = self.search_index.serialize()
        serialized = json.dumps(serialized_index)

        template = self.environment.get_template('hon-lunr.js.jinja')
        output = template.render({
            'hon_lunr': {
                'search_index': serialized
            }
        })

        hon_lunr_filename = 'hon-lunr.js'
        hon_lunr_filepath = os.path.join(js_output_dir, hon_lunr_filename)
        with open(hon_lunr_filepath, 'w') as f:
            f.write(output)

    def parse_search_text(self, page):
        """
        """
        parser = PageTextParser()
        parser.feed(page.text)
        return parser.text
