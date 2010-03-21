if (typeof(Gigs) == 'undefined') Gigs = {};

/**
 * Map functions.
 */
Gigs.map = {
	element: '',
	mediaUrl: '',
	apiKey: '',
	styleId: '',
	canvas: null,

	/**
	 * Prepare to show a map. Pass the id of the element to replace with the
	 * map, the relative path to the media URL, Cloudmade API key, and the
	 * Cloudmade map style id.
	 */
	init: function (element, mediaUrl, apiKey, styleId) {
		Gigs.map.element = element;
		Gigs.map.mediaUrl = mediaUrl;
		Gigs.map.apiKey = apiKey;
		Gigs.map.styleId = styleId;
	},

	/**
	 * Display a map on the page, centred on the passed longitude and latitude.
	 */
	show: function(lat, lng, zoom) {
		// Create the tile base.
		var cloudmade =  new CM.Tiles.Base({
			tileUrlTemplate: 'http://#{subdomain}.tile.cloudmade.com/' + Gigs.map.apiKey + '/' + Gigs.map.styleId + '/256/#{zoom}/#{x}/#{y}.png'
		});

		// Create the map and centre it.
		Gigs.map.canvas = new CM.Map(Gigs.map.element, cloudmade);
		Gigs.map.canvas.setCenter(new CM.LatLng(lat, lng), zoom);

		// Add a transparent overlay over the map, so when a user scrolls down
		// the page it doesn't zoom the map out.
		var mapElement = document.getElementById(Gigs.map.element);
		var mapOverlay = document.createElement('div');
		mapOverlay.setAttribute('id', 'map_overlay');
		mapElement.parentNode.insertBefore(mapOverlay, mapElement.nextSibling);
	},

	/**
	 * Create a custom marker to use on the map.
	 */
	createMarkerIcon: function() {
		Gigs.map.icon = new CM.Icon();
		Gigs.map.icon.image = Gigs.map.mediaUrl + "gigs/img/map_marker.png";
		Gigs.map.icon.iconSize = new CM.Size(16, 16);
	},

	/**
	 * Add a marker to the displayed map at the passed longitude and latitude.
	 * The tooltip displayed on hover will contain the title.
	 */
	addMarker: function (lat, lng, title) {
		if (typeof(Gigs.map.icon) == 'undefined') Gigs.map.createMarkerIcon();
		// Mark the place of interest on the map.
		var pointOfInterest = new CM.LatLng(lat, lng);
		var mapMarker = new CM.Marker(pointOfInterest, {
			title: title,
			icon: Gigs.map.icon
		});
		Gigs.map.canvas.addOverlay(mapMarker);
	}
}
