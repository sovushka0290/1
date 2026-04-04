import json
import os

idl_path = "protoqol_core/target/idl/protoqol_core_compat.json"

with open(idl_path, "r") as f:
    idl = json.load(f)

# Hard-reset instructions to ONLY what we need for setup
# and force-format it for legacy anchorpy
idl["instructions"] = [
    {
      "name": "add_oracle",
      "accounts": [
        {"name": "oracle_registry", "isMut": True, "isSigner": False},
        {"name": "admin", "isMut": True, "isSigner": True},
        {"name": "system_program", "isMut": False, "isSigner": False}
      ],
      "args": [{"name": "oracle_pubkey", "type": "publicKey"}]
    },
    {
      "name": "initialize_protocol",
      "accounts": [
        {"name": "stats", "isMut": True, "isSigner": False},
        {"name": "admin", "isMut": True, "isSigner": True},
        {"name": "system_program", "isMut": False, "isSigner": False}
      ],
      "args": []
    }
]

# Simple types for compatibility
idl["types"] = []
idl["accounts"] = []

with open(idl_path, "w") as f:
    json.dump(idl, f, indent=2)

print("✓ IDL Hard-Reset to legacy setup format.")

