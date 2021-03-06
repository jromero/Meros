#Types.
from typing import List, Tuple, Any

#Milagro sub-libraries.
from PythonTests.Libs.Milagro.PrivateKeysAndSignatures import MilagroCurve, Big384, FP1Obj, G1Obj, OctetObj, r
from PythonTests.Libs.Milagro.PublicKeysAndPairings import MilagroPairing, FP2Obj, G2Obj, FP12Obj

#CTypes.
from ctypes import Array, c_char_p, c_char, create_string_buffer, byref

#SHAKE256 standard function.
from hashlib import shake_256

A_FLAG: int = 1 << 5
B_FLAG: int = 1 << 6
C_FLAG: int = 1 << 7
CLEAR_FLAGS: int = ~(A_FLAG + B_FLAG + C_FLAG)

def msgToG(
    msg: bytes
) -> G1Obj:
    result: G1Obj = G1Obj()
    hashed: OctetObj = OctetObj()

    shake: Any = shake_256()
    shake.update(msg)
    hashed.val = c_char_p(shake.digest(48))
    hashed.len = 48
    hashed.max = 48

    MilagroCurve.ECP_BLS381_mapit(byref(result), hashed)
    return result

def serialize(
    g: Big384,
    largerY: bool
) -> bytearray:
    buffer: Array[c_char] = create_string_buffer(48)
    MilagroCurve.BIG_384_58_toBytes(buffer, g)

    result: bytearray = bytearray(buffer)
    result[0] = result[0] | C_FLAG

    inf: int = 1
    if result[0] == C_FLAG:
        while inf < 48:
            if result[inf] != 0:
                break
            inf += 1
        if inf == 48:
            result[0] = result[0] | B_FLAG
            return result

    if largerY:
        result[0] = result[0] | A_FLAG

    return result

def parse(
    gArg: bytes,
    second: bool = False
) -> Tuple[bool, bool, bool, Big384]:
    if len(gArg) != 48:
        raise Exception("Invalid length G.")

    flags = gArg[0]
    g: bytearray = bytearray(gArg)
    g[0] = g[0] & CLEAR_FLAGS

    if (not second) and (flags & C_FLAG == 0):
        raise Exception("Uncompressed G.")

    b: int = 1
    if flags & B_FLAG != 0:
        while b < 48:
            if g[b] != 0:
                break
            b += 1

    result: Big384 = Big384()
    MilagroCurve.BIG_384_58_fromBytesLen(result, c_char_p(bytes(g)), 48)

    return (flags & B_FLAG != 0, b == 48, flags & A_FLAG != 0, result)

class PublicKey():
    def __init__(
        self,
        key: bytes = bytes()
    ) -> None:
        self.value: G2Obj = G2Obj()
        if len(key) == 0:
            MilagroPairing.ECP2_BLS381_inf(byref(self.value))
            return

        if len(key) != 96:
            raise Exception("Invalid length Public Key.")

        if key[48] != (key[48] & CLEAR_FLAGS):
            raise Exception("G2's second G has flags set.")

        g1: Tuple[bool, bool, bool, Big384] = parse(key[0 : 48])
        g2: Tuple[bool, bool, bool, Big384] = parse(key[48 : 96], True)

        if g1[0] != (g1[1] & g2[1]):
            raise Exception("Infinite flag set improperly.")

        if g1[0]:
            MilagroPairing.ECP2_BLS381_inf(byref(self.value))
            return

        x: FP2Obj = FP2Obj()
        MilagroPairing.FP2_BLS381_from_BIGs(byref(x), g2[3], g1[3])
        if MilagroPairing.ECP2_BLS381_setx(byref(self.value), byref(x)) == 0:
            raise Exception("Invalid G2.")

        yNeg: FP2Obj = FP2Obj()
        cmpRes: int
        MilagroPairing.FP2_BLS381_neg(byref(yNeg), byref(self.value.y))

        a: Big384 = Big384()
        b: Big384 = Big384()
        MilagroCurve.FP_BLS381_redc(a, byref(self.value.y.b))
        MilagroCurve.FP_BLS381_redc(b, byref(yNeg.b))
        cmpRes = MilagroCurve.BIG_384_58_comp(a, b)
        if cmpRes == 0:
            MilagroCurve.FP_BLS381_redc(a, byref(self.value.y.a))
            MilagroCurve.FP_BLS381_redc(b, byref(yNeg.a))
            cmpRes = MilagroCurve.BIG_384_58_comp(a, b)

        if (cmpRes == 1) != g1[2]:
            self.value.y = yNeg

    def isInf(
        self
    ) -> bool:
        return int(MilagroPairing.ECP2_BLS381_isinf(byref(self.value))) == 1

    def serialize(
        self
    ) -> bytes:
        yNeg: FP2Obj = FP2Obj()
        cmpRes: int
        MilagroPairing.FP2_BLS381_neg(byref(yNeg), byref(self.value.y))

        a: Big384 = Big384()
        b: Big384 = Big384()
        MilagroCurve.FP_BLS381_redc(a, byref(self.value.y.b))
        MilagroCurve.FP_BLS381_redc(b, byref(yNeg.b))
        cmpRes = MilagroCurve.BIG_384_58_comp(a, b)
        if cmpRes == 0:
            MilagroCurve.FP_BLS381_redc(a, byref(self.value.y.a))
            MilagroCurve.FP_BLS381_redc(b, byref(yNeg.a))
            cmpRes = MilagroCurve.BIG_384_58_comp(a, b)

        MilagroCurve.FP_BLS381_redc(a, byref(self.value.x.a))
        MilagroCurve.FP_BLS381_redc(b, byref(self.value.x.b))
        result: bytearray = serialize(b, cmpRes == 1)
        result += serialize(a, False)
        result[48] = result[48] & CLEAR_FLAGS
        return bytes(result)

    @staticmethod
    def aggregate(
        keys: List[Any]
    ) -> Any:
        result: PublicKey = PublicKey.__new__(PublicKey)
        result.value = G2Obj()

        if not keys:
            MilagroPairing.ECP2_BLS381_inf(byref(result.value))
            return result

        result.value = keys[0].value
        for k in range(1, len(keys)):
            if keys[k].isInf():
                MilagroPairing.ECP2_BLS381_inf(byref(result.value))
                return result

            if not MilagroPairing.ECP2_BLS381_add(byref(result.value), byref(keys[k].value)) != 0:
                raise Exception("Milagro failed to add G2s.")

        return result

#pylint: disable=too-few-public-methods
class AggregationInfo():
    def __init__(
        self,
        key: PublicKey,
        msgArg: bytes
    ) -> None:
        if key.isInf():
            raise Exception("Infinite Public Key passed to newAggregationInfo.")

        msg: G1Obj = msgToG(msgArg)
        self.value: FP12Obj = FP12Obj()
        MilagroPairing.PAIR_BLS381_ate(byref(self.value), byref(key.value), byref(msg))

    @staticmethod
    def aggregate(
        agInfos: List[Any]
    ) -> Any:
        if not agInfos:
            raise Exception("No Aggregation Infos passed to aggregate.")

        result: AggregationInfo = AggregationInfo.__new__(AggregationInfo)
        result.value = agInfos[0].value
        for i in range(1, len(agInfos)):
            MilagroPairing.FP12_BLS381_mul(byref(result.value), byref(agInfos[i]))

        return result

class Signature():
    def __init__(
        self,
        sig: bytes = bytes()
    ) -> None:
        self.value: G1Obj = G1Obj()
        if len(sig) == 0:
            MilagroPairing.ECP_BLS381_inf(byref(self.value))
            return

        g: Tuple[bool, bool, bool, Big384] = parse(sig)

        if g[0] != g[1]:
            raise Exception("Infinite flag set improperly.")

        if g[0]:
            MilagroPairing.ECP_BLS381_inf(byref(self.value))
            return

        if MilagroPairing.ECP_BLS381_setx(byref(self.value), g[3], 0) != 1:
            raise Exception("Invalid G1.")

        yNeg: FP1Obj = FP1Obj()
        MilagroPairing.FP_BLS381_neg(byref(yNeg), byref(self.value.y))

        a: Big384 = Big384()
        b: Big384 = Big384()
        MilagroCurve.FP_BLS381_redc(a, byref(self.value.y))
        MilagroCurve.FP_BLS381_redc(b, byref(yNeg))
        if (MilagroCurve.BIG_384_58_comp(a, b) == 1) != g[2]:
            if MilagroPairing.ECP_BLS381_setx(byref(self.value), g[3], 1) != 1:
                raise Exception("Setting a proven valid X failed.")

    def isInf(
        self
    ) -> bool:
        return int(MilagroCurve.ECP_BLS381_isinf(byref(self.value))) == 1

    def verify(
        self,
        agInfo: AggregationInfo
    ) -> bool:
        if self.isInf():
            return False

        sig: G1Obj = self.value
        generator: G2Obj = G2Obj()
        sigPairing: FP12Obj = FP12Obj()

        MilagroCurve.ECP_BLS381_neg(byref(sig))
        MilagroPairing.ECP2_BLS381_generator(byref(generator))
        MilagroPairing.PAIR_BLS381_ate(byref(sigPairing), byref(generator), byref(sig))

        MilagroPairing.FP12_BLS381_ssmul(byref(sigPairing), byref(agInfo.value))
        MilagroPairing.PAIR_BLS381_fexp(byref(sigPairing))
        return int(MilagroPairing.FP12_BLS381_isunity(byref(sigPairing))) == 1

    def serialize(
        self
    ) -> bytes:
        x: Big384 = Big384()
        y: Big384 = Big384()
        MilagroCurve.ECP_BLS381_get(x, y, byref(self.value))

        yNeg: Big384 = Big384()
        MilagroCurve.FP_BLS381_neg(self.value.y, self.value.y)
        MilagroCurve.ECP_BLS381_get(x, yNeg, byref(self.value))
        MilagroCurve.FP_BLS381_neg(self.value.y, self.value.y)

        return bytes(serialize(x, MilagroCurve.BIG_384_58_comp(y, yNeg) == 1))

    @staticmethod
    def aggregate(
        sigs: List[Any]
    ) -> Any:
        result: Signature = Signature.__new__(Signature)
        result.value = G1Obj()

        if not sigs:
            MilagroPairing.ECP_BLS381_inf(byref(result.value))
            return result

        result.value = sigs[0].value
        for s in range(1, len(sigs)):
            if sigs[s].isInf():
                MilagroPairing.ECP_BLS381_inf(byref(result.value))
                return result

            MilagroPairing.ECP_BLS381_add(byref(result.value), byref(sigs[s].value))

        return result

class PrivateKey():
    def __init__(
        self,
        keyArg: bytes
    ) -> None:
        self.value: Big384 = Big384()
        MilagroCurve.BIG_384_58_fromBytesLen(self.value, c_char_p(keyArg), 48)
        MilagroCurve.BIG_384_58_mod(self.value, r)

    def toPublicKey(
        self
    ) -> PublicKey:
        result: PublicKey = PublicKey.__new__(PublicKey)
        result.value = G2Obj()

        MilagroPairing.ECP2_BLS381_generator(byref(result.value))
        MilagroPairing.ECP2_BLS381_mul(byref(result.value), self.value)

        return result

    def sign(
        self,
        msgArg: bytes
    ) -> Signature:
        result: Signature = Signature.__new__(Signature)
        result.value = msgToG(msgArg)
        MilagroPairing.ECP_BLS381_mul(byref(result.value), byref(self.value))
        return result

    def serialize(
        self
    ) -> bytes:
        result: Array[c_char] = create_string_buffer(48)
        MilagroCurve.BIG_384_58_toBytes(result, self.value)
        return bytes(result)
