# This is a guide for any Debian based system.

### Dependencies

Meros requires:
- Git
- GCC/G++
- Make (for LMDB)
- CMake (for BLS)

- Nim devel
- Nimble

- GMP
- Chia's BLS library
- LibSodium
- LMDB

To install the needed apt packages: `sudo apt-get install gcc g++ make cmake curl git libgmp3-dev gtk+-3.0 at-spi2-core webkit2gtk-4.0`

To install Nim/Nimble:
```
curl https://nim-lang.org/choosenim/init.sh -sSf | sh
choosenim devel
```

To install the Nimble packages: `nimble install BN https://github.com/MerosCrypto/ForceCheck https://github.com/MerosCrypto/Argon2 https://github.com/MerosCrypto/mc_bls https://github.com/MerosCrypto/mc_ed25519 https://github.com/MerosCrypto/mc_lmdb https://github.com/MerosCrypto/Nim-Meros-RPC https://github.com/MerosCrypto/mc_webview finals nimcrypto`

For instructions on setting up BLS, see https://github.com/MerosCrypto/mc_bls.

For instructions on setting up LibSodium, see https://github.com/MerosCrypto/mc_ed25519.

For instructions on setting up LMDB, see https://github.com/MerosCrypto/mc_lmdb.

### Meros

```
git clone https://github.com/MerosCrypto/Meros.git
cd Meros
nim c src/main.nim
```

If you want to build an optimized version, put `-d:release` after `c`. There's also a headless version which doesn't import any GUI files available via `-d:nogui`.

The binary will be available under `build/`.