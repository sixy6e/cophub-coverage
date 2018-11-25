#!/usr/bin/env python

import copy
from pathlib import Path
import tempfile
import json
import fiona
from fiona.transform import transform_geom
from shapely.geometry import mapping, MultiPolygon, shape
from shapely.ops import polygonize_full, unary_union
from auscophub import saraclient
import geopandas


def collection_info():
    """
    List the available collections and their products.
    """
    collections_url = "https://copernicus.nci.org.au/sara.server/1.0/collections.json"
    url_opener = saraclient.makeUrlOpener()
    info, err = saraclient.readJsonUrl(url_opener, collections_url)

    if err is None:
        return info
    else:
        raise Exception(err)


def query(collection, query_params, polygon_fname=None):
    """
    Submit the query to SARA and return a GeoJSON document.

    :param collection:
        A string containing the Collection as defined in SARA.

    :param query_params:
        A list containing additional query parameters to be used in
        querying SARA.

    :param polygon_fname:
        A string containing the full file pathname of an OGR compliant
        vector file. Ideally the vector file will contain a single
        polygon defining the Region Of Interest (ROI) to spatially
        constrain the search to.
    """
    # search by polygon, startDate, completionDate, collection, productType
    url_opener = saraclient.makeUrlOpener()

    params = copy.copy(query_params)

    if polygon_fname is not None:
        # only deal with the first feature at this point in time
        with fiona.open(polygon_fname, 'r') as src:
            feature = src[0]

        geom = shape(feature['geometry'])
        params.append("geometry={}".format(geom.wkt))

    # the searchSara api requires 1, 2 or 3, not S1, S2, or S3
    sentinel_number = collection[1]
    results = saraclient.searchSara(url_opener, sentinel_number, params)

    json_doc = {
        "type": "FeatureCollection",
        "properties": {},
        "features": results
    }

    return json_doc


def count(query_result):
    """
    Count Polygon overlaps.
    Only valid geometries will be included in the process.
    Polygon's crossing the dateline will be split along the meridian.

    The method is general enough to be used for any polygonal
    geometry input. As such, depending on the complexity of the
    geometry, and the number of features, this could take a while.

    The generic method is:
        * convert to line features (union then preserves nodes)
        * union all line geometries
        * polygonise unioned features (non-overlapping polygons)
        * create centroids of each non-overlapping polygon
        * spatial join (centroids contained within overlapping polygons)
        * summarise counts per non-overlapping polygon

    Refined smarts such as merging by a region identifier, i.e.
    Landsat Path/Row, or Sentinel-2 MGRS Tile ID, could significantly
    reduce the computational cost, in terms of processing time and
    memory used.
    However, the first cut is to have something generic that works
    across all sensor acquisition footprints.

    :param query_result:
        A GeoJSON dict as returned by `count_overlaps.query`.

    :return:
        A GeoDataFrame containing frequency counts determined by
        overlapping Polygons.
    """
    # temporarily write the result to disk
    with tempfile.TemporaryDirectory() as tmpdir:
        fname = str(Path(tmpdir, 'query.geojson'))
        with open(fname, 'w') as src:
            json.dump(query_result, src, indent=4)

        df = geopandas.read_file(fname)

    # TODO Look into the cause of invalid geometry and fix if required
    # only keep valid geometry
    valid = df[df.is_valid].copy()

    # manual workaround as geopandas returns errors when doing a unary_union
    # split geometries along the dateline meridian
    # convert geometries to line features (simplest is to use exterior),
    # that way the union will preserve the nodes
    exteriors = []
    for _, row in valid.iterrows():
        # split any geometries crossing the dateline
        split = transform_geom(df.crs, df.crs, mapping(row.geometry),
                               antimeridian_cutting=True)

        geom = shape(split)
        if isinstance(geom, MultiPolygon):
            exteriors.extend([g.exterior for g in geom])
        else:
            exteriors.append(geom.exterior)

    # union the line features, and convert to polygons
    union = unary_union(exteriors)
    result, dangles, cuts, invalids = polygonize_full(union)

    # separate the multi-geometry feature into individual features
    explode = [p for p in result]

    # insert into geopandas and create centroids
    non_overlaps = geopandas.GeoDataFrame(
        {'fid': range(len(explode))}, geometry=explode, crs=df.crs)
    non_overlaps['centroid'] = non_overlaps.centroid
    non_overlaps.set_geometry('centroid', inplace=True)

    # spatial join (centroids within observations)
    sjoin = geopandas.sjoin(non_overlaps, valid, how='left', op='within')

    # overlap count per centroid
    # overlap_count = sjoin.groupby(['fid']).agg(['count'])
    overlap_count = sjoin.groupby(['fid']).size().reset_index(name='observations')
    overlap_count.set_index('fid', inplace=True)

    # table join the centroid overlap count with the non-overlapping geometry
    non_overlaps.set_geometry('geometry', inplace=True)
    tjoin = non_overlaps.join(overlap_count, on='fid')

    # reset the non-overlapping polygons as the geometry source for the dataframe
    tjoin.set_geometry('geometry', inplace=True)
    tjoin.drop('centroid', axis=1, inplace=True)

    return tjoin
