# This file is part galatea_tutorial module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.cache import Cache
from .tools import slugify

__all__ = ['GalateaTutorial', 'GalateaTutorialWebSite', 'GalateaTutorialComment']


class GalateaTutorial(ModelSQL, ModelView):
    "Galatea Tutorial"
    __name__ = 'galatea.tutorial'
    name = fields.Char('Name', required=True, on_change=['name', 'slug'])
    slug = fields.Char('slug', required=True, translate=True,
        help='Cannonical uri.')
    slug_langs = fields.Function(fields.Dict(None, 'Slug Langs'), 'get_slug_langs')
    description = fields.Text('Description', required=True, translate=True,
        help='You could write wiki markup to create html content. Formats text following '
        'the MediaWiki (http://meta.wikimedia.org/wiki/Help:Editing) syntax.')
    long_description = fields.Text('Long Description', translate=True,
        help='You could write wiki markup to create html content. Formats text following '
        'the MediaWiki (http://meta.wikimedia.org/wiki/Help:Editing) syntax.')
    metadescription = fields.Char('Meta Description', translate=True, 
        help='Almost all search engines recommend it to be shorter ' \
        'than 155 characters of plain text')
    metakeywords = fields.Char('Meta Keywords',  translate=True,
        help='Separated by comma')
    metatitle = fields.Char('Meta Title',  translate=True)
    active = fields.Boolean('Active',
        help='Dissable to not show content tutorial.')
    websites = fields.Many2Many('galatea.tutorial-galatea.website', 
        'tutorial', 'website', 'Websites',
        help='Tutorial will be available in those websites')
    gallery = fields.Boolean('Gallery', help='Active gallery attachments.')
    comment = fields.Boolean('Comment', help='Active comments.')
    comments = fields.One2Many('galatea.tutorial.comment', 'tutorial', 'Comments')
    attachments = fields.One2Many('ir.attachment', 'resource', 'Attachments')
    _slug_langs_cache = Cache('galatea_tutorial.slug_langs')

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_websites():
        Website = Pool().get('galatea.website')
        return [p.id for p in Website.search([('registration','=',True)])]

    @classmethod
    def __setup__(cls):
        super(GalateaTutorial, cls).__setup__()
        cls._order.insert(0, ('name', 'ASC'))
        cls._error_messages.update({
            'delete_tutorials': ('You can not delete '
                'tutorials because you will get error 404 NOT Found. '
                'Dissable active field.'),
            })

    def on_change_name(self):
        res = {}
        if self.name and not self.slug:
            res['slug'] = slugify(self.name)
        return res

    @classmethod
    def copy(cls, tutorials, default=None):
        new_tutorials = []
        for tutorial in tutorials:
            default['slug'] = '%s-copy' % tutorial.slug
            new_tutorial, = super(GalateaTutorial, cls).copy([tutorial], default=default)
            tutorials.append(new_tutorial)
        return new_tutorials

    @classmethod
    def delete(cls, tutorials):
        cls.raise_user_error('delete_tutorials')

    def get_slug_langs(self, name):
        'Return dict slugs for each active languages'
        pool = Pool()
        Lang = pool.get('ir.lang')
        Tutorial = pool.get('galatea.tutorial')

        tutorial_id = self.id
        langs = Lang.search([
            ('active', '=', True),
            ('translatable', '=', True),
            ])

        slugs = {}
        for lang in langs:
            with Transaction().set_context(language=lang.code):
                tutorial, = Tutorial.read([tutorial_id], ['slug'])
                slugs[lang.code] = tutorial['slug']

        return slugs


class GalateaTutorialWebSite(ModelSQL):
    'Galatea Tutorial - Website'
    __name__ = 'galatea.tutorial-galatea.website'
    _table = 'galatea_tutorial_galatea_website'
    tutorial = fields.Many2One('galatea.tutorial', 'Tutorial', ondelete='CASCADE',
            select=True, required=True)
    website = fields.Many2One('galatea.website', 'Website', ondelete='RESTRICT',
            select=True, required=True)


class GalateaTutorialComment(ModelSQL, ModelView):
    "Galatea Tutorial Comment"
    __name__ = 'galatea.tutorial.comment'
    tutorial = fields.Many2One('galatea.tutorial', 'Tutorial', required=True)
    user = fields.Many2One('galatea.user', 'User', required=True)
    description = fields.Text('Description', required=True,
        help='You could write wiki markup to create html content. Formats text following '
        'the MediaWiki (http://meta.wikimedia.org/wiki/Help:Editing) syntax.')
    active = fields.Boolean('Active',
        help='Dissable to not show content tutorial.')
    comment_create_date = fields.Function(fields.Char('Create Date'),
        'get_comment_create_date')

    @classmethod
    def __setup__(cls):
        super(GalateaTutorialComment, cls).__setup__()
        cls._order.insert(0, ('create_date', 'DESC'))
        cls._order.insert(1, ('id', 'DESC'))

    @staticmethod
    def default_active():
        return True

    @classmethod
    def default_user(cls):
        Website = Pool().get('galatea.website')
        websites = Website.search([('active', '=', True)])
        if len(websites) == 1:
            if websites[0].tutorial_anonymous_user:
                return websites[0].tutorial_anonymous_user.id

    @classmethod
    def get_comment_create_date(cls, records, name):
        'Created domment date'
        res = {}
        DATE_FORMAT = '%s %s' % (Transaction().context['locale']['date'], '%H:%M:%S')
        for record in records:
            res[record.id] = record.create_date.strftime(DATE_FORMAT) or ''
        return res
