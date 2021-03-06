include MainMerit

proc mainConsensus() {.forceCheck: [].} =
    {.gcsafe.}:
        try:
            consensus = newConsensus(
                functions,
                database,
                merit.state,
                params.SEND_DIFFICULTY.toHash(384),
                params.DATA_DIFFICULTY.toHash(384)
            )
        except ValueError:
            doAssert(false, "Invalid initial Send/Data difficulty.")

        functions.consensus.getSendDifficulty = proc (): Hash[384] {.inline, forceCheck: [].} =
            consensus.filters.send.difficulty
        functions.consensus.getDataMinimumDifficulty = proc (): Hash[384] {.inline, forceCheck: [].} =
            minimumDataDifficulty
        functions.consensus.getDataDifficulty = proc (): Hash[384] {.inline, forceCheck: [].} =
            consensus.filters.data.difficulty

        #Provide access to if a holder is malicious.
        functions.consensus.isMalicious = proc (
            nick: uint16
        ): bool {.inline, forceCheck: [].} =
            consensus.malicious.hasKey(nick)

        #Provides access to a holder's nonce.
        functions.consensus.getNonce = proc (
            holder: uint16
        ): int {.inline, forceCheck: [].} =
            consensus.getNonce(holder)

        #Get if a hash has an archived packet or not.
        #Any hash with holder(s) that isn't unmentioned has an archived packet.
        functions.consensus.hasArchivedPacket = proc (
            hash: Hash[384]
        ): bool {.forceCheck: [
            IndexError
        ].} =
            var status: TransactionStatus
            try:
                status = consensus.getStatus(hash)
            except IndexError as e:
                fcRaise e

            return (status.holders.len != 0) and (not consensus.unmentioned.contains(hash))

        #Get a Transaction's status.
        functions.consensus.getStatus = proc (
            hash: Hash[384]
        ): TransactionStatus {.forceCheck: [
            IndexError
        ].} =
            try:
                result = consensus.getStatus(hash)
            except IndexError:
                raise newException(IndexError, "Couldn't find a Status for that hash.")

        functions.consensus.getThreshold = proc (
            epoch: int
        ): int {.inline, forceCheck: [].} =
            merit.state.nodeThresholdAt(epoch)

        functions.consensus.getPending = proc (): tuple[
            packets: seq[VerificationPacket],
            aggregate: BLSSignature
        ] {.inline, forceCheck: [].} =
            consensus.getPending()

        #Handle SignedVerifications.
        functions.consensus.addSignedVerification = proc (
            verif: SignedVerification
        ) {.forceCheck: [
            ValueError,
            DataExists
        ].} =
            #Print that we're adding the SignedVerification.
            echo "Adding a new Signed Verification."

            #Check if this is cause for a MaliciousMeritRemoval.
            try:
                consensus.checkMalicious(merit.state, verif)
            #Invalid signature.
            except ValueError as e:
                raise e
            #MeritHolder committed a malicious act against the network.
            except MaliciousMeritHolder as e:
                #Flag the MeritRemoval.
                consensus.flag(merit.blockchain, merit.state, cast[SignedMeritRemoval](e.removal))

                try:
                    #Broadcast the first MeritRemoval.
                    functions.network.broadcast(
                        MessageType.SignedMeritRemoval,
                        cast[SignedMeritRemoval](consensus.malicious[verif.holder][0]).signedSerialize()
                    )
                except KeyError as e:
                    doAssert(false, "Couldn't get the MeritRemoval of someone who just had one created: " & e.msg)
                return

            #See if the Transaction exists.
            try:
                discard transactions[verif.hash]
            except IndexError:
                raise newException(ValueError, "Unknown Verification.")

            #Add the SignedVerification to the Elements DAG.
            try:
                consensus.add(merit.state, verif)
            except DataExists as e:
                raise e

            echo "Successfully added a new Signed Verification."

            #Broadcast the SignedVerification.
            functions.network.broadcast(
                MessageType.SignedVerification,
                verif.signedSerialize()
            )

        #Handle VerificationPackets.
        functions.consensus.addVerificationPacket = proc (
            packet: VerificationPacket
        ) {.forceCheck: [].} =
            #Print that we're adding the VerificationPacket.
            echo "Adding a new Verification Packet from a Block."

            #Add the Verification to the Consensus DAG.
            consensus.add(merit.state, packet)

            echo "Successfully added a new Verification Packet."

        #Handle SendDifficulties.
        functions.consensus.addSendDifficulty = proc (
            sendDiff: SendDifficulty
        ) {.forceCheck: [].} =
            #Print that we're adding the SendDifficulty.
            echo "Adding a new Send Difficulty from a Block."

            #Add the SendDifficulty to the Consensus DAG.
            consensus.add(merit.state, sendDiff)

            echo "Successfully added a new Send Difficulty."

        #Handle SignedSendDifficulties.
        functions.consensus.addSignedSendDifficulty = proc (
            sendDiff: SignedSendDifficulty
        ) {.forceCheck: [
            ValueError
        ].} =
            #Print that we're adding the SendDifficulty.
            echo "Adding a new Send Difficulty."

            #Add the SendDifficulty.
            try:
                consensus.add(merit.state, sendDiff)
            except ValueError as e:
                raise e

            echo "Successfully added a new Signed Send Difficulty."

            #Broadcast the SendDifficulty.
            functions.network.broadcast(
                MessageType.SignedSendDifficulty,
                sendDiff.signedSerialize()
            )

        #Handle DataDifficulties.
        functions.consensus.addDataDifficulty = proc (
            dataDiff: DataDifficulty
        ) {.forceCheck: [].} =
            #Print that we're adding the DataDifficulty.
            echo "Adding a new Data Difficulty from a Block."

            #Add the DataDifficulty to the Consensus DAG.
            consensus.add(merit.state, dataDiff)

            echo "Successfully added a new Data Difficulty."

        #Handle SignedDataDifficulties.
        functions.consensus.addSignedDataDifficulty = proc (
            dataDiff: SignedDataDifficulty
        ) {.forceCheck: [
            ValueError
        ].} =
            #Print that we're adding the DataDifficulty.
            echo "Adding a new Data Difficulty."

            #Add the DataDifficulty.
            try:
                consensus.add(merit.state, dataDiff)
            except ValueError as e:
                raise e

            echo "Successfully added a new Signed Data Difficulty."

            #Broadcast the DataDifficulty.
            functions.network.broadcast(
                MessageType.SignedDataDifficulty,
                dataDiff.signedSerialize()
            )

        #Handle SignedMeritRemovals.
        functions.consensus.addSignedMeritRemoval = proc (
            mr: SignedMeritRemoval
        ) {.forceCheck: [
            ValueError
        ].} =
            #Print that we're adding the MeritRemoval.
            echo "Adding a new Merit Removal."

            #Add the MeritRemoval.
            try:
                consensus.add(merit.blockchain, merit.state, mr)
            except ValueError as e:
                raise e

            echo "Successfully added a new Signed Merit Removal."

            #Broadcast the first MeritRemoval.
            try:
                functions.network.broadcast(
                    MessageType.SignedMeritRemoval,
                    cast[SignedMeritRemoval](consensus.malicious[mr.holder][0]).signedSerialize()
                )
            except KeyError as e:
                doAssert(false, "Couldn't get the MeritRemoval of someone who just had one created: " & e.msg)
