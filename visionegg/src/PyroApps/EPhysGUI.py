#!/usr/bin/env python

# Copyright (c) 2002-2003 Andrew Straw.  Distributed under the terms
# of the GNU Lesser General Public License (LGPL).

import VisionEgg, string
__version__ = VisionEgg.release_name
__cvs__ = string.split('$Revision$')[1]
__date__ = string.join(string.split('$Date$')[1:3], ' ')
__author__ = 'Andrew Straw <astraw@users.sourceforge.net>'

import sys, socket, re, time, string, types, os
import pickle, random, math, threading
import Tkinter, tkMessageBox, tkSimpleDialog, tkFileDialog
import StringIO
import Pyro
import Numeric

import VisionEgg
import VisionEgg.PyroClient
import VisionEgg.PyroApps.ScreenPositionGUI
import VisionEgg.GUI

# Add your client modules here
import VisionEgg.PyroApps.TargetGUI
import VisionEgg.PyroApps.MouseTargetGUI
import VisionEgg.PyroApps.FlatGratingGUI
import VisionEgg.PyroApps.SphereGratingGUI
import VisionEgg.PyroApps.SpinningDrumGUI
import VisionEgg.PyroApps.GridGUI
import VisionEgg.PyroApps.ColorCalGUI

client_list = []
client_list.extend( VisionEgg.PyroApps.TargetGUI.get_control_list() )
client_list.extend( VisionEgg.PyroApps.MouseTargetGUI.get_control_list() )
client_list.extend( VisionEgg.PyroApps.FlatGratingGUI.get_control_list() )
client_list.extend( VisionEgg.PyroApps.SphereGratingGUI.get_control_list() )
client_list.extend( VisionEgg.PyroApps.SpinningDrumGUI.get_control_list() )
client_list.extend( VisionEgg.PyroApps.GridGUI.get_control_list() )
client_list.extend( VisionEgg.PyroApps.ColorCalGUI.get_control_list() )

class ContainedObjectBase:
    """Base class to encapsulate objects, provides useful methods when used in GUI"""
    def __init__(self):
        raise RuntimeError("Abstract base class!")
    def get_str_30(self):
        return "**** this is a generic str_30 ****"
    def get_contained(self):
        return self.contained
    header = "unknown parameters"

class ScrollListFrame(Tkinter.Frame):
    def __init__(self,master=None,list_of_contained_objects=None,contained_objectbject_maker=None,
                 container_class=ContainedObjectBase,
                 **cnf):
        Tkinter.Frame.__init__(self, master, **cnf)
        if list_of_contained_objects is None:
            self.list = []
        else:
            self.list = list_of_contained_objects
        self.container_class = container_class

        # allow column to expand
        self.columnconfigure(0,weight=1)

        # The frame that has the list and the vscroll
        self.frame = Tkinter.Frame(self,borderwidth=2)
        self.frame.grid(row=0,sticky="nwes")
        
        # allow column to expand
        self.frame.columnconfigure(0,weight=1)

        self.frame.vscroll = Tkinter.Scrollbar(self.frame,orient=Tkinter.VERTICAL)
        self.frame.hscroll = Tkinter.Scrollbar(self.frame,orient=Tkinter.HORIZONTAL)
        self.frame.title = Tkinter.Listbox(
            self.frame,
            relief=Tkinter.FLAT,
            font=('courier',10,'bold'),
            height=1,
#            selectbackground='#eed5b7',
#            selectborderwidth=0,
#            selectmode=None,
            exportselection=0)
        self.frame.title.insert(Tkinter.END, self.container_class.header)
        self.frame.list = Tkinter.Listbox(
            self.frame,
            relief=Tkinter.SUNKEN,
            font=('courier',10,'normal'),
            width=40, height=3,
            selectbackground='#eed5b7',
            selectborderwidth=0,
            selectmode=Tkinter.BROWSE,
            xscroll=self.frame.hscroll.set,
            yscroll=self.frame.vscroll.set,
            exportselection=0)

        self.frame.hscroll['command'] = self.delegate_hscroll
        self.frame.hscroll.grid(row=3,column=0,sticky='we')
        self.frame.vscroll['command'] = self.frame.list.yview
        self.frame.vscroll.grid(row=2,column=1,sticky='ns')
        self.frame.title.grid(row=1,column=0,ipady=0,pady=0,sticky='we')
        self.frame.list.grid(row=2,column=0,sticky='nwes')
        self.frame.list.bind('<Double-Button-1>',self.edit_selected)
        
        # The buttons on bottom
        self.bar = Tkinter.Frame(self,borderwidth=2)
        self.bar.grid(row=1,sticky="we")
        self.bar.add = Tkinter.Button(self.bar,text='Add...',command=self.add_new)
        self.bar.add.grid(row=0,column=0,sticky='we')
        self.bar.edit = Tkinter.Button(self.bar,text='Edit...',command=self.edit_selected)
        self.bar.edit.grid(row=0,column=1,sticky='we')
        self.bar.remove = Tkinter.Button(self.bar,text='Remove',command=self.remove_selected)
        self.bar.remove.grid(row=0,column=2,sticky='we')
        self.bar.move_up = Tkinter.Button(self.bar,text='Up',command=self.move_selected_up)
        self.bar.move_up.grid(row=0,column=3,sticky='we')
        self.bar.move_down = Tkinter.Button(self.bar,text='Down',command=self.move_selected_down)
        self.bar.move_down.grid(row=0,column=4,sticky='we')
        self.bar.tk_menuBar(self.bar.add,self.bar.remove)
        self.update_now()

    def delegate_hscroll(self,*args,**kw):
        self.frame.title.xview(*args,**kw)
        self.frame.list.xview(*args,**kw)
        
    def get_list_uncontained(self):
        results = []
        for contained_object_item in self.list:
            results.append( contained_object_item.get_contained() )
        return results

    def update_now(self):
        self.frame.list.delete(0,Tkinter.END)
        max_len = 0
        for item in self.list:
            item_str_30 = item.get_str_30()
            max_len = max(max_len,len(item_str_30))
            self.frame.list.insert(Tkinter.END,item_str_30)

        self.frame.title.delete(0,Tkinter.END)
        self.frame.title.insert(Tkinter.END, self.container_class.header.ljust(max_len))

    def add_new(self):
        contained_object = self.make_contained_object(self.container_class)
        if contained_object:
            self.list.append( contained_object )
        self.update_now()

    def edit_selected(self,dummy_arg=None):
        selected = self.get_selected()
        if selected is not None:
            orig_contained_object = self.list[selected]
            modified_contained_object = self.edit_contained_object( orig_contained_object )
            if modified_contained_object is not None: # "Cancel" press results in None
                self.list[selected] = modified_contained_object
            self.update_now()

    def remove_selected(self):
        selected = self.get_selected()
        if selected is not None:
            del self.list[selected]
            self.update_now()

    def move_selected_up(self,dummy_arg=None):
        selected = self.get_selected()
        if selected is not None:
            selected_object = self.list[selected]
            del self.list[selected]
            new_index = max(selected-1,0)
            self.list.insert(new_index, selected_object)
            self.update_now()
        self.frame.list.selection_set(new_index)

    def move_selected_down(self,dummy_arg=None):
        selected = self.get_selected()
        if selected is not None:
            selected_object = self.list[selected]
            del self.list[selected]
            new_index = min(selected+1,len(self.list))
            self.list.insert(new_index, selected_object)
            self.update_now()
        self.frame.list.selection_set(new_index)

    def make_contained_object(self, container_class):
        """Factory function for ContainedObjectBase"""
        if container_class == LoopContainedObject:
            return self.make_loop_contained_object()
        params = {}
        p = container_class.contained_class.parameters_and_defaults
        keys = p.keys()
        keys.sort()
        for pname in keys:
            if p[pname][1] == types.StringType:
                params[pname] = tkSimpleDialog.askstring(pname,pname,initialvalue=p[pname][0])
            elif p[pname][1] == types.IntType:
                params[pname] = tkSimpleDialog.askinteger(pname,pname,initialvalue=p[pname][0])
            elif p[pname][1] == types.FloatType:
                params[pname] = tkSimpleDialog.askfloat(pname,pname,initialvalue=p[pname][0])
            elif p[pname][1] == types.ListType:
                params[pname] = eval("["+tkSimpleDialog.askstring(pname,pname,initialvalue="1,2,3")+"]")
                if type(params[pname]) is not types.ListType:
                    params[pname] = [666] # XXX
            else:
                raise NotImplementedError("Don't know about type %s"%(p[pname][1],))
            if params[pname] is None:
                raise RuntimeError("Input cancelled")
        contained = container_class.contained_class(**params) # call constructor
        return container_class(contained)

    def edit_contained_object(self, contained_object):
        if not isinstance(contained_object,LoopContainedObject):
            raise NotImplementedError("")
        orig_contained = contained_object.get_contained()
        d = LoopParamDialog(self, title="Loop Parameters", orig_values=orig_contained )
        if d.result:
            return LoopContainedObject(d.result)
        else:
            return

    def make_loop_contained_object(self):
        d = LoopParamDialog(self, title="Loop Parameters" )
        if d.result:
            return LoopContainedObject(d.result)
        else:
            return

    def get_selected(self):
        items = self.frame.list.curselection()
        try:
            items = map(int, items)
        except ValueError: pass
        if len(items) > 0:
            return items[0]
        else:
            return None

###################################################

class Loop(VisionEgg.ClassWithParameters):
    parameters_and_defaults = {'variable':('<repeat>',
                                           types.StringType),
                               'sequence':([1, 1, 1],
                                           types.ListType),
                               'rest_duration_sec':(1.0,
                                                    types.FloatType)}
    def __init__(self,**kw):
        VisionEgg.ClassWithParameters.__init__(self,**kw)
        self.num_done = 0
    def is_done(self):
        return self.num_done >= len(self.parameters.sequence)
    def get_current(self):
        return self.parameters.sequence[self.num_done]
    def advance(self):
        self.num_done += 1
    def reset(self):
        self.num_done = 0

class LoopContainedObject(ContainedObjectBase):
    """Contrainer for Loop class"""
    contained_class = Loop
    header = "     variable    rest   N  values"
    def __init__(self,contained=None):
        self.contained = contained
    def get_str_30(self):
        p = self.contained.parameters
        seq_str = ""
        for val in p.sequence:
            seq_str += str(val) + " "
        name_str = p.variable
        if len(name_str) > 15:
            name_str = name_str[:15]
        return "% 15s % 4s % 4d  %s"%(name_str, str(p.rest_duration_sec), len(p.sequence), seq_str)

class LoopParamDialog(tkSimpleDialog.Dialog):
    def __init__(self,*args,**kw):
        #intercept orig_values argument
        if 'orig_values' in kw.keys():
            self.orig_values = kw['orig_values']
            del kw['orig_values']
        else:
            self.orig_values = None
        return tkSimpleDialog.Dialog.__init__(*(self,)+args, **kw )
        
    def body(self,master):
        Tkinter.Label(master,
                      text="Add sequence of automatic variable values",
                      font=("Helvetica",12,"bold"),).grid(row=0,column=0,columnspan=2)

        var_frame = Tkinter.Frame(master)
        var_frame.grid(row=1,column=0)

        sequence_frame = Tkinter.Frame(master)
        sequence_frame.grid(row=1,column=1)

        rest_dur_frame = Tkinter.Frame(master)
        rest_dur_frame.grid(row=2,column=0,columnspan=2)

        # loopable variable frame stuff
        var_frame_row = 0
        Tkinter.Label(var_frame,
                      text="Select a variable",
                      font=("Helvetica",12,"bold"),).grid(row=var_frame_row)
        
        self.var_name = Tkinter.StringVar()
        self.var_name.set("<repeat>")
        global loopable_variables
        var_names = loopable_variables[:] # copy
        var_names.sort()

        var_frame_row += 1
        Tkinter.Radiobutton( var_frame,
                     text="Repeat (Average)",
                     variable=self.var_name,
                     value="<repeat>",
                     anchor=Tkinter.W).grid(row=var_frame_row,sticky="w")
        var_frame_row += 1
        for var_name in var_names:
            Tkinter.Radiobutton( var_frame,
                                 text=var_name,
                                 variable=self.var_name,
                                 value=var_name,
                                 anchor=Tkinter.W).grid(row=var_frame_row,sticky="w")
            var_frame_row += 1

        # sequence entry frame
        seq_row = 0
        Tkinter.Label(sequence_frame,
                      text="Sequence values",
                      font=("Helvetica",12,"bold"),).grid(row=seq_row,column=0,columnspan=2)
        
        seq_row += 1
        self.sequence_type = Tkinter.StringVar()
        self.sequence_type.set("manual")

        Tkinter.Radiobutton( sequence_frame,
                     text="Manual:",
                     variable=self.sequence_type,
                     value="manual",
                     anchor=Tkinter.W).grid(row=seq_row,column=0,sticky="w")

        self.sequence_manual_string = Tkinter.StringVar()
        self.sequence_manual_string.set("[1,2,3]")
        Tkinter.Entry(sequence_frame,
                      textvariable=self.sequence_manual_string).grid(row=seq_row,column=1)

        seq_row += 1
        Tkinter.Radiobutton( sequence_frame,
                     text="Linear:",
                     variable=self.sequence_type,
                     value="linear",
                     anchor=Tkinter.W).grid(row=seq_row,column=0,sticky="w")

        self.lin_start_tk = Tkinter.DoubleVar()
        self.lin_start_tk.set(1.0)
        self.lin_stop_tk = Tkinter.DoubleVar()
        self.lin_stop_tk.set(100.0)
        self.lin_n_tk = Tkinter.IntVar()
        self.lin_n_tk.set(3)

        lin_frame = Tkinter.Frame( sequence_frame)
        lin_frame.grid(row=seq_row,column=1)
        Tkinter.Label(lin_frame,text="start:").grid(row=0,column=0)
        Tkinter.Entry(lin_frame,textvariable=self.lin_start_tk,width=6).grid(row=0,column=1)
        Tkinter.Label(lin_frame,text="  stop:").grid(row=0,column=2)
        Tkinter.Entry(lin_frame,textvariable=self.lin_stop_tk,width=6).grid(row=0,column=3)
        Tkinter.Label(lin_frame,text="  N:").grid(row=0,column=4)
        Tkinter.Entry(lin_frame,textvariable=self.lin_n_tk,width=6).grid(row=0,column=5)

        seq_row += 1
        Tkinter.Radiobutton( sequence_frame,
                     text="Log:",
                     variable=self.sequence_type,
                     value="log",
                     anchor=Tkinter.W).grid(row=seq_row,column=0,sticky="w")

        self.log_start_tk = Tkinter.DoubleVar()
        self.log_start_tk.set(-1.0)
        self.log_stop_tk = Tkinter.DoubleVar()
        self.log_stop_tk.set(2.0)
        self.log_n_tk = Tkinter.IntVar()
        self.log_n_tk.set(5)

        log_frame = Tkinter.Frame( sequence_frame)
        log_frame.grid(row=seq_row,column=1)
        Tkinter.Label(log_frame,text="start: 10^").grid(row=0,column=0)
        Tkinter.Entry(log_frame,textvariable=self.log_start_tk,width=6).grid(row=0,column=1)
        Tkinter.Label(log_frame,text="  stop: 10^").grid(row=0,column=2)
        Tkinter.Entry(log_frame,textvariable=self.log_stop_tk,width=6).grid(row=0,column=3)
        Tkinter.Label(log_frame,text="  N:").grid(row=0,column=4)
        Tkinter.Entry(log_frame,textvariable=self.log_n_tk,width=6).grid(row=0,column=5)

        seq_row += 1
        Tkinter.Radiobutton( sequence_frame,
                     text="Log:",
                     variable=self.sequence_type,
                     value="logb",
                     anchor=Tkinter.W).grid(row=seq_row,column=0,sticky="w")

        self.logb_start_tk = Tkinter.DoubleVar()
        self.logb_start_tk.set(0.1)
        self.logb_stop_tk = Tkinter.DoubleVar()
        self.logb_stop_tk.set(100.0)
        self.logb_n_tk = Tkinter.IntVar()
        self.logb_n_tk.set(5)

        logb_frame = Tkinter.Frame( sequence_frame)
        logb_frame.grid(row=seq_row,column=1)
        Tkinter.Label(logb_frame,text="start:").grid(row=0,column=0)
        Tkinter.Entry(logb_frame,textvariable=self.logb_start_tk,width=6).grid(row=0,column=1)
        Tkinter.Label(logb_frame,text="  stop:").grid(row=0,column=2)
        Tkinter.Entry(logb_frame,textvariable=self.logb_stop_tk,width=6).grid(row=0,column=3)
        Tkinter.Label(logb_frame,text="  N:").grid(row=0,column=4)
        Tkinter.Entry(logb_frame,textvariable=self.logb_n_tk,width=6).grid(row=0,column=5)

        # rest duration frame
        Tkinter.Label(rest_dur_frame,
                      text="Other sequence parameters",
                      font=("Helvetica",12,"bold"),).grid(row=0,column=0,columnspan=2)

        Tkinter.Label(rest_dur_frame,
                      text="Interval duration (seconds)").grid(row=1,column=0)
        self.rest_dur = Tkinter.DoubleVar()
        self.rest_dur.set(0.5)
        Tkinter.Entry(rest_dur_frame,
                      textvariable=self.rest_dur,
                      width=10).grid(row=1,column=1)

        self.shuffle_tk_var = Tkinter.BooleanVar()
        self.shuffle_tk_var.set(0)
        Tkinter.Checkbutton( rest_dur_frame,
                             text="Shuffle sequence order",
                             variable=self.shuffle_tk_var).grid(row=2,column=0,columnspan=2)
                             
        if self.orig_values is not None:
            self.var_name.set( self.orig_values.parameters.variable )
            
            self.sequence_manual_string.set( str(self.orig_values.parameters.sequence) )
            
            self.rest_dur.set( self.orig_values.parameters.rest_duration_sec )
            

    def validate(self):
        if self.sequence_type.get() == "manual":
            try:
                seq = eval(self.sequence_manual_string.get())
            except Exception, x:
                tkMessageBox.showwarning("Invalid sequence parameters",
                                         "Manual sequence entry: %s"%(str(x),),
                                         parent=self)
                return 0
            if type(seq) != types.ListType:
                tkMessageBox.showwarning("Invalid sequence parameters",
                                         "Manual sequence entry: Not a list",
                                         parent=self)
                return 0
        elif self.sequence_type.get() == "linear":
            start = self.lin_start_tk.get()
            stop = self.lin_stop_tk.get()
            n = self.lin_n_tk.get()
            if n < 2:
                tkMessageBox.showwarning("Invalid sequence parameters",
                                         "Must have n >= 2.",
                                         parent=self)
                return 0

            incr = (stop-start)/float(n-1)
            seq = range(n)
            for i in range(n):
                seq[i] = i*incr + start
        elif self.sequence_type.get() == "log":
            start = self.log_start_tk.get()
            stop = self.log_stop_tk.get()
            n = self.log_n_tk.get()
            if n < 2:
                tkMessageBox.showwarning("Invalid sequence parameters",
                                         "Must have n >= 2.",
                                         parent=self)
                return 0

            incr = (stop-start)/float(n-1)
            seq = range(n)
            for i in range(n):
                seq[i] = 10.0**( i*incr + start )
        elif self.sequence_type.get() == "logb":
            start = self.logb_start_tk.get()
            stop = self.logb_stop_tk.get()
            start = math.log10(start)
            stop = math.log10(stop)
            n = self.logb_n_tk.get()
            if n < 2:
                tkMessageBox.showwarning("Invalid sequence parameters",
                                         "Must have n >= 2.",
                                         parent=self)
                return 0
            incr = (stop-start)/float(n-1)
            seq = range(n)
            for i in range(n):
                seq[i] = 10.0**( i*incr + start )
        else:
            tkMessageBox.showwarning("Invalid sequence parameters",
                                     "Invalid sequence type.",
                                     parent=self)
            return 0
        rest_dur_sec = self.rest_dur.get()

        if self.shuffle_tk_var.get():
            random.shuffle(seq)
            
        self.result = Loop(variable=self.var_name.get(),
                           sequence=seq,
                           rest_duration_sec=rest_dur_sec)
        return 1
    
    def destroy(self):
        # clear tk variables
        self.var_name = None
        self.sequence_type = None
        self.sequence_manual_string = None
        self.rest_dur = None
        # call master's destroy method
        tkSimpleDialog.Dialog.destroy(self)

def get_server(hostname="",port=7766):
    class ConnectWindow(Tkinter.Frame):
        def __init__(self,master=None,hostname="",port=7766,**kw):
            Tkinter.Frame.__init__(self,master, **kw)
            self.winfo_toplevel().title("EPhysGUI Connect - Vision Egg")
            current_row = 0
            Tkinter.Message(self,\
                          text='Welcome to the "EPhys GUI" of the Vision Egg!\n\n'+\
                          'Please enter the hostname '+\
                          'and port number '+\
                          'of the computer on which you have the '+\
                          '"EPhys server" running.').grid(row=current_row,column=0,columnspan=2)
            hostname = socket.getfqdn(hostname)

            self.hostname_tk = Tkinter.StringVar()
            self.hostname_tk.set(hostname)
            current_row += 1
            Tkinter.Label(self,text="Hostname:").grid(row=current_row, column=0)
            Tkinter.Entry(self,textvariable=self.hostname_tk).grid(row=current_row, column=1)
          
            self.port_tk = Tkinter.IntVar()
            self.port_tk.set(port)
            current_row += 1
            Tkinter.Label(self,text="Port:").grid(row=current_row, column=0)
            Tkinter.Entry(self,textvariable=self.port_tk).grid(row=current_row, column=1)

            current_row += 1
            bf = Tkinter.Frame(self)
            bf.grid(row=current_row,column=0,columnspan=2)
            ok=Tkinter.Button(bf,text="OK",command=self.ok)
            ok.grid(row=0,column=0)
            ok.focus_force()
            ok.bind('<Return>',self.ok)
            Tkinter.Button(bf,text="Cancel",command=self.quit).grid(row=0,column=1)
            self.result = None
            
        def ok(self,dummy_arg=None):
            self.result = (self.hostname_tk.get(),self.port_tk.get())
            self.destroy()
            self.quit()
            
    connect_win = ConnectWindow(hostname=hostname,port=port)
    connect_win.pack()
    connect_win.mainloop()
    return connect_win.result

class GammaFrame(Tkinter.Frame):
    def __init__(self,
                 master=None,
                 ephys_server=None,**kw):
        Tkinter.Frame.__init__(self,master,**kw)
        self.winfo_toplevel().title("Gamma - Vision Egg")
        self.ephys_server = ephys_server
        
        self.columnconfigure(0,weight=1)

        row = 0
        Tkinter.Label(self,
                      font=("Helvetica",12,"bold"),
                      text="Load Gamma Table").grid(row=row)

        row += 1
        Tkinter.Button(self,
                       text="Set from .ve_gamma file...",
                       command=self.set_from_file).grid(row=row,sticky="w")

        row += 1
        Tkinter.Button(self,
                       text="Set to monitor default (linear gamma table)",
                       command=self.set_monitor_default).grid(row=row,sticky="w")

        row += 1
        invert_frame = Tkinter.Frame(self)
        invert_frame.grid(row=row,sticky="we")

        Tkinter.Button(invert_frame,
                       text="Linearize luminance for gammas",
                       command=self.linearize).grid(row=0,column=0)

        Tkinter.Label(invert_frame,
                      text="Red:").grid(row=0,column=1)

        self.red_gamma = Tkinter.DoubleVar()
        self.red_gamma.set(2.2)

        Tkinter.Entry(invert_frame,
                      textvariable=self.red_gamma,
                      width=5).grid(row=0,column=2)

        Tkinter.Label(invert_frame,
                      text="Green:").grid(row=0,column=3)

        self.green_gamma = Tkinter.DoubleVar()
        self.green_gamma.set(2.2)

        Tkinter.Entry(invert_frame,
                      textvariable=self.green_gamma,
                      width=5).grid(row=0,column=4)

        Tkinter.Label(invert_frame,
                      text="Blue:").grid(row=0,column=5)

        self.blue_gamma = Tkinter.DoubleVar()
        self.blue_gamma.set(2.2)

        Tkinter.Entry(invert_frame,
                      textvariable=self.blue_gamma,
                      width=5).grid(row=0,column=6)

        row += 1
        self.success_label = Tkinter.Label(self)
        self.success_label.grid(row=row)

    def get_corrected_gamma_table(self,gamma):
        # c is a constant scale factor.  It is always 1.0 when
        # luminance is normalized to range [0.0,1.0] and input units
        # in range [0.0,1.0], as is OpenGL standard.
        c = 1.0
        inc = 1.0/255
        target_luminances = Numeric.arange(0.0,1.0+inc,inc)
        output_ramp = Numeric.zeros(target_luminances.shape,Numeric.Int)
        for i in range(len(target_luminances)):
            L = target_luminances[i]
            if L == 0.0:
                v_88fp = 0
            else:
                v = math.exp( (math.log(L) - math.log(c)) /gamma)
                v_88fp = int(round((v*255) * 256)) # convert to from [0.0,1.0] floating point to [0.0,255.0] 8.8 fixed point
            output_ramp[i] = v_88fp # 8.8 fixed point format
        return list(output_ramp) # convert to Python list

    def linearize(self, dummy_arg=None):
        self.success_label.configure(text="Setting...")
        try:
            red = self.get_corrected_gamma_table(self.red_gamma.get())
            green = self.get_corrected_gamma_table(self.green_gamma.get())
            blue = self.get_corrected_gamma_table(self.blue_gamma.get())
        except:
            self.success_label.configure(text="Calculation error")
            raise
        try:
            if self.ephys_server.set_gamma_ramp(red,green,blue):
                self.success_label.configure(text="Success")
            else:
                self.success_label.configure(text="Failed: Invalid gamma values?")
        except Exception,x:
            self.success_label.configure(text="Failed: %s: %s"%(x.__class__,str(x)))
            raise

    def set_monitor_default(self, dummy_arg=None):
        self.success_label.configure(text="Setting...")
        try:
            red = self.get_corrected_gamma_table(1.0) # linear gamma table
        except:
            self.success_label.configure(text="Calculation error")
            raise
        green = red
        blue = red
        try:
            if self.ephys_server.set_gamma_ramp(red,green,blue):
                self.success_label.configure(text="Success")
            else:
                self.success_label.configure(text="Failed: Invalid gamma values?")
        except Exception,x:
            self.success_label.configure(text="Failed: %s: %s"%(x.__class__,str(x)))
            raise

    def set_from_file(self):
        self.success_label.configure(text="Setting...")
        filename = tkFileDialog.askopenfilename(
            parent=self,
            defaultextension=".ve_gamma",
            filetypes=[('Configuration file','*.ve_gamma')],
            initialdir=VisionEgg.config.VISIONEGG_USER_DIR)
        if not filename:
            self.success_label.configure(text="No file given")
            return
        fd = open(filename,"r")
        gamma_values = []
        for line in fd.readlines():
            line = line.strip() # remove leading/trailing whitespace
            if line.startswith("#"): # comment, ignore
                continue
            try:
                gamma_values.append( map(int, line.split() ) )
            except Exception, x:
                self.success_label.configure(text="File error")
                raise
            if len(gamma_values[-1]) != 3:
                self.success_label.configure(text="File error")
                raise RuntimeError("expected 3 values per gamma entry")
        if len(gamma_values) != 256:
            self.success_label.configure(text="File error")
            raise RuntimeError("expected 256 gamma entries")
        red, green, blue = zip(*gamma_values)
        try:
            if self.ephys_server.set_gamma_ramp(red,green,blue):
                self.success_label.configure(text="Success")
            else:
                self.success_label.configure(text="Failed: Invalid gamma values?")
        except Exception,x:
            self.success_label.configure(text="Failed: %s: %s"%(x.__class__,str(x)))
            raise
            
class ImageSequenceLauncher(Tkinter.Toplevel):
    def __init__(self,master=None,ephys_server=None,**cnf):
        Tkinter.Toplevel.__init__(self,master,**cnf)
        if ephys_server is None:
            raise ValueError("Must specify ephys_server")
        self.ephys_server = ephys_server

        self.columnconfigure(1,weight=1)
        
        row = 0
        Tkinter.Label(self,text="Frames per second").grid(row=row,column=0)
        self.fps_var = Tkinter.DoubleVar()
        self.fps_var.set(12.0)
        Tkinter.Entry(self,textvariable=self.fps_var).grid(row=row,column=1,sticky="we")
        row += 1
        Tkinter.Label(self,text="Filename base").grid(row=row,column=0)
        self.filename_base = Tkinter.StringVar()
        self.filename_base.set("im")
        Tkinter.Entry(self,textvariable=self.filename_base).grid(row=row,column=1,sticky="we")
        row += 1
        Tkinter.Label(self,text="Filename suffix").grid(row=row,column=0)
        self.filename_suffix = Tkinter.StringVar()
        self.filename_suffix.set(".tif")
        Tkinter.Entry(self,textvariable=self.filename_suffix).grid(row=row,column=1,sticky="we")
        row += 1
        Tkinter.Label(self,text="Save directory on server").grid(row=row,column=0)
        self.server_save_dir = Tkinter.StringVar()
        server_dir = self.ephys_server.get_cwd()
        self.server_save_dir.set(server_dir)
        Tkinter.Entry(self,textvariable=self.server_save_dir).grid(row=row,column=1,sticky="we")
        row += 1
        Tkinter.Button(self,text="Save movie",command=self.do_it).grid(row=row,column=0,columnspan=2)
        self.focus_set()
        self.grab_set()
    def do_it(self):
        fps = self.fps_var.get()
        filename_base = self.filename_base.get()
        filename_suffix = self.filename_suffix.get()
        server_save_dir = self.server_save_dir.get()
        self.ephys_server.save_image_sequence(fps=fps,
                                              filename_base=filename_base,
                                              filename_suffix=filename_suffix,
                                              save_dir=server_save_dir)
        self.destroy()
        
class AppWindow(Tkinter.Frame):
    def __init__(self,
                 master=None,
                 client_list=None,
                 server_hostname='',
                 server_port=7766,
                 **cnf):
        # Keep original exception handler
        self._orig_report_callback_exception = Tkinter.Tk.report_callback_exception
        self._tk = Tkinter.Tk
        # Use Vision Egg exception handler
        Tkinter.Tk.report_callback_exception = VisionEgg._exception_hook_keeper.handle_exception
        
        # create myself
        Tkinter.Frame.__init__(self,master, **cnf)
        self.winfo_toplevel().title("EPhysGUI - Vision Egg")

        self.client_list = client_list

        self.server_hostname = server_hostname
        self.server_port = server_port
        
        self.pyro_client = VisionEgg.PyroClient.PyroClient(self.server_hostname,self.server_port)
        self.ephys_server = self.pyro_client.get("ephys_server")
        self.ephys_server.first_connection()

        self.stim_onset_cal_tk_var = Tkinter.BooleanVar()
        self.stim_onset_cal_tk_var.set(0)

        self.autosave_dir = Tkinter.StringVar()
        self.autosave_dir.set( os.path.abspath(os.curdir) )
        
        self.autosave_basename = Tkinter.StringVar()

        # create menu bar
        self.bar = Tkinter.Menu(tearoff=0)
        top = self.winfo_toplevel()
        top.configure(menu=self.bar)
        
        self.bar.file_menu = Tkinter.Menu(self.bar, name="file_menu")
        self.bar.add_cascade(label="File",menu=self.bar.file_menu)

        self.bar.file_menu.add_command(label='Save image sequence...', command=self.save_image_sequence)
        self.bar.file_menu.add_command(label='Save configuration file...', command=self.save_config)
        self.bar.file_menu.add_command(label='Load configuration file...', command=self.load_config)
        self.bar.file_menu.add_command(label='Load auto-saved .py parameter file...', command=self.load_params)
##        if sys.platform == 'win32':
##            quit_accelerator = "Ctrl-Q"
##        elif sys.platform == 'darwin':
##            quit_accelerator = "Command-Q"
##        else:
##            quit_accelerator = None
        self.bar.file_menu.add_command(label='Quit',
                                       command=self.quit,
#                                       accelerator=quit_accelerator
                                       )
        
        stimkey = self.ephys_server.get_stimkey()
        self.stimulus_tk_var = Tkinter.StringVar()
        self.stimulus_tk_var.set( stimkey )

        self.bar.stimuli_menu = Tkinter.Menu(self.bar, name="stimuli_menu")
        self.bar.add_cascade(label="Stimuli",menu=self.bar.stimuli_menu)
        for maybe_stimkey, maybe_control_frame, maybe_title in self.client_list:
            self.bar.stimuli_menu.add_radiobutton(label=maybe_title,
                                                  command=self.change_stimulus,
                                                  variable=self.stimulus_tk_var,
                                                  value=maybe_stimkey)

        self.bar.calibration_menu = Tkinter.Menu(self.bar, name="calibration_menu")
        self.bar.add_cascade(label="Configure/Calibrate",
                             menu=self.bar.calibration_menu)
        
        self.bar.calibration_menu.add_command(label='3D Perspective...', command=self.launch_screen_pos)
        self.bar.calibration_menu.add_command(label='Stimulus onset timing...', command=self.launch_stim_onset_cal)
        self.bar.calibration_menu.add_command(label='Load gamma table...', command=self.launch_gamma_panel)
        self.notify_on_dropped_frames = Tkinter.BooleanVar()
        self.notify_on_dropped_frames.set(1)
        self.bar.calibration_menu.add_checkbutton(label='Warn on frame skip',
                                                  variable=self.notify_on_dropped_frames)

        row = 0

        # options for self.stim_frame in grid layout manager
        self.stim_frame_cnf = {'row':row,
                               'column':0,
                               'columnspan':2,
                               'sticky':'nwes'}
        
        row += 1
        Tkinter.Label(self,
                      text="Sequence information",
                      font=("Helvetica",12,"bold")).grid(row=row,column=0)
        row += 1
        # options for self.loop_frame in grid layout manager
        self.loop_frame_cnf = {'row':row,
                               'column':0,
                               'sticky':'nwes'}

        row -= 1
        Tkinter.Label(self,
                      text="Parameter Save Options",
                      font=("Helvetica",12,"bold")).grid(row=row,column=1)
        row += 1
        self.auto_save_frame = Tkinter.Frame(self)
        asf = self.auto_save_frame # shorthand
        asf.grid(row=row,column=1,sticky="nwes")
        asf.columnconfigure(1,weight=1)

        asf.grid_row = 0
        self.autosave = Tkinter.BooleanVar()
        self.autosave.set(1)
        self.auto_save_button = Tkinter.Checkbutton(asf,
                                                    text="Auto save trial parameters",
                                                    variable=self.autosave)
        self.auto_save_button.grid(row=asf.grid_row,column=0,columnspan=2)

        self.param_file_type_tk_var = Tkinter.StringVar()
        self.param_file_type_tk_var.set("Python format")
        filetype_bar = Tkinter.Menubutton(asf,
                                 textvariable=self.param_file_type_tk_var,
                                 relief=Tkinter.RAISED)
        filetype_bar.grid(row=asf.grid_row,column=2)
        filetype_bar.menu = Tkinter.Menu(filetype_bar,tearoff=0)
        filetype_bar.menu.add_radiobutton(label="Python format",
                                 value="Python format",
                                 variable=self.param_file_type_tk_var)
        filetype_bar.menu.add_radiobutton(label="Matlab format",
                                 value="Matlab format",
                                 variable=self.param_file_type_tk_var)
        filetype_bar['menu'] = filetype_bar.menu
        
        asf.grid_row += 1
        Tkinter.Label(asf,
                      text="Parameter file directory:").grid(row=asf.grid_row,column=0,sticky="e")
        Tkinter.Entry(asf,
                      textvariable=self.autosave_dir).grid(row=asf.grid_row,column=1,sticky="we")
        Tkinter.Button(asf,
                       text="Set...",command=self.set_autosave_dir).grid(row=asf.grid_row,column=2)
        asf.grid_row += 1
        Tkinter.Label(asf,
                      text="Parameter file basename:").grid(row=asf.grid_row,column=0,sticky="e")
        Tkinter.Entry(asf,
                      textvariable=self.autosave_basename).grid(row=asf.grid_row,column=1,sticky="we")
        Tkinter.Button(asf,
                       text="Reset",command=self.reset_autosave_basename).grid(row=asf.grid_row,column=2)
        
        row += 1
        Tkinter.Button(self, text='Do single trial', command=self.do_single_trial).grid(row=row,column=0)
        Tkinter.Button(self, text='Do sequence', command=self.do_loops).grid(row=row,column=1)

        row += 1
        self.progress = VisionEgg.GUI.ProgressBar(self,
                                                  width=300,
                                                  relief="sunken",
                                                  doLabel=0,
                                                  labelFormat="%s")
        self.progress.labelText = "Starting..."
        self.progress.updateProgress(0)
        self.progress.grid(row=row,column=0,columnspan=2)#,sticky='we')

        # Allow rows and columns to expand
        for i in range(2):
            self.columnconfigure(i,weight=1)
        for i in range(row+1):
            self.rowconfigure(i,weight=1)

        self.switch_to_stimkey( stimkey )

    def __del__( self ):
        self._tk.report_callback_exception = self._orig_report_callback_exception

    def switch_to_stimkey( self, stimkey ):
        success = 0
        for maybe_stimkey, maybe_control_frame, maybe_title in self.client_list:
            if stimkey == maybe_stimkey:
                control_frame_klass = maybe_control_frame
                success = 1

        if not success:
            raise RuntimeError("Could not find valid client for server stimkey %s"%stimkey)

        if hasattr(self, 'stim_frame'):
            # clear old frame
            self.stim_frame.destroy()
            del self.stim_frame

        self.stim_frame = control_frame_klass(self,suppress_go_buttons=1)
        self.stim_frame.connect(self.server_hostname,self.server_port)
        self.stim_frame.grid( **self.stim_frame_cnf )
        
        global loopable_variables
        loopable_variables = self.stim_frame.get_loopable_variable_names()
        if hasattr(self, 'loop_frame'):
            # clear old frame
            self.loop_frame.destroy()
            del self.loop_frame
        self.loop_frame = ScrollListFrame(master=self,
                                          container_class=LoopContainedObject)
        self.loop_frame.grid( **self.loop_frame_cnf )

        self.autosave_basename.set( self.stim_frame.get_shortname() )
        
        self.stimulus_tk_var.set( self.stim_frame.get_shortname() ) # set menuitem

        self.progress.labelText = "Ready"
        self.progress.updateProgress(0)

    def change_stimulus(self, dummy_arg=None, new_stimkey=None ):
        # if new_stimkey is None, get from the tk variable
        if new_stimkey is None:
            new_stimkey = self.stimulus_tk_var.get()

        found = 0
        for maybe_stimkey, maybe_control_frame, maybe_title in self.client_list:
            if new_stimkey == maybe_stimkey:
                new_control_frame_klass = maybe_control_frame
                new_stimkey = maybe_stimkey
                found = 1
                break

        if not found:
            raise RuntimeError("Don't know about stimkey %s"%new_stimkey)
        
        if new_control_frame_klass != self.stim_frame.__class__:
                                
            # make wait cursor
            root = self.winfo_toplevel()
            old_cursor = root["cursor"]
            root["cursor"] = "watch"
            root.update()

            self.progress.labelText = "Changing stimulus..."
            self.progress.updateProgress(0)
            
            self.ephys_server.set_next_stimkey( new_stimkey )

            # new stimulus type
            self.stim_frame.quit_server() # disconnect

            self.ephys_server.get_stimkey() # wait for server to load

            self.switch_to_stimkey( new_stimkey)
            
            #restore cursor
            root["cursor"] = old_cursor
            root.update()
            
    def save_image_sequence(self):
        ImageSequenceLauncher(self,ephys_server=self.ephys_server)
        
    def save_config(self):
        filename = tkFileDialog.asksaveasfilename(
            parent=self,
            defaultextension=".ve_cfg",
            filetypes=[('Configuration file','*.ve_cfg')],
            initialdir=VisionEgg.config.VISIONEGG_USER_DIR)
        if not filename:
            return
        fd = open(filename,"wb")
        save_dict = {'stim_type':self.stim_frame.get_shortname(),
                     'loop_list':self.loop_frame.list,
                     'stim_frame_dict':self.stim_frame.get_parameters_dict(),
                     'autosave':self.autosave.get(),
                     'autosave_dir':self.autosave_dir.get(),
                     'autosave_basename':self.autosave_basename.get()}
        pickle.dump( save_dict, fd )

    def load_config(self):
        filename = tkFileDialog.askopenfilename(
            parent=self,
            defaultextension=".ve_cfg",
            filetypes=[('Configuration file','*.ve_cfg')],
            initialdir=VisionEgg.config.VISIONEGG_USER_DIR)
        if not filename:
            return
        fd = open(filename,"rb")
        file_contents = fd.read()
        file_contents = file_contents.replace('\r\n','\n') # deal with Windows newlines
        memory_file = StringIO.StringIO(file_contents)
        load_dict = pickle.load(memory_file)       
        if load_dict['stim_type'] != self.stim_frame.get_shortname():
            self.change_stimulus(new_stimkey=load_dict['stim_type']+"_server")
        self.loop_frame.list = load_dict['loop_list']
        self.loop_frame.update_now()
        self.stim_frame.set_parameters_dict( load_dict['stim_frame_dict'] )
        self.autosave.set(load_dict['autosave'])
        self.autosave_dir.set(load_dict['autosave_dir'])
        self.autosave_basename.set(load_dict['autosave_basename'])
        
        self.stim_frame.update_tk_vars()

    def load_params(self,orig_load_dict={}):
        filename = tkFileDialog.askopenfilename(
            parent=self,
            defaultextension=".py",
            filetypes=[('Auto-saved parameter file','*.py')])
        if not filename:
            return
        locals = {}
        load_dict = orig_load_dict.copy() # make copy of default values
        execfile(filename,locals,load_dict) # execute the file
        if load_dict['stim_type'] != self.stim_frame.get_shortname():
            self.change_stimulus(new_stimkey=load_dict['stim_type']+"_server")
        self.loop_frame.list = [] # clear loop list
        self.loop_frame.update_now()
        new_params = {}
        exception_info = []
        for param_name in dir(self.stim_frame.meta_params):
            if param_name[:2] != "__":
                try:
                    new_params[param_name] = load_dict[param_name]
                except Exception, x:
                    exception_info.append(sys.exc_info()) # don't die on exception
                else:
                    del load_dict[param_name]
        for exc_type, exc_value, exc_traceback in exception_info:
            # ignore actual traceback
            VisionEgg.GUI.showexception(exc_type,exc_value,"")
        self.stim_frame.set_parameters_dict( new_params )
        self.autosave_basename.set(load_dict['stim_type'])
        
        self.stim_frame.update_tk_vars()
        return load_dict # return unused variables

    def launch_screen_pos(self, dummy_arg=None):
        dialog = Tkinter.Toplevel(self)
        frame = VisionEgg.PyroApps.ScreenPositionGUI.ScreenPositionControlFrame(dialog,
                                                                                auto_connect=1,
                                                                                server_hostname=self.server_hostname,
                                                                                server_port=self.server_port)
        frame.winfo_toplevel().title("3D Calibration - Vision Egg")
        frame.pack(expand=1,fill=Tkinter.BOTH)

    def launch_stim_onset_cal(self, dummy_arg=None):
        dialog = Tkinter.Toplevel(self)
        frame = Tkinter.Frame(dialog)
        frame.winfo_toplevel().title("Timing Calibration - Vision Egg")
        Tkinter.Label(frame,
                      font=("Helvetica",12,"bold"),
                      text="Stimulus onset timing").grid(row=0,column=0)
        Tkinter.Label(frame,
                      text="Use a light detector to verify the onset of a trial."
                      ).grid(row=1,column=0)
        Tkinter.Checkbutton( frame,
                             text="Black box (always) with white box (during trial)",
                             variable=self.stim_onset_cal_tk_var,
                             command=self.update_stim_onset_cal).grid(row=2,column=0)

        x,y,width,height = self.ephys_server.get_stim_onset_cal_location()

        location_frame = Tkinter.Frame(frame)
        location_frame.grid(row=3,column=0)
        self.stim_onset_x = Tkinter.DoubleVar()
        self.stim_onset_x.set(x)
        self.stim_onset_y = Tkinter.DoubleVar()
        self.stim_onset_y.set(y)
        self.stim_onset_width = Tkinter.DoubleVar()
        self.stim_onset_width.set(width)
        self.stim_onset_height = Tkinter.DoubleVar()
        self.stim_onset_height.set(height)
        
        Tkinter.Label( location_frame, text="Center X:").grid(row=0,column=0)
        Tkinter.Entry( location_frame, textvariable=self.stim_onset_x,width=5).grid(row=0,column=1)
        Tkinter.Label( location_frame, text="Center Y:").grid(row=0,column=2)
        Tkinter.Entry( location_frame, textvariable=self.stim_onset_y,width=5).grid(row=0,column=3)
        Tkinter.Label( location_frame, text="Width:").grid(row=1,column=0)
        Tkinter.Entry( location_frame, textvariable=self.stim_onset_width,width=5).grid(row=1,column=1)
        Tkinter.Label( location_frame, text="Height:").grid(row=1,column=2)
        Tkinter.Entry( location_frame, textvariable=self.stim_onset_height,width=5).grid(row=1,column=3)

        Tkinter.Button( frame,
                        text="update position and size",
                        command=self.set_stim_onset_cal_position).grid(row=4,column=0)
        self.set_stim_onset_cal_position() # call it once to send server our initial values
        frame.pack(expand=1,fill=Tkinter.BOTH)

    def launch_gamma_panel(self, dummy_arg=None):
        dialog = Tkinter.Toplevel(self)
        frame = GammaFrame(dialog,
                           self.ephys_server)
        frame.pack(expand=1,fill=Tkinter.BOTH)

    def set_autosave_dir(self):
        self.autosave_dir.set( os.path.abspath( tkFileDialog.askdirectory() ) )

    def reset_autosave_basename(self):
        self.autosave_basename.set( self.stim_frame.get_shortname() )

    def update_stim_onset_cal(self, dummy_arg=None):
        on = self.stim_onset_cal_tk_var.get()
        self.ephys_server.set_stim_onset_cal(on)

    def set_stim_onset_cal_position(self, dummy_arg=None):
        x = self.stim_onset_x.get()
        y = self.stim_onset_y.get()
        width = self.stim_onset_width.get()
        height = self.stim_onset_height.get()
        self.ephys_server.set_stim_onset_cal_location(center=(x,y),size=(width,height))
        
    def do_loops(self):
        loop_list = self.loop_frame.get_list_uncontained()
        global need_rest_period
        need_rest_period = 0

        if not len(loop_list):
            return

        def process_loops(depth): # recursive processing of loops
            
            class LoopInfoFrame(Tkinter.Frame):
                def __init__(self, master=None, **kw):
                    Tkinter.Frame.__init__(self,master,**kw)
                    Tkinter.Label(self, 
                        text="Doing sequence").grid(row=0,column=0)
                    self.status_tk_var = Tkinter.StringVar()
                    Tkinter.Label(self,
                        textvariable = self.status_tk_var).grid(row=1, column=0)
                    self.cancel_asap = 0
                    Tkinter.Button(self,
                        text="Cancel",command=self.cancel).grid(row=2,column=0)
                    self.focus_set()
                    self.grab_set()
                def cancel(self, dummy_arg=None):
                    self.cancel_asap = 1
        
            global need_rest_period

            global loop_info_frame
            if depth == 0: # only make one LoopInfoFrame
                top = Tkinter.Toplevel(self)
                loop_info_frame = LoopInfoFrame(top)
                loop_info_frame.pack()
                        
            loop = loop_list[depth]
            max_depth = len(loop_list)-1
            while not loop.is_done() and not loop_info_frame.cancel_asap:
                if loop.parameters.variable != "<repeat>":
                    self.stim_frame.set_loopable_variable(loop.parameters.variable,loop.get_current())
                if depth < max_depth:
                    process_loops(depth+1)
                elif depth == max_depth: # deepest level -- do the trial
                    if need_rest_period:
                        self.progress.labelText = "Resting"
                        self.sleep_with_progress(loop.parameters.rest_duration_sec)
                    self.do_single_trial()
                    need_rest_period = 1
                else:
                    raise RuntimeError("Called with max_depth==-1:")
                loop.advance()
            loop.reset()
            if depth == 0: # destroy LoopInfoFrame
                top.destroy()

        process_loops(0) # start recursion on top level
        
    def do_single_trial(self):
        # this class is broken into parts so it can be subclassed more easily
        self.do_single_trial_pre()
        self.do_single_trial_work()

    def do_single_trial_pre(self, file_stream=None):
        # if file_stream is None, open default file
        if self.autosave.get():
            duration_sec = self.stim_frame.get_duration_sec()
            (year,month,day,hour24,min,sec) = time.localtime(time.time()+duration_sec)[:6]
            self.trial_time_str = "%04d%02d%02d_%02d%02d%02d"%(year,month,day,hour24,min,sec)
            if self.param_file_type_tk_var.get() == "Python format":
                if file_stream is None:
                    # Figure out filename to save results in
                    filename = self.autosave_basename.get() + self.trial_time_str + "_params.py"
                    fullpath_filename = os.path.join( self.autosave_dir.get(), filename)
                    file_stream = open(fullpath_filename,"w")
                file_stream.write("stim_type = '%s'\n"%self.stim_frame.get_shortname())
                file_stream.write("finished_time = %04d%02d%02d%02d%02d%02d\n"%(year,month,day,hour24,min,sec))
                parameter_list = self.stim_frame.get_parameters_as_py_strings()
                for parameter_name, parameter_value in parameter_list:
                    file_stream.write("%s = %s\n"%(parameter_name, parameter_value))
            elif self.param_file_type_tk_var.get() == "Matlab format":
                if file_stream is None:
                    # Figure out filename to save results in
                    filename = self.autosave_basename.get() + self.trial_time_str + "_params.m"
                    fullpath_filename = os.path.join( self.autosave_dir.get(), filename)
                    file_stream = open(fullpath_filename,"w")
                file_stream.write("stim_type = '%s';\n"%self.stim_frame.get_shortname())
                file_stream.write("finished_time = %04d%02d%02d%02d%02d%02d;\n"%(year,month,day,hour24,min,sec))
                parameter_list = self.stim_frame.get_parameters_as_m_strings()
                for parameter_name, parameter_value in parameter_list:
                    file_stream.write("%s = %s;\n"%(parameter_name, parameter_value))
            else:
                raise RuntimeError("Unknown parameter file type") # Should never get here
                
    def do_single_trial_work(self):
        # make wait cursor
        root = self.winfo_toplevel()
        self.old_cursor = root["cursor"]
        root["cursor"] = "watch"
        root.update()

        self.progress.labelText = "Doing trial..."
        self.progress.updateProgress(0)
        
        duration_sec = self.stim_frame.get_duration_sec()
        self.stim_frame.go() # start server going, but this return control immediately
        self.sleep_with_progress(duration_sec)
        while self.ephys_server.is_in_go_loop(): # make sure go loop is really done
            time.sleep(0.1) # wait 100 msec for end of go loop and try again
        if self.notify_on_dropped_frames.get():
            if self.ephys_server.were_frames_dropped_in_last_go_loop():
                tkMessageBox.showwarning("Dropped frame(s)",
                                         "During the last trial, at least 1 frame was dropped.",
                                         parent=self)
        root["cursor"] = self.old_cursor
        root.update()

        # restore status bar
        self.progress.labelText = "Ready"
        self.progress.updateProgress(0)

    def sleep_with_progress(self, duration_sec):
        if duration_sec == 0.0:
            return # don't do anything
        start_time = time.time()
        stop_time = start_time + duration_sec
        percent_done = 0
        while percent_done < 100:
            if sys.platform != 'darwin': # Mac OS X Tk bug... sigh...
                self.progress.updateProgress(percent_done)
            time.sleep(0.01) # wait 10 msec
            percent_done = (time.time() - start_time)/duration_sec*100

    def quit(self):
        self.ephys_server.set_quit_status(1)
        # call parent class
        Tkinter.Frame.quit(self)

    def destroy(self):
        try:
            self.ephys_server.set_quit_status(1)
        except:
            pass
        Tkinter.Frame.destroy(self)
        
class BarButton(Tkinter.Menubutton):
    # Taken from Guido van Rossum's Tkinter svkill demo
        def __init__(self, master=None, **cnf):
            Tkinter.Menubutton.__init__(self, master, **cnf)
            self.pack(side=Tkinter.LEFT)
            self.menu = Tkinter.Menu(self, name='menu', tearoff=0)
            self['menu'] = self.menu
                
if __name__ == '__main__':
    hostname = os.getenv("ephys_server_hostname","")
    port = int(os.getenv("ephys_server_port","7766"))
    result = get_server(hostname=hostname,port=port)
    if result:
        hostname,port = result
        app_window = AppWindow(client_list=client_list,
                               server_hostname=hostname,
                               server_port=port)

        app_window.winfo_toplevel().wm_iconbitmap()
        app_window.pack(expand=1,fill=Tkinter.BOTH)
        app_window.mainloop()