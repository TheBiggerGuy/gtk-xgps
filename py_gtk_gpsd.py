#!/usr/bin/env python

# example helloworld.py

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import cairo

import gps
import time

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
        self.drawingarea  = builder.get_object( "drawingarea" )

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

        self.entry_time.set_text(	str(gpsd.fix.time))
        self.entry_latitude.set_text(	str(gpsd.fix.latitude))
        self.entry_longitude.set_text(	str(gpsd.fix.longitude))
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

    session = gps.gps(verbose=0)
    session.send("nmea")
    session.send("raw")
    gui = GUI()
    gui.main(session)
