#!/usr/bin/env python

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap, cm
#from matplotlib import GridSpec, rcParams, colors
import matplotlib.gridspec as gridspec
from matplotlib import colors as c
from pylab import *
import numpy as np
import pygrib, datetime, time, os, sys, subprocess
import multiprocessing
import scipy, ncepy
from ncepgrib2 import Grib2Encode, Grib2Decode



def extrema(mat,mode='wrap',window=100):
    # find the indices of local extrema (max only) in the input array.
    mx = scipy.ndimage.filters.maximum_filter(mat,size=window,mode=mode)
    # (mat == mx) true if pixel is equal to the local max
    return np.nonzero(mat == mx)


def plt_Ls(m,mat,lons,lats,ax,mode='wrap',window='10'):
  # From: http://matplotlib.org/basemap/users/examples.html
  # m is the map handle
  x, y = m(lons, lats)
  local_min, local_max = ncepy.extrema(mat,mode,window)
  xlows = x[local_min]; xhighs = x[local_max]
  ylows = y[local_min]; yhighs = y[local_max]
  lowvals = mat[local_min]; highvals = mat[local_max]
  # plot lows as red L's, with min pressure value underneath.
  xyplotted = []
  # don't plot if there is already a L or H within dmin meters.
  yoffset = 0.022*(m.ymax-m.ymin)
  dmin = yoffset
  for x,y,p in zip(xlows, ylows, lowvals):
    if x < m.xmax and x > m.xmin and y < m.ymax and y > m.ymin:
        dist = [np.sqrt((x-x0)**2+(y-y0)**2) for x0,y0 in xyplotted]
        if not dist or min(dist) > dmin:
            ax.text(x,y,'L',fontsize=14,fontweight='bold',
                    ha='center',va='center',color='k',zorder=10)
         #  plt.text(x,y-yoffset,repr(int(p)),fontsize=9,zorder=10,
         #          ha='center',va='top',color='r',
         #          bbox = dict(boxstyle="square",ec='None',fc=(1,1,1,0.5)))
            xyplotted.append((x,y))


def plt_Hs_and_Ls(m,mat,lons,lats,ax,mode='wrap',window='10'):
  # From: http://matplotlib.org/basemap/users/examples.html
  # m is the map handle
  x, y = m(lons, lats)
  local_min, local_max = ncepy.extrema(mat,mode,window)
  xlows = x[local_min]; xhighs = x[local_max]
  ylows = y[local_min]; yhighs = y[local_max]
  lowvals = mat[local_min]; highvals = mat[local_max]
  # plot lows as red L's, with min pressure value underneath.
  xyplotted = []
  # don't plot if there is already a L or H within dmin meters.
  yoffset = 0.022*(m.ymax-m.ymin)
  dmin = yoffset
  for x,y,p in zip(xlows, ylows, lowvals):
    if x < m.xmax and x > m.xmin and y < m.ymax and y > m.ymin:
        dist = [np.sqrt((x-x0)**2+(y-y0)**2) for x0,y0 in xyplotted]
        if not dist or min(dist) > dmin:
            ax.text(x,y,'L',fontsize=14,fontweight='bold',
                    ha='center',va='center',color='k',zorder=10)
         #  plt.text(x,y-yoffset,repr(int(p)),fontsize=9,zorder=10,
         #          ha='center',va='top',color='r',
         #          bbox = dict(boxstyle="square",ec='None',fc=(1,1,1,0.5)))
            xyplotted.append((x,y))
  # plot highs as blue H's, with max pressure value underneath.
  xyplotted = []
  for x,y,p in zip(xhighs, yhighs, highvals):
    if x < m.xmax and x > m.xmin and y < m.ymax and y > m.ymin:
        dist = [np.sqrt((x-x0)**2+(y-y0)**2) for x0,y0 in xyplotted]
        if not dist or min(dist) > dmin:
            ax.text(x,y,'H',fontsize=14,fontweight='bold',
                    ha='center',va='center',color='k',zorder=10)
         #  plt.text(x,y-yoffset,repr(int(p)),fontsize=9,
         #          ha='center',va='top',color='b',zorder=10,
         #          bbox = dict(boxstyle="square",ec='None',fc=(1,1,1,0.5)))
            xyplotted.append((x,y))




# Determine initial date/time
try:
   ymdh = str(sys.argv[1])
except IndexError:
   ymdh = None

if ymdh is None:
   ymdh = raw_input('Enter time for case (YYYYMMDDHH): ')

YYYY = int(ymdh[0:4])
MM   = int(ymdh[4:6])
DD   = int(ymdh[6:8])
HH   = int(ymdh[8:10])
print YYYY, MM, DD, HH

date_str = datetime.datetime(YYYY,MM,DD,HH,0,0)


# Set path and create graphx directory (if not already created)
WSRP_DIR = os.getcwd()

# Set up for Theia
if WSRP_DIR == '/scratch4/NCEPDEV/stmp4/Logan.Dawson/WSRP':
   CASE_DIR = os.path.join(WSRP_DIR, ymdh)
   DATA_DIR = os.path.join(WSRP_DIR, ymdh, 'data')
   GRAPHX_DIR = os.path.join(WSRP_DIR, ymdh, 'graphx')

# Set up for Tide/Gyre
elif WSRP_DIR == '/gpfs/td1/emc/meso/save/Logan.Dawson/WSRP' or WSRP_DIR =='/gpfs/gd1/emc/meso/save/Logan.Dawson/WSRP':
   DATA_DIR = os.path.join('/meso/noscrub/Logan.Dawson/WSRP', ymdh, 'data')
   GRAPHX_DIR = os.path.join('/ptmpp2/Logan.Dawson/WSRP', ymdh, 'graphx')



if os.path.exists(DATA_DIR):
   if not os.path.exists(GRAPHX_DIR):
      os.makedirs(GRAPHX_DIR)
else:
   raise NameError, 'data for '+ymdh+' case not found'



# By default, will ask for command line input to determine which analysis files to pull 
# User can uncomment and modify the next line to bypass the command line calls
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


print 'Array of hours is: '
print nhrs

date_list = [date_str + datetime.timedelta(hours=x) for x in nhrs]


#Specify plots to make
levels = ['250', '300', '500', '700', '850', 'sfc']


def main():

   pool = multiprocessing.Pool(len(levels))
   pool.map(plot_levels,levels)


def plot_levels(level):


   if level == '250':
      domain = 'NA'
      upper_hghts = hghts_250
      upper_isotachs = isotach_250
      HLwindow = 175
   elif level == '300':
      domain = 'NA'
      upper_hghts = hghts_300
      upper_isotachs = isotach_300
      HLwindow = 175
   elif level == '500':
      domain = 'NA'
      HLwindow = 150
   elif level == '700':
      domain = 'NA'
      domain = 'EastNA'
      HLwindow = 100
   elif level == '850':
      domain = 'EastNA'
      skip = 6
      HLwindow = 50
   elif level == 'sfc':
      domain = 'EastNA'
      HLwindow = 50


   # create figure and axes instances
   if domain == 'CONUS':
      fig = plt.figure(figsize=(6.9,4.9))
   elif domain == 'SRxSE':
      fig = plt.figure(figsize=(6.9,4.75))
   else:
   #  fig = plt.figure(figsize=(8,8))
      fig = plt.figure(figsize=(11,11))
   ax = fig.add_axes([0.1,0.1,0.8,0.8])


   if domain == 'NA':
      m = Basemap(llcrnrlon=-142.5,llcrnrlat=12.5,urcrnrlon=-12.5,urcrnrlat=52., \
                  resolution='i',projection='stere',\
                  lat_ts=50.,lat_0=50.,lon_0=-98.5,area_thresh=1000.,ax=ax)
   elif domain == 'EastNA':
        m = Basemap(llcrnrlon=-108.,llcrnrlat=20.,urcrnrlon=-45.,urcrnrlat=52., \
                    resolution='i',projection='stere',\
                    lat_ts=50.,lat_0=40.,lon_0=-82.5,area_thresh=1000.,ax=ax)

   m.drawcoastlines()
   m.drawstates(linewidth=0.25)
   m.drawcountries()
   parallels = np.arange(0.,90.,10.)
   m.drawparallels(parallels,labels=[1,1,0,0],fontsize=10)
   meridians = np.arange(180.,360.,10.)
   m.drawmeridians(meridians,labels=[0,0,0,1],fontsize=10)


   if level == '250' or level == '300':
      clevs = [50,60,70,80,90,100]
      tlevs = [50,60,70,80,90]
      colorlist = ['steelblue','white','mediumblue','white','mediumpurple']
    # colorlist = ['skyblue','dodgerblue','lightpink','hotpink','fuchsia']
      fill = m.contourf(lons,lats,upper_isotachs,clevs,colors=colorlist,extend='max',latlon=True)

      cint = np.arange(720,1200,12)
      contours = m.contour(lons,lats,upper_hghts,cint,colors='k',linewidths=1.5,latlon=True)
      ax.clabel(contours,cint,colors='k',inline=1,fmt='%.0f',fontsize=10)

      plt_Ls(m,upper_hghts,lons,lats,ax,mode='reflect',window=HLwindow)

      cbar = plt.colorbar(fill,ax=ax,ticks=tlevs,orientation='horizontal',pad=0.04,shrink=0.5,aspect=15)
      cbar.ax.tick_params(labelsize=10)
      cbar.set_label('m $\mathregular{s^{-1}}$')


   elif level == '500':
      clevs1 = [30,40,50,60,70,80]
      tlevs1 = [30,40,50,60,70]
      colorlist1 = ['skyblue','white','steelblue','white','mediumblue']
    # colorlist1 = ['lightsteelblue','skyblue','deepskyblue','dodgerblue','lightpink']
      fill1 = m.contourf(lons,lats,isotach_400,clevs1,colors=colorlist1,extend='max',latlon=True)

      clevs2 = [16,20,24,28,32]
      tlevs2 = [16,20,24,28]
      colorlist2 = ['yellow','orange','brown','red']
    # colorlist2 = ['yellow','orange','darkorange','red']
      fill2 = m.contourf(lons,lats,vort_500,clevs2,colors=colorlist2,extend='max',latlon=True)

      cint = np.arange(498.,651.,6.)
      contours = m.contour(lons,lats,hghts_500,cint,colors='k',linewidths=1.5,latlon=True)
      ax.clabel(contours,cint,colors='k',inline=1,fmt='%.0f',fontsize=10)
      plt_Hs_and_Ls(m,hghts_500,lons,lats,ax,mode='reflect',window=HLwindow)

    # cax1 = fig.add_axes([0.06,0.01,0.3,0.03])
    # cbar1 = plt.colorbar(fill1,cax=cax1,ticks=tlevs1,orientation='horizontal')
    # cbar1.ax.tick_params(labelsize=10)
    # cbar1.set_label('m $\mathregular{s^{-1}}$')

      cbar1 = plt.colorbar(fill1,ax=ax,ticks=tlevs1,orientation='horizontal',pad=0.04,shrink=0.5,aspect=10,anchor=(0.15,1.0))
      cbar1.ax.tick_params(labelsize=10)
      cbar1.set_label('m $\mathregular{s^{-1}}$')

     #cbar2 = plt.colorbar(fill2,ax=ax,ticks=tlevs2,orientation='horizontal',pad=0.04,shrink=0.5,aspect=10,anchor=(0.85,1.0))
      cbar2 = plt.colorbar(fill2,ax=ax,ticks=tlevs2,orientation='horizontal',shrink=0.5,aspect=10,anchor=(0.85,1.0))
      cbar2.ax.tick_params(labelsize=10)
      cbar2.set_label('$\mathregular{10^{-5} s^{-1}}$')


    # cax2 = fig.add_axes([0.56,0.01,0.35,0.03])
    # cbar2 = plt.colorbar(fill2,cax=cax2,ticks=tlevs2,orientation='horizontal')
    # cbar2.ax.tick_params(labelsize=10)
    # cbar2.set_label('$\mathregular{10^{-5} s^{-1}}$')


   elif level == '700':
      clevs = [70,90,100]
      tlevs = [70,90]
      colorlist = ['greenyellow','limegreen']
      fill = m.contourf(lons,lats,rh_700,clevs,latlon=True,colors=colorlist,extend='max')

      cint = np.arange(265.,366.,5.)
      contours = m.contour(lons,lats,hghts_700,cint,colors='k',linewidths=1.5,latlon=True)
      ax.clabel(contours,cint,colors='k',inline=1,fmt='%.0f',fontsize=10)

      cint = np.arange(-50.,1.,5.)
      contours = m.contour(lons,lats,omega_700,cint,colors='orange',linewidths=1,latlon=True)
    # plt.clabel(contours,cint,colors='orange',inline=1,fmt='%.0f',fontsize=9)

      plt_Hs_and_Ls(m,hghts_700,lons,lats,ax,mode='reflect',window=HLwindow)

      cbar = plt.colorbar(fill,ax=ax,ticks=tlevs,orientation='horizontal',pad=0.04,shrink=0.5,aspect=15)
      cbar.ax.tick_params(labelsize=10)
    # cbar.set_label('$\mathregular{\mu}$b $\mathregular{s^{-1}}$')
      cbar.set_label('%')




   elif level == '850':
      clevs = [20,25,30,35,40,45]
      tlevs = [20,25,30,35,40]
      colorlist = ['skyblue','white','steelblue','white','red']
   #  colorlist = ['lightsteelblue','skyblue','dodgerblue','lightpink','fuchsia']
      fill = m.contourf(lons,lats,isotach_850,clevs,latlon=True,colors=colorlist,extend='max')

      cint = np.arange(120.,181.,3.)  # 850 heights
      contours = m.contour(lons,lats,hghts_850,cint,colors='k',linewidths=1.5,latlon=True)
      ax.clabel(contours,cint,colors='k',inline=1,fmt='%.0f',fontsize=10)

      cint = np.arange(-50.,1.,5.)
      contours = m.contour(lons,lats,temp_850,cint,colors='blue',linestyles='dashed',linewidths=1,latlon=True)
      plt.clabel(contours,cint,colors='blue',inline=1,fmt='%.0f',fontsize=9)

      cint = np.arange(5.,51.,5.)
      contours = m.contour(lons,lats,temp_850,cint,colors='red',linestyles='dashed',linewidths=1,latlon=True)
      plt.clabel(contours,cint,colors='red',inline=1,fmt='%.0f',fontsize=9)

      vectors = m.quiver(lons[::skip,::skip],lats[::skip,::skip],uwind_850[::skip,::skip],vwind_850[::skip,::skip],latlon=True,scale=700)

      plt_Hs_and_Ls(m,hghts_850,lons,lats,ax,mode='reflect',window=HLwindow)

      cbar = plt.colorbar(fill,ax=ax,ticks=tlevs,orientation='horizontal',pad=0.04,shrink=0.5,aspect=15)
      cbar.ax.tick_params(labelsize=10)
      cbar.set_label('m $\mathregular{s^{-1}}$')


   elif level == 'sfc':
      cint  = np.arange(900.,1101.,4.)
      contours = m.contour(lons,lats,mslp,cint,colors='k',linewidths=1.5,latlon=True)
      ax.clabel(contours,cint,colors='k',inline=1,fmt='%.0f',fontsize=10)

      cint = np.arange(498.,541.,6.)
      contours = m.contour(lons,lats,thick1000_500,cint,colors='blue',linestyles='dashed',linewidths=1,latlon=True)
      plt.clabel(contours,cint,colors='blue',inline=1,fmt='%.0f',fontsize=9)

      cint = np.arange(546.,601.,6.)
      contours = m.contour(lons,lats,thick1000_500,cint,colors='red',linestyles='dashed',linewidths=1,latlon=True)
      plt.clabel(contours,cint,colors='red',inline=1,fmt='%.0f',fontsize=9)

      plt_Hs_and_Ls(m,mslp,lons,lats,ax,mode='reflect',window=HLwindow)



   valid_str = date_list[j].strftime('%H00 UTC %d %B %Y')
   ax.text(0.5, 0.03, valid_str,  horizontalalignment='center', weight='bold', transform=ax.transAxes, bbox=dict(facecolor='white',alpha=0.85))

   fname = level+'plot_'+YYYYMMDDCC+'.png'
   fname = level+'vol2plot_'+YYYYMMDDCC+'.png'
   plt.savefig(GRAPHX_DIR+'/'+fname,bbox_inches='tight')
   plt.close()



#Loop to plot
for j in range(len(date_list)):
#for j in range(1):

   YYYYMMDDCC = date_list[j].strftime("%Y%m%d%H")

   grbs = pygrib.open(DATA_DIR+'/gfsanl.'+YYYYMMDDCC[0:8]+'.t'+YYYYMMDDCC[8:]+'z.pgrb2.0p25.f000.grib2')

   # Geopotential Heights in decameters
   hghts_250  = grbs.select(name='Geopotential Height',typeOfLevel='isobaricInhPa',level=250)[0].values*0.1
   hghts_300  = grbs.select(name='Geopotential Height',typeOfLevel='isobaricInhPa',level=300)[0].values*0.1
   hghts_500  = grbs.select(name='Geopotential Height',typeOfLevel='isobaricInhPa',level=500)[0].values*0.1
   hghts_700  = grbs.select(name='Geopotential Height',typeOfLevel='isobaricInhPa',level=700)[0].values*0.1
   hghts_850  = grbs.select(name='Geopotential Height',typeOfLevel='isobaricInhPa',level=850)[0].values*0.1
   hghts_1000 = grbs.select(name='Geopotential Height',typeOfLevel='isobaricInhPa',level=1000)[0].values*0.1

   thick1000_500 = hghts_500 - hghts_1000


   # U and V wind components in meters per second
   uwind_250 = grbs.select(name='U component of wind',typeOfLevel='isobaricInhPa',level=250)[0].values
   vwind_250 = grbs.select(name='V component of wind',typeOfLevel='isobaricInhPa',level=250)[0].values
   uwind_300 = grbs.select(name='U component of wind',typeOfLevel='isobaricInhPa',level=300)[0].values
   vwind_300 = grbs.select(name='V component of wind',typeOfLevel='isobaricInhPa',level=300)[0].values
   uwind_400 = grbs.select(name='U component of wind',typeOfLevel='isobaricInhPa',level=400)[0].values
   vwind_400 = grbs.select(name='V component of wind',typeOfLevel='isobaricInhPa',level=400)[0].values
   uwind_850 = grbs.select(name='U component of wind',typeOfLevel='isobaricInhPa',level=850)[0].values
   vwind_850 = grbs.select(name='V component of wind',typeOfLevel='isobaricInhPa',level=850)[0].values

   # Isotachs in meters per second
   isotach_250 = np.sqrt(uwind_250**2+vwind_250**2)
   isotach_300 = np.sqrt(uwind_300**2+vwind_300**2)
   isotach_400 = np.sqrt(uwind_400**2+vwind_400**2)
   isotach_850 = np.sqrt(uwind_850**2+vwind_850**2)


   # Absolute vorticity (x10^5 s-1)
   vort_500 = grbs.select(name='Absolute vorticity',typeOfLevel='isobaricInhPa',level=500)[0].values*1.e5


   # Relative humidity
   rh_700 = grbs.select(name='Relative humidity',typeOfLevel='isobaricInhPa',level=700)[0].values


   # Vertical velocity (1x10^-3 mb/s)
   omega_700 = grbs.select(name='Vertical velocity',typeOfLevel='isobaricInhPa',level=700)[0].values*10.
   print omega_700.min(), omega_700.max()


   # Temperature in Celsius
   temp_850 = grbs.select(name='Temperature',typeOfLevel='isobaricInhPa',level=850)[0].values-273.15


   # MSLP in mb
   try:
      grb = grbs.select(name='MSLP (Eta model reduction)')[0]
   except ValueError:
      MSLET = None  # MSLET does not exist in file so plot PRMSL 
      try:
         grb = grbs.select(name='Pressure reduced to MSL')[0]
      except:
         grb = grbs.select(name='Mean sea level pressure')[0]
   # will also need to handle PRMSL/MSLET smoothing differently

   mslp = grb.values*0.01
   lats, lons = grb.latlons()
   grbs.close()


   hghts_250 = scipy.ndimage.gaussian_filter(hghts_250,2)
   isotach_250 = scipy.ndimage.gaussian_filter(isotach_250,2)

   hghts_300 = scipy.ndimage.gaussian_filter(hghts_300,2)
   isotach_300 = scipy.ndimage.gaussian_filter(isotach_300,2)

   hghts_500 = scipy.ndimage.gaussian_filter(hghts_500,2)
   isotach_400 = scipy.ndimage.gaussian_filter(isotach_400,2)
   vort_500 = scipy.ndimage.gaussian_filter(vort_500,2)

   hghts_700 = scipy.ndimage.gaussian_filter(hghts_700,2)
   omega_700 = scipy.ndimage.gaussian_filter(omega_700,2)
   rh_700 = scipy.ndimage.gaussian_filter(rh_700,2)

   hghts_850 = scipy.ndimage.gaussian_filter(hghts_850,2)
   isotach_850 = scipy.ndimage.gaussian_filter(isotach_850,2)
   uwind_850 = scipy.ndimage.gaussian_filter(uwind_850,2)
   vwind_850 = scipy.ndimage.gaussian_filter(vwind_850,2)
   temp_850 = scipy.ndimage.gaussian_filter(temp_850,2)

   mslp = scipy.ndimage.gaussian_filter(mslp,2)
   thick1000_500 = scipy.ndimage.gaussian_filter(thick1000_500,2)


   main()

