#!/bin/ksh
#BSUB -J gfs_htar
#BSUB -o gfs_htar.%J.out
#BSUB -e gfs_htar.%J.out
#BSUB -n 1
#BSUB -W 00:45
#BSUB -P GFS-T2O
#BSUB -q transfer
#BSUB -R "rusage[mem=1000]"
#BSUB -R "affinity[core]"

module use -a /u/Benjamin.Blake/modulefiles
module load anaconda2/latest


#==============================================  BEGIN CHANGES  ================================================

CASE=2000012212
CYCLE=2000012612

FHR_START=0
FHR_END=48
FHR_INC=6

if [ $SITE = GYRE ]; then
   RETRO_DIR="/meso/noscrub/$USER/WSRP/${CASE}/data"
elif [ $SITE = TIDE ]; then
   RETRO_DIR="/meso/noscrub/$USER/WSRP/${CASE}/data"
fi

#===============================================  END CHANGES  =================================================

REPO_DIR="/meso/save/Logan.Dawson/EMC_meg/Logan_MEG/FV3retro_scripts"

mkdir -p $RETRO_DIR

cd $RETRO_DIR

/bin/rm -rf htar_gfsanl_done

YYYY=`echo $CYCLE | cut -c 1-4`
YYYYMM=`echo $CYCLE | cut -c 1-6`
YYYYMMDD=`echo $CYCLE | cut -c 1-8`
HH=`echo $CYCLE | cut -c 9-10`

file="${CYCLE}_valids.txt"
if [[ -e ${RETRO_DIR}/${file} ]] ; then
   echo ""
else
   python ${REPO_DIR}/valids.py $CYCLE $FHR_START $FHR_END $FHR_INC
fi

#===============================================  GET ANALYSES  =================================================
AVN_DATES=2003010100
GFS_CHANGE_DATE1=2016051000
GFS_CHANGE_DATE2=2017072000

while IFS= read -r line ; do
   VALID="`echo $line`"
   YYYY=`echo $VALID | cut -c 1-4`
   YYYYMM=`echo $VALID | cut -c 1-6`
   YYYYMMDD=`echo $VALID | cut -c 1-8`
   HH=`echo $VALID | cut -c 9-10`

##### GFS
   if ((${VALID} < ${AVN_DATES})) ; then
      GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/com_avn_prod_avn.${VALID}.tar
      GFS_FILE1=gblav.t${HH}z.pgrbf00
      GFS_FILE2=gfs.${YYYYMMDD}.t${HH}z.pgrb.1p00.f000.grib

   elif ((${VALID} < ${GFS_CHANGE_DATE1})) ; then
      GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/com_gfs_prod_gfs.${VALID}.pgrb2_0p25.tar
      GFS_FILE1=gfs.t${HH}z.pgrb2.0p25.f000
      GFS_FILE2=gfs.${YYYYMMDD}.t${HH}z.pgrb2.0p25.f000.grib2

   elif (((${VALID} >= ${GFS_CHANGE_DATE1}) && (${VALID} <= ${GFS_CHANGE_DATE2}))) ; then
      GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/com2_gfs_prod_gfs.${VALID}.pgrb2_0p25.tar
      GFS_FILE1=gfs.t${HH}z.pgrb2.0p25.f000
      GFS_FILE2=gfs.${YYYYMMDD}.t${HH}z.pgrb2.0p25.f000.grib2

   elif ((${VALID} > ${GFS_CHANGE_DATE2})) ; then
      GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/gpfs_hps_nco_ops_com_gfs_prod_gfs.${VALID}.pgrb2_0p25.tar
      GFS_FILE1=gfs.t${HH}z.pgrb2.0p25.f000
      GFS_FILE2=gfs.${YYYYMMDD}.t${HH}z.pgrb2.0p25.f000.grib2
   fi

   # make temporary directory to download into
   mkdir -p $RETRO_DIR/gfsanl.${CYCLE}
   cd $RETRO_DIR/gfsanl.${CYCLE}

   if [[ -e ${RETRO_DIR}/${GFS_FILE2} ]] ; then
      echo ${VALID}" GFS analysis exists"
   else
      echo "Extracting "${VALID}" GFS analysis"
#     htar -xvf $GFS_ARCHIVE ./gfs.t${HH}z.pgrb2.0p25.f000 
#     mv ./gfs.t${HH}z.pgrb2.0p25.f000 ${RETRO_DIR}/gfs.${YYYYMMDD}.t${HH}z.pgrb2.0p25.f000.grib2

      htar -xvf $GFS_ARCHIVE ./${GFS_FILE1}
      mv ./${GFS_FILE1} ${RETRO_DIR}/${GFS_FILE2}
   fi

done <"$file"
#==============================================================================================================

cd $RETRO_DIR
/bin/rm -fR $RETRO_DIR/gfsanl.${CYCLE}

touch htar_gfsanl_done



exit
