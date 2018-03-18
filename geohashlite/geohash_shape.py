from shapely.geometry import box, Point, shape, geo
from shapely.ops import cascaded_union

from . import geohash


def neighbor(geo_hash, direction):
    """
    Find neighbor of a geohash string in certain direction.
    :param geo_hash: geohash string
    :type geo_hash: str
    :param direction: Direction is a two-element array, i.e. [1,0] means north, [1,1] means northeast
    :type direction: list
    :return: geohash string
    :rtype: str
    """
    decode_result = geohash.decode_exactly(geo_hash)
    neighbor_lat = decode_result[0] + direction[0] * decode_result[2] * 2
    neighbor_lon = decode_result[1] + direction[1] * decode_result[3] * 2
    return geohash.encode(neighbor_lat, neighbor_lon, len(geo_hash))


def geohash_shape(shp, precision, mode='intersect', threshold=None):
    """
    Find list of geohashes to cover the shape
    :param shp: shape to cover
    :type shp: BaseGeometry
    :param precision: geohash precision
    :type precision: int
    :param mode: 'intersect' - all geohashes intersect the shape
                               use 'threashold' option to specify a percentage of least coverage
                 'inside' - all geohashes inside the shape
                 'center' - all geohashes whose center is inside the shape
    :type mode: str
    :param threshold: percentage of least coverage
    :type threshold: float
    :return: list of geohashes
    :rtype: list
    """
    (min_lon, min_lat, max_lon, max_lat) = shp.bounds

    hash_south_west = geohash.encode(min_lat, min_lon, precision)
    hash_north_east = geohash.encode(max_lat, max_lon, precision)

    box_south_west = geohash.decode_exactly(hash_south_west)
    box_north_east = geohash.decode_exactly(hash_north_east)

    per_lat = box_south_west[2] * 2
    per_lon = box_south_west[3] * 2

    lat_step = int(round((box_north_east[0] - box_south_west[0]) / per_lat))
    lon_step = int(round((box_north_east[1] - box_south_west[1]) / per_lon))

    hash_list = []

    for lat in range(0, lat_step + 1):
        for lon in range(0, lon_step + 1):
            next_hash = neighbor(hash_south_west, [lat, lon])
            if mode == 'center':
                (lat_center, lon_center) = geohash.decode(next_hash)
                if shp.contains(Point(lon_center, lat_center)):
                    hash_list.append(next_hash)
            else:
                next_bbox = geohash.bbox(next_hash)
                next_bbox_geom = box(next_bbox['w'], next_bbox['s'], next_bbox['e'], next_bbox['n'])

                if mode == 'inside':
                    if shp.contains(next_bbox_geom):
                        hash_list.append(next_hash)
                elif mode == 'intersect':
                    if shp.intersects(next_bbox_geom):
                        if threshold is None:
                            hash_list.append(next_hash)
                        else:
                            intersected_area = shp.intersection(next_bbox_geom).area
                            if (intersected_area / next_bbox_geom.area) >= threshold:
                                hash_list.append(next_hash)

    return hash_list


def geohash_2_geojson(geohash_list):
    """
    Convert a list of geohash to a geojson feature collection
    :param geohash_list:
    :return:
    """

    geohash_list = list(geohash_list)

    features = []

    for hash_code in geohash_list:
        _box = geohash.bbox(hash_code)

        to_append = {
            "type": "Feature",
            "properties": {
                "geohash": hash_code
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [_box["w"], _box["s"]],
                        [_box["e"], _box["s"]],
                        [_box["e"], _box["n"]],
                        [_box["w"], _box["n"]],
                        [_box["w"], _box["s"]],
                    ]
                ]
            }
        }

        features += [to_append]

    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }

    return feature_collection


def geohash_2_multipolygon(geohash_list):
    """
    Convert a list of geohash code to a MultiPolygon geometry
    :param geohash_list:
    :return: dict
    {
        "type": "MultiPolygon",
        "coordinates": [...]
    }
    """

    if not isinstance(geohash_list, list):
        geohash_list = list(geohash_list)

    coordinates = []

    for hash_code in geohash_list:
        _box = geohash.bbox(hash_code)

        to_append = [
            [
                [_box["w"], _box["s"]],
                [_box["e"], _box["s"]],
                [_box["e"], _box["n"]],
                [_box["w"], _box["n"]],
                [_box["w"], _box["s"]],
            ]
        ]
        coordinates += [to_append]

    output = {
        "type": "MultiPolygon",
        "coordinates": coordinates
    }

    return output


def cascaded_union_geohash(geohash_list):
    """
    Calculate the cascaded union
    :param geohash_list:
    :return: dict, a geojson gemetry
    """

    geometry = geohash_2_multipolygon(geohash_list)

    geometry_shp = shape(geometry)
    polygon_union = cascaded_union(geometry_shp)

    new_geometry = geo.mapping(polygon_union)

    return new_geometry


def geojson_2_geohash(feature_collection, precision):
    """
    Convert a geojson feature collection to a list of geohash
    :param feature_collection: geojson feature collection
    :param precision: int, length of geohash
    :return: list of geohash (length of geohash is defined by precision)
    """
    geohash_output = []

    for feature in feature_collection["features"]:
        li_geohash = geometry_2_geohash(feature['geometry'], precision=precision)
        geohash_output += li_geohash

    return list(set(geohash_output))


def geometry_2_geohash(geometry, precision):
    """
    Convert a geojson geometry to a list of geohash

    :param geometry: geojson geometry
    :param precision: int, length of geohash
    :return: list of geohash (length of geohash is defined by precision)
    """
    geometry_shp = shape(geometry)
    li_geohash = geohash_shape(geometry_shp, precision=precision)

    return li_geohash


def add_geohash(feature_collection, precision):
    """
    For each feature of the geojson FeatureCollection, add the corresponding geohash list
    to its properties

    :param feature_collection: geojson feature collection
    :param precision: length of the geohash
    :return: A geojson FeatureCollection
    """

    for feature in feature_collection['features']:
        feature['properties']['geohash'] = geometry_2_geohash(feature['geometry'],
                                                              precision=precision)

    return feature_collection
