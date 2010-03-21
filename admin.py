from django.contrib import admin

from gigs.models import Gig, Artist, Album, Venue, Town, Promoter,\
    ImportIdentifier


class GigAdmin(admin.ModelAdmin):

    """Django ModelAdmin class for the Gig model."""

    date_hierarchy = 'date'
    fieldsets = (
        (None, {
            'fields': ('slug', ('artist', 'venue', 'promoter'), 'date',
                ('price', 'sold_out', 'cancelled'), 'extra_information',
                'published')
        }),
        ('Import options', {
            'classes': ('collapse',),
            'fields': ('import_identifiers',)
        }),
    )
    filter_horizontal = ('import_identifiers',)
    list_display = ('artist', 'venue', 'promoter', 'date', 'price', 'sold_out',
        'cancelled', 'published')
    list_filter = ('sold_out', 'cancelled', 'published', 'venue', 'promoter')
    list_select_related = True
    ordering = ('-date', 'artist__slug')
    prepopulated_fields = {'slug': ('artist',)}
    search_fields = ('artist__name',)


class ArtistAdmin(admin.ModelAdmin):

    """Django ModelAdmin class for the Artist model."""

    date_hierarchy = 'updated'
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'biography', 'photo', 'web_site',
                'published')
        }),
        ('Import options', {
            'classes': ('collapse',),
            'fields': ('import_identifiers',)
        }),
    )
    filter_horizontal = ('import_identifiers',)
    list_display = ('name', 'number_of_upcoming_gigs', 'published')
    list_filter = ('published',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


class AlbumAdmin(admin.ModelAdmin):

    """Django ModelAdmin class for the Album model."""

    date_hierarchy = 'release_date'
    list_display = ('title', 'artist', 'release_date', 'asin', 'published')
    list_filter = ('published', 'artist')
    list_select_related = True
    search_fields = ('title',)


class VenueAdmin(admin.ModelAdmin):

    """Django ModelAdmin class for the Venue model."""

    date_hierarchy = 'updated'
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'address', 'town',
                'latitude', 'longitude', 'web_site', 'published')
        }),
        ('Import options', {
            'classes': ('collapse',),
            'fields': ('import_identifiers',)
        }),
    )
    filter_horizontal = ('import_identifiers',)
    list_display = ('name', 'town', 'number_of_upcoming_gigs', 'published')
    list_filter = ('published', 'town',)
    list_select_related = True
    prepopulated_fields = {'slug': ('name',)}


class TownAdmin(admin.ModelAdmin):

    """Django ModelAdmin class for the Town model."""

    date_hierarchy = 'updated'
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'latitude', 'longitude', 'published')
        }),
        ('Import options', {
            'classes': ('collapse',),
            'fields': ('import_identifiers',)
        }),
    )
    filter_horizontal = ('import_identifiers',)
    list_display = ('name', 'number_of_upcoming_gigs', 'published')
    list_filter = ('published',)
    prepopulated_fields = {'slug': ('name',)}


class PromoterAdmin(admin.ModelAdmin):

    """Django ModelAdmin class for the Promoter model."""

    date_hierarchy = 'updated'
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'web_site', 'published')
        }),
        ('Import options', {
            'classes': ('collapse',),
            'fields': ('import_identifiers',)
        }),
    )
    filter_horizontal = ('import_identifiers',)
    list_display = ('name', 'number_of_upcoming_gigs')
    list_filter = ('published',)
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Gig, GigAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Album, AlbumAdmin)
admin.site.register(Venue, VenueAdmin)
admin.site.register(Town, TownAdmin)
admin.site.register(Promoter, PromoterAdmin)
