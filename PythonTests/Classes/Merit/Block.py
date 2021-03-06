#Types.
from typing import Dict, Any

#BLS lib.
from PythonTests.Libs.BLS import PrivateKey

#BlockHeader and BlockBody classes.
from PythonTests.Classes.Merit.BlockHeader import BlockHeader
from PythonTests.Classes.Merit.BlockBody import BlockBody

#Argon2 lib.
import argon2

#Block class.
class Block:
    #Constructor.
    def __init__(
        self,
        header: BlockHeader,
        body: BlockBody
    ) -> None:
        self.header: BlockHeader = header
        self.body: BlockBody = body

    #Mine.
    def mine(
        self,
        privKey: PrivateKey,
        difficulty: int
    ) -> None:
        self.header.proof = -1
        while (
            (self.header.proof == -1) or
            (int.from_bytes(self.header.hash, "big") < difficulty)
        ):
            self.header.proof += 1
            self.header.hash = argon2.low_level.hash_secret_raw(
                self.header.serializeHash(),
                self.header.proof.to_bytes(8, "big"),
                1,
                65536,
                1,
                48,
                argon2.low_level.Type.D
            )
            self.header.signature = privKey.sign(self.header.hash).serialize()

            self.header.hash = argon2.low_level.hash_secret_raw(
                self.header.hash,
                self.header.signature,
                1,
                65536,
                1,
                48,
                argon2.low_level.Type.D
            )

    #Serialize.
    def serialize(
        self
    ) -> bytes:
        return self.header.serialize() + self.body.serialize(self.header.sketchSalt)

    #Block -> JSON.
    def toJSON(
        self
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = self.body.toJSON()
        result["header"] = self.header.toJSON()
        result["hash"] = self.header.hash.hex().upper()
        return result

    #JSON -> Block.
    @staticmethod
    def fromJSON(
        json: Dict[str, Any]
    ) -> Any:
        return Block(
            BlockHeader.fromJSON(json["header"]),
            BlockBody.fromJSON(json)
        )
