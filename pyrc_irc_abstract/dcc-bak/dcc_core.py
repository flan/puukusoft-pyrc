"""
 PyRC module: ircAbstract.dccCore
 Purpose: Contains common DCC-related functions.
 
 All code, unless otherwise indicated, is original, and subject to the terms of
 the attached licensing agreement.
 
 (C) Neil Tallim, 2004
 Version: 1.0.0

 This module falls under the terms of the license stipulated in PyRC.py, which
 you should have received with it.
"""

#This module will need to provide some form of management for all DCC events, since they can't be stored in the server,
#and they must persist outside of the interface.
#A singleton approach should work fine.

#One name/IP pair per chat.


#socket provides functions that can handle these processes.
def numToIP(numIn):
    num = long(numIn)
    ipList = map(str, map(int, [num >> 24 & 0xFF, num >> 16 & 0xFF, num >> 8 & 0xFF, num & 0xFF]))
    return '.'.join(ipList)

def ipToNum(ipIn):
    ipList = map(long, ipIn.split("."))
    num = str((ipList[0] << 24) | (ipList[1] << 16) | (ipList[2] << 8) | ipList[3])
    if num[-1] == "L":
        num = num[:-1]
        
    return num
    
