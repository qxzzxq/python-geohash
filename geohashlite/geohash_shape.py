import logging

from shapely.geometry import box, Point, shape, geo
from shapely.ops import cascaded_union

from . import geohash

logger = logging.getLogger(__name__)


class ExistedValueError(Exception):
    pass


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


def geojson_2_geohash(feature_collection, precision):
    """
    Convert a geojson feature collection to a list of geohash
    :param feature_collection: geojson feature collection
    :param precision: int, length of geohash
    :return: list of geohash (length of geohash is defined by precision)
    """
    # geohash_output = []
    # for feature in feature_collection["features"]:
    #     li_geohash = geometry_2_geohash(feature['geometry'], precision=precision)
    #     geohash_output += li_geohash

    hash_codes = [geometry_2_geohash(feature['geometry'], precision=precision)
                  for feature in feature_collection["features"]]

    return list(set(hash_codes))


def geohash_2_multipolygon(geohash_list, union=False):
    """
    Convert a list of geohash code to a MultiPolygon geometry
    :param geohash_list:
    :param union: if True, then return a cascaded union of all the multipolygons
    :return: a geometry of multipolygon. dict
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

    geometry = {
        "type": "MultiPolygon",
        "coordinates": coordinates
    }

    if union:
        geometry_shp = shape(geometry)
        polygon_union = cascaded_union(geometry_shp)
        geometry = geo.mapping(polygon_union)

    return geometry


def cascaded_union_geohash(geohash_list):
    """
    Depreciated. Keep for backward compatibility.
    Calculate the cascaded union
    :param geohash_list:
    :return: dict, a geojson gemetry
    """
    logger.warning("The function cascaded_union_geohash is depreciated, "
                   "use geohash_2_multipolygon(geohash_list, union=True). "
                   "It is kept for backward compatibility.")

    geometry = geohash_2_multipolygon(geohash_list)

    geometry_shp = shape(geometry)
    polygon_union = cascaded_union(geometry_shp)

    new_geometry = geo.mapping(polygon_union)

    return new_geometry


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


class GeoJsonHasher:

    def __init__(self):
        self.__geohash_codes = None
        self.__geojson = None

    @property
    def geohash_codes(self):
        return self.__geohash_codes

    @geohash_codes.setter
    def geohash_codes(self, value):
        if value:
            if isinstance(value, list):
                self.__geohash_codes = value
            else:
                self.__geohash_codes = list(value)
            logger.debug('Add {} geohash codes'.format(len(self.__geohash_codes)))

    @property
    def geojson(self):
        return self.__geojson

    @geojson.setter
    def geojson(self, value):
        if value:
            if isinstance(value, dict):
                if value.get("type", "none").lower() == "featurecollection":
                    self.__geojson = value
                else:
                    raise ValueError("Unknown GeoJSON type {}".format(value.get("type", "none")))
            else:
                raise TypeError("Please convert geojson to a dict")

    def encode_geojson(self, keep_json_format=False, precision=7, mode='intersect', threshold=None, overwrite=False):
        """
        Encode the GeoJson format dict with a given precision

        :param keep_json_format: if set to True, then the geohash code will be added as property to each feature
        :type keep_json_format: bool
        :param precision: precision level of geohash
        :type precision: int
        :param mode: 'intersect' - all geohashes intersect the shape
                                   use 'threashold' option to specify a percentage of least coverage
                     'inside' - all geohashes inside the shape
                     'center' - all geohashes whose center is inside the shape
        :type mode: str
        :param threshold: percentage of least coverage
        :type threshold: float
        :param overwrite: if True, overwrite the existing value of the object
        :return: a GeoJSON format dict if keep_json_format is True, else a list of Geohash codes
        """

        if self.__geohash_codes and not overwrite:
            raise ExistedValueError('The GeoJsonHasher object has existing geohash codes. '
                                    'Set overwrite to True to overwrite it.')

        if keep_json_format:
            logger.debug('Keep json format: True')

            __geohash_buffer = []
            for f in self.__geojson['features']:
                geometry_shp = shape(f['geometry'])
                li_geohash = geohash_shape(geometry_shp, precision=precision, mode=mode, threshold=threshold)
                f['properties'] = {"geohash": li_geohash}
                __geohash_buffer += li_geohash

            # remove duplicated geohash codes
            self.__geohash_codes = list(set(__geohash_buffer))

            # Debugging info
            logger.debug('Removed {} duplicated geohash codes.'.format(
                len(__geohash_buffer) - len(self.__geohash_codes))
            )
            logger.debug('Added {} geohash code.'.format(len(self.__geohash_codes)))

            return self.__geojson

        li_geometry = [shape(f['geometry']) for f in self.__geojson['features']]
        li_geohash = []
        for geo_shape in li_geometry:
            hashes = geohash_shape(geo_shape, precision=precision, mode=mode, threshold=threshold)
            li_geohash += hashes

        self.__geohash_codes = list(set(li_geohash))

        return self.__geohash_codes

    def decode_geohash(self, multipolygon=False, union=True, overwrite=False):
        """
        Decode a geohash list and return a GeoJSON format dict
        :param multipolygon: by default, decode_geohash will create a GeoJSON polygon for each geohash code, by
                             setting multipolygon to True, only one multipolygon that contains all geohash codes
                             will be created.
        :param union: set to True to calculate the cascaded union of all the polygons
        :param overwrite:
        :return: a GeoJSON format dict
        """
        if self.__geojson and not overwrite:
            raise ExistedValueError('The GeoJsonHasher object has existing geojson. Set overwrite '
                                    'to True to overwrite it.')

        if not self.__geohash_codes:
            raise ValueError('GeoJsonHasher has no GeoHash codes.')

        if multipolygon:
            coordinates = [self._polygon_coordinates(geohash.bbox(i)) for i in self.__geohash_codes]
            logger.debug('Calculating coordinates.')

            __geometry = {
                "type": "MultiPolygon",
                "coordinates": coordinates
            }

            if union:
                geometry_shp = shape(__geometry)
                polygon_union = cascaded_union(geometry_shp)
                __geometry = geo.mapping(polygon_union)
                logger.debug('Calculate cascaded union.')

            __feature = {
                "type": "Feature",
                "properties": {
                    "geohash": self.__geohash_codes
                },
                "geometry": __geometry
            }

            __features = [__feature]

        else:
            __features = [
                {
                    "type": "Feature",
                    "properties": {
                        "geohash": [i]
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": self._polygon_coordinates(geohash.bbox(i))
                    }
                } for i in self.__geohash_codes
            ]
            logger.debug('multipolygon: False, creating features.')

        __feature_collection = {
            "type": "FeatureCollection",
            "features": __features
        }
        self.__geojson = __feature_collection
        return self.__geojson

    @staticmethod
    def _polygon_coordinates(bbox):
        """Find coordinates of a Polygon geometry type"""
        coordinates = [
            [
                [bbox["w"], bbox["s"]],
                [bbox["e"], bbox["s"]],
                [bbox["e"], bbox["n"]],
                [bbox["w"], bbox["n"]],
                [bbox["w"], bbox["s"]],
            ]
        ]

        return coordinates
