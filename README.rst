================================================================================
                         Ripping Records gigs Django app
================================================================================


The ``gigs`` package is a standalone Django app that transforms gigs listed on
the `web site of the Edinburgh institution Ripping Records`_ and into a set of
database models: ``Gig``, ``Artist``, ``Venue``, ``Town``, and ``Promoter``.

.. _web site of the Edinburgh institution Ripping Records: http://www.rippingrecords.com/tickets01.html


How the screen scraping works
===============================

Although the information is collected through screen scraping it isn't done
directly.  Google Docs has a fantastic spreadsheets function named
``ImportHtml`` that allows you to take a list or table from any web page and
make it a spreadsheet.  To screen scrape the information create a new
spreadsheet and in cell A1 type::

    =ImportHtml("http://rippingrecords.com/tickets01.html", "table", 1)

Hit enter and the spreadsheet will be filled with the gigs information and will
update every hour.  From there click the *Share* button in the top right and
select *Publish as a web page* from the drop-down menu.  Choose to publish
Sheet 1 only, tick *Automatically republish when changes are made* and click
*Start publishing*.

In the second section titled *Get a link to the published data* choose
*CSV (comma separated values)* from the first drop-down and then copy the link
from the text box.  My `original CSV data`_ is is available but I strongly
recommend creating your own spreadsheet so you retain full control.

.. _original CSV data: http://spreadsheets.google.com/pub?key=thBslf6p90trUBz_tFOBo1g&output=csv


How to install the app
========================

Clone this Git repository and add the ``gigs`` package to your Django project.
The ``gigs`` directory must be on your ``PYTHON_PATH`` as everything is imported
directly — for example, ``from gigs.models import Artist``.

Take the CSV link you copied above and create a variable in your project's
``settings.py`` named ``RIPPING_RECORDS_SPREADSHEET_URL``::

    RIPPING_RECORDS_SPREADSHEET_URL = 'http://spreadsheets.google.com/pub?key=thBslf6p90trUBz_tFOBo1g&output=csv'

Include the gigs app in your project's ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        # ...
        'gigs',
    )

And finally run ``django-admin.py syncdb`` to create the database tables.


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

The data import is complete but the app is missing views and templates for
outputting the data outside the Django admin app.  I hope to rectify this
shortly.


Get in touch
==============

Improvements to the code and to this documentation especially is welcomed.
Please fork the code and `contact me`_ whenever you wish.

.. _contact me: http://www.flother.com/contact/
