"""Bounded read-only decoder for cache-25/26 fixed-width bincode diagnostics.

No output hashing or reuse decision is performed. Directory comparisons are a
point-in-time observation and may race a live command's own filesystem effects.
"""
from collections import Counter
from pathlib import Path


class Decoder:
    def __init__(self, data):
        self.data = data
        self.offset = 0

    def take(self, length):
        if length < 0 or self.offset + length > len(self.data):
            raise ValueError('truncated metadata')
        result = self.data[self.offset:self.offset+length]
        self.offset += length
        return result

    def integer(self, size=8, signed=False):
        return int.from_bytes(self.take(size), 'little', signed=signed)

    def count(self):
        count = self.integer()
        if count > 65536: raise ValueError('metadata item limit')
        return count

    def text(self):
        length = self.integer()
        if length > 1024*1024: raise ValueError('metadata string limit')
        return self.take(length).decode('utf-8')

    def timestamps(self):
        modified = self.integer(16)
        changed = self.integer(8, True)*1_000_000_000 + self.integer(8, True)
        return {'modified_ns':modified, 'changed_ns':changed}

    def key(self, depth=0):
        if depth > 16: raise ValueError('nested dependency limit')
        tag = self.integer(4)
        if tag == 0: return {'kind':'absent'}
        if tag == 1:
            return {'kind':'parent', 'mode':self.integer(4), 'uid':self.integer(4),
                    'gid':self.integer(4), 'access':self.integer(1)}
        if tag == 2: return {'kind':'uncacheable'}
        if tag == 3: return {'kind':'all', 'keys':[self.key(depth+1) for _ in range(self.count())]}
        if tag in (4,5,6):
            result = {'kind':{4:'file',5:'directory',6:'symlink'}[tag]}
            if tag == 6: result['target'] = self.text()
            result.update(self.timestamps())
            if tag == 4: result['size'] = self.integer()
            result['mode'] = self.integer(4)
            return result
        if tag == 7: return {'kind':'hash','hash':self.integer()}
        if tag == 9: return {'kind':'not_directory'}
        if tag == 8:
            initial = self.key(depth+1)
            self.take(53)  # ProducedFile's fixed integer fields, without padding.
            return {'kind':'overwrite','initial':initial}
        raise ValueError(f'unknown dependency variant {tag}')


def decode(path):
    with Path(path).open('rb') as stream:
        data = stream.read(32*1024**2+1)
    if len(data)>32*1024**2: raise ValueError('diagnostic metadata byte limit')
    reader = Decoder(data)
    exit_code = reader.integer(4,True)
    barriers = [reader.text() for _ in range(reader.count())]
    dependencies = {}
    for _ in range(reader.count()):
        path = reader.text()
        dependencies[path] = reader.key()
    outputs = [reader.text() for _ in range(reader.count())]
    compressed = reader.integer(1)
    if compressed not in (0,1): raise ValueError('invalid compressed flag')
    reader.take(16)  # Persisted stdout/stderr integrity hashes, not revalidated.
    if reader.offset != len(data): raise ValueError('unexpected trailing metadata')
    return {'exit_code':exit_code,'barriers':barriers,'dependencies':dependencies,'outputs':outputs}


def directory_summary(path):
    data = decode(path)
    mismatches = []
    directories = 0
    for name, key in data['dependencies'].items():
        if key['kind'] != 'directory': continue
        directories += 1
        try:
            metadata = Path(name).lstat()
            actual = {'modified_ns':metadata.st_mtime_ns, 'changed_ns':metadata.st_ctime_ns,
                      'mode':metadata.st_mode}
            expected = {field:key[field] for field in actual}
            if actual != expected:
                mismatches.append({'path':name,'expected':expected,'actual':actual})
        except OSError as error:
            mismatches.append({'path':name,'error':str(error)})
    return {'dependent_scripts':[name for name in data['dependencies'] if name.endswith(('/scripts/segment.py','/scripts/classify.py'))],
            'dependency_kinds':dict(Counter(key['kind'] for key in data['dependencies'].values())),
            'directory_count':directories, 'directory_metadata_mismatches':mismatches,
            'scope':'Directory metadata only; not a full cache validation'}
