#Types.
from typing import IO, Dict, List, Any

#BLS lib.
from PythonTests.Libs.BLS import PrivateKey, PublicKey

#DataDifficulty class.
from PythonTests.Classes.Consensus.DataDifficulty import SignedDataDifficulty

#Blockchain classes.
from PythonTests.Classes.Merit.BlockHeader import BlockHeader
from PythonTests.Classes.Merit.BlockBody import BlockBody
from PythonTests.Classes.Merit.Block import Block
from PythonTests.Classes.Merit.Blockchain import Blockchain

#Blake2b standard function.
from hashlib import blake2b

#JSON standard lib.
import json

#Blockchain.
bbFile: IO[Any] = open("PythonTests/Vectors/Merit/BlankBlocks.json", "r")
blocks: List[Dict[str, Any]] = json.loads(bbFile.read())
blockchain: Blockchain = Blockchain.fromJSON(
    b"MEROS_DEVELOPER_NETWORK",
    60,
    int("FAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", 16),
    blocks
)
bbFile.close()

#BLS Keys.
blsPrivKey: PrivateKey = PrivateKey(blake2b(b'\0', digest_size=48).digest())
blsPubKey: PublicKey = blsPrivKey.toPublicKey()

#Create a DataDifficulty.
dataDiff: SignedDataDifficulty = SignedDataDifficulty(bytes.fromhex("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"), 0)
dataDiff.sign(0, blsPrivKey)

#Generate a Block containing the DataDifficulty.
block = Block(
    BlockHeader(
        0,
        blockchain.last(),
        BlockHeader.createContents([], [dataDiff.toSignedElement()]),
        1,
        bytes(4),
        bytes(48),
        0,
        blockchain.blocks[-1].header.time + 1200
    ),
    BlockBody([], [dataDiff.toSignedElement()], dataDiff.signature)
)
#Mine it.
block.mine(blsPrivKey, blockchain.difficulty())

#Add it.
blockchain.add(block)
print("Generated DataDifficulty Block " + str(len(blockchain.blocks)) + ".")

#Mine 24 more Blocks until there's a vote.
for _ in range(24):
    block = Block(
        BlockHeader(
            0,
            blockchain.last(),
            bytes(48),
            1,
            bytes(4),
            bytes(48),
            0,
            blockchain.blocks[-1].header.time + 1200
        ),
        BlockBody()
    )
    #Mine it.
    block.mine(blsPrivKey, blockchain.difficulty())

    #Add it.
    blockchain.add(block)
    print("Generated DataDifficulty Block " + str(len(blockchain.blocks)) + ".")

#Now that we have aa vote, update our vote.
dataDiff = SignedDataDifficulty(bytes.fromhex("888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888"), 1)
dataDiff.sign(0, blsPrivKey)

#Generate a Block containing the new DataDifficulty.
block = Block(
    BlockHeader(
        0,
        blockchain.last(),
        BlockHeader.createContents([], [dataDiff.toSignedElement()]),
        1,
        bytes(4),
        bytes(48),
        0,
        blockchain.blocks[-1].header.time + 1200
    ),
    BlockBody([], [dataDiff.toSignedElement()], dataDiff.signature)
)
#Mine it.
block.mine(blsPrivKey, blockchain.difficulty())

#Add it.
blockchain.add(block)
print("Generated DataDifficulty Block " + str(len(blockchain.blocks)) + ".")

result: Dict[str, Any] = {
    "blockchain": blockchain.toJSON()
}
vectors: IO[Any] = open("PythonTests/Vectors/Consensus/Difficulties/DataDifficulty.json", "w")
vectors.write(json.dumps(result))
vectors.close()
