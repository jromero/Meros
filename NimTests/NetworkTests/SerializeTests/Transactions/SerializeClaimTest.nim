#Serialize Claim Test.

#Util lib.
import ../../../../src/lib/Util

#Hash lib.
import ../../../../src/lib/Hash

#Wallet libs.
import ../../../../src/Wallet/Wallet
import ../../../../src/Wallet/MinerWallet

#Mint and Claim lib.
import ../../../../src/Database/Transactions/Mint as MintFile
import ../../../../src/Database/Transactions/Claim

#Serialize libs.
import ../../../../src/Network/Serialize/Transactions/SerializeClaim
import ../../../../src/Network/Serialize/Transactions/ParseClaim

#Compare Transactions lib.
import ../../../DatabaseTests/TransactionsTests/CompareTransactions

#Random standard lib.
import random

proc test*() =
    #Seed Random via the time.
    randomize(int64(getTime()))

    var
        #Inputs.
        inputs: seq[FundedInput]
        #Input Hash.
        inputHash: Hash[384]
        #Claim.
        claim: Claim
        #Reloaded Claim.
        reloaded: Claim
        #Wallet.
        wallet: Wallet = newWallet("")

    #Test 255 serializations.
    for s in 0 .. 255:
        #Create inputs.
        inputs = newSeq[FundedInput](rand(254) + 1)
        for i in 0 ..< inputs.len:
            for b in 0 ..< inputHash.data.len:
                inputHash.data[b] = uint8(rand(255))
            inputs[i] = newFundedInput(inputHash, rand(255))

        #Create the Claim.
        claim = newClaim(inputs, wallet.next(last = uint32(s * 1000)).publicKey)

        #The Meros protocol requires this signature be produced by the aggregate of every unique MinerWallet paid via the Mints.
        #Serialization/Parsing doesn't care at all.
        newMinerWallet().sign(claim)

        #Serialize it and parse it back.
        reloaded = claim.serialize().parseClaim()

        #Compare the Claims.
        compare(claim, reloaded)

        #Test the serialized versions.
        assert(claim.serialize() == reloaded.serialize())

    echo "Finished the Network/Serialize/Transactions/Claim Test."
