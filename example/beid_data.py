# 
# This example is a python implementation of the data.c example
# provided with the Belgian EID-MW SDK
# 
# https://github.com/Fedict/eid-mw
#
# https://nlnetlabs.nl/downloads/publications/hsm/hsm_node9.html
# pkcs11-tool -L -v --module ./cardcomm/pkcs11/src/.libs/libbeidpkcs11.so
#
import os
import cffi
import re

ffi = cffi.FFI()

#
# platform dependent macro definitions
#

ck_callback_function = re.compile(r'typedef CK_CALLBACK_FUNCTION\((?P<returnType>\w*), (?P<name>\w*)\)\(')

#
# type definitions
#
pkcs11t = os.path.join('doc', 'sdk', 'include', 'rsaref220', 'pkcs11t.h')
type_definitions = []
with open(pkcs11t) as definition_file:
    for line in definition_file.readlines():
        if line.startswith('#if'):
            continue
        if line.startswith('#endif'):
            continue
        #
        # begin skip lines
        #
        if line.startswith('#define CKA_UNWRAP_TEMPLATE'):
            continue
        elif line.startswith('#define CKA_ALLOWED_MECHANISMS'):
            continue
        elif line.startswith('#define CKA_SUB_PRIME_BITS'):
            continue
        elif line.startswith('#define TRUE'):
            line = '#define TRUE 1'
        elif line.startswith('#define FALSE'):
            line = '#define FALSE 0'
        elif line.startswith('#define CKA_WRAP_TEMPLATE'):
            continue
        #
        # end skip lines
        #
        line = line.replace('\\', '')
        line = line.replace('(~0UL)', '0xffffffff')
        line = line.replace('CK_PTR', '*')
        ck_match = ck_callback_function.search(line)
        if ck_match:
            new_line = 'typedef {0} (* {1})('.format(
                ck_match.group('returnType'),
                ck_match.group('name')
            )
            type_definitions.append(new_line)
            continue
        
        type_definitions.append(line)

ffi.cdef(
    '\n'.join(type_definitions)
)

#
# functions
#

ffi.cdef("""
CK_RV C_Initialize (
  CK_VOID_PTR   pInitArgs  /* if this is not NULL_PTR, it gets
                            * cast to CK_C_INITIALIZE_ARGS_PTR
                            * and dereferenced */
);

CK_RV C_GetSlotList (
  CK_BBOOL       tokenPresent,  /* only slots with tokens? */
  CK_SLOT_ID_PTR pSlotList,     /* receives array of slot IDs */
  CK_ULONG_PTR   pulCount       /* receives number of slots */
);

CK_RV C_OpenSession (
  CK_SLOT_ID            slotID,        /* the slot's ID */
  CK_FLAGS              flags,         /* from CK_SESSION_INFO */
  CK_VOID_PTR           pApplication,  /* passed to callback */
  CK_NOTIFY             Notify,        /* callback function */
  CK_SESSION_HANDLE_PTR phSession      /* gets session handle */
);

CK_RV C_CloseSession (
  CK_SESSION_HANDLE hSession  /* the session's handle */
);

CK_RV C_GetSlotInfo (
  CK_SLOT_ID       slotID,  /* the ID of the slot */
  CK_SLOT_INFO_PTR pInfo    /* receives the slot information */
);

CK_RV C_FindObjectsInit (
  CK_SESSION_HANDLE hSession,   /* the session's handle */
  CK_ATTRIBUTE_PTR  pTemplate,  /* attribute values to match */
  CK_ULONG          ulCount     /* attrs in search template */
);

CK_RV C_FindObjects (
 CK_SESSION_HANDLE    hSession,          /* session's handle */
 CK_OBJECT_HANDLE_PTR phObject,          /* gets obj. handles */
 CK_ULONG             ulMaxObjectCount,  /* max handles to get */
 CK_ULONG_PTR         pulObjectCount     /* actual # returned */
);

CK_RV C_FindObjectsFinal (
  CK_SESSION_HANDLE hSession  /* the session's handle */
);

CK_RV C_GetAttributeValue (
  CK_SESSION_HANDLE hSession,   /* the session's handle */
  CK_OBJECT_HANDLE  hObject,    /* the object's handle */
  CK_ATTRIBUTE_PTR  pTemplate,  /* specifies attrs; gets vals */
  CK_ULONG          ulCount     /* attributes in template */
);

""")

eid_lib = ffi.dlopen('./cardcomm/pkcs11/src/.libs/libbeidpkcs11.so')
#eid_lib = ffi.dlopen('/usr/lib/x86_64-linux-gnu/libbeidpkcs11.so.0')
if eid_lib.C_Initialize(ffi.NULL) != 0:
    raise Exception('failed initialization')

# get slot count
slot_list = ffi.new('CK_SLOT_ID_PTR')
slot_count = ffi.new('CK_ULONG_PTR')
ret_val = eid_lib.C_GetSlotList(1, ffi.NULL, slot_count)
print(hex(ret_val))
print('slot count : ', slot_count[0])

# get slot list
slot_list = ffi.new('CK_SLOT_ID[100]')
slot_count = ffi.new('CK_ULONG_PTR')
ret_val = eid_lib.C_GetSlotList(1, slot_list, slot_count)
print(hex(ret_val))

for i in range(slot_count[0]):
    print('slot index :', i)
    slot_id = slot_list[i]
    print('slot id : ', slot_id)
    slot_info = ffi.new('CK_SLOT_INFO_PTR')
    ret_val = eid_lib.C_GetSlotInfo(slot_id, slot_info)
    print(hex(ret_val))
    print('slot description :', ffi.string(slot_info.slotDescription, 64))
    print('slot description :', ffi.string(slot_info.manufacturerID, 32))
    print('hardware version :', slot_info.hardwareVersion)
    print('flags :', slot_info.flags)
    session = ffi.new('CK_SESSION_HANDLE *')
    eid_lib.C_OpenSession(
        slot_id,
        eid_lib.CKF_SERIAL_SESSION,
        ffi.NULL, ffi.NULL,
        session)
    class_type = ffi.new("CK_ULONG[]", [eid_lib.CKO_DATA])
    object_template = ffi.new(
        'CK_ATTRIBUTE_PTR',
        {'type':eid_lib.CKA_CLASS, 'pValue':class_type,
         'ulValueLen':ffi.sizeof('CK_ULONG')}
    )
    object_handle = ffi.new('CK_OBJECT_HANDLE*')
    object_count = ffi.new('CK_ULONG_PTR')
    ret_val = eid_lib.C_FindObjectsInit(session[0], object_template, 1)
    print('find objects init : ', hex(ret_val))
    assert ret_val==0
    object_count[0] = 1

    while object_count[0] > 0:
        eid_lib.C_FindObjects(session[0], object_handle, 1, object_count)
        print('object id :', object_handle[0])
        label_template = ffi.new(
            'CK_ATTRIBUTE*',
            {'type':eid_lib.CKA_LABEL, 'pValue':ffi.NULL, 'ulValueLen':0}
        )
        eid_lib.C_GetAttributeValue(session[0], object_handle[0], label_template, 1)
        print('label size', label_template[0].ulValueLen)
        if label_template[0].ulValueLen > 0:
            label_template[0].pValue = ffi.new('char[]', label_template[0].ulValueLen)
            eid_lib.C_GetAttributeValue(session[0], object_handle[0], label_template, 1)
            value = ffi.cast('char*', label_template[0].pValue)
            print('label : ', ffi.string(value, label_template[0].ulValueLen))
            #print('object label', ffi.string(label_template[0].pValue, label_template[0].ulValueLen))
    eid_lib.C_FindObjectsFinal(session[0])
    eid_lib.C_CloseSession(session[0])

