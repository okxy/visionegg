"""VisionEgg TCPController module

The following are examples of how to change the controller for "name".

name=const(1.0,0.0,Types.Floattype,Time_sec_absolute,Every_frame)
name=eval_str("t*5.0*360.0","0.0",types.FloatType,TIME_SEC_ABSOLUTE,EVERY_FRAME)
"""

# Copyright (c) 2002 Andrew Straw.  Distributed under the terms
# of the GNU Lesser General Public License (LGPL).

import VisionEgg
import VisionEgg.Core
import socket, select, re, string
import types

__version__ = VisionEgg.release_name
__cvs__ = string.split('$Revision$')[1]
__date__ = string.join(string.split('$Date$')[1:3], ' ')
__author__ = 'Andrew Straw <astraw@users.sourceforge.net>'

class Parser:
    def __init__(self,tcp_name,most_recent_command):
        self.tcp_name = tcp_name
        self.most_recent_command = most_recent_command

    def parse_func(self,match):
        # Make this into a lambda function
        self.most_recent_command[self.tcp_name] = match.groups()[-1]
        return ""

class TCPServer:
    def __init__(self,
                 hostname="localhost",
                 port=7834):
        server_address = (hostname,port)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(server_address)

    def create_listener_once_connected(self):
        VisionEgg.Core.message.add(
            """Awaiting connection to TCPServer at %s"""%(self.server_socket.getsockname(),),
            level=VisionEgg.Core.Message.INFO)
        self.server_socket.listen(1)
        client, client_address = self.server_socket.accept()
        return SocketListenController(client,client_address)

class SocketListenController(VisionEgg.Core.Controller):
    re_line = re.compile(r"(?:^(.*)\n)+",re.MULTILINE)
    re_const = re.compile(r'const\(\s?(.*)\s?(?:,\s?(.*)\s?(?:,\s?(.*)\s?(?:\,\s?(.*)\s?(?:,\s?(.*)\s?)?)?)?)?\)',re.MULTILINE)
    re_eval_str = re.compile(r'eval_str\(\s?"(.*)"\s?(?:,\s?"(.*)"\s?(?:,\s?(.*)\s?(?:\,\s?(.*)\s?(?:,\s?(.*)\s?)?)?)?)?\)',re.MULTILINE)
    #re_eval_str = re.compile(r'eval_str\(\s?"(.*)"\s?,\s?"(.*)"\s?,\s?(.*)\s?\,\s?(.*)\s?,\s?(.*)\s?\)',re.MULTILINE)
    def __init__(self,
                 socket,
                 client_address,
                 temporal_variable_type = VisionEgg.Core.Controller.TIME_SEC_ABSOLUTE,
                 eval_frequency = VisionEgg.Core.Controller.EVERY_FRAME ):
        VisionEgg.Core.Controller.__init__(self,
                                           return_type = types.NoneType,
                                           temporal_variable_type = temporal_variable_type,
                                           eval_frequency = eval_frequency)
        self.socket = socket
        self.client_address = client_address
        
        VisionEgg.Core.message.add(
            "Handling connection from %s"%(self.client_address,),
            level=VisionEgg.Core.Message.INFO)
        
        self.socket.setblocking(0) # don't block on this socket
        
        self.socket.send("Hello. This is %s version %s.\n"%(self.__class__,__version__))
        self.socket.send("Begin sending commands now.\n")

        self.buffer = ""

        self.names = {} # ( controller, name_re, parser )
        self.last_command = {}

    def __check_socket(self):
        # First, update the buffer XXX Check for socket errors!
        ready_to_read, temp, temp2 = select.select([self.socket],[],[],0)
        new_info = 0
        while len(ready_to_read):
            new = self.socket.recv(1024)
            if len(new) == 0:
                raise RuntimeError("Socket disconnected!")
            #assert(ready_to_read[0] == self.socket)
            self.buffer = self.buffer + new
            new_info = 1
            ready_to_read, temp, temp2 = select.select([self.socket],[],[],0)

        # Second, convert the buffer to command_queue entries
        if new_info:
            # Handle variations on newlines:
            self.buffer = string.replace(self.buffer,chr(0x0D),"") # no CR
            self.buffer = string.replace(self.buffer,chr(0x0A),"\n") # LF = newline
            # Handle each line for which we have a tcp_name
            for tcp_name in self.names.keys():
                (controller, name_re_str, parser) = self.names[tcp_name]
                # If the following line makes a match, it
                # sticks the result in self.last_command[tcp_name].
                self.buffer = name_re_str.sub(parser,self.buffer)
                # Now act based on the command parsed
                command = self.last_command[tcp_name]
                if command is not None:
                    self.__do_command(tcp_name,command)
                    self.last_command[tcp_name] = None
            # Clear any complete lines for which we don't have a tcp_name
            self.buffer = SocketListenController.re_line.sub(self.__unknown_line,self.buffer)

    def __unknown_line(self,match):
        for str in match.groups():
            self.socket.send("Error with line: "+str+"\n")
            VisionEgg.Core.message.add("Error with line: "+str+"\n",
                                       level=VisionEgg.Core.Message.INFO)
        return ""

    def create_tcp_controller(self,
                              tcp_name=None,
                              initial_controller=None):
        if tcp_name is None:
            raise ValueError("Must specify tcp_name")
        if tcp_name in self.names.keys():
            raise ValueError('tcp_name "%s" already in use.'%tcp_name)
        if initial_controller is None:
            # create default controller
            initial_controller = VisionEgg.Core.ConstantController(
                during_go_value=1.0,
                between_go_value=0.0)
        else:
            if not isinstance(initial_controller,VisionEgg.Core.Controller):
                raise ValueError('initial_controller not an instance of VisionEgg.Core.Controller')
        # Create initial None value for self.last_command dict
        self.last_command[tcp_name] = None
        # Create values for self.names dict tuple ( controller, name_re, most_recent_command, parser )
        controller = TCPController(
            tcp_name=tcp_name,
            contained_controller=initial_controller
            )
        name_re_str = re.compile(r"^"+tcp_name+r"\s*=\s*(.*)\s*$",re.MULTILINE)
        parser = Parser(tcp_name,self.last_command).parse_func
        self.names[tcp_name] = (controller, name_re_str, parser)
        self.socket.send("%s controllable with this connection.\n"%tcp_name)
        return controller
    
    def __do_command(self,tcp_name,command):
        new_contained_controller = None
        match = SocketListenController.re_const.match(command)
        if match is not None:
            try:
                match_groups = match.groups()
                go_val = eval(match_groups[0])
                if match_groups[1] is not None:
                    not_go_val = eval(match_groups[1])
                else:
                    not_go_val = go_val
                if match_groups[2] is not None:
                    return_type = eval(match_groups[2])
                else:
                    return_type = type(go_val)
                if match_groups[3] is not None:
                    temporal_variable_type = eval("VisionEgg.Core.Controller.%s"%match_groups[3])
                else:
                    temporal_variable_type = VisionEgg.Core.Controller.TIME_SEC_ABSOLUTE
                if match_groups[4] is not None:
                    eval_frequency = eval("VisionEgg.Core.Controller.%s"%match_groups[4])
                else:
                    eval_frequency = VisionEgg.Core.Controller.NOW_THEN_TRANSITIONS
                #eval_frequency = VisionEgg.Core.Controller.EVERY_FRAME
                #temporal_variable_type = VisionEgg.Core.Controller.TIME_SEC_ABSOLUTE
                new_contained_controller = VisionEgg.Core.ConstantController(
                    during_go_value = go_val,
                    between_go_value = not_go_val,
                    return_type = return_type,
                    temporal_variable_type = temporal_variable_type,
                    eval_frequency = eval_frequency)
            except Exception, x:
                self.socket.send("Error parsing const for %s: %s\n"%(tcp_name,x))
                VisionEgg.Core.message.add("Error parsing const for %s: %s\n"%(tcp_name,x),
                                           level=VisionEgg.Core.Message.INFO)
        else:
            match = SocketListenController.re_eval_str.match(command)
            if match is not None:
                try:
                    match_groups = match.groups()
                    go_str = match_groups[0]
                    if match_groups[1] is not None:
                        not_go_str = match_groups[1]
                    else:
                        not_go_str = go_str
                    if match_groups[2] is not None:
                        return_type = eval(match_groups[2])
                    else:
                        t = 0.0 # Create time variable in local namespace
                        return_type = type(eval(go_str))
                    if match_groups[3] is not None:
                        temporal_variable_type = eval("VisionEgg.Core.Controller.%s"%match_groups[3])
                    else:
                        temporal_variable_type = VisionEgg.Core.Controller.TIME_SEC_ABSOLUTE
                    if match_groups[4] is not None:
                        eval_frequency = eval("VisionEgg.Core.Controller.%s"%match_groups[4])
                    else:
                        eval_frequency = VisionEgg.Core.Controller.EVERY_FRAME
                    new_contained_controller = VisionEgg.Core.EvalStringController(
                        during_go_eval_string = go_str,
                        between_go_eval_string = not_go_str,
                        return_type = return_type,
                        temporal_variable_type = temporal_variable_type,
                        eval_frequency = eval_frequency)
                except Exception, x:
                    self.socket.send("Error parsing eval_str for %s: %s\n"%(tcp_name,x))
                    VisionEgg.Core.message.add("Error parsing eval_str for %s: %s\n"%(tcp_name,x),
                                               level=VisionEgg.Core.Message.INFO)
            else:
                self.socket.send("Error parsing command for %s: %s\n"%(tcp_name,command))
                VisionEgg.Core.message.add("Error parsing command for %s: %s\n"%(tcp_name,command),
                                           level=VisionEgg.Core.Message.INFO)
        # create controller based on last command_queue
        if new_contained_controller is not None:
            (controller, name_re_str, parser) = self.names[tcp_name]
            controller.set_value(new_contained_controller)

    def during_go_eval(self):
        self.__check_socket()
        return None

    def between_go_eval(self):
        self.__check_socket()
        return None   

class TCPController(VisionEgg.Core.Controller):
    # Contains another controller...
    def __init__(self, tcp_name, contained_controller):
        self.tcp_name = tcp_name
        self.contained_controller = contained_controller
        self.__sync_mimic()

    def set_value(self,new_contained_controller):
        self.contained_controller = new_contained_controller
        self.__sync_mimic()

    def __sync_mimic(self):
        self.return_type = self.contained_controller.return_type
        self.temporal_variable = self.contained_controller.temporal_variable
        self.temporal_variable_type = self.contained_controller.temporal_variable_type
        self.eval_frequency = self.contained_controller.eval_frequency
        
    def during_go_eval(self):
        self.contained_controller.temporal_variable = self.temporal_variable
        # XXX HACK to fix:
        if self.contained_controller.temporal_variable is None:
            self.contained_controller.temporal_variable = 0.0
        return self.contained_controller.during_go_eval()

    def between_go_eval(self):
        self.contained_controller.temporal_variable = self.temporal_variable
        return self.contained_controller.between_go_eval()