#State DB Test.

#Util lib.
import ../../../../src/lib/Util

#Hash lib.
import ../../../../src/lib/Hash

#MinerWallet lib.
import ../../../../src/Wallet/MinerWallet

#Element libs.
import ../../../../src/Database/Consensus/Elements/Elements

#Difficulty, Block, Blockchain, and State libs.
import ../../../../src/Database/Merit/Difficulty
import ../../../../src/Database/Merit/Block
import ../../../../src/Database/Merit/Blockchain
import ../../../../src/Database/Merit/State

#Elements Testing lib.
import ../../ConsensusTests/ElementsTests/TestElements

#Merit Testing lib.
import ../TestMerit

#Compare Merit lib.
import ../CompareMerit

#Random standard lib.
import random

proc test*() =
    #Seed random.
    randomize(int64(getTime()))

    var
        #Database.
        db: DB = newTestDatabase()
        #Blockchain.
        blockchain: Blockchain = newBlockchain(
            db,
            "STATE_TEST",
            30,
            "".pad(48).toHash(384)
        )
        #State.
        state: State = newState(db, 30, blockchain.height)

        #Thresholds.
        thresholds: seq[int] = @[]

        #Miners.
        miners: seq[MinerWallet] = @[]
        #Miners we can remove Merit from.
        removable: seq[MinerWallet]
        #Selected miner to remove Merit from/for the next Block.
        miner: int

        #Elements we're adding to the Block.
        elements: seq[BlockElement]
        #Block we're mining.
        mining: Block

    #Iterate over 20 'rounds'.
    for r in 1 .. 20:
        #Add the current Node Threshold to thresholds.
        thresholds.add(state.protocolThresholdAt(r))

        #Remove Merit from a random amount of Merit Holders every few Blocks.
        if rand(3) == 0:
            removable = miners
            for _ in 0 .. min(rand(2), high(miners)):
                miner = rand(high(removable))
                elements.add(
                    newRandomMeritRemoval(
                        state.reverseLookup(removable[miner].publicKey)
                    )
                )
                removable.del(miner)

        #Decide if this is a nickname or new miner Block.
        if (miners.len == 0) or (rand(2) == 0):
            #New miner.
            miner = miners.len
            miners.add(newMinerWallet())

            #Create the Block with the new miner.
            mining = newBlankBlock(
                last = blockchain.tail.header.hash,
                miner = miners[miner],
                elements = elements
            )
        else:
            #Grab a random miner.
            miner = rand(high(miners))

            #Create the Block with the existing miner.
            mining = newBlankBlock(
                last = blockchain.tail.header.hash,
                nick = uint16(miner),
                miner = miners[miner],
                elements = elements
            )

        #Mine it.
        while blockchain.difficulty.difficulty > mining.header.hash:
            miners[miner].hash(mining.header, mining.header.proof + 1)

        #Add it to the Blockchain and State.
        blockchain.processBlock(mining)
        discard state.processBlock(blockchain)

        #Commit the DB.
        db.commit(blockchain.height)

        #Clear the Elements.
        elements = @[]

        #Reload and compare the States.
        compare(state, newState(db, 30, blockchain.height))

    #Check that the State saved it had 0 Merit at the start.
    assert(state.loadUnlocked(0) == 0)
    #Check the threshold is just plus one.
    assert(state.protocolThresholdAt(0) == 1)

    #Check every existing threshold.
    for t in 0 ..< thresholds.len:
        assert(state.protocolThresholdAt(t) == thresholds[t])

    #Checking loading the Merit for the latest Block returns the State's Merit.
    assert(state.loadUnlocked(21) == state.unlocked)

    #Check future thresholds.
    for t in len(thresholds) + 2 ..< len(thresholds) + 22:
        assert(state.protocolThresholdAt(t) == min(state.unlocked + (t - 21), state.deadBlocks) div 2 + 1)

    echo "Finished the Database/Merit/State/DB Test."
