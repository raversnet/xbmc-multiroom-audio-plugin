# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


"""
    Plugin for True "Syncronized" Multiroom Streaming Audio/Video
"""

# main imports
import sys
import os
import xbmc
import xbmcgui
import xbmcplugin, xbmcaddon

import time
import re
import urllib

Addon = xbmcaddon.Addon(id=os.path.basename(os.getcwd()))
# source path for multiroomaudio data
BASE_CURRENT_SOURCE_PATH = xbmc.translatePath( os.path.join( "special://home/", "addons", sys.modules[ "__main__" ].__plugin__, "resources", "avsources.xml" ) )
SHORTCUT_FILE = xbmc.translatePath( os.path.join( "special://profile/addon_data", sys.modules[ "__main__" ].__plugin__, "shortcut.cut" ) )
PROFILE_PATH = xbmc.translatePath( os.path.join( "special://profile", "" ) )

# avsource - source script file generation operators for sourceX and sourceXdata creation/maintenance respectfully
SOURCE_TEMPLATES_FILE_PATH = xbmc.translatePath( os.path.join( "special://home/", "addons", sys.modules[ "__main__" ].__plugin__, "resources", "" ) )
SOURCEXX_FILE_TEMPLATE = xbmc.translatePath( os.path.join( "special://home/", "addons", sys.modules[ "__main__" ].__plugin__, "resources", "sourceXtemplate" ) )
SOURCEXXDATA_FILE_TEMPLATE = xbmc.translatePath( os.path.join( "special://home/", "addons", sys.modules[ "__main__" ].__plugin__, "resources", "sourceXdatatemplate" ) )
PCOREXMLDATA_FILE_TEMPLATE = xbmc.translatePath( os.path.join( "special://home/", "addons", sys.modules[ "__main__" ].__plugin__, "resources", "PCXMLdatatemplate" ) )
CHMODCMDCHMODCMD = "chmod"
CHMODVAR1 = "777"
CHMODVAR2 = "+x"
CHMODVAR3 = "sources*"
DEFAULT_IMG = xbmc.translatePath(os.path.join( "special://home/", "addons", sys.modules[ "__main__" ].__plugin__, "resources", "default.tbn" ) )

REMOVE_COMMAND = "%%REMOVE%%"
ADD_COMMAND = "%%ADD%%"
IMPORT_COMMAND = "%%IMPORT%%"
SCAN_COMMAND = "%%SCAN%%"
RENAME_COMMAND = "%%RENAME%%"
EDIT_COMMAND = "%%EDIT%%"
COMMAND_ARGS_SEPARATOR = "^^"

pDialog = xbmcgui.DialogProgress()
pDialog.create( sys.modules[ "__main__" ].__plugin__ )

class Main:
    BASE_CACHE_PATH = xbmc.translatePath(os.path.join( "special://profile/Thumbnails", "Pictures" ))
    avsources = {}

    ''' initializes plugin and run the requiered action
        arguments:
            argv[0] - the path of the plugin (supplied by XBMC)
            argv[1] - the handle of the plugin (supplied by XBMC)
            argv[2] - one of the following (Addon.getLocalizedString( 30000 ) and 'avclient' can be any avsource name or avclient name created with the plugin) :
                /avsource - open the specific avsource (if exists) and browse its avclients
                            if the avsource is standalone - run it.
                /avsource/avclient - run the specifiec avclient using it's avsource.
                                ignore command if doesn't exists.
                /avsource/%%REMOVE%% - remove the avsource
                /avsource/%%ADD%% - add a new avclient (open wizard)
                /avsource/avclient/%%REMOVE%% - remove the avclient
                /avsource/%%IMPORT%% - import avclients from avclient path into avsource
                /avsource/%%SCAN%% - scan for avsource & avclients data from the internet
                /avsource/avclient/%%SCAN%% - scan for avclient data from the internet
                /avsource/%%WAIT_TOGGLE%% - toggle wait state 
                /%%ADD%% - add a new avsource (open wizard)
                
                (blank)     - open a list of the available avsources. if no avsource exists - open the avsource creation wizard.
    '''                        
#############################################################################################################
    def __init__( self ):
        # store an handle pointer
        self._handle = int(sys.argv[ 1 ])
        print self._handle
                    
        self._path = sys.argv[ 0 ]

        # get users preference
        self._get_settings()
        self._load_avsources(self.get_xml_source())
	os.system('chmod 777 '+SOURCE_TEMPLATES_FILE_PATH+'source*')
	# os.system(CHMODCMD, CHMODVAR1, SOURCE_TEMPLATES_FILE_PATH)
	os.system('chmod +x '+SOURCE_TEMPLATES_FILE_PATH+'source*')
	# os.system(CHMODCMD, CHMODVAR2, SOURCE_TEMPLATES_FILE_PATH)

        # if a commmand is passed as parameter
        param = sys.argv[ 2 ]
        if param:
            param = param[1:]
            command = param.split(COMMAND_ARGS_SEPARATOR)
            dirname = os.path.dirname(command[0])
            basename = os.path.basename(command[0])
            
            # check the action needed
            if (dirname):
                avsource = dirname
                avclient = basename
                if (avclient == REMOVE_COMMAND):
                    # check if it is a single avclient or a avsource
                    if (not os.path.dirname(avsource)):
                        self._remove_avsource(avsource)
                    else:
                        self._remove_avclient(os.path.dirname(avsource), os.path.basename(avsource))
                if (avclient == RENAME_COMMAND):
                    # check if it is a single avclient or a avsource
                    if (not os.path.dirname(avsource)):
                        self._rename_avsource(avsource)
                    else:
                        self._rename_avclient(os.path.dirname(avsource), os.path.basename(avsource))
                if (avclient == EDIT_COMMAND):
                    # check if it is a single avclient or a avsource
                    if (not os.path.dirname(avsource)):
                        self._edit_avsource(avsource)
                    else:
                        self._edit_avclient(os.path.dirname(avsource), os.path.basename(avsource))
                elif (avclient == SCAN_COMMAND):
                    # check if it is a single avclient scan or a avsource scan
                    if (not os.path.dirname(avsource)):
                        self._scan_avsource(avsource)
                    else:
                        avclientname = os.path.basename(avsource)
                        avsource = os.path.dirname(avsource)
                elif (avclient == ADD_COMMAND):
                    self._add_new_avclient(avsource)
                elif (avclient == IMPORT_COMMAND):
                    self._import_avclients(avsource)
                else:
                    self._run_avclient(avsource, avclient)
            else:
                avsource = basename
                # if it's an add command
                if (avsource == ADD_COMMAND):
                    self._add_new_avsource()
                else:
                    # if there is no avclientpath (a standalone avsource)
                    if (self.avsources[avsource]["avclientpath"] == ""):
                        # launch it
                        self._run_avsource(avsource)
                    else:
                        # otherwise, list the avclients
                        self._get_avclients(avsource)                    
        else:
            # otherwise get the list of the programs in the current folder
            if (not self._get_avsources()):
                # if no avsource found - attempt to add a new one
                if (self._add_new_avsource()):
                    self._get_avsources()
                else:
                    xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=False , cacheToDisc=False)

#############################################################################################################                    
    def _remove_avclient(self, avsource, avclient):        
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30010 ) % avclient)
        if (ret):
            self.avsources[avsource]["avclients"].pop(avclient)
            self._save_avsources()
            xbmc.executebuiltin("Container.Refresh")

#############################################################################################################            
    def _remove_avsource(self, avsourceName):
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30010 ) % avsourceName)
        if (ret):
            self.avsources.pop(avsourceName)
            self._save_avsources()
            xbmc.executebuiltin("Container.Refresh")

#############################################################################################################            
    def _rename_avclient(self, avsource, avclient):        
        keyboard = xbmc.Keyboard(self.avsources[avsource]["avclients"][avclient]["name"], Addon.getLocalizedString( 30018 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self.avsources[avsource]["avclients"][avclient]["name"] = keyboard.getText()
            self._save_avsources()
            xbmc.executebuiltin("Container.Refresh")

#############################################################################################################        
    def _rename_avsource(self, avsourceName):
        keyboard = xbmc.Keyboard(self.avsources[avsourceName]["name"], Addon.getLocalizedString( 30025 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self.avsources[avsourceName]["name"] = keyboard.getText()
            self._save_avsources()
            xbmc.executebuiltin("Container.Refresh")

#############################################################################################################
    def _edit_avclient(self, avsource, avclient):        
        keyboard = xbmc.Keyboard(self.avsources[avsource]["avclients"][avclient]["name"], Addon.getLocalizedString( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self.avsources[avsource]["avclients"][avclient]["name"] = keyboard.getText()
            self._save_avsources()
            xbmc.executebuiltin("Container.Refresh")

#############################################################################################################        
    def _edit_avsource(self, avsourceName):
        keyboard = xbmc.Keyboard(self.avsources[avsourceName]["streamsrc"], Addon.getLocalizedString( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self.avsources[avsourceName]["streamsrc"] = keyboard.getText()
            self._save_avsources()
            xbmc.executebuiltin("Container.Refresh")

#############################################################################################################
    def _run_avsource(self, avsourceName):
        if (self.avsources.has_key(avsourceName)):
	    avsource = self.avsources[avsourceName]
	    xbmc_img = DEFAULT_IMG
	    xbmc.executehttpapi("Stop")
	    xbmc.executebuiltin("Notification(Multiroom Audio,"+ avsourceName +" is ACTIVE,10000,"+ xbmc_img +")")
            if (os.environ.get( "OS", "xbox" ) == "xbox"):
                xbmc.executebuiltin('XBMC.Runxbe(' + avsource["application"] + ')')
            else:
                if (sys.platform == 'win32'):
                    if (avsource["wait"] == "true"):
                        cmd = "System.ExecWait"
                    else:
                        cmd = "System.Exec"
                    xbmc.executebuiltin("%s(\"%s\" \"%s\")" % (cmd, avsource["application"], avsource["args"]))
                elif (sys.platform.startswith('linux')):
                    os.system("%s %s" % (avsource["application"], avsource["args"]))
                elif (sys.platform.startswith('darwin')):
                    os.system("\"%s\" %s" % (avsource["application"], avsource["args"]))
                else:
		    
                    pass;
                    # unsupported platform
                             
#############################################################################################################
    def _run_avclient(self, avsourceName, avclientName):
        if (self.avsources.has_key(avsourceName)):
            avsource = self.avsources[avsourceName]
            if (avsource["avclients"].has_key(avclientName)):
                avclient = self.avsources[avsourceName]["avclients"][avclientName]
                if (os.environ.get( "OS", "xbox" ) == "xbox"):
                    f=open(SHORTCUT_FILE, "wb")
                    f.write("<shortcut>\n")
                    f.write("    <path>" + avsource["application"] + "</path>\n")
                    f.write("    <custom>\n")
                    f.write("       <game>" + avclient["filename"] + "</game>\n")
                    f.write("    </custom>\n")
                    f.write("</shortcut>\n")
                    f.close()
                    xbmc.executebuiltin('XBMC.Runxbe(' + SHORTCUT_FILE + ')')                    
                else:
                    if (sys.platform == 'win32'):
                        if (avsource["wait"] == "true"):
                            cmd = "System.ExecWait"
                        else:
                            cmd = "System.Exec"
                        xbmc.executebuiltin("%s(\"%s\" %s \"%s\")" % (cmd, avsource["application"], avsource["args"], avclient["filename"]))
                    elif (sys.platform.startswith('linux')):
 						os.system("\"%s\" %s \"%s\"" % (avsource["application"], avsource["args"], avclient["filename"]))
                    elif (sys.platform.startswith('darwin')):
                        os.system("\"%s\" %s \"%s\"" % (avsource["application"], avsource["args"], avclient["filename"]))
                    else:
                        pass;
                        # unsupported platform

    ''' get an xml data from an xml file '''
#############################################################################################################
    def get_xml_source( self ):
        try:
            usock = open( BASE_CURRENT_SOURCE_PATH, "r" )
            # read source
            xmlSource = usock.read()
            # close socket
            usock.close()
            ok = True
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            ok = False
        if ( ok ):
            # return the xml string without \n\r (newline)
            return xmlSource.replace("\n","").replace("\r","")
        else:
            return ""

#############################################################################################################
    def _save_avsources (self):
        # make settings directory if doesn't exists
        if (not os.path.isdir(os.path.dirname(BASE_CURRENT_SOURCE_PATH))):
            os.makedirs(os.path.dirname(BASE_CURRENT_SOURCE_PATH));

        self._save_sourceXXfile()
	self._save_sourceXXdatafile()
	usock = open( BASE_CURRENT_SOURCE_PATH, "w" )
        usock.write("<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>\n")
        usock.write("<avsources>\n")
        for avsourceIndex in self.avsources:
            avsource = self.avsources[avsourceIndex]
            usock.write("\t<avsource>\n")
            usock.write("\t\t<name>"+avsource["name"]+"</name>\n")
            usock.write("\t\t<application>"+avsource["application"]+"</application>\n")
            usock.write("\t\t<args>"+avsource["args"]+"</args>\n")
	    usock.write("\t\t<streamsrc>"+avsource["streamsrc"]+"</streamsrc>\n")
            usock.write("\t\t<avclientpath>"+avsource["avclientpath"]+"</avclientpath>\n")
            usock.write("\t\t<avclientext>"+avsource["avclientext"]+"</avclientext>\n")
            usock.write("\t\t<srcA>"+avsource["srcA"]+"</srcA>\n")
            usock.write("\t\t<srcB>"+avsource["srcB"]+"</srcB>\n")
            usock.write("\t\t<thumb>"+avsource["thumb"]+"</thumb>\n")
	    usock.write("\t\t<srctype>"+avsource["srctype"]+"</srctype>\n")
            usock.write("\t\t<wait>"+avsource["wait"]+"</wait>\n")
            usock.write("\t\t<avclients>\n")
            for avclientIndex in avsource["avclients"]:
                avclientdata = avsource["avclients"][avclientIndex]
                usock.write("\t\t\t<avclient>\n")
                usock.write("\t\t\t\t<name>"+avclientdata["name"]+"</name>\n")
                usock.write("\t\t\t\t<filename>"+avclientdata["filename"]+"</filename>\n")
                usock.write("\t\t\t\t<thumb>"+avclientdata["thumb"]+"</thumb>\n")
                usock.write("\t\t\t</avclient>\n")
            usock.write("\t\t</avclients>\n")
            usock.write("\t</avsource>\n")            
        usock.write("</avsources>")
        usock.close()
	os.system('chmod 777 '+SOURCE_TEMPLATES_FILE_PATH+'s*')
	
#############################################################################################################
    def _save_sourceXXfile (self):
        # make settings directory if doesn't exists
        if (not os.path.isdir(os.path.dirname(BASE_CURRENT_SOURCE_PATH))):
            os.makedirs(os.path.dirname(BASE_CURRENT_SOURCE_PATH));
            
        for avsourceIndex in self.avsources:
	    xbmc_img = DEFAULT_IMG
            avsource = self.avsources[avsourceIndex]
            usock = open( SOURCEXX_FILE_TEMPLATE, "w" )
            usock.write("#!/bin/bash\n")
            usock.write("\n")
            usock.write("if pidof vlc | grep [0-9] > /dev/null\n")
            usock.write("then\n")
	    usock.write("WID=`xdotool search --class \"XBMC\"`;\n")
	    usock.write("wmctrl -c \""+avsource["srctype"]+"B\"\n")
	    usock.write("xdotool windowactivate $WID\n")
	    usock.write("wget -q \"http://localhost:8081/xbmcCmds/xbmcHttp?command=ExecBuiltIn(Notification(Multiroom Audio,"+avsource["name"]+" - DeActivated,30000,"+ xbmc_img +"))\"\n")
	    usock.write("else\n")
            usock.write("xterm -display :0 -T "+avsource["srctype"]+"B -e "+SOURCE_TEMPLATES_FILE_PATH+"./"+avsource["srcB"]+"\n")
	    usock.write("\n")
            usock.write("fi")
            usock.close()
	    os.system('cp '+SOURCEXX_FILE_TEMPLATE+' '+SOURCE_TEMPLATES_FILE_PATH+''+avsource["srcA"]+'')

#############################################################################################################
    def _save_sourceXXdatafile (self):
        # make settings directory if doesn't exists
        if (not os.path.isdir(os.path.dirname(BASE_CURRENT_SOURCE_PATH))):
            os.makedirs(os.path.dirname(BASE_CURRENT_SOURCE_PATH));

        for avsourceIndex in self.avsources:
	    xbmc_img = DEFAULT_IMG
            avsource = self.avsources[avsourceIndex]            
            usock = open( SOURCEXXDATA_FILE_TEMPLATE, "w" )
            usock.write("#!/bin/bash\n")
            usock.write("\n")
            usock.write("WID=`xdotool search --class \"XBMC\"`;\n")
            usock.write("xdotool windowactivate $WID\n")
            usock.write("wmctrl -c \""+avsource["srctype"]+"A\"\n")
	    # (Additional options: --audio-visual visual --effect-list spectrometer)
	    usock.write("cvlc "+avsource["streamsrc"]+" --fullscreen --file-caching=0\n")
            usock.close()
	    os.system('cp '+SOURCEXXDATA_FILE_TEMPLATE+' '+SOURCE_TEMPLATES_FILE_PATH+''+avsource["srcB"]+'')

#############################################################################################################
    def _save_serverXXfile (self):
        # make settings directory if doesn't exists
        if (not os.path.isdir(os.path.dirname(BASE_CURRENT_SOURCE_PATH))):
            os.makedirs(os.path.dirname(BASE_CURRENT_SOURCE_PATH));
            
        for avsourceIndex in self.avsources:
            avsource = self.avsources[avsourceIndex]
            usock = open( SOURCEXX_FILE_TEMPLATE, "w" )
            usock.write("#!/bin/bash\n")
            usock.write("\n")
            usock.write("if pidof vlc | grep [0-9] > /dev/null\n")
            usock.write("then\n")
	    usock.write("WID=`xdotool search --class \"XBMC\"`;\n")
	    usock.write("wmctrl -c \""+avsource["srctype"]+"B\"\n")
	    usock.write("xdotool windowactivate $WID\n")
	    usock.write("wget -q \"http://localhost:8081/xbmcCmds/xbmcHttp?command=ExecBuiltIn(Notification(Multiroom Audio,"+avsource["name"]+" - DeActivated,30000,"+ xbmc_img +"))\"\n")
	    usock.write("else\n")
            usock.write("xterm -display :0 -T "+avsource["srctype"]+"B -e "+SOURCE_TEMPLATES_FILE_PATH+"./"+avsource["srcB"]+"\n")
	    usock.write("\n")
            usock.write("fi")
            usock.close()
	    os.system('cp '+SOURCEXX_FILE_TEMPLATE+' '+SOURCE_TEMPLATES_FILE_PATH+''+avsource["srcA"]+'')

#############################################################################################################
    def	_save_serverXXdatafile (self): 
        # make settings directory if doesn't exists
        if (not os.path.isdir(os.path.dirname(BASE_CURRENT_SOURCE_PATH))):
            os.makedirs(os.path.dirname(BASE_CURRENT_SOURCE_PATH));
	    
        for avsourceIndex in self.avsources:
            avsource = self.avsources[avsourceIndex]            
            usock = open( SOURCEXXDATA_FILE_TEMPLATE, "w" )
            usock.write("#!/bin/bash\n")
            usock.write("\n")
            usock.write("WID=`xdotool search --class \"XBMC\"`;\n")
            usock.write("xdotool windowactivate $WID\n")
            usock.write("wmctrl -c \""+avsource["srctype"]+"A\"\n")
	    # (Additional options: --audio-visual visual --effect-list spectrometer)
	    usock.write("cvlc "+avsource["streamsrc"]+"\n")
            usock.close()
	    os.system('cp '+SOURCEXXDATA_FILE_TEMPLATE+' '+SOURCE_TEMPLATES_FILE_PATH+''+avsource["srcB"]+'')
	    
#############################################################################################################
    def	_save_playercorefactoryfile( self ): 
	    vlc_loc    =  Addon.getSetting( "vlc_loc" )
	    video_sout =  Addon.getSetting( "video_sout" )
	    video_fc   =  Addon.getSetting( "video_fc" )
	    audio_sout =  Addon.getSetting( "audio_sout" )
	    audio_fc   =  Addon.getSetting( "audio_fc" )
            usock = open( PCOREXMLDATA_FILE_TEMPLATE, "w" )
            usock.write("<playercorefactory>\n")
            usock.write("  <players>\n")
            usock.write("    <!-- This File was created by Multiroom Streaming AV Plugin for XBMC\n")
            usock.write("    These are compiled-in as re-ordering them would break scripts\n")
            usock.write("    The following aliases may also be used:\n")
            usock.write("    audiodefaultplayer, videodefaultplayer, videodefaultdvdplayer\n")
            usock.write("    <player name=\"DVDPlayer\" audio=\"true\" video=\"true\" />\n")
            usock.write("    <player name=\"DVDPlayer\" /> placeholder for MPlayer\n")
            usock.write("    <player name=\"PAPlayer\" audio=\"true\" />\n")
            usock.write("    -->\n")
            usock.write("    <player name=\"Video_Stream\" type=\"ExternalPlayer\" audio=\"false\" video=\"true\">\n")
            usock.write("      <filename>"+vlc_loc+"</filename>\n")
            usock.write("      <args>--intf dummy \"{1}\" --play-and-exit "+video_sout+" --file-caching="+video_fc+"</args>\n")
            usock.write("      <hideconsole>false</hideconsole>\n")
            usock.write("      <hidecursor>false</hidecursor>\n")
            usock.write("      <forceontop>false</forceontop>\n")
            usock.write("    </player>\n")
            usock.write("    <player name=\"Audio_Stream\" type=\"ExternalPlayer\" audio=\"true\" video=\"false\">\n")
            usock.write("      <filename>"+vlc_loc+"</filename>\n")
            usock.write("      <args>--intf dummy \"{1}\" --play-and-exit "+audio_sout+" --file-caching="+audio_fc+"</args>\n")
            usock.write("      <hideconsole>false</hideconsole>\n")
            usock.write("      <hidecursor>false</hidecursor>\n")
            usock.write("      <forceontop>false</forceontop>\n")
            usock.write("    </player>\n")
            usock.write("  </players>\n")
            usock.write("    <rules name=\"system rules\">\n")
            usock.write("      <rule name=\"rtv\" protocols=\"rtv\" player=\"DVDPlayer\" />\n")
            usock.write("      <rule name=\"hdhomerun/myth/rtmp/mms/udp\" protocols=\"hdhomerun|myth|cmyth|rtmp|mms|mmsh|udp\" player=\"DVDPlayer\" />\n")
            usock.write("      <rule name=\"lastfm/shout\" protocols=\"lastfm|shout\" player=\"PAPlayer\" />\n")
            usock.write("\n")  
            usock.write("      <!-- dvdplayer can play standard rtsp streams -->\n")
            usock.write("      <rule name=\"rtsp\" protocols=\"rtsp\" filetypes=\"!(rm|ra)\"  player=\"PAPlayer\" />\n")
            usock.write("\n")  
            usock.write("      <!-- Internet streams -->\n")
            usock.write("      <rule name=\"streams\" internetstream=\"true\">\n")
            usock.write("        <rule name=\"flv/aacp/sdp\" mimetypes=\"video/x-flv|video-flv|audio/aacp|application/sdp\" player=\"DVDPlayer\" />\n")
            usock.write("        <rule name=\"mp2\" mimetypes=\"application/octet-stream\" filetypes=\"mp2\" player=\"PAPlayer\" />\n")
            usock.write("      </rule>\n")
            usock.write("\n")  
            usock.write("      <!-- DVDs -->\n")
            usock.write("      <rule name=\"dvd\" dvd=\"true\" player=\"videodefaultdvdplayer\" />\n")
            usock.write("      <rule name=\"dvdfile\" dvdfile=\"true\" player=\"videodefaultdvdplayer\" />\n")
            usock.write("      <rule name=\"dvdimage\" dvdimage=\"true\" player=\"videodefaultdvdplayer\" />\n")
            usock.write("\n")
            usock.write("      <!-- Only dvdplayer can handle these normally -->\n")
            usock.write("      <rule name=\"sdp/asf\" filetypes=\"sdp|asf\" player=\"DVDPlayer\" />\n")
            usock.write("\n")  
            usock.write("      <!-- Pass these to dvdplayer as we do not know if they are audio or video -->\n")
            usock.write("      <rule name=\"nsv\" filetypes=\"nsv\" player=\"DVDPlayer\" />\n")
            usock.write("    </rules>\n")
            usock.write("</playercorefactory>\n")
            usock.close()
	    os.system('cp '+PCOREXMLDATA_FILE_TEMPLATE+' '+PROFILE_PATH+'playercorefactory.xml')

    ''' read the list of avsources and avclients from avsources.xml file '''
#############################################################################################################
    def _load_avsources( self , xmlSource):
        avsources = re.findall( "<avsource>(.*?)</avsource>", xmlSource )
        print "AVsource: found %d avsources" % ( len(avsources) )
        for avsource in avsources:
            name = re.findall( "<name>(.*?)</name>", avsource )
            application = re.findall( "<application>(.*?)</application>", avsource )
            args = re.findall( "<args>(.*?)</args>", avsource )
            streamsrc = re.findall( "<streamsrc>(.*?)</streamsrc>", avsource )
            avclientpath = re.findall( "<avclientpath>(.*?)</avclientpath>", avsource )
            avclientext = re.findall( "<avclientext>(.*?)</avclientext>", avsource )
            srcA = re.findall( "<srcA>(.*?)</srcA>", avsource )
            srcB = re.findall( "<srcB>(.*?)</srcB>", avsource )
            thumb = re.findall( "<thumb>(.*?)</thumb>", avsource )
	    srctype = re.findall( "<srctype>(.*?)</srctype>", avsource )
            wait = re.findall( "<wait>(.*?)</wait>", avsource )
            avclientsxml = re.findall( "<avclient>(.*?)</avclient>", avsource )

            if len(name) > 0 : name = name[0]
            else: name = "unknown"

            if len(application) > 0 : application = application[0]
            else: application = ""

            if len(args) > 0 : args = args[0]
            else: args = ""

	    if len(streamsrc) > 0 : streamsrc = streamsrc[0]
	    else: streamsrc = ""

            if len(avclientpath) > 0 : avclientpath = avclientpath[0]
            else: avclientpath = ""

            if len(avclientext) > 0: avclientext = avclientext[0]
            else: avclientext = ""

	    if len(srcA) > 0 : srcA = srcA[0]
	    else: srcA = ""

	    if len(srcB) > 0 : srcB = srcB[0]
	    else: srcB = ""

            if len(thumb) > 0: thumb = thumb[0]
            else: thumb = ""

            if len(srctype) > 0: srctype = srctype[0]
	    else: srctype = ""

            if len(wait) > 0: wait = wait[0]
            else: wait = ""
            
            avclients = {}
            for avclient in avclientsxml:
                avclientname = re.findall( "<name>(.*?)</name>", avclient )
                avclientfilename = re.findall( "<filename>(.*?)</filename>", avclient )
                avclientthumb = re.findall( "<thumb>(.*?)</thumb>", avclient )

                if len(avclientname) > 0 : avclientname = avclientname[0]
                else: avclientname = "unknown"

                if len(avclientfilename) > 0 : avclientfilename = avclientfilename[0]
                else: avclientfilename = ""

                if len(avclientthumb) > 0 : avclientthumb = avclientthumb[0]
                else: avclientthumb = ""

                # prepare avclient object data
                avclientdata = {}
                avclientdata["name"] = avclientname
                avclientdata["filename"] = avclientfilename
                avclientdata["thumb"] = avclientthumb

                # add avclient to the avclients list (using name as index)
                avclients[avclientname] = avclientdata

            # prepare avsource object data
            avsourcedata = {}
            avsourcedata["name"] = name
            avsourcedata["application"] = application
            avsourcedata["args"] = args
	    avsourcedata["streamsrc"] = streamsrc
            avsourcedata["avclientpath"] = avclientpath
            avsourcedata["avclientext"] = avclientext
            avsourcedata["srcA"] = srcA
            avsourcedata["srcB"] = srcB
            avsourcedata["thumb"] = thumb
            avsourcedata["srctype"] = srctype
            avsourcedata["wait"] = wait
            avsourcedata["avclients"] = avclients

            # add avsource to the avsources list (using name as index)
	    self._save_playercorefactoryfile()
            self.avsources[name] = avsourcedata

#############################################################################################################    
    def _get_avsources( self ):
        if (len(self.avsources) > 0):
            for index in self.avsources:
                avsource = self.avsources[index]
                self._add_avsource(avsource["name"], avsource["application"], avsource["avclientpath"], avsource["avclientext"], avsource["thumb"], avsource["wait"], avsource["avclients"], len(self.avsources))
            xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )
            return True   
        else:
            return False

#############################################################################################################
    def _get_avclients( self, avsourceName ):
        if (self.avsources.has_key(avsourceName)):
            selectedAVsource = self.avsources[avsourceName]
            avclients = selectedAVsource["avclients"]
            print "AVsource: %s : found %d avclients " % (avsourceName, len(avclients))
            if (len(avclients) > 0) :
                for index in avclients :
                    avclient = avclients[index]
                    self._add_avclient(avsourceName, avclient["name"], avclient["filename"], avclient["thumb"], len(avclients))
            else:
                dialog = xbmcgui.Dialog()
                ret = dialog.yesno(Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30013 ))
                if (ret):
                    self._import_avclients(avsourceName, addavclients = True)
            xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )
            return True
        else:
            return False

#############################################################################################################
    def _report_hook( self, count, blocksize, totalsize ):
         percent = int( float( count * blocksize * 100) / totalsize )
         msg1 = Addon.getLocalizedString( 30033 )  % ( os.path.split( self.url )[ 1 ], )
         pDialog.update( percent, msg1 )
         if ( pDialog.iscanceled() ): raise

#############################################################################################################        
    def _scan_avsource(self, avsourcename):
        self._save_avsources()

#############################################################################################################
    def _import_avclients(self, avsourceName, addavclients = False):
        dialog = xbmcgui.Dialog()
        avclientsCount = 0
        filesCount = 0
        skipCount = 0
        selectedAVsource = self.avsources[avsourceName]
        pDialog = xbmcgui.DialogProgress()
        path = selectedAVsource["avclientpath"]
        exts = selectedAVsource["avclientext"]
        avclients = selectedAVsource["avclients"]
        ret = pDialog.create(Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30014 ) % (path));
        
        files = os.listdir(path)
        for f in files:
            pDialog.update(filesCount * 100 / len(files))
            fullname = os.path.join(path, f)
            for ext in exts.split("|"):
                avclientadded = False
                if f.upper().endswith("." + ext.upper()):
                    avclientname =  f[:-len(ext)-1].capitalize()
                    if (not avclients.has_key(avclientname)):
                        # prepare avclient object data
                        avclientdata = {}
                        avclientname =  f[:-len(ext)-1].capitalize()
                        avclientdata["name"] = avclientname
                        avclientdata["filename"] = fullname 
                        avclientdata["thumb"] = ""

                        # add avclient to the avclients list (using name as index)
                        avclients[avclientname] = avclientdata
                        avclientsCount = avclientsCount + 1
                        
                        if (addavclients):
                            self._add_avclient(avsourceName, avclientdata["name"], avclientdata["filename"], avclientdata["thumb"], len(files))
                            avclientadded = True
                if not avclientadded:
                    skipCount = skipCount + 1
               
            filesCount = filesCount + 1    
        pDialog.close()
        self._save_avsources()
        if (skipCount == 0):
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 6000)" % (Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30015 ) % (avclientsCount) + " " + Addon.getLocalizedString( 30050 )))
            #dialog.ok(Addon.getLocalizedString( 30000 ), (Addon.getLocalizedString( 30015 )+ "\n" + Addon.getLocalizedString( 30050 )) % (avclientsCount))
        else:
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 12000)" % (Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30016 ) % (avclientsCount, skipCount) + " " + Addon.getLocalizedString( 30050 )))
            #dialog.ok(Addon.getLocalizedString( 30000 ), (Addon.getLocalizedString( 30016 )+ "\n" + Addon.getLocalizedString( 30050 )) % (avclientsCount, skipCount))

#############################################################################################################
    def _get_thumbnail( self, thumbnail_url ):
        # make the proper cache filename and path so duplicate caching is unnecessary
        if ( not thumbnail_url.startswith( "http://" ) ): return thumbnail_url
        try:
            filename = xbmc.getCacheThumbName( thumbnail_url )
            filepath = xbmc.translatePath( os.path.join( self.BASE_CACHE_PATH, filename[ 0 ], filename ) )
            # if the cached thumbnail does not exist fetch the thumbnail
            if ( not os.path.isfile( filepath ) ):
                # fetch thumbnail and save to filepath
                info = urllib.urlretrieve( thumbnail_url, filepath )
                # cleanup any remaining urllib cache
                urllib.urlcleanup()
            return filepath
        except:
            # return empty string if retrieval failed
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return ""

#############################################################################################################        
    def _get_thumb(self, displayName, fileName):
        exts = ["jpg", "png", "gif","bmp"]
        for ext in exts:
            thumbfilename = os.path.join(self.settings[ "thumbs_path" ], "%s.%s" % (displayName, ext))
            if (os.path.isfile(thumbfilename)):
                return thumbfilename
            thumbfilename = os.path.join(self.settings[ "thumbs_path" ], "%s.%s" % (os.path.basename(fileName).split(".")[0], ext))
            if (os.path.isfile(thumbfilename)):
                return thumbfilename            

#############################################################################################################
    def _add_avsource(self, name, cmd, path, ext, thumb, wait, avclients, total) :
        commands = []
        commands.append((Addon.getLocalizedString( 30101 ), "XBMC.RunPlugin(%s?%s)" % (self._path, ADD_COMMAND) , ))
        if (sys.platform == "win32"):
		commands.append((Addon.getLocalizedString( 30103 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, WAIT_TOGGLE_COMMAND) , ))
        commands.append((Addon.getLocalizedString( 30107 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, RENAME_COMMAND) , ))
        commands.append((Addon.getLocalizedString( 30104 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, REMOVE_COMMAND) , ))
        commands.append((Addon.getLocalizedString( 30108 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, EDIT_COMMAND) , ))
        
        if (path == ""):
            folder = False
            icon = "DefaultProgram.png"
        else:
            folder = True
            icon = "DefaultFolder.png"
            commands.append((Addon.getLocalizedString( 30105 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, IMPORT_COMMAND) , ))
            commands.append((Addon.getLocalizedString( 30106 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, ADD_COMMAND) , ))            
        if (thumb):
            thumbnail = thumb
        else:
            thumbnail = self._get_thumb(name, cmd)
           
        if (thumbnail):
            listitem = xbmcgui.ListItem( name, iconImage=icon, thumbnailImage=thumbnail)
        else:
            listitem = xbmcgui.ListItem( name, iconImage=icon )
        listitem.addContextMenuItems( commands )
        xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s"  % (self._path, name), listitem=listitem, isFolder=folder, totalItems=total)

#############################################################################################################
    def _add_avclient( self, avsource, name, cmd , thumb, total):
        if (thumb):
            thumbnail = thumb
        else:
            thumbnail = self._get_thumb(name, cmd)
        icon = "DefaultProgram.png"
        if (thumbnail):
            listitem = xbmcgui.ListItem( name, iconImage=icon, thumbnailImage=thumbnail)
        else:
            listitem = xbmcgui.ListItem( name, iconImage=icon )
        commands = []
        commands.append(( Addon.getLocalizedString( 30107 ), "XBMC.RunPlugin(%s?%s/%s/%s)" % (self._path, avsource, name, RENAME_COMMAND) , ))
        commands.append(( Addon.getLocalizedString( 30108 ), "XBMC.RunPlugin(%s?%s/%s/%s)" % (self._path, avsource, name, EDIT_COMMAND) , ))
        commands.append(( Addon.getLocalizedString( 30104 ), "XBMC.RunPlugin(%s?%s/%s/%s)" % (self._path, avsource, name, REMOVE_COMMAND) , ))
        listitem.addContextMenuItems( commands )
        xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s/%s"  % (self._path, avsource, name), listitem=listitem, isFolder=False, totalItems=total)

#############################################################################################################
    def _add_new_avclient ( self , avsourceName) :
        dialog = xbmcgui.Dialog()
        avsource = self.avsources[avsourceName]
        ext = avsource["avclientext"]
        avclients = avsource["avclients"]
        avclientpath = avsource["avclientpath"]
        
        avclientfile = dialog.browse(1, Addon.getLocalizedString( 30017 ),"files", "."+ext, False, False, avclientpath)
        if (avclientfile):
            title=os.path.basename(avclientfile).split(".")[0].capitalize()
            keyboard = xbmc.Keyboard(title, Addon.getLocalizedString( 30018 ))
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                title = keyboard.getText()

                # prepare avclient object data
                avclientdata = {}
                avclientdata["name"] = title
                avclientdata["filename"] = avclientfile
                avclientdata["thumb"] = ""

                # add avclient to the avclients list (using name as index)
                avclients[title] = avclientdata

                xbmc.executebuiltin("XBMC.Notification(%s,%s, 6000)" % (Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30019 ) + " " + Addon.getLocalizedString( 30050 )))
                #xbmcgui.Dialog().ok(Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30019 )+ "\n" + Addon.getLocalizedString( 30050 ))
        self._save_avsources()

#############################################################################################################
    def _add_new_avsource ( self ) :
        dialog = xbmcgui.Dialog()
        type = dialog.select(Addon.getLocalizedString( 30020 ), [Addon.getLocalizedString( 30021 )])
        if (os.environ.get( "OS", "xbox" ) == "xbox"):
            filter = ".xbe|.cut"
        else:
            if (sys.platform == "win32"):
                filter = ".bat|.exe"
            else:
                filter = ""
            
        if (type == 0):
            appkeyboard = xbmc.Keyboard("", Addon.getLocalizedString( 30023 ))
            appkeyboard.doModal()
           ### app = xbmcgui.Dialog().browse(1,Addon.getLocalizedString( 30023 ),"files",filter)
            if (appkeyboard.isConfirmed()): ### (app):
		srctype = "client"
                appvarA = "xterm -display :0 -T clientA -e "
                appvar1 = SOURCE_TEMPLATES_FILE_PATH
		appvar2 = "./"
		appvar3 = "source"
		appvar4 = "data"              
		appvar5 = appkeyboard.getText();
		appvar6 = " --fullscreen"
                app = appvarA+appvar1+appvar2+appvar3+appvar5 
                argkeyboard = xbmc.Keyboard("", Addon.getLocalizedString( 30024 ))
                argkeyboard.doModal()
                if (argkeyboard.isConfirmed()):
                    args = argkeyboard.getText();
                    streamsrckeyboard = xbmc.Keyboard("", Addon.getLocalizedString( 30037 ))
                    streamsrckeyboard.doModal()
                    if (streamsrckeyboard.isConfirmed()):
                        streamsrc = streamsrckeyboard.getText();
                        title = os.path.basename(app).split(".")[0].capitalize()
                        keyboard = xbmc.Keyboard(title, Addon.getLocalizedString( 30025 ))
                        keyboard.doModal()
                        if (keyboard.isConfirmed()):
                            title = keyboard.getText()                    
                            # prepare avsource object data
                            avsourcedata = {}
                            avsourcedata["name"] = title
                            avsourcedata["application"] = app
                            avsourcedata["args"] = args
   		      	    avsourcedata["streamsrc"] = streamsrc 
                            avsourcedata["avclientpath"] = ""
                            avsourcedata["avclientext"] = ""
   		      	    avsourcedata["srcA"] = appvar3+appvar5
   		      	    avsourcedata["srcB"] = appvar3+appvar5+appvar4
                            avsourcedata["thumb"] = ""
                            avsourcedata["srctype"] = srctype
                            avsourcedata["wait"] = "true"
                            avsourcedata["avclients"] = {}
                    
                        # add avsource to the avsources list (using name as index)
                        self.avsources[title] = avsourcedata
                        self._save_avsources()

                        xbmc.executebuiltin("Container.Refresh")
                        return True
        elif (type == 1):
            appkeyboard = xbmc.Keyboard("", Addon.getLocalizedString( 30038 ))
            appkeyboard.doModal()
           ### app = xbmcgui.Dialog().browse(1,Addon.getLocalizedString( 30023 ),"files",filter)
            if (appkeyboard.isConfirmed()): ### (app):
		srctype = "srvr" 
                appvarA = "xterm -display :0 -T srvrA -e "
                appvar1 = SOURCE_TEMPLATES_FILE_PATH
		appvar2 = "./"
		appvar3 = "server"
		appvar4 = "data"              
		appvar5 = appkeyboard.getText();
                app = appvarA+appvar1+appvar2+appvar3+appvar5 
                argkeyboard = xbmc.Keyboard("", Addon.getLocalizedString( 30024 ))
                argkeyboard.doModal()
                if (argkeyboard.isConfirmed()):
                    args = argkeyboard.getText();
                    streamsrckeyboard = xbmc.Keyboard("", Addon.getLocalizedString( 30039 ))
                    streamsrckeyboard.doModal()
                    if (streamsrckeyboard.isConfirmed()):
                        streamsrc = streamsrckeyboard.getText();
			titleprefix = "Master Streamer - "
                        titlesuffix = os.path.basename(app).split(".")[0].capitalize()
			title = titleprefix+titlesuffix
                        keyboard = xbmc.Keyboard(title, Addon.getLocalizedString( 30025 ))
                        keyboard.doModal()
                        if (keyboard.isConfirmed()):
                            title = keyboard.getText()                    
                            # prepare avsource object data
                            avsourcedata = {}
                            avsourcedata["name"] = title
                            avsourcedata["application"] = app
                            avsourcedata["args"] = args
   		      	    avsourcedata["streamsrc"] = streamsrc 
                            avsourcedata["avclientpath"] = ""
                            avsourcedata["avclientext"] = ""
   		      	    avsourcedata["srcA"] = appvar3+appvar5
   		      	    avsourcedata["srcB"] = appvar3+appvar5+appvar4
                            avsourcedata["thumb"] = ""
                            avsourcedata["srctype"] = srctype
                            avsourcedata["wait"] = "true"
                            avsourcedata["avclients"] = {}
                    
                        # add avsource to the avsources list (using name as index)
                        self.avsources[title] = avsourcedata
                        self._save_avsources()

                        xbmc.executebuiltin("Container.Refresh")
                        return True
        return False

#############################################################################################################
    def _get_search_engine( self ):
        exec "import resources.search_engines.%s.search_engine as search_engine" % ( self.settings[ "search_engine" ], )
        return search_engine.SearchEngine()

#############################################################################################################                                
    def _get_settings( self ):
        self.settings = {}
	self.settings[ "thumbs_path" ]     =  xbmc.translatePath(Addon.getSetting( "thumbs_path" ))
	self.settings[ "search_engine" ]   =  Addon.getSetting( "search_engine" )      
	if (not os.path.isdir(os.path.dirname(self.settings[ "thumbs_path" ]))):
		os.makedirs(os.path.dirname(self.settings[ "thumbs_path" ]));
