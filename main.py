# InfinityServer


# Release Version 0.1



## TODO FOR TEWTOW SERVER
## * CHECK FOR SERVER VERSION DIFERENCES BETWEEN CLIENT & SERVER (REFUSE/DISCONNECT THE CLIENT (OR MAYBE 1337 HAX0R IF SO.)!!! (DONE!)
## * CHECK FOR DCFILE DIFFERENCES AND REFUSE TO LET CLIENT CONNECT IF SO.
## * CHECK FOR ANY SERVER-SIDED VULNS FROM OG TOONTOWN (NICE GOING DISNEY)
## * FINISH DATAGRAMS/MSGTYPES!
## * DATABASE (JSON? MONGODB?) IMPLEMENTATION. (PLAY TOKEN, ETC)

from pandac.PandaModules import ConfigVariableString
ConfigVariableString('window-type', 'none').setValue('none')

import ctypes
ctypes.windll.kernel32.SetConsoleTitleA("Toontown/Tewtow Server Emulator by Infinity/Average")

from pandac.PandaModules import *

from direct.distributed.MsgTypes import *
from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from direct.directbase import DirectStart
from direct.distributed.ServerRepository import ServerRepository
from direct.distributed.ClientRepository import ClientRepository
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from datetime import datetime
import time
CLIENT_SET_ZONE = 29

MAINTENANCE = False

SERVER_VERSION = 'sv1.0.47.38'


DistributedClassFiles = ["dclass/otp.dc", "dclass/toon.dc"]
 
class TTServerRepository(ServerRepository):
 
    notify = directNotify.newCategory('TTServerRepository')
 
    def __init__(self):
        PORT = base.config.GetInt('server-port', 6668)
        ServerRepository.__init__(self, PORT, None, dcFileNames=DistributedClassFiles)
        self.connectionList = []	
 
        print '''                                                                                                                                                                                   
,--------.                       ,--.                                 ,---.                                           ,------.                  ,--.          ,--.                 
'--.  .--',---.  ,---. ,--,--, ,-'  '-. ,---. ,--.   ,--.,--,--,     '   .-'  ,---. ,--.--.,--.  ,--.,---. ,--.--.    |  .---',--,--,--.,--.,--.|  | ,--,--.,-'  '-. ,---. ,--.--. 
   |  |  | .-. || .-. ||      \'-.  .-'| .-. ||  |.'.|  ||      \    `.  `-. | .-. :|  .--' \  `'  /| .-. :|  .--'    |  `--, |        ||  ||  ||  |' ,-.  |'-.  .-'| .-. ||  .--' 
   |  |  ' '-' '' '-' '|  ||  |  |  |  ' '-' '|   .'.   ||  ||  |    .-'    |\   --.|  |     \    / \   --.|  |       |  `---.|  |  |  |'  ''  '|  |\ '-'  |  |  |  ' '-' '|  |    
   `--'   `---'  `---' `--''--'  `--'   `---' '--'   '--'`--''--'    `-----'  `----'`--'      `--'   `----'`--'       `------'`--`--`--' `----' `--' `--`--'  `--'   `---' `--'    '''    
        print "DEBUG: Sucessfully started server emulator."

	
    def readDCFile(self, dcFileNames):
        print 'DEBUG: Loading required Distributed Class files...'
        dcFile = self.dcFile
        dcFile.clear()
        self.dclassesByName = {}
        self.dclassesByNumber = {}
        self.hashVal = 0
        dcImports = {}
        if dcFileNames:
            searchPath = DSearchPath()
            searchPath.appendDirectory(Filename('.'))
            for dcFileName in dcFileNames:
                pathname = Filename(dcFileName)
                vfs.resolveFilename(pathname, searchPath)
                readResult = dcFile.read(pathname)
        self.hashVal = dcFile.getHash()
        for i in range(dcFile.getNumClasses()):
            dclass = dcFile.getClass(i)
            number = dclass.getNumber()
            className = dclass.getName() + self.dcSuffix
            self.dclassesByName[className] = dclass
            if number >= 0:
                self.dclassesByNumber[number] = dclass

    def handleDatagram(self, dg):
        if not dg.getLength() > 0:
            return None
        dgi = PyDatagramIterator(dg)
        connection = dg.getConnection()
        msgType = dgi.getUint16()
        if msgType == CLIENT_HEARTBEAT:
            self.notify.debug('Recieved heartbeat.')
        elif msgType == CLIENT_DISCONNECT:
            if connection in self.connectionList:
                self.connectionList.remove(connection)
        elif msgType == CLIENT_SET_ZONE:
            self.handleSetZone(dgi, connection)
        elif msgType == CLIENT_REMOVE_ZONE:
            self.handleRemoveZone(dgi, connection)
        elif msgType == CLIENT_CREATE_OBJECT_REQUIRED:
            self.handleClientCreateObjectRequired(dg, dgi)
        elif msgType == CLIENT_OBJECT_UPDATE_FIELD:
            doId = dgi.getUint32()
            fieldId = dgi.getUint16()
            print "DEBUG: Got Toontown field update for Toontown doId = %d and Toontown fieldId = %d" % (doId, fieldId)
        elif msgType == CLIENT_OBJECT_DELETE:
            self.handleClientDeleteObject(dg, dgi.getUint32())
        elif msgType == CLIENT_OBJECT_DISABLE:
            self.handleClientDisable(dg, dgi.getUint32())
        elif msgType == CLIENT_ADD_INTEREST:
            #self.handleClientAddInterest(self, Client, dgi)
           
            handle = dgi.getUint16()
            contextId = dgi.getUint32()
            parentId = dgi.getUint32()
            zoneList = [dgi.getUint32()]  
            print 'DEBUG: Network :: Interest -> (%d, %d, %d)' % (handle, contextId, parentId)
            while True:
                remainingData = (dg.getLength() - dgi.getCurrentIndex())
                if remainingData == 0:
                    break
                zoneList.append(dgi.getUint32())
            if handle == 2: #Aww yeah we found the tewtow shard list interest!
                datagram = PyDatagram()
                datagram.addUint16(CLIENT_CREATE_OBJECT_REQUIRED_OTHER_RESP)
                datagram.addUint32(4618) #parentId
                datagram.addUint32(3) #zoneId
                datagram.addUint16(58) #ToontownDistrict DClass Field
                datagram.addUint32(316000000) #Shard ID (doId)
                datagram.addString('Astron is for n00bs') #District name
                datagram.addUint8(1) # 1 - Enabled 0 - Disabled
                datagram.addBool(0)
                self.cw.send(datagram, connection)
            if handle == 4:
                datagram = PyDatagram()
                datagram.addUint16(CLIENT_CREATE_OBJECT_REQUIRED_OTHER_RESP)
                datagram.addUint32(4618) #parentId
                datagram.addUint32(3) #zoneId
                datagram.addUint16(387) #ToontownDistrict DClass Field
                datagram.addUint32(900000000) #Shard ID (doId)
                datagram.addString("2013-08-22 23:49:46")
                self.cw.send(datagram, connection)
               
                datagran2 = PyDatagram()
                datagran2.addUint16(CLIENT_CREATE_OBJECT_REQUIRED_OTHER_RESP)
                datagran2.addUint32(0)
                datagran2.addUint32(0)
                datagran2.addUint16(172)
                datagran2.addUint32(637100008)
                arg = []
                datagran2.addUint16(len(arg) << 1)
                for i in arg:
                    datagran2.addInt16(int(i))
                datagran2.addUint16(len(arg) << 1)
                for i in arg:
                    datagran2.addInt16(int(i))
                datagran2.addUint16(len(arg) << 1)
                for i in arg:
                    datagran2.addInt16(int(i))
                datagran2.addUint16(len(arg) << 1)
                for i in arg:
                    datagran2.addInt16(int(i))
                #arg = [64, 65, 66, 10, 15]
                datagran2.addUint16(len(arg))
                for i in arg:
                    datagran2.addUint16(int(i))
                self.cw.send(datagran2, connection)
           
            if handle == 5:
                datagram = PyDatagram()
                datagram.addUint16(CLIENT_OBJECT_UPDATE_FIELD)
                datagram.addUint32(1) #doId
                datagram.addUint16(112) #fieldId
                datagram.addUint32(316000000)
                self.cw.send(datagram, connection)
            datagram = PyDatagram()
            datagram.addUint16(CLIENT_DONE_INTEREST_RESP)
            datagram.addUint16(handle)
            datagram.addUint32(contextId)
            datagram.addUint32(parentId)
            for zoneId in zoneList:
                datagram.addUint32(zoneId)
            self.cw.send(datagram, connection)
            datagram = PyDatagram()
            datagram.addUint16(CLIENT_DONE_INTEREST_RESP)
            datagram.addUint16(handle)
            datagram.addUint32(contextId)
            datagram.addUint32(parentId)
            for zoneId in zoneList:
                datagram.addUint32(zoneId)
            self.cw.send(datagram, connection)
        elif msgType == CLIENT_REMOVE_INTEREST:
            return None
        #Lets start with the tewtow specific msgtypes.
        elif msgType == CLIENT_LOGIN_TOONTOWN:
            self.handleClientLoginToontown(dgi, connection)
        elif msgType == CLIENT_GET_AVATARS:
            self.handleGetAvatars(dgi, connection)			

        elif msgType == CLIENT_GET_AVATARS:
            self.handleGetAvatars(dgi, connection)

        elif msgType == CLIENT_CREATE_AVATAR:
            #return None
            datagram = PyDatagram()
            datagram.addUint16(CLIENT_CREATE_AVATAR_RESP)
            datagram.addUint16(0) #echoContext
            datagram.addUint8(0) #returnCode
            datagram.addUint32(1)
            self.cw.send(datagram, connection)
        elif msgType == CLIENT_SET_NAME_PATTERN:
            datagram = PyDatagram()
            datagram.addUint16(CLIENT_SET_NAME_PATTERN_ANSWER)
            datagram.addUint32(1)
            datagram.addUint8(0)
            self.cw.send(datagram, connection)
        elif msgType == CLIENT_SET_AVATAR:
            datagram = PyDatagram()
            self.cw.send(datagram, connection)

               
        elif msgType == CLIENT_SET_WISHNAME:
            avId = dgi.getUint16()
            unknown = dgi.getString()
            pendingName = dgi.getString()
            print pendingName
            divide = pendingName.split(' ')
            lenStr = len(divide)
            s = 0
            while s != lenStr:
                nameCheck = divide[s]
                s += 1
            with open ("TewtowBlacklist.txt", "r") as badWordFile:
                data=badWordFile.readlines()
                for word in data:
                    chrList = list(word)
                    if chrList.count('\n') == 1:
                        chrList.remove('\n')
                    badWord = ''.join(chrList)
                    if nameCheck == badWord:
                        print 'Bad name detected, are you trying to get banned?'
                        datagram = PyDatagram()
                        datagram.addUint16(CLIENT_SET_WISHNAME_RESP)
                        datagram.addUint32(avId)
                        datagram.addUint16(0)
                        datagram.addString('NO')
                        datagram.addString('NO')
                        datagram.addString('')
                        message = PyDatagram()
                        message.addUint16(CLIENT_SYSTEM_MESSAGE)
                        message.addString('Sorry, That name is not allowed.')
                        self.cw.send(message, connection)
                    else:
                        datagram = PyDatagram()
                        datagram.addUint16(CLIENT_SET_WISHNAME_RESP)
                        datagram.addUint32(avId)
                        datagram.addUint16(0)
                        datagram.addString('NO')
                        datagram.addString('')
                        datagram.addString('NO')
                        self.cw.send(datagram, connection)
 
        elif msgType == CLIENT_OBJECT_LOCATION:
            doId = dgi.getUint32()
            parentId = dgi.getUint32()
            zoneId = dgi.getUint32()
            print 'Network :: Location -> (%d, %d, %d)' % (doId, parentId, zoneId)
            if zoneId == 2000:
               
                #DistributedMickey
                datagram = PyDatagram()
                datagram.addUint16(CLIENT_CREATE_OBJECT_REQUIRED_OTHER_RESP)
                datagram.addUint32(316000000) #parentId
                datagram.addUint32(2) #zoneId
                #datagram.addUint16(83)
                datagram.addUint16(65)
                datagram.addUint32(433103088)
                datagram.addString("a")
                datagram.addString("a")
                datagram.addInt16(0)
                self.cw.send(datagram, connection)
           
            if zoneId == 1000:
                datagram = PyDatagram()
                datagram.addUint16(CLIENT_CREATE_OBJECT_REQUIRED_OTHER_RESP)
                datagram.addUint32(316000000) #parentId
                datagram.addUint32(2) #zoneId
                #datagram.addUint16(83)
                datagram.addUint16(108)
                datagram.addUint32(433103088)
                datagram.addString("DockedEast")
                datagram.addInt16(100)
                self.cw.send(datagram, connection)
            if zoneId == 5000:
                '''
                datagram = PyDatagram()
                datagram.addUint16(CLIENT_CREATE_OBJECT_REQUIRED_OTHER_RESP)
                datagram.addUint32(316000000) #parentId
                datagram.addUint32(2) #zoneId
                datagram.addUint16(68)
                datagram.addUint32(433103088)
                datagram.addString("a")
                datagram.addString("a")
                datagram.addInt16(0)
                self.cw.send(datagram, connection)
                '''
               
        #self.cw.send(datagram, connection)
            if zoneId == 2000:
                pass
                '''#message = PyDatagram()
                #message.addUint16(CLIENT_SYSTEM_MESSAGE)
                #message.addString('Surprised? I thought so. :P')
                #self.cw.send(message, connection)
                datagram = PyDatagram()
                datagram.addUint16(CLIENT_CREATE_OBJECT_REQUIRED_OTHER_RESP)
                datagram.addUint32(316000000) #parentId
                datagram.addUint32(2) #zoneId
                #datagram.addUint16(83)
                datagram.addUint16(65)
                datagram.addUint32(433103088)
                datagram.addString("b")
                datagram.addString("a")
                datagram.addInt16(0)
                self.cw.send(datagram, connection)'''
               
            if zoneId == 3000:
                datagram = PyDatagram()
                datagram.addUint16(CLIENT_CREATE_OBJECT_REQUIRED_OTHER_RESP)
                datagram.addUint32(316000000) #parentId
                datagram.addUint32(2) #zoneId
                #datagram.addUint16(83)
                datagram.addUint16(79)
                datagram.addUint32(433103089)
                datagram.addString("a")
                datagram.addString("a")
                datagram.addInt16(0)
                self.cw.send(datagram, connection)
               
                datagram = PyDatagram()
                datagram.addUint16(CLIENT_GET_STATE_RESP)
                self.cw.send(datagram, connection)

			
        else:
            self.notify.warning('Got a datagram %d; but could not handle it.' % msgType)
	
    def handleClientLoginToontown(self, di, conn):
        if(MAINTENANCE == True):
            dg = PyDatagram()
            dg.addUint16(CLIENT_GO_GET_LOST)
            dg.addUint16(151)
            dg.addString('The servers are currently closed for maintenance.')
            self.cw.send(dg, conn)
        else:
            token = di.getString()
            sv = di.getString()
            if (token != 'daXy321/4432125/DSaGSX=='):
                self.notify.warning('Client doesn\'t have temporary token, booting.')
                dg = PyDatagram()
                dg.addUint16(CLIENT_GO_GET_LOST)
                dg.addUint16(101)
                dg.addString('Login token: %s doesn\'t exist.' % token)
                self.cw.send(dg, conn)
            elif (sv != SERVER_VERSION):
                self.notify.warning('Booting client out.')
                dg = PyDatagram()
                dg.addUint16(CLIENT_GO_GET_LOST)
                dg.addUint16(124)
                dg.addString('Client and Server version do not match. Server is running ' + SERVER_VERSION + ', while client was running ' + sv + '.')
                self.cw.send(dg, conn)
            else:
                now = datetime.now
                dg = PyDatagram()
                dg.addUint16(CLIENT_LOGIN_TOONTOWN_RESP)
                dg.addUint8(0) #Return Code
                dg.addString('OK') #respString
                dg.addUint32(123456) #Account Number
                dg.addString('Infinity') #Account Name
                dg.addUint8(1) #accountNameApproved
                dg.addString('YES') #self.openChatEnabled
                dg.addString('YES') #self.createFriendsWithChat
                dg.addString('YES') #chatCodeCreationRule
                dg.addUint32(time.time()) #sec?
                dg.addUint32(time.clock()) #usec?
                dg.addString('FULL') #self.isPaid
                dg.addString('YES') #WhiteListReponse
                dg.addString(time.strftime('%Y-%m-%d'))#lastLoggedInStr
                dg.addInt32(0) #accountDays
                dg.addString('NO_PARENT_ACCOUNT')
                dg.addString('Infinity')
                self.cw.send(dg, conn)

    def handleGetAvatars(self, dgi, connection):
        datagram = PyDatagram()
        datagram.addUint16(CLIENT_GET_AVATARS_RESP)
        datagram.addUint8(0) # return code
        datagram.addUint16(0) # number of avatars
        self.cw.send(datagram, connection)
				
class TTAIRepository(ClientRepository):

    notify = directNotify.newCategory('TTAIRepository')

    def __init__(self):
        ClientRepository.__init__(self, dcFileNames=[], dcSuffix='AI')
        PORT = base.config.GetInt('server-port', 6668)
        self.connect([URLSpec('http://localhost:%s' % PORT)],
                      successCallback=self.connectSuccess,
                      failureCallback=self.connectFailure)

    def connectFailure(self, statusCode, statusString):
        raise StandardError, statusString

    def connectSuccess(self):
        self.acceptOnce('gotCreateReady', self.getCreateReady)

    def getCreateReady(self):
        self.setInterestZones([3])
		
		
simbase = TTServerRepository()
simbase.air = TTAIRepository()		
		
run()