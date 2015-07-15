import os
import cffi
import re

ffi = cffi.FFI()
ffi.set_source("_ffi", None)

#
# platform dependent macro definitions
#
ck_callback_function = re.compile(
    r'typedef CK_CALLBACK_FUNCTION\((?P<returnType>\w*), (?P<name>\w*)\)\(')

#
# type definitions
#
pkcs11t = os.path.join('inc', 'pkcs11t.h')
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

CK_RV C_Finalize (
  CK_VOID_PTR   pReserved  /* reserved.  Should be NULL_PTR */
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

CK_RV C_GetTokenInfo (
  CK_SLOT_ID        slotID,  /* ID of the token's slot */
  CK_TOKEN_INFO_PTR pInfo    /* receives the token information */
);
""")

ffi.compile()
