#Meros RPC module.
import MerosRPC

#Async standard lib.
import asyncdispatch

#JSON standard lib.
import json

#Seq utils standard lib.
import sequtils

var
    #RPC.
    rpc: MerosRPC = waitFor newMerosRPC()
    #DB.
    db: JSONNode = %* {
        "verifications": {},
        "blockchain": [],
        "lattice": {}
    }
    #List of Lattice Entries.
    hashes: seq[string] = @[]

#Get every Block.
for nonce in 0 ..< waitFor rpc.merit.getHeight():
    db["blockchain"].add(waitFor rpc.merit.getBlock(nonce))

#Get every Verification.
for syncBlock in db["blockchain"]:
    for record in syncBlock["records"]:
        if not db["verifications"].hasKey(record["verifier"].getStr()):
            db["verifications"][record["verifier"].getStr()] = %* []

        for nonce in db["verifications"][record["verifier"].getStr()].len .. record["nonce"].getInt():
            var hash: JSONNode = (waitFor rpc.verifications.getVerification(record["verifier"].getStr(), nonce))["hash"]
            db["verifications"][record["verifier"].getStr()].add(
                hash
            )
            hashes.add(hash.getStr())

#Get every Entry.
hashes = hashes.deduplicate()
for hash in hashes:
    db["lattice"][hash] = waitFor rpc.lattice.getEntryByHash(hash)

#Get every Mint.
for nonce in 0 ..< waitFor rpc.lattice.getHeight("minter"):
    var mint: JSONNode = waitFor rpc.lattice.getEntryByIndex("minter", nonce)
    db["lattice"][mint["hash"].getStr()] = mint

#Write it to a file.
"data/db.json".writeFile(db.pretty(4))