#!/bin/bash

display_usage() {
    echo ""
    echo "*******************************************************************************"
    echo "* collate_S1_results: Collate Sentinel-1 shapefile results into central       *"
    echo "*                     directories.                                            *"
    echo "*                                                                             *"
    echo "* input:  [dir]        name of shapefile results directory                    *"
    echo "*                        (eg. 20160531_IW_SLC_shapefiles)                     *"
    echo "*                                                                             *"
    echo "* author: Sarah Lawrie @ GA       17/04/2018, v1.1                            *"
    echo "*******************************************************************************"
    echo -e "Usage: collate_S1_results.bash [dir]"
    }

if [ $# -lt 1 ]
then
    display_usage
    exit 1
fi

list_date=`echo $1 | cut -d '_' -f1`
mode=`echo $1 | cut -d '_' -f2`
type=`echo $1 | cut -d '_' -f3`
proj_dir=/g/data1/dg9/INSAR_ANALYSIS/Sentinel-1_shapefiles/$type
shp_dir=$proj_dir/$1

cd $proj_dir

mkdir -p $proj_dir/$list_date"_"$mode"_"$type"_results"
results=$proj_dir/$list_date"_"$mode"_"$type"_results"

cd $results

mkdir -p shapefiles
shape=$results/shapefiles

cd $shp_dir
ls -d 20* > dir_list

while read dir; do
    cd $dir/shapefiles
    ls 20*.* > shp_list
    while read shp; do
	cp $shp $shape
    done < shp_list
    rm -f shp_list
    cd $shp_dir
done < $shp_dir/dir_list

rm -f $shp_dir/dir_list
