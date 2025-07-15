#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# This script is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) [2022] [Javier Galán] [www.javiergalanrico.com/]
#

#
#
# 0		1		2         3
# gop.py <fileforlisten> <outputdir> [hexbytes]
#
# glitch operator 0.01
#
# This script watches a .blend file and triggers and enques a datamoshing job each time is saved
# by performing this operations:
#	
#	·A animation render from the timeline is rendered
#	·Everything is packed in mp4/.h264 with ffmpeg
#	·The resulting video is corrupted using DataMosher.Py (mandatory!)
#	·An mplayer instance pop ups the glitched video 
# 
#
#
#
import subprocess
from subprocess import Popen
import sys
import time
import os
import threading
import random
from getkey import getkey, keys #<--- Utilitzar això en comptes de keyboard, aquesta no funciona bé!!!

#Imprimir amb ANSI codes, tret de https://www.geeksforgeeks.org/print-colors-python-terminal/
def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))
def prYellow(skk): print("\033[93m {}\033[00m" .format(skk))
def prCyan(skk): print("\033[96m {}\033[00m" .format(skk))


def PrintCoolTitle() :

	print("\n")                                                                                            
	prYellow("   'xKNWWWNKd   :kXNWWWNO:  .WWWWWWWXk.     ")
	prYellow("  .MMX....MMM. lMMx...xMMN  oMMd...KMM;        ")
	prYellow("  xMM:   .ooc  NMM.   KMM:  NMM.   WMW                      .XNX.   cXXl     ")
	prYellow("  WMW         ;MMO   'MMX  ,MMWooo0MW:          dXXKKXXKk'   .NMX '0M0'  ")
	prYellow(" cMMx dxxxxo  OMM,   xMMc  OMMxoool;.           WMW;..dMMO    'WMXMNc  ")
	prYellow(" XMM. ;;KMMl .MMX   .WMW  .MMX                 lMMd   OMM,     dMMO  ")
	prYellow(",MMN...;WMN  dMMk...xMMo  xMMc         ;XWN:'  NMM.  .MMX      XMM.   ")
	prYellow(" xXNNNNX0d.  .OXNNNNXk:   XNN         .lMMKc  ,MMN...kMMc     .NN0    ")
	prYellow("		                         ....   OMMXWWWXO:       ")
	prYellow("		                               .MMN       ")
	prYellow("		                               :KKc        ")
				                                                         
				                                                         

# Settings....
Blender = "/home/javi/Blender/blender-3.0.1-linux-x64/blender"
DataMosher = "/home/javi/Scripts/DataMosher.Py"
DataMosherBytes = 66 #Podria arribar a plantejar-se random fins i tot


# Internal
CueJobs = []
fc_lapse = 0.5 # Lapse de temps per revisar canvis en f
gop_size = 3000 # Donen un interval elevat per inserir keyframes i trencar mes facilmente el video.

#Variables d'estat
Status = True 		# True representa el programa corrent i False el programa en pause
SkipRender = False 	# <--No s'utilitza de moment. True representa que l'usuari vol abortar render, False que no s'ha emprès cap acció

global RenderPr



PrintCoolTitle()

prCyan("G L I T CH__ O_PE__RA_T_O__R  " ) # † , buscar codi tipus  \xf9
print("GOP.py")

def PrintUse() :

	print("gop.py <file-for-listen> <outputdir> [hexbytes]")
	print("Use <file-for-listen> in order to watch a .blend file and <outputdir> to ")
	print("specify the working folder where the results will keep stored.")
	print("<hexbytes> specifies the quantity of bytes to corrupt: 78 for example or an interval between 23-93 can generate a random value in this thresold.")
	print("")


                                   


if len(sys.argv) == 3 or len(sys.argv) == 4 :

	f = sys.argv[1]		#.blend
	wd = sys.argv[2]	#directori base per treballar i guardar resultats
	
	#Posem o no el backlash si escau, per no crear 
	#el directori erroniament
	if os.path.dirname(f) == "":
		wd =  os.path.dirname(f)  + wd #
	else:
		wd =  os.path.dirname(f) + "/" + wd #
		
	#Mirem si s'ha emprat el paràmetre opcional [hexbytes]
	try:
		sys.argv[3]
	except:
		pass
	else:
		#D'aquesta forma fiquem tant si l'usuari ha indicat un nombre sencer
		#o bé l'interval. En aquest ultim cas es crea un tuple de dos registres.
		
		hexbytes = sys.argv[3].split("-")
	
else:
	print("Incorrect number of arguments")
	PrintUse()
	sys.exit()

print (">>Creating working dir at " + wd )

try:
	os.mkdir(wd)
except:

	if os.path.exists(wd) :
		
		print("This folder already exists, we going on..\n" )
		
	else:
	
		print("Error: The working dir cannot be created")	
		sys.exit()
else:
	print("Ok.")


prGreen("Listening the file  '" + f + "', waiting the upcoming save action (ctrl + s)")
print(" Press [SPACE] per pause/continue listening.")
print(" Pres [ESC] for render Skip>>.")


def ShowPendingJobs():

	if len(CueJobs) > 0:
	
		print ( "Pending tasks..." + str(CueJobs))
		sys.stdout.flush()
	
	elif len(CueJobs) == 0:
		print("There are no jobs reamaining :)")
		sys.stdout.flush()
		
def Execute(ts):

	global DataMosherBytes, RenderPr
	#ts indica el timestamp de la feina pendent
	#ja que cada task es guardarà al seu propi directori
	

	print("Processing #" + str(ts))
	
	print("[1# Creating folders...]--->", end="")
	sys.stdout.flush()
	
	td = wd + "/" + str(ts) #Task Dir, directori individual per cada feina
	
	try:
		os.mkdir(td)
	except:
		pass
	else:
		rd = td + "/render/"
		os.mkdir(rd)  #Creem el directori on guardarem el render

		RenderCmd = [Blender, "-b", f, "-o", rd , "-a"]
		
		print("[2# Launching render....", end=" ")
		sys.stdout.flush() #<----Important!!! per a que Popen NO bloqueji la surtida del print!!
		

		RenderPr = Popen(RenderCmd, shell = False , stdout=subprocess.DEVNULL) # 
		RenderPr.wait()
		
		RenderPr.communicate()
		if RenderPr.returncode == 0 : 		#S'ha terminat el render adientment
			print ("OK]--->", end="")
			sys.stdout.flush()
		
		else:
			print ("Skip >> ]--->" , end="") #S'ha terminat el render per interacció de l usuario
			sys.stdout.flush()

		#Nombre total de frames a rd
		Frames = len(os.listdir(rd))
		
		#Si el directori està buit, surtim, ja que no hi 
		#ha res mes que fer aquí
		
		if Frames == 0:
			print (" [Empty folder,finishing task]")
			print("#" + str(ts) + " finished")
			sys.stdout.flush()
			return()
			
		else: 
			#Si hi ha algun frame, deixem preparat el primer frame per pasar-li al encoder.
			#en cas de no indicar-li quan ffmpeg trobi un interval diferent a 0001-00xx ens fotra un error
			#es a dir, un interval tipus 0034-0099
			
			#Es MOLT important afegir sorted, per ordenar numericament els frames en el tuple obtingut.
			#i realitzar a posteriori adientment la compressió.
			
			startFrame = sorted(os.listdir(rd))[0].split(".")[0]
			
			
		print("[3# Compressing " + str(Frames) + " frames into a video:", end="")
		sys.stdout.flush()

		
		#Evaluem quantitat de frames , 
		#per donar-li loop a la fase d'encoding
		
		if Frames  < 25  : streamLoop_opt = 10
		elif Frames >= 25 and Frames < 100 : streamLoop_opt = 5
		elif Frames >= 100 : streamLoop_opt = 2
		
		Frames_suffix = startFrame + "-" + str(int(startFrame) + int(Frames))
		
		print("looping " + str(streamLoop_opt) + " times(" + Frames_suffix + ") ", end="")	
		sys.stdout.flush()
		
		

		Video_out = td + "/" + Frames_suffix + ".mp4"
		
		FFmpegCmd = [	"ffmpeg" ,
				"-stream_loop", str(streamLoop_opt),
				"-loglevel", "-8",
				"-framerate", "24",
				"-start_number", startFrame,
				"-i", rd + "/%4d.png",
				"-b", "4000k", 
				"-g", str(gop_size),
				"-minrate", "4000k",
				"-maxrate", "4000k",
				 "-c:v", "libx264", 
				 "-r", "24", 
				 Video_out 
				]
				
		FFmpegPr = Popen(FFmpegCmd, shell= False, stdout=subprocess.DEVNULL)
		FFmpegPr.wait()
		
		FFmpegPr.communicate()
		if FFmpegPr.returncode == 0 : 
			print ("OK]--->", end="")
		else:	
			print("...unable to compress video. Finishing task ]") 
			print("#" + str(ts) + " finished")
			return()
		
		print("[4# DataMosher.Py....", end="")
		sys.stdout.flush()
		
		#En cas d'haver indicat hexbytes (int o interval) 
		#a la línea de comanda, farem override o no
		#a la variable per defecte DataMosherBytes
		#per indicar el valor triat per l'usuari.
		
		try:
			hexbytes
		except:
			pass
		else:
			if len(hexbytes) == 1:
				DataMosherBytes = hexbytes[0]
				print("Hexbytes override: " + str(hexbytes[0]) + " ", end="")
				
			elif len(hexbytes) == 2:
			
				DataMosherBytes = random.randint(int(hexbytes[0]), int(hexbytes[1]))
				print("Hexbytes override: " + str(DataMosherBytes) + "rnd(" + str(hexbytes[0]) + "-" + str(hexbytes[1]) + ") ", end="")
				
			sys.stdout.flush()
		
		Video_hex_out = td + "/" + Frames_suffix + "_hex.mp4"
		
		print (str(DataMosherBytes) + " bytes" )
		DataMosherCmd = [DataMosher, Video_out , str(DataMosherBytes), Video_hex_out ]

		DataMosherPr = Popen(DataMosherCmd, shell=False, stdout=subprocess.DEVNULL)
		DataMosherPr.wait()
		
		DataMosherPr.communicate()
		if DataMosherPr.returncode == 0 : print (" ,OK]--->", end="")
		
		print("[5# Poping out result]")
		sys.stdout.flush()

		
		VideoPlayerCmd = [	"mplayer",
					"-msglevel", "all=-1",
					 Video_hex_out, "-loop", "0" 
				 ]
		
		
		VideoPlayerPr = Popen(VideoPlayerCmd, shell=False, stdout=subprocess.DEVNULL)
		VideoPlayerPr.wait()
		
		print("#" + str(ts) + " finished")
		sys.stdout.flush()

	
	
def ProcessCueJobs():

	while True:
	
		if len(CueJobs) > 0:
			
			#Cada vegada que iterem dins de CueJobs i rep cada item de l'array

			for i in CueJobs:
			
				#Codi/Simulacre
				#print ("Simulant processant " + str(i))				
				#time.sleep(8)
				#print ("Fi d'aquesta tasca")
				#
				Execute(i)
				
				#Eliminem aquesta tasca una vegada hem acabat
				CueJobs.remove(i)
				ShowPendingJobs()
		
		#Hem posat aixó per "ralentir" aquést thread i no sobrecarregar CPU
		time.sleep(0.2)
			

def WatchFile(f):

	global Status
	# D'aquesta manera, mitjançant un petit lapse de temps
	# i obtenint dos timestamps podem esbrinar 
	# si s'ha guardat de nou l'arxiu

	while True:
	
		try:
			f_ts = os.stat(f)[9]				
									
		except:							
			print("Warning: file not found " + f)
		
		else:
			time.sleep(fc_lapse)			 
			#current timestamp				
			c_f_ts  = os.stat(f)[9]
			
			#Si ha canviat l'arxiu (diferents timestamps)
			if c_f_ts != f_ts :
			
				if Status == True: # Nomès en el cas que estigui activat el listener, afegim canvis.
				
					print ( "\n" + os.path.basename(f) + " : Adding to the working qeue--> #" + str(c_f_ts))
					CueJobs.append(c_f_ts)
					
					ShowPendingJobs()


def KeyListener():

	global Status, RenderPr
	while True:
				
		key = getkey()	
		
		#Pausar/Depausar listener
		if key == keys.SPACE :

			# Donem la volta al valor
			Status = not Status
			
			if Status == True:
				prGreen("\n[UNPAUSE]Enabling listener.")

				
			elif Status == False:
				prYellow("\n[PAUSE]Disabling listener.")
			pass
			
		#abortar render	
		if key == keys.ESC :
		
			try:
				RenderPr
			except:
				#Basicament aquest missatge salta quan encara no s'ha declarat la variable
				print ("There are no render in progress")
			else:
				#Seria interessant implementar per aqui un codi
				#que esbrini mitjançant el pid si el proces está viu o no
				#amb tal de dir-li a l'usuari que no hi ha cap cap render en curs
				#i donar-li una mica de concordança a aquesta funció.
				
				subprocess.Popen.kill(RenderPr)
				
				

		
if __name__ == "__main__":

	#Empaquetem tot a un thread, per correr la funció principal
	#de forma asíncrona

	 #L'ùnic argument que li pasem ho fem per aquí, sempre afegint la coma.
	watch = threading.Thread(target=WatchFile, args=(f,)) 
	watch.start() #Inicialitzem a pelo, tal qual.
	
	#Inicialitzem fil per controlar la cua de taskes pendents
	#Aquí tenim el problema de sobrecarrega de CPU, a aquest thread:
	process = threading.Thread(target=ProcessCueJobs, args=())
	process.start()
	
	#...KeyListener
	
	keylistener = threading.Thread(target = KeyListener, args=())
	keylistener.start()
	
	



	
	
	
