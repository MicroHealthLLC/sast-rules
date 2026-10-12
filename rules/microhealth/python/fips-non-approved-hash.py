import hashlib

# ruleid: python.fips-non-approved-hash
hashlib.md5(b"x")
# ruleid: python.fips-non-approved-hash
hashlib.new("md5", b"x")
# ruleid: python.fips-non-approved-hash
hashlib.blake2b(b"x")
# ok: python.fips-non-approved-hash
hashlib.md5(b"x", usedforsecurity=False)
# ok: python.fips-non-approved-hash
hashlib.sha256(b"x")
