#!/bin/ksh
#BSUB -J gfs_wget
#BSUB -o gfs_wget.%J.out
#BSUB -n 1
#BSUB -W 00:15
#BSUB -P GFS-T2O
#BSUB -q transfer
#BSUB -R "rusage[mem=1000]"
#BSUB -R "affinity[core]"

module use -a /u/Benjamin.Blake/modulefiles
module load anaconda2/latest


#==============================================  BEGIN CHANGES  ================================================#

CASE=2011012600
CYCLE=2011012600

FHR_START=-96
FHR_END=96
FHR_INC=6

if [ $SITE = GYRE ]; then
   RETRO_DIR="/meso/noscrub/$USER/WSRP/${CASE}/data"
elif [ $SITE = TIDE ]; then
   RETRO_DIR="/meso/noscrub/$USER/WSRP/${CASE}/data"
fi

#===============================================  END CHANGES  =================================================#

REPO_DIR="/meso/save/Logan.Dawson/EMC_meg/Logan_MEG/FV3retro_scripts"

mkdir -p $RETRO_DIR

cd $RETRO_DIR

/bin/rm -rf wget_gfsanl_done

YYYY=`echo $CYCLE | cut -c 1-4`
YYYYMM=`echo $CYCLE | cut -c 1-6`
YYYYMMDD=`echo $CYCLE | cut -c 1-8`
HH=`echo $CYCLE | cut -c 9-10`

file="${RETRO_DIR}/${CYCLE}_valids.txt"
if [[ -e ${file} ]] ; then
   echo ""
else
   python ${REPO_DIR}/valids.py $CYCLE $FHR_START $FHR_END $FHR_INC
fi



#===============================================  GET ANALYSES  =================================================#
GRIB_CHANGE_DATE=2006101000

# make temporary directory to download into
mkdir -p $RETRO_DIR/gfsanalysis.${CYCLE}
cd $RETRO_DIR/gfsanalysis.${CYCLE}


while IFS= read -r line ; do
   VALID="`echo $line`"
   YYYY=`echo $VALID | cut -c 1-4`
   MM=`echo $VALID | cut -c 5-6`
   YYYYMM=`echo $VALID | cut -c 1-6`
   YYYYMMDD=`echo $VALID | cut -c 1-8`
   HH=`echo $VALID | cut -c 9-10`


   GFS_ARCHIVE=https://nomads.ncdc.noaa.gov/data/gfsanl/${YYYYMM}/${YYYYMMDD}

   if ((${VALID} < ${GRIB_CHANGE_DATE})) ; then
      GFS_FILE1=gfsanl_3_${YYYYMMDD}_${HH}00_000.grb
      GFS_FILE2=gfs.${YYYYMMDD}.t${HH}z.pgrb2.1p00.f000.grib2

      if ((${YYYY} == 2003)) ; then
         GFS_ARCHIVE=https://rda.ucar.edu/data/ds083.2/grib1/${YYYY}/${YYYY}.${MM}
         GFS_FILE1=fnl_${YYYYMMDD}_${HH}_00.grib1
      fi

   elif ((${VALID} >= ${GRIB_CHANGE_DATE})) ; then
      GFS_FILE1=gfsanl_4_${YYYYMMDD}_${HH}00_000.grb2
      GFS_FILE2=gfs.${YYYYMMDD}.t${HH}z.pgrb2.0p50.f000.grib2
   fi



   if [[ -e ${RETRO_DIR}/${GFS_FILE2} ]] ; then
      echo ${VALID}" GFS analysis exists"
   else
      echo "Extracting "${VALID}" GFS analysis"
         wget ${GFS_ARCHIVE}/${GFS_FILE1}

         if ((${VALID} < ${GRIB_CHANGE_DATE})) ; then
            # convert grib1 to grib2
            cnvgrib -g12 ./${GFS_FILE1} ${RETRO_DIR}/${GFS_FILE2}
         elif ((${VALID} >= ${GRIB_CHANGE_DATE})) ; then
            # simply moves and renames grib2 files
            mv ./${GFS_FILE1} ${RETRO_DIR}/${GFS_FILE2}
         fi
   fi

done <"$file"
#==============================================================================================================

cd $RETRO_DIR
/bin/rm -fR $RETRO_DIR/gfsanalysis.${CYCLE}

touch wget_gfsanl_done



exit
