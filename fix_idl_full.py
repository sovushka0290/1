
import json
import os

idl_path = "protoqol_core/target/idl/protoqol_core_compat.json"
orig_idl = "protoqol_core/target/idl/protoqol_core.json"

with open(orig_idl, "r") as f:
    idl = json.load(f)

# Convert all instructions to legacy format
for inst in idl.get("instructions", []):
    if "discriminator" in inst: del inst["discriminator"]
    for acc in inst.get("accounts", []):
        acc["isMut"] = acc.get("writable", False)
        acc["isSigner"] = acc.get("signer", False)
        for key in ["writable", "signer", "pda", "address"]:
            if key in acc: del acc[key]
    for arg in inst.get("args", []):
        if arg.get("type") == "pubkey": arg["type"] = "publicKey"

# Convert all types
for acc_type in idl.get("types", []):
    if "type" in acc_type and "fields" in acc_type["type"]:
        for field in acc_type["type"]["fields"]:
            if field.get("type") == "pubkey": field["type"] = "publicKey"

# Clean top level
if "metadata" in idl:
    for k,v in idl["metadata"].items(): idl[k] = v
    del idl["metadata"]
if "address" in idl: del idl["address"]

with open(idl_path, "w") as f:
    json.dump(idl, f, indent=2)

print("✓ Full IDL restored to legacy compatibility format.")
