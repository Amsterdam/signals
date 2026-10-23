// SPDX-License-Identifier: MPL-2.0
// Copyright (C) 2026 Gemeente Amsterdam
/* global MapWidget, ol */
'use strict';

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-admin-osm-widget]').forEach(function(container) {
        const options = {
            base_layer: new ol.layer.Tile({source: new ol.source.OSM()}),
            default_lat: Number(container.dataset.defaultLat),
            default_lon: Number(container.dataset.defaultLon),
            default_zoom: Number(container.dataset.defaultZoom),
            geom_name: container.dataset.geomName,
            id: container.dataset.fieldId,
            map_id: container.dataset.mapId,
            map_srid: Number(container.dataset.mapSrid),
            name: container.dataset.fieldName,
        };

        window[container.dataset.module] = new MapWidget(options);
    });
});
