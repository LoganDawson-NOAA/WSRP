#!/usr/bin/env python

import numpy as np
import datetime, time, os, sys, subprocess


# Determine date/time information
try:
   ymdh = str(sys.argv[1])
except IndexError:
   ymdh = None

if ymdh is None:
   ymdh = raw_input('Enter time for case (YYYYMMDDHH): ')

YYYY  = int(ymdh[0:4])
MM    = int(ymdh[4:6])
DD    = int(ymdh[6:8])
HH    = int(ymdh[8:10])

date_str = datetime.datetime(YYYY,MM,DD,HH,0,0)


# Set path
WSRP_DIR = os.getcwd()


# Set up for Theia
if WSRP_DIR == '/scratch4/NCEPDEV/stmp4/Logan.Dawson/WSRP':
   WGRIB2 = '/apps/wgrib2/0.1.9.5.1/bin/wgrib2'
   DATA_DIR = os.path.join(WSRP_DIR, ymdh, 'data')

# Set up for Tide/Gyre
elif WSRP_DIR == '/gpfs/td1/emc/meso/save/Logan.Dawson/WSRP' or WSRP_DIR =='/gpfs/gd1/emc/meso/save/Logan.Dawson/WSRP':
   WGRIB = '/nwprod/util/exec/wgrib'
   WGRIB2 = '/nwprod/util/exec/wgrib2'
   COPYGB = '/nwprod/util/exec/copygb'
   DATA_DIR = os.path.join('/meso/noscrub/Logan.Dawson/WSRP', ymdh, 'data')

   OUT_DIR = os.path.join('/gpfs/'+WSRP_DIR[6]+'p2/ptmp/Logan.Dawson/WSRP', ymdh, 'data')
   if not os.path.exists(OUT_DIR):
      os.makedirs(OUT_DIR)

   LOG_DIR = os.path.join('/gpfs/'+WSRP_DIR[6]+'p2/ptmp/Logan.Dawson/WSRP', ymdh, 'logs')
   if not os.path.exists(LOG_DIR):
      os.makedirs(LOG_DIR)

os.chdir(DATA_DIR)



# By default, will ask for command line input to determine which analysis files to pull 
# User can uncomment and modify the next line to bypass the command line calls
#   nhrs = np.arange(-96,121,6)
nhrs = np.arange(-96,97,6)

try:
   nhrs
except NameError:
   nhrs = None

if nhrs is None:
   hrb = input('Enter first hour (normally -96, for 4 days lead time): ')
   hre = input('Enter last hour: ')
   step = input('Enter hourly step: ')
   nhrs = np.arange(hrb,hre+1,step)


#print 'Array of hours is: '
#print nhrs

date_list = [date_str + datetime.timedelta(hours=x) for x in nhrs]


try:
   resolution = str(sys.argv[2])
   if resolution == '0.25':
      print 'subsetting '+resolution+'-deg data'
   # expecting a string with '0.25'
except IndexError:
   resolution = None

if resolution is None:
   if YYYY < 2007:
      resolution = '1.0'
   elif YYYY >= 2007:
      resolution = '0.5'
   print 'subsetting '+resolution+'-deg data'


grib1file = DATA_DIR+'/gfs.'+ymdh[0:8]+'.t'+ymdh[8:]+'z.pgrb.'+resolution[0]+'p'+resolution[2:].ljust(2,'0')+'.f000.grib'
grib2file = DATA_DIR+'/gfs.'+ymdh[0:8]+'.t'+ymdh[8:]+'z.pgrb2.'+resolution[0]+'p'+resolution[2:].ljust(2,'0')+'.f000.grib2'
if os.path.exists(grib2file) and not os.path.exists(grib1file):
   grib_mod = 'pgrb2' 
   grib_ext = 'grib2' 
   WGRIB_COMMAND = WGRIB2
elif os.path.exists(grib1file) and not os.path.exists(grib2file):
   grib_mod = 'pgrb' 
   grib_ext = 'grib' 
   WGRIB_COMMAND = WGRIB
else:
   print 'gribfile name error'



isobaric_levels = [10, 20, 30, 50, 70, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 925, 950, 975, 1000]
isobaric_vars1 = ['HGT', 'TMP', 'UGRD', 'VGRD']
isobaric_vars2 = ['RH', 'VVEL', 'CLWMR']

sfc_vars = ['PRES', 'HGT', 'TMP', 'WEASD', 'SNOD', 'LAND', 'ICEC'] 
pvu_vars = ['UGRD', 'VGRD', 'TMP', 'HGT', 'PRES', 'VWSH']


for j in range(len(date_list)):
#for j in range(1):

   YYYYMMDDCC = date_list[j].strftime("%Y%m%d%H")
   print "Subsetting analysis for "+YYYYMMDDCC+" cycle"

   anl_orig = 'gfs.'+YYYYMMDDCC[0:8]+'.t'+YYYYMMDDCC[8:]+'z.'+grib_mod+'.'+resolution[0]+'p'+resolution[2:].ljust(2,'0')+'.f000.'+grib_ext
   anl_temp = 'gfstemp.'+YYYYMMDDCC[0:8]+'.t'+YYYYMMDDCC[8:]+'z.'+grib_mod+'.'+resolution[0]+'p'+resolution[2:].ljust(2,'0')+'.f000.'+grib_ext
   anl_file = 'gfsanl.'+YYYYMMDDCC[0:8]+'.t'+YYYYMMDDCC[8:]+'z.'+grib_mod+'.'+resolution[0]+'p'+resolution[2:].ljust(2,'0')+'.f000.'+grib_ext

   orig_inv = 'gribfile_'+resolution[0]+'p'+resolution[2:].ljust(2,'0')+'.inv'
   anl_inv = 'gfsanl_'+resolution[0]+'p'+resolution[2:].ljust(2,'0')+'.inv'

#  if ymdh == '2016012200':
#     anl_orig = 'gfs.'+YYYYMMDDCC[0:8]+'.t'+YYYYMMDDCC[8:]+'z.pgrb2.0p25.anl'
#     anl_file = 'gfsanl.'+YYYYMMDDCC[0:8]+'.t'+YYYYMMDDCC[8:]+'z.pgrb2.0p25.anl'
#  elif ymdh == '2016012212':
#     anl_orig = 'gfs.'+YYYYMMDDCC[0:8]+'.t'+YYYYMMDDCC[8:]+'z.pgrb2.0p25.f000.grib2'
#     anl_temp = 'gfstemp.'+YYYYMMDDCC[0:8]+'.t'+YYYYMMDDCC[8:]+'z.pgrb2.0p25.f000.grib2'
#     anl_file = 'gfsanl.'+YYYYMMDDCC[0:8]+'.t'+YYYYMMDDCC[8:]+'z.pgrb2.0p25.f000.grib2'
#  elif ymdh == '2000012400':
#     anl_orig = 'gblav.'+YYYYMMDDCC[0:8]+'.t'+YYYYMMDDCC[8:]+'z.pgrbanl'
             

   os.system('rm -rf '+anl_temp+' '+anl_file+' '+orig_inv)
   os.system(WGRIB_COMMAND+' '+anl_orig+' > '+orig_inv)

   # Do isobaric level data first
   for press in isobaric_levels:

      for var in isobaric_vars1:
         if press == 10:
            # write first grib message to new file  
            try:
               subprocess.check_output(['grep',':'+var+':'+str(press)+' mb:',orig_inv])
               os.system('grep \':'+var+':'+str(press)+' mb:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
            except subprocess.CalledProcessError:
               print str(press)+' mb '+var+' does not exist in file'
         else:
            # append additional messages to same file
            try:
               subprocess.check_output(['grep',':'+var+':'+str(press)+' mb:',orig_inv])
               os.system('grep \':'+var+':'+str(press)+' mb:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
            except subprocess.CalledProcessError:
               print str(press)+' mb '+var+' does not exist in file'

      if press >= 100:
         for var in isobaric_vars2:
            try:
               subprocess.check_output(['grep',':'+var+':'+str(press)+' mb:',orig_inv])
               os.system('grep \':'+var+':'+str(press)+' mb:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
            except subprocess.CalledProcessError:
               print str(press)+' mb '+var+' does not exist in file'

         if press == 500:
            try:
               subprocess.check_output(['grep',':ABSV:'+str(press)+' mb:',orig_inv])
               os.system('grep \':ABSV:'+str(press)+' mb:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
            except subprocess.CalledProcessError:
               print str(press)+' mb ABSV does not exist in file'

            try:
               subprocess.check_output(['grep',':5WAVH:'+str(press)+' mb:',orig_inv])
               os.system('grep \':5WAVH:'+str(press)+' mb:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
            except subprocess.CalledProcessError:
               print str(press)+' mb 5WAVH does not exist in file'

            try:
               subprocess.check_output(['grep',':5WAVA:'+str(press)+' mb:',orig_inv])
               os.system('grep \':5WAVA:'+str(press)+' mb:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
            except subprocess.CalledProcessError:
               print str(press)+' mb 5WAVA does not exist in file'
   
 
   # Do surface data next
   for var in sfc_vars:
      try:
         subprocess.check_output(['grep',':'+var+':surface:',orig_inv])
         os.system('grep \':'+var+':surface:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
      except subprocess.CalledProcessError:
         if var == 'HGT' or var == 'TMP' or var == 'PRES':
            print str(press)+' mb '+var+' does not exist in file'
         else:
            print var+' does not exist in file'

     
   try:
      subprocess.check_output(['grep',':MSLET:mean sea level:',orig_inv])
      os.system('grep \':MSLET:mean sea level:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print 'MSLET does not exist in file'

   try:
      subprocess.check_output(['grep',':PRMSL:mean sea level:',orig_inv])
      os.system('grep \':PRMSL:mean sea level:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print 'PRMSL does not exist in file'

   try:
      subprocess.check_output(['grep',':TMP:2 m above ground:',orig_inv])
      os.system('grep \':TMP:2 m above ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print '2m TMP does not exist in file'

   try:
      subprocess.check_output(['grep',':DPT:2 m above ground:',orig_inv])
      os.system('grep \':DPT:2 m above ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print '2m DPT does not exist in file'

   try:
      subprocess.check_output(['grep',':RH:2 m above ground:',orig_inv])
      os.system('grep \':RH:2 m above ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print '2m RH does not exist in file'

   try:
      subprocess.check_output(['grep',':UGRD:10 m above ground:',orig_inv])
      os.system('grep \':UGRD:10 m above ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print '10m UGRD does not exist in file'

   try:
      subprocess.check_output(['grep',':VGRD:10 m above ground:',orig_inv])
      os.system('grep \':VGRD:10 m above ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print '10m VGRD does not exist in file'
   

   # Do underground data next
   try:
      subprocess.check_output(['grep',':TSOIL:0-0.1 m below ground:',orig_inv])
      os.system('grep \':TSOIL:0-0.1 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print '0-0.1 m TSOIL does not exist in file. Trying 0-0.1 m TMP'
      try:
         subprocess.check_output(['grep',':TMP:0-0.1 m below ground:',orig_inv])
         os.system('grep \':TMP:0-0.1 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
      except subprocess.CalledProcessError:
         print '0-0.1 m TMP does not exist in file'

   try:
      subprocess.check_output(['grep',':SOILW:0-0.1 m below ground:',orig_inv])
      os.system('grep \':SOILW:0-0.1 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print '0-0.1 m SOILW does not exist in file'

   try:
      subprocess.check_output(['grep',':TSOIL:0.1-0.4 m below ground:',orig_inv])
      os.system('grep \':TSOIL:0.1-0.4 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print '0.1-0.4 m TSOIL does not exist in file. Trying 0.1-0.4 m TMP'
      try:
         subprocess.check_output(['grep',':TMP:0.1-0.4 m below ground:',orig_inv])
         os.system('grep \':TMP:0.1-0.4 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
      except subprocess.CalledProcessError:
         print '0.1-0.4 m TMP does not exist in file. Will check for just two soil layers'

   try:
      subprocess.check_output(['grep',':SOILW:0.1-0.4 m below ground:',orig_inv])
      os.system('grep \':SOILW:0.1-0.4 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
      soil_layers = 4
   except subprocess.CalledProcessError:
      print '0.1-0.4 m SOILW does not exist in file. Will check for just two soil layers'
      soil_layers = 2


   if soil_layers == 4:

      try:
         subprocess.check_output(['grep',':TSOIL:0.4-1 m below ground:',orig_inv])
         os.system('grep \':TSOIL:0.4-1 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
      except subprocess.CalledProcessError:
         print '0.4-1 m TSOIL does not exist in file. Trying 0.4-1 m TMP'
         try:
            subprocess.check_output(['grep',':TMP:0.4-1 m below ground:',orig_inv])
            os.system('grep \':TMP:0.4-1 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
         except subprocess.CalledProcessError:
            print '0.4-1 m TMP does not exist in file'

      try:
         subprocess.check_output(['grep',':SOILW:0.4-1 m below ground:',orig_inv])
         os.system('grep \':SOILW:0.4-1 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
      except subprocess.CalledProcessError:
         print '0.4-1 m SOILW does not exist in file'

      try:
         subprocess.check_output(['grep',':TSOIL:1-2 m below ground:',orig_inv])
         os.system('grep \':TSOIL:1-2 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
      except subprocess.CalledProcessError:
         print '1-2 m TSOIL does not exist in file. Trying 1-2 m TMP'
         try:
            subprocess.check_output(['grep',':TMP:1-2 m below ground:',orig_inv])
            os.system('grep \':TMP:1-2 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
         except subprocess.CalledProcessError:
            print '1-2 m TMP does not exist in file'

      try:
         subprocess.check_output(['grep',':SOILW:1-2 m below ground:',orig_inv])
         os.system('grep \':SOILW:1-2 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
      except subprocess.CalledProcessError:
         print '1-2 m SOILW does not exist in file'

   elif soil_layers == 2:

      try:
         subprocess.check_output(['grep',':TSOIL:0.1-2 m below ground:',orig_inv])
         os.system('grep \':TSOIL:0.1-2 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
      except subprocess.CalledProcessError:
         print '0.1-2 m TSOIL does not exist in file. Trying 0.1-2 m TMP'
         try:
            subprocess.check_output(['grep',':TMP:0.1-2 m below ground:',orig_inv])
            os.system('grep \':TMP:0.1-2 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
         except subprocess.CalledProcessError:
            print '0.1-2 m TMP does not exist in file'

      try:
         subprocess.check_output(['grep',':SOILW:0.1-2 m below ground:',orig_inv])
         os.system('grep \':SOILW:0.1-2 m below ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
      except subprocess.CalledProcessError:
         print '0.1-2 m SOILW does not exist in file'


   # Do total column data next
   try:
      subprocess.check_output(['grep',':PWAT:',orig_inv])
      os.system('grep \':PWAT:entire atmosphere (considered as a single layer):\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print 'PWAT does not exist in file'

   try:
      subprocess.check_output(['grep',':CWAT:',orig_inv])
      os.system('grep \':CWAT:entire atmosphere (considered as a single layer):\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print 'CWAT does not exist in file'

   try:
      subprocess.check_output(['grep',':TOZNE:',orig_inv])
      os.system('grep \':TOZNE:entire atmosphere (considered as a single layer):\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print 'TOZNE does not exist in file'


   # Do instability data next
   try:
      subprocess.check_output(['grep',':4LFTX:surface:',orig_inv])
      os.system('grep \':4LFTX:surface:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print '4LFTX does not exist in file'

   try:
      subprocess.check_output(['grep',':CAPE:surface:',orig_inv])
      os.system('grep \':CAPE:surface:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print 'SBCAPE does not exist in file'

   try:
      subprocess.check_output(['grep',':CIN:surface:',orig_inv])
      os.system('grep \':CIN:surface:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print 'SBCIN does not exist in file'

   try:
      subprocess.check_output(['grep',':CAPE:180-0 mb above ground:',orig_inv])
      os.system('grep \':CAPE:180-0 mb above ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print '180-0 mb CAPE does not exist in file'

   try:
      subprocess.check_output(['grep',':CIN:180-0 mb above ground:',orig_inv])
      os.system('grep \':CIN:180-0 mb above ground:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print '180-0 mb CIN does not exist in file'

   try:
      subprocess.check_output(['grep',':POT:0.995 sigma level:',orig_inv])
      os.system('grep \':POT:0.995 sigma level:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
   except subprocess.CalledProcessError:
      print '0.995 sigma POT does not exist in file'


   # Do 2-PVU level data last
   for var in pvu_vars:
      try:
         subprocess.check_output(['grep',':'+var+':PV=2e-06 (Km^2/kg/s) surface:',orig_inv])
         os.system('grep \':'+var+':PV=2e-06 (Km^2/kg/s) surface:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
      except subprocess.CalledProcessError:
         print 'Looking for different 2-PVU '+var+' in file'
         try:
            subprocess.check_output(['grep',':'+var+':PV=2e-09 (Km^2/kg/s) surface:',orig_inv])
            os.system('grep \':'+var+':PV=2e-06 (Km^2/kg/s) surface:\' '+orig_inv+' | '+WGRIB_COMMAND+' -append -i '+anl_orig+' -grib '+anl_temp+' > dummy')
         except subprocess.CalledProcessError:
            print '2-PVU '+var+' does not exist in file'


   #Finally subset to Northern/Western Hemisphere and remove temporary file
   os.system(WGRIB_COMMAND+' '+anl_temp+' -set_grib_type same -small_grib 170:360 10:90 '+anl_file+' > '+anl_inv)
   os.system('rm '+anl_temp)

   os.system('mv '+anl_file+' '+OUT_DIR+'/'+anl_file)
   os.system('mv '+anl_inv+' '+LOG_DIR+'/'+anl_inv)

print "Done"
