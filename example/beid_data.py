#
# This example is a python implementation of the data.c example
# provided with the Belgian EID-MW SDK
#
# https://github.com/Fedict/eid-mw
#
# pkcs11-tool -L -v --module ./cardcomm/pkcs11/src/.libs/libbeidpkcs11.so
#
from pkcs11 import ffi

# the self compiled module appears not to work, because it cannot ask
# a question on wether the application can access the card

#eid_lib = ffi.dlopen('./cardcomm/pkcs11/src/.libs/libbeidpkcs11.so')
eid_lib = ffi.dlopen('/usr/lib/x86_64-linux-gnu/libbeidpkcs11.so.0')
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
    label = ffi.new("char[]", b"surname")
    object_template = ffi.new(
        'CK_ATTRIBUTE[2]',[
        {'type':eid_lib.CKA_CLASS,
         'pValue':class_type,
         'ulValueLen':ffi.sizeof('CK_ULONG')},
        {'type':eid_lib.CKA_LABEL,
         'pValue':label,
         'ulValueLen':ffi.sizeof("char")*len(b"surname")}
        ]
    )
    object_handle = ffi.new('CK_OBJECT_HANDLE*')
    object_count = ffi.new('CK_ULONG_PTR')
    ret_val = eid_lib.C_FindObjectsInit(session[0], object_template, 2)
    print('find objects init : ', hex(ret_val))
    assert ret_val==0
    object_count[0] = 1

    while object_count[0] > 0:
        eid_lib.C_FindObjects(session[0], object_handle, 1, object_count)
        print('object id :', object_handle[0])
        value_template = ffi.new(
            'CK_ATTRIBUTE*',
            {'type':eid_lib.CKA_VALUE, 'pValue':ffi.NULL, 'ulValueLen':0}
        )
        eid_lib.C_GetAttributeValue(session[0], object_handle[0], value_template, 1)
        print('value size', value_template[0].ulValueLen)
        if value_template[0].ulValueLen > 0:
            value_template[0].pValue = ffi.new('char[]', value_template[0].ulValueLen)
            eid_lib.C_GetAttributeValue(session[0], object_handle[0], value_template, 1)
            value = ffi.cast('char*', value_template[0].pValue)
            print('value : ', ffi.string(value, value_template[0].ulValueLen))
    eid_lib.C_FindObjectsFinal(session[0])
    eid_lib.C_CloseSession(session[0])
