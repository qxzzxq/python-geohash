# Geohash Lite

GeohashLite is a Python package for dealing with GeoHash code. It support also conversion between GeoJSON 
and a list of GeoHash.

## Installation
Clone this repository
```git
git clone https://github.com/qxzzxq/python-geohash.git
```

Then install with python
```
cd python-geohash
python setup.py install
```

## Dependencies
[Shapely](https://pypi.python.org/pypi/Shapely)

## Usage

**Coordinates encoding**
```python
import geohashlite
geohashlite.encode(48.86913, 2.32275, 7)
```

**Geohash decoding**
```python
geohashlite.decode('u09whb7')
```

**Conversion between GeoJSON and GeoHash**
```python
# GeoHash to GeoJSON
converter_1 = geohashlite.GeoJsonHasher()
x = ['u09k', 'u095', 'u08g', 'u09h', 'u09e', 'u097']
converter_1.geohash_codes = x
converter_1.decode_geohash(multipolygon=True)
print(converter_1.geojson)


# GeoJSON to GeoHash
converter_2 = geohashlite.GeoJsonHasher()
fc = {
  "type": "FeatureCollection",
  "features": [
    "GeoJSON_Feature",
  ]
}
converter_2.geojson = fc
converter_2.encode_geojson(precision=4)
print(converter_2.geohash_codes)

```

**Convert a geohash list to geojson (deprecated)**
```python
geohashlite.geohash_2_geojson(['u09whb7'])
```

**Convert geojson to a geohash list (deprecated)**
```python
fc = {
  "type": "FeatureCollection",
  "features": [
    "a_GeoJSON_Feature"
  ]
}

geohashlite.geojson_2_geohash(fc, precision=7)
``` 

### Acknowledgement
Thanks [Hiroaki Kawai](https://github.com/hkwi/python-geohash) 
and [Jerry Xu](https://testpypi.python.org/pypi/geohashshape).
