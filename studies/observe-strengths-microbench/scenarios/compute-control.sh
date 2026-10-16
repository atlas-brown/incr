#!/usr/bin/env bash
set -e
set -o pipefail
IFS= read -r version < config.txt
IFS= read -r limit < limit.txt
/usr/bin/openssl kdf -keylen 32 -kdfopt digest:SHA256 -kdfopt "pass:$version" -kdfopt salt:fixed -kdfopt "iter:$((limit * 25000))" PBKDF2 </dev/null
