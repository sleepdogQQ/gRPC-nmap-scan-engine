
OID_SYSTEM = '1.3.6.1.2.1.1'

BASE_DEVICEINFO_VALUE = ["sysDescr", "sysObjectID", "sysUpTime", 
"sysContact", "sysName", "sysLocation", "sysServices", "sysORLastChange"]

OID_DEVICEINFO = {
    "1.3.6.1.2.1.1.1.0": "sysDescr",
    "1.3.6.1.2.1.1.2.0": "sysObjectID",
    "1.3.6.1.2.1.1.3.0": "sysUpTime",
    "1.3.6.1.2.1.1.4.0": "sysContact",
    "1.3.6.1.2.1.1.5.0": "sysName",
    "1.3.6.1.2.1.1.6.0": "sysLocation",
    "1.3.6.1.2.1.1.7.0": "sysServices",
    "1.3.6.1.2.1.1.8.0": "sysORLastChange"
}

# snmp hash table
SNMP_HASH_TABLE ={
    "1.3.6.1.6.3.1.1.6.1": "snmpSetSerialNo(1)",
    "1.3.6.1.6.3.10.2.1.1": "snmpEngineID(1)",
    "1.3.6.1.6.3.10.2.1.2": "snmpEngineBoots(2)",
    "1.3.6.1.6.3.10.2.1.3": "snmpEngineTime(3)",
    "1.3.6.1.6.3.10.2.1.4": "snmpEngineMaxMessageSize(4)",
    "1.3.6.1.6.3.11.2.1.1": "snmpUnknownSecurityModels(1)",
    "1.3.6.1.6.3.11.2.1.2": "snmpInvalidMsgs(2)",
    "1.3.6.1.6.3.11.2.1.3": "snmpUnknownPDUHandlers(3)",
    "1.3.6.1.6.3.12.1.1": "snmpTargetSpinLock(1)",
    "1.3.6.1.6.3.12.1.4": "snmpUnavailableContexts(4)",
    "1.3.6.1.6.3.12.1.5": "snmpUnknownContexts(5)"
}




