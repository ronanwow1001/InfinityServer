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
                packer = DCPacker()
                dclass = self.dclassesByName['DistributedToon']
                datagram = PyDatagram()
                datagram.addUint16(15) #CLIENT_GET_AVATAR_DETAILS_RESP Msgtype
                datagram.addUint32(1)
                datagram.addUint8(0)
                datagram.addString('Infinity') #Toon name
                datagram.addString('Unknown')
                datagram.addUint32(0)
                datagram.addBool(1)
                datagram.addString('t\x05\x01\x00\x01\x39\x1b\x33\x1b\31\x1b\x14\x00\x14\x14') #DNA (blob)
                datagram.addUint8(1) #GM
                datagram.addUint16(2500) #Max Bank
                datagram.addUint16(0) #Current Bank
                datagram.addUint16(40) #Max Jellybeans
                datagram.addUint16(0) #Current Jellybeans
                datagram.addUint16(15) #Max Laff
                datagram.addUint16(15) #Current Laff
                datagram.addUint32(0) #Battle ID
                datagram.addString('Unknown') #Experience (blob)
                datagram.addUint8(10) #Max Gag Carry
 
                #setTrackAccess
 
                field = dclass.getField(13)
                print field
                arg = [0, 0, 0, 0, 1, 1, 0]
                datagram.addUint16(len(arg) << 1)
                for i in arg:
                    datagram.addInt16(int(i))

                datagram.addInt8(3) #Track Progress 1
                datagram.addUint32(9) #Track Progress 2
 
               
 
                #setTrackBonusLevel
 
                field = dclass.getField(15)
                print field
 
                arg = [0, 0, 0, 0, 1, 1, 0]
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addInt8(int(i))

                datagram.addString('') #setInventory
 
                #setMaxNPCFriends (Uint16)
 
                datagram.addUint16(16)
               
 
                arg = []
                datagram.addUint16(len(arg) * 5)
                for i in arg:
                    datagram.addUint32(int(i))
 
                datagram.addUint32(316000000) #setDefaultShard
 
                datagram.addUint32(2000) #setDefaultZone
 
                datagram.addString('')
 
 
                field = dclass.getField(22)
                print field
 
                arg = [1000, 2000 , 3000, 4000, 5000, 6000, 8000, 9000, 10000, 11000, 12000, 13000]
                datagram.addUint16(len(arg) << 2)
                for i in arg:
                    datagram.addUint32(int(i))
 

                field = dclass.getField(23)
                print field
 
                arg = [1000, 2000 , 3000, 4000, 5000, 6000, 8000, 9000, 10000, 11000, 12000, 13000]
                datagram.addUint16(len(arg) << 2)
                for i in arg:
                    datagram.addUint32(int(i))
 
                datagram.addString('') #setInterface
 
                datagram.addUint32(2000) #setLastHood
 
                datagram.addUint8(1) #setTutorialAck
 
                datagram.addUint32(25) #setMaxClothes
 
                #setClothesTopsList(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
 
                #setClothesBottomsList(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                datagram.addUint32(0) #setMaxAccessories
 
                #setHatList(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setGlassessList(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setBackpackList(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setShoesList(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                datagram.addUint8(0) #setHat 1
                datagram.addUint8(0) #setHat 2
                datagram.addUint8(0) #setHat 3
 
                datagram.addUint8(0) #setGlasses 1
                datagram.addUint8(0) #setGlasses 2
                datagram.addUint8(0) #setGlasses 3
 
                datagram.addUint8(0) #setBackpack 1
                datagram.addUint8(0) #setBackpack 2
                datagram.addUint8(0) #setBackpack 3
 
                datagram.addUint8(0) #setShoes 1
                datagram.addUint8(0) #setShoes 2
                datagram.addUint8(0) #setShoes 3
 
                datagram.addString('')
 
                #setEmoteAccess(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setCustomMeeages(uint16array)
 
                arg = []
                datagram.addUint16(len(arg) << 1)
                for i in arg:
                    datagram.addUint16(int(i))
 
                datagram.addString('') #setResistanceMessages
 
                #setPetTrickPhrases(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                datagram.addUint16(0) #setCatalogSchedule 1
                datagram.addUint32(0) #setVatalogSchedule 2
 
                datagram.addString('') #setCatalog 1
                datagram.addString('') #setCatalog 2
                datagram.addString('') #setCatalog 3
 
                datagram.addString('') #setMailBoxContents
 
                datagram.addString('') #SetDeliverySchedule
 
                datagram.addString('') #setGiftSchedule
 
                datagram.addString('') #setAwardMailboxContents
 
                datagram.addString('') #setAwardSchedule
 
                datagram.addUint8(0) #setAwardNotify
 
                datagram.addUint8(0) #setCatalogNotify 1
 
                datagram.addUint8(0) #setCatalogNotify 2
 
                datagram.addUint8(0) #setSpeedChatStyleIndex
 
                #setTeleportAccess (uint32array)
 
                arg = [1000, 2000 , 3000, 4000, 5000, 6000, 8000, 9000, 10000, 11000, 12000, 13000]
                datagram.addUint16(len(arg) << 2)
                for i in arg:
                    datagram.addUint32(int(i))
 
                #setCogStatus (uint32array)
                arg = []
                datagram.addUint16(len(arg) << 2)
                for i in arg:
                    datagram.addUint32(int(i))
 
                #setCogCount (uint32array)
                arg = []
                datagram.addUint16(len(arg) << 2)
                for i in arg:
                    datagram.addUint32(int(i))
 
                #setCogRadar(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setBuildingRadar(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setCogLevels(uint8array)
 
                arg = [0, 0, 0, 0]
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setCogTypes(uint8array)
 
                arg = [0, 0, 0, 0]
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setCogParts (uint32array)
                arg = [0, 0, 0, 0]
                datagram.addUint16(len(arg) << 2)
                for i in arg:
                    datagram.addUint32(int(i))
 
                #setCogMerits(uint16array)
 
                arg = [0, 0, 0, 0]
                datagram.addUint16(len(arg) << 1)
                for i in arg:
                    datagram.addUint16(int(i))
 
                datagram.addUint32(0) #setHouseId
 
                #setQuests (uint32array)
                arg = []
                datagram.addUint16(len(arg) << 2)
                for i in arg:
                    datagram.addUint32(int(i))
 
                #setQuestHistory(uint16array)
 
                arg = []
                datagram.addUint16(len(arg) << 1)
                for i in arg:
                    datagram.addUint16(int(i))
 
                datagram.addUint8(0) #setRewardHistory 1
 
                #setRewardHistory 2(uint16array)
 
                arg = []
                datagram.addUint16(len(arg) << 1)
                for i in arg:
                    datagram.addUint16(int(i))
 
 
                datagram.addUint8(1) #setQuestCarryLimit
 
                datagram.addInt16(0) #setCheesyEffect 1
                datagram.addUint32(0) #setCheesyEffect 2
                datagram.addUint32(0) #setCheesyEffect 3
 
                datagram.addUint8(0) #setPosIndex
 
                #setFishCollection 1(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setFishCollection 2(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setFishCollection 3(uint16array)
 
                arg = []
                datagram.addUint16(len(arg) << 1)
                for i in arg:
                    datagram.addUint16(int(i))
 
                datagram.addUint8(20) #setMaxFishTank
 
                #setFishTank 1(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setFishTank 2(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setFishTank 3(uint16array)
 
                arg = []
                datagram.addUint16(len(arg) << 1)
                for i in arg:
                    datagram.addUint16(int(i))
 
                datagram.addUint8(1) #setFishingRod
 
                #setFishingTrophies(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setFlowerCollection 1(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setFlowerCollection 2(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setFlowerBasket 1(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                #setFlowerBasket 2(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                datagram.addUint8(25) #setMaxFlowerBasket
 
                #setGardenTrophies(uint8array)
 
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                datagram.addUint8(1) #setShovel
 
                datagram.addUint32(0) #setShovelSkill
 
                datagram.addUint8(1) #setWateringCan
 
                datagram.addUint32(0) #setWateringCanSkill
 
                datagram.addUint32(0) #setPetID
 
                datagram.addUint8(0) #setPetTutorialDone
 
                datagram.addUint8(0) #setFishBingoTutorialDone
 
                datagram.addUint8(0) #setFishBingoMarkTutorialDone
 
                datagram.addInt8(0) #setKartBodyType
 
                datagram.addInt8(0) #setKartBodyColor
 
                datagram.addInt8(0) #setKartAccessoryColor
 
                datagram.addInt8(0) #setKartEngineBlockType
 
                datagram.addInt8(0) #setKartSpoilerType
 
                datagram.addInt8(0) #setKartFrontWheelWellType
 
                datagram.addInt8(0) #setKartBackWheelWellType
 
                datagram.addInt8(0) #setKartRimType
 
                datagram.addInt8(0) #setKartDecalType
 
                datagram.addUint32(100) #setTickets
 
                datagram.addUint8(0) #setKartingHistory 1
                datagram.addUint8(0) #setKartingHistory 2
                datagram.addUint8(0) #setKartingHistory 3
                datagram.addUint8(0) #setKartingHistory 4
                datagram.addUint8(0) #setKartingHistory 5
                datagram.addUint8(0) #setKartingHistory 6
                datagram.addUint8(0) #setKartingHistory 7
                datagram.addUint8(0) #setKartingHistory 8
                datagram.addUint8(0) #setKartingHistory 9
                datagram.addUint8(0) #setKartingHistory 10
                datagram.addUint8(0) #setKartingHistory 11
                datagram.addUint8(0) #setKartingHistory 12
                datagram.addUint8(0) #setKartingHistory 13
                datagram.addUint8(0) #setKartingHistory 14
                datagram.addUint8(0) #setKartingHistory 15
                datagram.addUint8(0) #setKartingHistory 16
 
               
                datagram.addUint8(0) #setKartingTrophies 1
                datagram.addUint8(0) #setKartingTrophies 2
                datagram.addUint8(0) #setKartingTrophies 3
                datagram.addUint8(0) #setKartingTrophies 4
                datagram.addUint8(0) #setKartingTrophies 5
                datagram.addUint8(0) #setKartingTrophies 6
                datagram.addUint8(0) #setKartingTrophies 7
                datagram.addUint8(0) #setKartingTrophies 8
                datagram.addUint8(0) #setKartingTrophies 9
                datagram.addUint8(0) #setKartingTrophies 11
                datagram.addUint8(0) #setKartingTrophies 11
                datagram.addUint8(0) #setKartingTrophies 12
                datagram.addUint8(0) #setKartingTrophies 13
                datagram.addUint8(0) #setKartingTrophies 14
                datagram.addUint8(0) #setKartingTrophies 15
                datagram.addUint8(0) #setKartingTrophies 16
                datagram.addUint8(0) #setKartingTrophies 17
                datagram.addUint8(0) #setKartingTrophies 18
                datagram.addUint8(0) #setKartingTrophies 19
                datagram.addUint8(0) #setKartingTrophies 20
                datagram.addUint8(0) #setKartingTrophies 21
                datagram.addUint8(0) #setKartingTrophies 22
                datagram.addUint8(0) #setKartingTrophies 23
                datagram.addUint8(0) #setKartingTrophies 24
                datagram.addUint8(0) #setKartingTrophies 25
                datagram.addUint8(0) #setKartingTrophies 26
                datagram.addUint8(0) #setKartingTrophies 27
                datagram.addUint8(0) #setKartingTrophies 28
                datagram.addUint8(0) #setKartingTrophies 29
                datagram.addUint8(0) #setKartingTrophies 30
                datagram.addUint8(0) #setKartingTrophies 31
                datagram.addUint8(0) #setKartingTrophies 32
                datagram.addUint8(0) #setKartingTrophies 33
 
                datagram.addUint32(0) #setKartingPersonalBest 1
                datagram.addUint32(0) #setKartingPersonalBest 2
                datagram.addUint32(0) #setKartingPersonalBest 3
                datagram.addUint32(0) #setKartingPersonalBest 4
                datagram.addUint32(0) #setKartingPersonalBest 5
                datagram.addUint32(0) #setKartingPersonalBest 6
 
                datagram.addUint32(0) #setKartingPersonalBest2 1
                datagram.addUint32(0) #setKartingPersonalBest2 2
                datagram.addUint32(0) #setKartingPersonalBest2 3
                datagram.addUint32(0) #setKartingPersonalBest2 4
                datagram.addUint32(0) #setKartingPersonalBest2 5
                datagram.addUint32(0) #setKartingPersonalBest2 6
                datagram.addUint32(0) #setKartingPersonalBest2 7
                datagram.addUint32(0) #setKartingPersonalBest2 8
                datagram.addUint32(0) #setKartingPersonalBest2 9
                datagram.addUint32(0) #setKartingPersonalBest2 10
                datagram.addUint32(0) #setKartingPersonalBest2 11
                datagram.addUint32(0) #setKartingPersonalBest2 12
 
                #setKartAccessoriesOwned [16]
                datagram.addInt8(0)
                datagram.addInt8(0)
                datagram.addInt8(0)
                datagram.addInt8(0)
                datagram.addInt8(0)
                datagram.addInt8(0)
                datagram.addInt8(0)
                datagram.addInt8(0)
                datagram.addInt8(0)
                datagram.addInt8(0)
                datagram.addInt8(0)
                datagram.addInt8(0)
                datagram.addInt8(0)
                datagram.addInt8(0)
                datagram.addInt8(0)
                datagram.addInt8(0)
 
                #setCogSummonsEarned
                arg = []
                datagram.addUint16(len(arg))
                for i in arg:
                    datagram.addUint8(int(i))
 
                datagram.addUint8(0) #setGardenStart
 
                #setGolfHistory [18]
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
                datagram.addUint16(0)
 
                #setPackedGolfHoleBest [18]
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
 
                #setGolfCourseBest
                datagram.addUint8(0)
                datagram.addUint8(0)
                datagram.addUint8(0)
 
                datagram.addUint8(0) #setPinkSlips
 
                datagram.addUint8(0) #setNametagStyle

                self.cw.send(datagram, connection)

               
        elif msgType == CLIENT_SET_WISHNAME:
            #print dgi
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