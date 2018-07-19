#!/usr/bin/env python

## script uses pyshp library. This is located '/home/547/mcg547/dg9-apps/modules'. To enable running, it may need to be added to your local python library path (run 'python setup.py install --user')


# create_S1_shapefiles: For each month, this script creates a set of polygons
#                       for all the Sentinel 1 SLC images acquired over      
#                       GA's area of interest. Only works for SM and IW mode data.                               
#
#                       It uses the KML data to create the polygon extent. 
#                       The polygon attribute data is acquired from the 
#                       image's xml metadata.      
#
# input:  [zip_list]    List of zip files for a particular month 
#                          - the zip list is created by running 'create_S1_zipfile_list.bash'
#
# Usage: create_S1_SLC_shapefile.py [zip_list]


## Load NCI Modules and Import Required Python Libraries
import os
import sys
from xml.dom.minidom import parseString
from decimal import *
import shutil
import zipfile
import shapefile # pyshp library 

zip_list = sys.argv[1]


## Setup Directories
proj_dir = os.getcwd()
sar_dir = "/g/data1/fj7/Copernicus/Sentinel-1/C-SAR/SLC"
temp_dir = os.path.join(proj_dir, "temp")
shape_dir = os.path.join(proj_dir, "shapefiles")

os.chdir(proj_dir)

if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)
if not os.path.exists(shape_dir):
    os.makedirs(shape_dir)

## Output Shapefile
list1 = zip_list.split('_')
mode1 = list1[1]
mode2 = list(mode1)[0]
if mode2 == "S":
    mode = "SM"
elif mode2 == "I": 
    mode = "IW"
yr_mth = list1[3]
list2 = yr_mth.split('-')
yr = list2[0]
shape_file = "%s_%s_S1_SLC.shp" %(yr_mth,mode)
prj_file = "%s_%s_S1_SLC" %(yr_mth,mode)


###----------------FUNCTIONS----------------###

class s1_shapefile:
   "Create polygon shapefile and geotif for Sentinel-1 SLC data"

   def __init__(self, grid, filename):
       self.grid_dir = grid
       self.zip_file = filename

   def zip_details(self):
       # insert zip details top of NCI .e file
       params = "echo "" 1>&2"
       os.system(params)
       params = "echo "" 1>&2"
       os.system(params)
       params = "echo PROCESSING: %s 1>&2" %(zip_file)
       os.system(params)
       params = "echo "" 1>&2"
       os.system(params)  
       # insert zip details top of NCI .o file
       params = "echo """
       os.system(params)
       params = "echo """
       os.system(params)
       params = "echo PROCESSING: %s" %(zip_file)
       os.system(params)
       params = "echo """
       os.system(params)

   def filenames(self):
      self.base = os.path.splitext(zip_file)[0]
      self.zip_split = self.base.split('_')
      self.zip_dir = self.base + ".SAFE"
  
   def extract_zip(self):
      self.zip_loc1 = os.path.join(sar_dir, yr, yr_mth, self.grid_dir, self.zip_file)
      self.zip_loc = self.zip_loc1.strip()
      self.temp_loc1 = os.path.join(temp_dir, zip_file)
      self.temp_loc = self.temp_loc1.strip()
      shutil.copyfile(self.zip_loc, self.temp_loc)
      self.preview_dir = os.path.join(self.zip_dir, 'preview')
      self.anno_dir = os.path.join(self.zip_dir, 'annotation')

      with zipfile.ZipFile(zip_file) as z:
          for member in z.namelist():
              filename = os.path.basename(member)
              dirname = os.path.dirname(member)
              # skip files not in directories
              if not dirname:
                  continue

               # make relevant directories for unzipped files
              if dirname == self.preview_dir or dirname == self.anno_dir:
                  if not os.path.exists(self.preview_dir):
                      os.makedirs(self.preview_dir)
                  if not os.path.exists(self.anno_dir):
                      os.makedirs(self.anno_dir)
                  # extract files
                  z.extract(member)
      os.remove(zip_file)

   def sorted_xml_list(self):
       os.chdir(self.anno_dir)
       top = os.getcwd()
       with open("temp1", "w") as a:
           for path, subdirs, files in os.walk(top):
               for file in files:
                   if file.endswith('.xml'):
                       a.write(str(file) + os.linesep) 
       with open("temp1", "r") as b:
           sorted_list = sorted(b, key=lambda x: x.split("-", 9)[-1])
       with open("xml_list", "w") as c:
           c.writelines(sorted_list)
       os.remove("temp1")

   def mode_beam(self):
       x=open("xml_list")
       self.lines=x.readlines()
       xml = self.lines[0]
       xml = xml.strip()
       file = open(xml)
       data = file.read()
       file.close()
       self.dom = parseString(data)
       for d in self.dom.getElementsByTagName('mode'):
           self.mode_beam1 = d.firstChild.data
           mode_beam2 = self.mode_beam1[0]
           self.mode_beam = mode_beam2.strip()
  
   def polarisation(self):
       self.count = 0
       with open("xml_list") as f:
           for line in f:
               if line.strip():
                   self.count += 1
       if self.mode_beam == "S" and self.count == 1: # single polarisation
           x=open("xml_list")
           self.lines=x.readlines()
           xml = self.lines[0]
           xml = xml.strip()
           file = open(xml)
           data = file.read()
           file.close()
           self.dom = parseString(data)
           for d in self.dom.getElementsByTagName('polarisation'):
               self.polar = d.firstChild.data
       elif self.mode_beam == "S" and self.count == 2: # dual polarisation
           x=open("xml_list")
           self.lines=x.readlines()
           xml1 = self.lines[0]
           xml1 = xml1.strip()
           file1 = open(xml1)
           data1 = file1.read()
           file1.close()
           self.dom1 = parseString(data1)
           xml2 = self.lines[1]
           xml2 = xml2.strip()
           file2 = open(xml2)
           data2 = file2.read()
           file2.close()
           self.dom2 = parseString(data2)
           for d in self.dom1.getElementsByTagName('polarisation'):
               polar1 = d.firstChild.data
           for d in self.dom2.getElementsByTagName('polarisation'):
               polar2 = d.firstChild.data
           self.polar = polar1 + "-" + polar2
       elif self.mode_beam == "I" and self.count == 3: # single polarisation
           x=open("xml_list")
           self.lines=x.readlines()
           xml = self.lines[0]
           xml = xml.strip()
           file = open(xml)
           data = file.read()
           file.close()
           self.dom = parseString(data)
           for d in self.dom.getElementsByTagName('polarisation'):
               self.polar = d.firstChild.data
       elif self.mode_beam == "I" and self.count == 6: # dual polarisation
           x=open("xml_list")
           self.lines=x.readlines()
           xml1 = self.lines[0]
           xml1 = xml1.strip()
           file1 = open(xml1)
           data1 = file1.read()
           file1.close()
           self.dom1 = parseString(data1)
           xml2 = self.lines[3]
           xml2 = xml2.strip()
           file2 = open(xml2)
           data2 = file2.read()
           file2.close()
           self.dom2 = parseString(data2)
           for d in self.dom1.getElementsByTagName('polarisation'):
               polar1 = d.firstChild.data
           for d in self.dom2.getElementsByTagName('polarisation'):
               polar2 = d.firstChild.data
           self.polar = polar1 + "-" + polar2

   def mission(self):
       x=open("xml_list")
       self.lines=x.readlines()
       xml = self.lines[0]
       xml = xml.strip()
       file = open(xml)
       data = file.read()
       file.close()
       self.dom = parseString(data)
       for d in self.dom.getElementsByTagName('missionId'):
           self.mission = d.firstChild.data

   def product_type(self):
       x=open("xml_list")
       self.lines=x.readlines()
       xml = self.lines[0]
       xml = xml.strip()
       file = open(xml)
       data = file.read()
       file.close()
       self.dom = parseString(data)
       for d in self.dom.getElementsByTagName('productType'):
           self.product_type = d.firstChild.data

   def date(self):
       date1 = self.zip_split[6]
       date2 = date1.split('T')
       self.date = date2[0]

   def orientation(self):
       x=open("xml_list")
       self.lines=x.readlines()
       xml = self.lines[0]
       xml = xml.strip()
       file = open(xml)
       data = file.read()
       file.close()
       self.dom = parseString(data)
       for d in self.dom.getElementsByTagName('pass'):
           self.orient = d.firstChild.data

   def absolute_orbit(self):
       x=open("xml_list")
       self.lines=x.readlines()
       xml = self.lines[0]
       xml = xml.strip()
       file = open(xml)
       data = file.read()
       file.close()
       self.dom = parseString(data)
       for d in self.dom.getElementsByTagName('absoluteOrbitNumber'):
           self.absolute_orbit = d.firstChild.data

   def relative_orbit(self): #formula: mod (absolute_orbit - 73, 175) + 1 )
       rel1 = int(self.absolute_orbit) - 73
       rel2 = rel1 % 175
       self.relative_orbit = rel2 + 1 

   def frame(self): # temporary frame number, finalise later if a number can be assigned to a stack of scenes that cover the same area
       self.frame = "001"       

   def unique_product_id(self):
       self.unique_product_id = self.zip_split[9]

   def datatake_id(self):
       x=open("xml_list")
       self.lines=x.readlines()
       xml = self.lines[0]
       xml = xml.strip()
       file = open(xml)
       data = file.read()
       file.close()
       self.dom = parseString(data)
       for d in self.dom.getElementsByTagName('missionDataTakeId'):
           self.datatake_id = d.firstChild.data

   def resolution_class(self):
       resolution_class1 = self.zip_split[3]
       if not resolution_class1:
           self.resolution_class = "-"
       elif resolution_class1 == "F":
           self.resolution_class = "Full"
       elif resolution_class1 == "H":
           self.resolution_class = "High"
       elif resolution_class1 == "M":
           self.resolution_class = "Medium"

   def processing_level(self):
       processing_level1 = self.zip_split[4]
       processing_level2 = processing_level1[0]
       self.processing_level = processing_level2.strip()

   def product_class(self):  
       product_class1 = self.zip_split[4]
       product_class2 = product_class1[1]
       product_class3 = product_class2.strip()
       if product_class3 == "S":
           self.product_class = "Standard"
       elif product_class3 == "A":
           self.product_class = "Annotation"

   def start_stop_times(self):
       if self.mode_beam == "S":
           x=open("xml_list")
           self.lines=x.readlines()
           xml = self.lines[0]
           xml = xml.strip()
           file = open(xml)
           data = file.read()
           file.close()
           self.dom = parseString(data)
           for d in self.dom.getElementsByTagName('startTime'):
               start1 = d.firstChild.data
               start2 = start1.split('T')
               self.start_time = start2[1] 
           for d in self.dom.getElementsByTagName('stopTime'):
               stop1 = d.firstChild.data
               stop2 = stop1.split('T')
               self.stop_time = stop2[1]
       elif self.mode_beam == "I": 
           x=open("xml_list")
           self.lines=x.readlines()
           xml1 = self.lines[0]
           xml1 = xml1.strip()
           file1 = open(xml1)
           data1 = file1.read()
           file1.close()
           self.dom1 = parseString(data1)
           xml2 = self.lines[2]
           xml2 = xml2.strip()
           file2 = open(xml2)
           data2 = file2.read()
           file2.close()
           self.dom2 = parseString(data2)
           for d in self.dom1.getElementsByTagName('startTime'):
               start1 = d.firstChild.data
               start2 = start1.split('T')
               self.start_time = start2[1] 
           for d in self.dom2.getElementsByTagName('stopTime'):
               stop1 = d.firstChild.data
               stop2 = stop1.split('T')
               self.stop_time = stop2[1]
 
   def kml_coords(self): 
       preview_dir2 = os.path.join(temp_dir, self.preview_dir)
       os.chdir(preview_dir2)
       file = open("map-overlay.kml")
       data = file.read()
       file.close()
       dom = parseString(data)
       for d in dom.getElementsByTagName('coordinates'):
           coord_val = d.firstChild.data
       coords = coord_val.split()
       ul = coords[0]
       ul2 = ul.split(',')
       ul_lon = ul2[0]
       ul_lat = ul2[1]
       self.ul_lon1 = float(ul_lon)
       self.ul_lat = float(ul_lat)
       ur = coords[1]
       ur2 = ur.split(',')
       ur_lon = ur2[0]
       ur_lat = ur2[1]
       self.ur_lon1 = float(ur_lon)
       self.ur_lat = float(ur_lat)
       lr = coords[2]
       lr2 = lr.split(',')
       lr_lon = lr2[0]
       lr_lat = lr2[1]
       self.lr_lon1 = float(lr_lon)
       self.lr_lat = float(lr_lat)
       ll = coords[3]
       ll2 = ll.split(',')
       ll_lon = ll2[0]
       ll_lat = ll2[1]
       self.ll_lon1 = float(ll_lon)
       self.ll_lat = float(ll_lat)

   def fix_lon_coords(self):
       # fix lon coordinates if over 180 longitude, so polygons plot in ArcGIS properly
       ul_lon1 = self.ul_lon1
       ll_lon1 = self.ll_lon1
       ur_lon1 = self.ur_lon1
       lr_lon1 = self.lr_lon1
       if self.orient == 'Ascending':
          if ul_lon1 > 0 and ll_lon1 > 0 and ur_lon1 < 0 and lr_lon1 < 0: # left and right split by line
             self.ul_lon = ul_lon1 - 360
             self.ll_lon = ll_lon1 - 360
             self.ur_lon = ur_lon1
             self.lr_lon = lr_lon1
          elif ul_lon1 > 0 and ur_lon1 > 0 and lr_lon1 < 0 and ll_lon1 < 0: # upper and lower split by line
             self.ul_lon = ul_lon1
             self.ur_lon = ur_lon1
             self.ll_lon = ll_lon1 + 360
             self.lr_lon = lr_lon1 + 360
          elif ul_lon1 > 0 and ll_lon1 < 0 and ur_lon1 < 0 and lr_lon1 < 0: # UL corner cut, rest on other side of line
             self.ul_lon = ul_lon1 - 360
             self.ll_lon = ll_lon1
             self.ur_lon = ur_lon1
             self.lr_lon = lr_lon1
          elif ul_lon1 > 0 and ll_lon1 > 0 and ur_lon1 > 0 and lr_lon1 < 0: # LR corner cut, rest on other side of line
             self.ul_lon = ul_lon1
             self.ll_lon = ll_lon1
             self.ur_lon = ur_lon1
             self.lr_lon = lr_lon1 + 360 
          else:
             self.ul_lon = ul_lon1
             self.ll_lon = ll_lon1
             self.ur_lon = ur_lon1
             self.lr_lon = lr_lon1       
       elif self.orient == 'Descending':
          if ur_lon1 > 0 and lr_lon1 > 0 and ul_lon1 < 0 and ll_lon1 < 0: # left and right split by line
             self.ur_lon = ur_lon1 - 360
             self.lr_lon = lr_lon1 - 360
             self.ul_lon = ul_lon1
             self.ll_lon = ll_lon1
          elif ul_lon1 < 0 and ur_lon1 < 0 and lr_lon1 > 0 and ll_lon1 > 0: # upper and lower split by line
             self.ul_lon = ul_lon1 + 360
             self.ur_lon = ur_lon1 + 360
             self.ll_lon = ll_lon1
             self.lr_lon = lr_lon1
          elif ul_lon1 > 0 and ur_lon1 > 0 and lr_lon1 < 0 and ll_lon1 < 0: # upper and lower split by line
             self.ul_lon = ul_lon1
             self.ur_lon = ur_lon1
             self.ll_lon = ll_lon1 + 360
             self.lr_lon = lr_lon1 + 360
          elif ul_lon1 > 0 and ll_lon1 < 0 and ur_lon1 < 0 and lr_lon1 < 0: # UL corner cut, rest on other side of line
             self.ul_lon = ul_lon1 - 360
             self.ll_lon = ll_lon1
             self.ur_lon = ur_lon1
             self.lr_lon = lr_lon1 
          elif ul_lon1 > 0 and ll_lon1 > 0 and ur_lon1 > 0 and lr_lon1 < 0: # LR corner cut, rest on other side of line
             self.ul_lon = ul_lon1
             self.ll_lon = ll_lon1
             self.ur_lon = ur_lon1
             self.lr_lon = lr_lon1 + 360 
          elif ul_lon1 > 0 and ll_lon1 < 0 and ur_lon1 > 0 and lr_lon1 > 0: # LL corner cut, rest on other side of line
             self.ul_lon = ul_lon1
             self.ll_lon = ll_lon1 + 360
             self.ur_lon = ur_lon1
             self.lr_lon = lr_lon1 
          else:
             self.ul_lon = ul_lon1
             self.ll_lon = ll_lon1
             self.ur_lon = ur_lon1
             self.lr_lon = lr_lon1 

   def kml_centre_coords(self):
       if self.orient == 'Ascending':
           #longitude (UL & LR)
           xcen1 = Decimal(self.ul_lon) - Decimal(self.lr_lon)
           xcen2 = Decimal(xcen1) / 2
           cen_lon = Decimal(self.lr_lon) + Decimal(xcen2)
           self.cen_lon = '%.6f'%(cen_lon)
           #latitude  (UR & LL)
           ycen1 = Decimal(self.ll_lat) - Decimal(self.ur_lat)
           ycen2 = Decimal(ycen1) / 2
           cen_lat = Decimal(self.ur_lat) + Decimal(ycen2)
           self.cen_lat = '%.6f'%(cen_lat)
       elif self.orient == 'Descending':
           #longitude (LL & UR)
           xcen1 = Decimal(self.ll_lon) - Decimal(self.ur_lon)
           xcen2 = Decimal(xcen1) / 2
           cen_lon = Decimal(self.ur_lon) + Decimal(xcen2)
           self.cen_lon = '%.6f'%(cen_lon)
           #latitude (UL & LR)
           ycen1 = Decimal(self.ul_lat) - Decimal(self.lr_lat)
           ycen2 = Decimal(ycen1) / 2
           cen_lat = Decimal(self.lr_lat) + Decimal(ycen2)
           self.cen_lat = '%.6f'%(cen_lat)
       else:
           pass

   def create_polygon_attributes(self):
       os.chdir(shape_dir)
       shape = "polygon"
       self.Mission1 = self.mission
       self.ModeBeam1 = self.mode_beam1
       self.ProductTyp1 = self.product_type
       self.Date1 = self.date
       self.Pass1 = self.orient
       self.Polar1 = self.polar
       self.AbOrbit1 = self.absolute_orbit
       self.RelOrbit1 = self.relative_orbit
       self.Frame1 = self.frame
       self.UniqProdID1 = self.unique_product_id
       self.DatatakeID1 = self.datatake_id
       self.ResClass1 = self.resolution_class
       self.ProcLevel1 = self.processing_level
       self.ProdClass1 = self.product_class
       self.StartTime1 = self.start_time
       self.StopTime1 = self.stop_time
       self.CenLon1 = self.cen_lon
       self.CenLat1 = self.cen_lat
       self.UL_Lon1 = self.ul_lon
       self.UL_Lat1 = self.ul_lat
       self.UR_Lon1 = self.ur_lon
       self.UR_Lat1 = self.ur_lat
       self.LR_Lon1 = self.lr_lon
       self.LR_Lat1 = self.lr_lat
       self.LL_Lon1 = self.ll_lon
       self.LL_Lat1 = self.ll_lat
       self.GridDir1 = self.grid_dir
       self.ZipFile1 = self.zip_file
       self.parts = [[[self.UL_Lon1, self.UL_Lat1], [self.UR_Lon1, self.UR_Lat1], [self.LR_Lon1, self.LR_Lat1], [self.LL_Lon1, self.LL_Lat1]]]

   def write_shapefile(self):
       w = shapefile.Writer(shapefile.POLYGON)
       w.autoBalance = 1 
       w.poly(parts=self.parts)
       w.field('Mission','C',3)
       w.field('ModeBeam','C',2) 
       w.field('ProductTyp','C',3) 
       w.field('Date','N',8) 
       w.field('Pass','C',12) 
       w.field('Polar','C',6) 
       w.field('AbOrbit','N',10) 
       w.field('RelOrbit','N',4) 
       w.field('Frame','N',4) 
       w.field('UniqProdID','C',8) 
       w.field('DatatakeID','N',8) 
       w.field('ResClass','C',2) 
       w.field('ProcLevel','N',2) 
       w.field('ProdClass','C',12) 
       w.field('StartTime','C',10)
       w.field('StopTime','C',10) 
       w.field('CenLon','N',14,8)
       w.field('CenLat','N',14,8)
       w.field('UL_Lon','N',14,8)
       w.field('UL_Lat','N',14,8)
       w.field('UR_Lon','N',14,8)
       w.field('UR_Lat','N',14,8)
       w.field('LR_Lon','N',14,8)
       w.field('LR_Lat','N',14,8)
       w.field('LL_Lon','N',14,8)
       w.field('LL_Lat','N',14,8)
       w.field('GridDir','C',20)
       w.field('ZipFile','C',80)
       w.record(self.Mission1,self.ModeBeam1,self.ProductTyp1,self.Date1,self.Pass1,self.Polar1,self.AbOrbit1,self.RelOrbit1,self.Frame1,self.UniqProdID1,self.DatatakeID1,self.ResClass1,self.ProcLevel1,self.ProdClass1,self.StartTime1,self.StopTime1,self.CenLon1,self.CenLat1,self.UL_Lon1,self.UL_Lat1,self.UR_Lon1,self.UR_Lat1,self.LR_Lon1,self.LR_Lat1,self.LL_Lon1,self.LL_Lat1,self.GridDir1,self.ZipFile1)
       w.save(shape_file)
       # create projection file
       prj = open("%s.prj" % prj_file, "w") 
       epsg = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]' 
       prj.write(epsg) 
       prj.close()
       os.chdir(temp_dir)
       shutil.rmtree(self.zip_dir)
       os.chdir(proj_dir)

   def append_shapefile(self):
       w = shapefile.Editor(shape_file)
       w.poly(parts=self.parts)
       w.record(self.Mission1,self.ModeBeam1,self.ProductTyp1,self.Date1,self.Pass1,self.Polar1,self.AbOrbit1,self.RelOrbit1,self.Frame1,self.UniqProdID1,self.DatatakeID1,self.ResClass1,self.ProcLevel1,self.ProdClass1,self.StartTime1,self.StopTime1,self.CenLon1,self.CenLat1,self.UL_Lon1,self.UL_Lat1,self.UR_Lon1,self.UR_Lat1,self.LR_Lon1,self.LR_Lat1,self.LL_Lon1,self.LL_Lat1,self.GridDir1,self.ZipFile1)
       w.save(shape_file)
       w = None
       os.chdir(temp_dir)
       shutil.rmtree(self.zip_dir)
       os.chdir(proj_dir)



###----------------LOOP OVER ZIP FILE LIST----------------###


## Loop over each zip file to create shapefile and geotiff image 
with open(zip_list) as file_list:
   for index, f in enumerate(file_list):
      temp = f.split(' ')
      grid_dir1 = temp[1]
      grid_dir = grid_dir1.strip()
      zip_file1 = temp[2]
      zip_file = zip_file1.strip()
      if index == 0: # create shapefile with first iteration
          
          os.chdir(temp_dir)

          ## Setup Files
          obj = s1_shapefile(grid_dir,zip_file)
          obj.zip_details()
          obj.filenames()
          obj.extract_zip()
        
          ## Determine Variables
          obj.sorted_xml_list()
          obj.mode_beam()
          obj.polarisation()
          obj.mission()
          obj.product_type()
          obj.date()
          obj.orientation()
          obj.absolute_orbit()
          obj.relative_orbit()
          obj.frame()
          obj.unique_product_id()
          obj.datatake_id()
          obj.resolution_class()
          obj.processing_level()
          obj.product_class()
          obj.start_stop_times()
          
          ## Extract KML information
          obj.kml_coords()
          obj.fix_lon_coords()
          obj.kml_centre_coords()
        
          ## Create Polygon Shapefile
          obj.create_polygon_attributes()
          obj.write_shapefile()
        
      else: # append to shapefile with subsequent iterations
          os.chdir(temp_dir)

          ## Setup Files
          obj = s1_shapefile(grid_dir,zip_file)
          obj.zip_details()
          obj.filenames()
          obj.extract_zip()
          
          ## Determine Variables
          obj.sorted_xml_list()
          obj.mode_beam()
          obj.polarisation()
          obj.mission()
          obj.product_type()
          obj.date()
          obj.orientation()
          obj.absolute_orbit()
          obj.relative_orbit()
          obj.frame()
          obj.unique_product_id()
          obj.datatake_id()
          obj.resolution_class()
          obj.processing_level()
          obj.product_class()
          obj.start_stop_times()
          
          ## Extract KML information
          obj.kml_coords()
          obj.fix_lon_coords()
          obj.kml_centre_coords()

          ## Append Polygon Shapefile
          obj.create_polygon_attributes()
          obj.append_shapefile()

