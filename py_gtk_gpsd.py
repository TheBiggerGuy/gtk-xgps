#!/usr/bin/env python

# example helloworld.py

import pygtk
pygtk.require('2.0')
import gtk
import gobject

import gps
import socket

import time
import math

class SatWidget(gtk.DrawingArea):

    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.expose)
        self.context = None

    def expose(self, widget, event):
        self.context = widget.window.cairo_create()
        
        # set a clip region for the expose event
        self.context.rectangle(event.area.x, event.area.y,
                               event.area.width, event.area.height)
        self.context.clip()

        self.width = event.area.width
        self.height = event.area.height
        
        self.draw()
        
    def draw(self, satList=None):

        if self.context == None:
            return True

        context = self.context
        height = self.height
        width = self.width

        centerx = width/2
        centery = height/2
        small   = min(height, width)/4 - 10
        large   = small * 2

        # center dot
        context.set_source_rgb(0.0, 255, 0)
        context.arc(centerx, centery, 10 , 0, 2*math.pi)
        context.fill()

        # small
        context.set_source_rgb(0.0, 1.5, 0.5)
	context.set_line_width(2.0)
        context.arc(centerx, centery, small , 0, 2*math.pi)
        context.stroke()

        # large
        context.set_source_rgb(0.0, 0.5, 1.5)
	context.set_line_width(2.0)
        context.arc(centerx, centery, large, 0, 2*math.pi)
        context.stroke()

        # if sats
        if satList == None:
            return True

        for sat in satList:
            # work out loc
            x = centerx + (large * math.sin(sat.azimuth))
            y = centery + (large * math.cos(sat.azimuth))
            context.set_source_rgb(255, 255, 255)
            context.arc(x, y, 10 , 0, 2*math.pi)
            context.fill()

class GUI:

    def delete_event(self, widget, event, data=None):
        # If you return FALSE in the "delete_event" signal handler,
        # GTK will emit the "destroy" signal. Returning TRUE means
        # you don't want the window to be destroyed.
        # This is useful for popping up 'are you sure you want to quit?'
        # type dialogs.
        print "delete event occurred"

        # Change FALSE to TRUE and the main window will not be destroyed
        # with a "delete_event".
        return False

    def destroy(self, widget=None, data=None):
        print "destroy signal occurred"
        gtk.main_quit()
        exit()

    def __init__( self ):
        self.failCount = 0

        builder = gtk.Builder()
        builder.add_from_file( "glade.glade" )
        
        self.window       = builder.get_object( "window" )
        self.statusbar    = builder.get_object( "statusbar")
	self.label_raw    = builder.get_object( "label_raw" )

        self.entry_time		= builder.get_object( "entry_time" )
        self.entry_latitude	= builder.get_object( "entry_latitude" )
        self.entry_longitude	= builder.get_object( "entry_longitude" )
        self.entry_altitude	= builder.get_object( "entry_altitude" )
        self.entry_speed	= builder.get_object( "entry_speed" )
        self.entry_EPH  	= builder.get_object( "entry_EPH" )
        self.entry_EPV  	= builder.get_object( "entry_EPV" )
        self.entry_climb  	= builder.get_object( "entry_climb" )
        self.entry_track 	= builder.get_object( "entry_track" )
        self.entry_status  	= builder.get_object( "entry_status" )

        self.treeview     = builder.get_object( "treeview" )

        # now build the data modle for the right hand side list
        self.liststore_satList = gtk.ListStore(str, str, str, str, str)

        cell = gtk.CellRendererText()
        col1 = gtk.TreeViewColumn("PRN",	cell, text=0)
        col2 = gtk.TreeViewColumn("elevation",	cell, text=1)
        col3 = gtk.TreeViewColumn("azimuth",	cell, text=2)
        col4 = gtk.TreeViewColumn("ss",		cell, text=3)
        col5 = gtk.TreeViewColumn("used",	cell, text=4)

        self.treeview.append_column(col1)
        self.treeview.append_column(col2)
        self.treeview.append_column(col3)
        self.treeview.append_column(col4)
        self.treeview.append_column(col5)

        self.treeview.set_model(self.liststore_satList)

        self.image = SatWidget()
        builder.get_object( "hbox1" ).pack_start(self.image, expand=True, fill=True, padding=0)
        self.image.show_all()

        # connect signals
        builder.connect_signals(self)

    def on_timeout_update(self, *args):
        gpsd = self.gpsd

        if not gpsd.waiting():
            # no data so move on
            return True

        status = gpsd.poll()
        if status == -1:
            self.failCount = self.failCount + 1
            if self.failCount < 3:
                self.statusbar.push(self.statusbar.get_context_id("gpsd poll failed"), "Error, retrying")
                return True
            else:
                self.statusbar.push(self.statusbar.get_context_id("gpsd poll failed"), "Error, NOT retrying")
                return False

        # clean up the latitude
	if gpsd.fix.latitude == 0:
            latitude = str(gpsd.fix.latitude)
        elif gpsd.fix.latitude > 0:
            latitude = str(gpsd.fix.latitude) + " N"
        else:
            latitude = str( gpsd.fix.latitude * -1) + " S"

        # clean up the longitude
	if gpsd.fix.longitude == 0:
            longitude = str(gpsd.fix.longitude)
        elif gpsd.fix.longitude > 0:
            longitude = str(gpsd.fix.longitude) + " E"
        else:
            longitude = str(gpsd.fix.longitude * -1) + " W"

        self.entry_time.set_text(	str(gpsd.fix.time))
        self.entry_latitude.set_text(	    latitude)
        self.entry_longitude.set_text(	    longitude)
        self.entry_altitude.set_text(	str(gpsd.fix.altitude) + "m")
        self.entry_speed.set_text(	str(gpsd.fix.speed) + "m/s")

        self.entry_EPH.set_text(	str(gpsd.fix.eph))
        self.entry_EPV.set_text(	str(gpsd.fix.epv))
        self.entry_climb.set_text(	str(gpsd.fix.climb))
        self.entry_track.set_text(	str(gpsd.fix.track))

        self.entry_status.set_text(	("NO_FIX","FIX","DGPS_FIX")[gpsd.status])

        self.liststore_satList.clear()
        for sat in gpsd.satellites:
            self.liststore_satList.append([sat.PRN, sat.elevation, sat.azimuth, sat.ss, sat.used])

        #self.image.draw(gpsd.satellites)

        return True

    def updateRawString(self, newString):
        newString = newString.replace("\n", "") # lf
        newString = newString.replace("\r", "") # cr
        self.label_raw.set_label(newString)

    def main(self, gpsd):
        self.gpsd = gpsd
	self.gpsd.set_raw_hook(self.updateRawString)

        #set up the call back every 3 s
        gobject.timeout_add(3*1000, self.on_timeout_update)
        # and run now
        self.on_timeout_update()

	# and the window
        self.window.show()
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()

# If the program is run directly or passed as an argument to the python
# interpreter then create a HelloWorld instance and show it
if __name__ == "__main__":

    try:
        session = gps.gps(verbose=0)
    except socket.error, msg:
        print "Error: Cannot connect to gpsd. Python returned this meg \"" + str(msg) + "\""
	exit(-1)

    session.send("nmea")
    #session.send("raw")
    gui = GUI()
    gui.main(session)
