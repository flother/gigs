from django.contrib import admin

from gigs.models import Gig, Artist, Venue, Town, Promoter, ImportIdentifier


class GigAdmin(admin.ModelAdmin):

    """Django ModelAdmin class for the Gig model."""

    date_hierarchy = 'date'
    fieldsets = (
        (None, {
            'fields': ('slug', ('artist', 'venue', 'promoter'), 'date',
                ('price', 'sold_out'), 'extra_information', 'published')
        }),
        ('Import options', {
            'classes': ('collapse',),
            'fields': ('import_identifiers',)
        }),
    )
    filter_horizontal = ('import_identifiers',)
    list_display = ('artist', 'venue', 'promoter', 'date', 'price', 'sold_out',
        'published')
    list_filter = ('venue', 'promoter')
    prepopulated_field = {'slug': ('artist',)}


class ArtistAdmin(admin.ModelAdmin):

    """Django ModelAdmin class for the Artist model."""

    date_hierarchy = 'updated'
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'biography', 'photo', 'web_site')
        }),
        ('Import options', {
            'classes': ('collapse',),
            'fields': ('import_identifiers',)
        }),
    )
    filter_horizontal = ('import_identifiers',)
    list_display = ('name', 'number_of_upcoming_gigs')
    prepopulated_field = {'slug': ('title',)}


class VenueAdmin(admin.ModelAdmin):

    """Django ModelAdmin class for the Venue model."""

    date_hierarchy = 'updated'
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'address', 'town',
                'photo', 'web_site')
        }),
        ('Import options', {
            'classes': ('collapse',),
            'fields': ('import_identifiers',)
        }),
    )
    filter_horizontal = ('import_identifiers',)
    list_display = ('name', 'town', 'number_of_upcoming_gigs')
    list_filter = ('town',)
    prepopulated_field = {'slug': ('name',)}


class TownAdmin(admin.ModelAdmin):

    """Django ModelAdmin class for the Town model."""

    date_hierarchy = 'updated'
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'photo', 'longitude', 'latitude')
        }),
        ('Import options', {
            'classes': ('collapse',),
            'fields': ('import_identifiers',)
        }),
    )
    filter_horizontal = ('import_identifiers',)
    list_display = ('name', 'number_of_upcoming_gigs')
    prepopulated_field = {'slug': ('name',)}


class PromoterAdmin(admin.ModelAdmin):

    """Django ModelAdmin class for the Promoter model."""

    date_hierarchy = 'updated'
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'web_site')
        }),
        ('Import options', {
            'classes': ('collapse',),
            'fields': ('import_identifiers',)
        }),
    )
    filter_horizontal = ('import_identifiers',)
    list_display = ('name', 'number_of_upcoming_gigs')
    prepopulated_field = {'slug': ('title',)}


admin.site.register(Gig, GigAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Venue, VenueAdmin)
admin.site.register(Town, TownAdmin)
admin.site.register(Promoter, PromoterAdmin)
