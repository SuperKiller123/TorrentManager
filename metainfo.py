# -*- coding: utf-8 -*-
"""Bencode csak a torrent teljes méretének megállapításához.
Ismeretlen vagy hibás metainfó esetén a letöltés megtagadva.
"""
class TorrentMetadataError(ValueError):
    pass

def torrent_size(data):
    if not isinstance(data, bytes) or len(data) > 20 * 1024 * 1024:
        raise TorrentMetadataError("Túl nagy vagy érvénytelen .torrent metaadat.")
    def decode(pos, depth):
        if depth > 40 or pos >= len(data):
            raise TorrentMetadataError("Hibás bencode mélység/vég.")
        first = data[pos:pos+1]
        if first == b'i':
            stop = data.find(b'e', pos+1)
            if stop < 0 or stop - pos > 32:
                raise TorrentMetadataError("Hibás számérték.")
            try: val = int(data[pos+1:stop])
            except ValueError as exc: raise TorrentMetadataError("Hibás számérték.") from exc
            return val, stop+1
        if first in (b'l', b'd'):
            pos += 1
            output = [] if first == b'l' else {}
            count = 0
            while pos < len(data) and data[pos:pos+1] != b'e':
                count += 1
                if count > 100000:
                    raise TorrentMetadataError("Túl sok metaadat-bejegyzés.")
                if first == b'd':
                    key, pos = decode(pos, depth+1)
                    if not isinstance(key, bytes):
                        raise TorrentMetadataError("A kulcs nem bájtsorozat.")
                    value, pos = decode(pos, depth+1)
                    output[key] = value
                else:
                    value, pos = decode(pos, depth+1)
                    output.append(value)
            if pos >= len(data): raise TorrentMetadataError("Lezáratlan bencode.")
            return output, pos+1
        if b'0' <= first <= b'9':
            sep = data.find(b':', pos, pos+22)
            if sep < 0: raise TorrentMetadataError("Hiányzó string-hossz.")
            try: length = int(data[pos:sep])
            except ValueError as exc: raise TorrentMetadataError("Hibás string-hossz.") from exc
            end = sep+1+length
            if length < 0 or end > len(data): raise TorrentMetadataError("Hibás string-vég.")
            return data[sep+1:end], end
        raise TorrentMetadataError("Hibás bencode-típus.")
    decoded, end = decode(0, 0)
    if end != len(data) or not isinstance(decoded, dict) or not isinstance(decoded.get(b'info'), dict):
        raise TorrentMetadataError("Hiányzó torrent info szekció.")
    info = decoded[b'info']
    if b'length' in info:
        sizes = [info[b'length']]
    elif isinstance(info.get(b'files'), list):
        sizes = [entry.get(b'length') for entry in info[b'files'] if isinstance(entry, dict)]
        if len(sizes) != len(info[b'files']): raise TorrentMetadataError("Hibás fájllista.")
    else:
        # v2-only torrent: file tree feldolgozás
        def walk(node, depth=0):
            if depth > 30 or not isinstance(node, dict):
                raise TorrentMetadataError("Hibás v2 fájlfa.")
            for key, value in node.items():
                if key == b'':
                    if not isinstance(value, dict) or b'length' not in value:
                        raise TorrentMetadataError("Hiányzó v2 fájlméret.")
                    yield value[b'length']
                else:
                    yield from walk(value, depth+1)
        sizes = list(walk(info.get(b'file tree', {})))
    if not sizes or any(not isinstance(n, int) or n < 0 for n in sizes):
        raise TorrentMetadataError("Érvénytelen fájlméret.")
    return sum(sizes)
