#!/usr/bin/env python

import copy
from pathlib import Path
import tempfile
import click
import json
import fiona
from shapely.geometry import shape
from shapely.ops import polygonize_full, unary_union
from auscophub import saraclient
import geopandas


def _collection_info():
    """
    An internal util for retrieving the SARA Collections information.
    """
    collections_url = "https://copernicus.nci.org.au/sara.server/1.0/collections.json"
    url_opener = saraclient.makeUrlOpener()
    collection_info, err = saraclient.readJsonUrl(url_opener, collections_url)

    if err is None:
        return collection_info
    else:
        raise Exception(err)


def collection_info(outdir=None):
    """
    List the available collections and their products.
    """
    collection_info = _collection_info()

    for collection in collection_info:
        name = collection['name']
        products = collection['statistics']['facets']['productType']

        print("{}:\n".format(name))

        for product, _ in products.items():
            print("\t{}\n".format(product))

    if outdir is not None:
        out_fname = Path(outdir).joinpath('collections.json')

        if not out_fname.parent.exists():
            out_fname.mkdir()

        with out_fname.open('w') as src:
            json.dump(collection_info, src, indent=4)


def query(collection, query_params, polygon_fname=None):
    """
    
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
    results = saraclient.searchSara(url_opener, collection[1], params)

    json_doc = {
        "type": "FeatureCollection",
        "properties": {},
        "features": results
    }

    return json_doc


def count(query_result):
    """
    Count Polygon overlaps
    TODO:
        * have optional bounding box instead of the provided geometry
    """
    # temporarily write the result to disk
    with tempfile.TemporaryDirectory() as tmpdir:
        fname = str(Path(tmpdir, 'query.geojson'))
        with open(fname, 'w') as src:
            json.dump(query_result, src, indent=4)

        df = geopandas.read_file(fname)

    # only keep valid geometry
    valid = df[df.is_valid].copy()

    # workaround as geopandas returns errors when doing a unary_union
    geoms = []
    for _, row in valid.iterrows():
        # convert to line (simplest is to use the exterior),
        # that way the union will keep the nodes
        geoms.append(row.geometry.exterior)

    # union the line features, and convert to polygons
    union = unary_union(geoms)
    result, dangles, cuts, invalids = polygonize_full(union)

    # separate the multi-geometry feature into individual features
    explode = [p for p in result]

    # insert into geopandas and create centroids
    non_overlaps = geopandas.GeoDataFrame({'fid': range(len(explode))},
                                          geometry=explode, crs=df.crs)
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
