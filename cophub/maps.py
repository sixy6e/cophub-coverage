#!/usr/bin/env python

"""
A small util to produce the monthly coverage heat maps for
the Australasia Copernicus Data Hub.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import geopandas
from cartopy import crs as ccrs


def monthly_coverage(indir, outdir, countries_fname=None):
    """
    Produce the monthly coverage heatmaps for the
    Copernicus Australasia Data Hub.

    :param indir:
        The input directory that will be globbed for `*.geojson`.

    :param outdir:
        The output directory that will contain the maps as PNG's.

    :param countries_fname:
        Optional. A filename to a fiona supported vector file that
        provides world locational context for the output map.
        Example, TM_WORLD_BORDERS.

    :return:
        None. Outputs are written to disk.
    """
    title_fmt_lookup = {
        "S1": "{collection} {product} {mode} {direction} {year_month}",
        "S2": "{collection} {product} {year_month}",
        "S3": "{collection} {product} {year_month}"
    }

    # output crs, centred over the Great Australian Bight
    crs = ccrs.SouthPolarStereo(131, -32)
    crs_proj4 = crs.proj4_init

    # TM World Borders, or some other countries backdrop
    if countries_fname is None:
        tm_gdf = None
    else:
        tm_gdf = geopandas.read_file(countries_fname).to_crs(crs_proj4)

    for fname in [f for f in Path(indir).glob('*.geojson')]:
        gdf = geopandas.read_file(str(fname)).to_crs(crs_proj4)

        # fname format is "(<query_param>=<query_value>)_"
        parts = dict([i.split('=') for i in fname.stem.split('_')])

        # expected keys are "collection", "startDate", "endDate"
        title_fmt = title_fmt_lookup[parts['collection']]
        year_month = parts['startDate'][0:7]
        if 'sensorMode' in parts:
            # Sentinel-1
            title = title_fmt.format(collection=parts['collection'],
                                     product=parts['productType'],
                                     mode=parts['sensorMode'],
                                     direction=parts['orbitDirection'],
                                     year_month=year_month)
        else:
            # Sentinel-2
            title = title_fmt.format(collection=parts['collection'],
                                     product=parts['productType'],
                                     year_month=year_month)


        # setup the plot
        fig, axes = plt.subplots()
        gdf.plot(column='observations', legend=True, cmap='rainbow',
                 linewidth=0, ax=axes)

        if tm_gdf is not None:
            tm_gdf.plot(linewidth=0.25, edgecolor='black', facecolor='none',
                        ax=axes)

        axes.set_title(title)

        # these axis limits were found by plotting a few examples
        axes.set_xlim(-11436864.243194133, 12196121.573371675)
        axes.set_ylim(-2593925.0238779895, 15765584.618743382)

        # output filename
        out_fname = Path(outdir).joinpath('{}.png'.format(fname.stem))
        if not out_fname.parent.exists():
            out_fname.parent.mkdir()

        fig.savefig(out_fname)
        plt.close(fig)
        # fig = axes = None
