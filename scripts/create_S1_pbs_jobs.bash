#!/bin/bash

display_usage() {
    echo ""
    echo "*******************************************************************************"
    echo "* create_S1_pbs_jobs: Creates PBS jobs for Sentinel-1 processing and          *"
    echo "*                     automatically starts them for each year/month.          *"
    echo "*                     Used for either creating shapefiles or                  *"
    echo "*                     checking zip files to see if they are corrupt           *"
    echo "*                                                                             *"
    echo "* input:  [list_dir]   name of list directory (eg. 20160531_SLC_lists)        *"
    echo "*                        - created by create_S1_zipfile_list.bash             *"
    echo "*         [mode]       sensor mode (IW, SM only)                              *"
    echo "*         [compare]    compare was used for zipfile list creation             *"
    echo "*                      (0=no, 1=yes)                                          *"
    echo "*                                                                             *"
    echo "* author: Sarah Lawrie @ GA       17/04/2018, v1.1                           *"
    echo "*******************************************************************************"
    echo -e "Usage: create_S1_pbs_jobs.bash [list_dir] [mode] [compare]"
    }

if [ $# -lt 3]
then
    display_usage
    exit 1
fi

mode=$2
compare=$3
type=`echo $1 | cut -d '_' -f2`
list_date=`echo $1 | cut -d '_' -f1`
proj_dir=/g/data1/dg9/INSAR_ANALYSIS/Sentinel-1_shapefiles/$type
list_dir=$proj_dir/$1

cd $list_dir

full_list="zip_list_"$mode"_"$type"_"$list_date
awk -F' ' '{print > "list_""'$mode'""_""'$type'""_"$1}' $full_list
ls "list_"$mode"_"$type* > text_list
text_files=$list_dir/text_list

cd $proj_dir

if [ $compare == 0 ]; then
    if [ $mode == 'SM' ]; then
	jobtime='5:00:00'
	queue='express'
    elif [ $mode == 'IW' ]; then
	jobtime='48:00:00'
	queue='normal'
    fi
elif [ $compare == 1 ]; then 
    if [ $mode == 'SM' ]; then
	jobtime='2:00:00'
	queue='express'
    elif [ $mode == 'IW' ]; then
	jobtime='24:00:00'
	queue='express'
    fi
fi

## Create PBS jobs for shapefile creation
shp_dir=$proj_dir/$list_date"_"$mode"_"$type"_shapefiles"
mkdir -p $shp_dir
cd $shp_dir
while read list; do
    yr_mth=`echo $list | cut -d '_' -f4`
    dir=$shp_dir/$yr_mth"_S1_"$mode"_"$type
    mkdir -p $dir
    cp $list_dir/$list $dir
    cd $dir
    job="S1_"$mode$type"_"$yr_mth
    echo \#\!/bin/bash > $job
    echo \#\PBS -lother=gdata1 >> $job
    echo \#\PBS -l walltime=$jobtime >> $job
    echo \#\PBS -l mem=4GB >> $job
    echo \#\PBS -l ncpus=1 >> $job
    echo \#\PBS -l wd >> $job
    echo \#\PBS -q $queue >> $job
    echo "module load gdal/1.11.1-python" >> $job
    echo "module load python/2.7.6" >> $job
    echo /g/data1/dg9/INSAR_ANALYSIS/Sentinel-1_shapefiles/scripts/"create_S1_"$type"_shapefile.py" $list >> $job
    chmod +x $job
    qsub $job
    cd ../
done < $text_files
rm -f $text_files



