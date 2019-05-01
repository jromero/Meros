#Errors lib.
import ../../../lib/Errors

#Util lib.
import ../../../lib/Util

#Hash lib.
import ../../../lib/Hash

#MinerWallet lib.
import ../../../Wallet/MinerWallet

#Verification object.
import ../../../Database/Verifications/objects/VerificationObj

#Common serialization functions.
import ../SerializeCommon

#Serialize a Verification.
func serialize*(
    verif: Verification
): string {.forceCheck: [].} =
    result =
        verif.verifier.toString() &
        verif.nonce.toBinary().pad(INT_LEN) &
        verif.hash.toString()