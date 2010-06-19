================================================================================
                         Ripping Records gigs Django app
================================================================================


The ``gigs`` package is a standalone Django app that screen-scrapes gigs listed
on the `web site of the Edinburgh institution Ripping Records`_, turning them
into a set of database models: ``Gig``, ``Artist``, ``Album``, ``Venue``,
``Town``, and ``Promoter``.

.. _web site of the Edinburgh institution Ripping Records: http://www.rippingrecords.com/tickets01.html


How the screen scraping works
===============================

Although the information is collected through screen scraping the Ripping
Records web site, it isn't done directly.

Google Docs has a fantastic spreadsheets function named ``ImportHtml`` that
allows you to take a list or table from any web page and convert it into a
spreadsheet.

If you wan to scrape the information yourself create a new spreadsheet and in
cell A1 type::

    =ImportHtml("http://rippingrecords.com/tickets01.html", "table", 1)

Hit enter and the spreadsheet will be filled with the gigs information and will
update roughly every hour.  From there click the *Share* button in the top right
and select *Publish as a web page* from the drop-down menu.  Choose to publish
Sheet 1 only, tick *Automatically republish when changes are made*, and then
click *Start publishing*.

In the second section titled *Get a link to the published data* choose
*CSV (comma separated values)* from the first drop-down and then copy the link
from the text box.  My `original CSV data`_ is is available but I strongly
recommend creating your own spreadsheet so you retain full control.

.. _original CSV data: http://spreadsheets.google.com/pub?key=thBslf6p90trUBz_tFOBo1g&output=csv


Requirements
==============

* Python 2.5
* Django 1.1.1
* sorl-thumbnail: http://sorl-thumbnail.googlecode.com/
* Markdown: http://www.freewisdom.org/projects/python-markdown/

Optional libraries
====================

* pylast 0.4: http://pylast.googlecode.com/
* musicbrainz2 0.7.0: http://musicbrainz.org/doc/PythonMusicBrainz2
* Haystack 1.0.1: http://haystacksearch.org/

When a new artist is created the `Last.fm`_ and `MusicBrainz`_ APIs are used to
find the artist's photos, biographies, albums, and cover art.  This requires the
``pylast`` and ``musicbrainz2`` libraries.  If you don't install them you won't
see any errors (the code fails gracefully) but you won't get the artist metadata
either.

.. _Last.fm: http://www.last.fm/api
.. _MusicBrainz: http://musicbrainz.org/doc/XML_Web_Service

The ``action`` element on the home page's search form links to
``{% url haystack_search %}``, and Haystack search indexes are included in
``gigs.search_indexes``.  If you want to use Haystack, follow the
`installation instructions`_ in the Haystack documentation.  If you don't,
modify or remove the search form from the home page.

.. _installation instructions: http://haystacksearch.org/docs/tutorial.html


How to install the app
========================

Clone this Git repository and add the ``gigs`` app to your Django project. The
``gigs`` directory must be on your ``PYTHON_PATH`` as everything is imported
directly -- for example, ``from gigs.models import Artist``.

Take the CSV link you copied above and create a variable in your project's
``settings.py`` named ``RIPPING_RECORDS_SPREADSHEET_URL``::

    RIPPING_RECORDS_SPREADSHEET_URL = 'http://spreadsheets.google.com/pub?key=thBslf6p90trUBz_tFOBo1g&output=csv'

Include the gigs app in your project's ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        # ...
        'gigs',
    )

If you intend to use the ``import_artist_photos`` management command you'll need
to include your Last.fm API key in your Django project's settings::

  LASTFM_API_KEY = 'YOUR_API_KEY_HERE'

If you use the ``import_albums`` management command (detailed below), each
artist's page will include links to their albums on Amazon.  If you want these
links to include your Amazon affiliate tag include the following setting in your
project's settings file::

  AMAZON_AFFILIATE_TAG = 'your-affiliate-link'

You'll also need to add the ``gigs.context_processors.amazon_affiliate_tag``
context processor to your project's settings::

  TEMPLATE_CONTEXT_PROCESSORS = (
      # ...
      'gigs.context_processors.amazon_affiliate_tag',
  )

Some of the templates display a `Cloudmade`_ map.  In order for the map to be
displayed you need to add two settings and a context processor::

  TEMPLATE_CONTEXT_PROCESSORS = (
      # ...
      'gigs.context_processors.cloudmade',
  )

  CLOUDMADE_API_KEY = 'your-api-key-here'
  CLOUDMADE_STYLE_ID = 1

You can apply for an API key find out more about Cloudmade from the
`Web Maps Studio web site`_

.. _Cloudmade: http://www.cloudmade.com/
.. _Web Maps Studio web site: http://developers.cloudmade.com/projects/show/web-maps-studio

And finally run ``django-admin.py syncdb`` to create the database tables.


Templates and media
=====================

You need to create a symlink named ``gigs`` to the ``gigs/media`` directory
directly underneath your projects media directory.  For example, if your
``MEDIA_URL`` is ``/media/`` this app's media files must be served from
``/media/gigs/``.

The templates included with the app make some assumptions about what blocks will
be available.  You must define the following:

* ``title``: the content for the ``head`` ``title`` element
* ``body_id``: the content of the ``<body id="">`` attribute
* ``body``: the wrapper around the content of the page, somewhere within the
  ``body`` element
* ``content_intro``: a block immediately before the content ``block``
* ``content``: the content of the page; a block within the ``body`` block


Management commands
=====================

There are three management commands included with this app, found in
``gigs.management.commands`` and available to use via ``django-admin.py``.

* ``import_albums``: imports albums from MusicBrainz for each artist.  Cover art
  for imported albums is also imported from Last.fm.
* ``import_artist_metadata``: import a photo and biography for each artist from
  Last.fm.
* ``import_gigs_from_ripping_records``: the main management command that imports
  all gigs occurring in Edinburgh and Glasgow from the Ripping Records web site.
  This command is detailed in the section `Importing the gigs data`_ below.


Importing the gigs data
=========================

The ``gigs`` package includes a management command named
``import_gigs_from_ripping_records``.  This is designed to be run as a regular
cron job, e.g.::

    django-admin.py import_gigs_from_ripping_records

By default the command only outputs to ``stdout`` when a ``Gig``, ``Artist``,
``Venue``, ``Town``, or ``Promoter`` model is created but you can get reams of
debug information if you set the verbosity level to 2::

    django-admin.py import_gigs_from_ripping_records --verbosity=2


Notes on the data import
==========================

The data on the Ripping Records site is entered manually by their staff and so
inevitably errors and ambiguities creep in.  Every attempt is made to normalise
the data upon import, however misspellings will need to be handled by you.

For example, the venue Sneaky Pete's is often spelled Sneaky Petes, and so two
``Venue`` model objects are created.  The ``ImportIdentifier`` model is designed
to solve this problem.  You can use it to link multiple spellings to a single
model object.


Functionality left to implement
=================================

The code is in a working state and can been seen running at
`rippedrecords.com`_.  However, as always, there are always improvements to be
made.  Some that I hope will make there way in soon are:

* Linking similar gigs to one another
* Mark all strings for translation
* Functionality to allow people to email a page's URL to a friend

.. _rippedrecords.com: http://www.rippedrecords.com/

Get in touch
==============

Improvements to the code and to this documentation especially is welcomed.
Please fork the code and `contact me`_ whenever you wish.

.. _contact me: http://www.flother.com/contact/
