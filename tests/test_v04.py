# -*- coding: utf-8 -*-
"""v0.4 offline tesztek: migráció, torrentméret, saját torrentek biztonságos törlése."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import policy
import motor
from metainfo import torrent_size, TorrentMetadataError


def enc(value):
    if isinstance(value, int):return b'i'+str(value).encode()+b'e'
    if isinstance(value, bytes):return str(len(value)).encode()+b':'+value
    if isinstance(value, list):return b'l'+b''.join(enc(v) for v in value)+b'e'
    if isinstance(value, dict):
        return b'd'+b''.join(enc(k)+enc(value[k]) for k in sorted(value))+b'e'
    raise TypeError(type(value))

class SettingsPolicyTests(unittest.TestCase):
    def test_old_saved_settings_migrated_without_accidental_deletion(self):
        migrated=policy.normalize_settings({'dry_run':False,'enable_additions':True,
            'enable_deletions':True,'delete_files':False,'browse_url':'wrong','top_count':1,
            'max_disk_usage_percent':70.0, 'github_repository':''})
        self.assertEqual(migrated['mode'],'add')
        self.assertEqual(migrated['max_disk_usage_percent'],70)
        self.assertNotIn('github_repository',migrated)
        for obsolete in ('browse_url','top_count','enable_additions','delete_files'):
            self.assertNotIn(obsolete,migrated)
        self.assertEqual(policy.normalize_settings({'dry_run':False,'enable_additions':True,
            'enable_deletions':True,'delete_files':True})['mode'],'full')
    def test_validates_integer_disk_and_size(self):
        self.assertEqual(policy.validate_settings({'max_disk_usage_percent':'71'})['max_disk_usage_percent'],71)
        for bad in ('70.5','70.0','test'):
            with self.assertRaises(ValueError):policy.validate_settings({'max_disk_usage_percent':bad})
        with self.assertRaises(ValueError):policy.validate_settings({'min_size_gb':10,'max_size_gb':1})
        self.assertFalse(policy.allowed_size(5*10**9, {'min_size_gb':'10','max_size_gb':''}))
        self.assertTrue(policy.allowed_size(15*10**9, {'min_size_gb':'10','max_size_gb':'20'}))
        self.assertFalse(policy.allowed_size(30*10**9, {'min_size_gb':'10','max_size_gb':'20'}))

class MetainfoTests(unittest.TestCase):
    def test_single_file(self):
        torrent=enc({b'info':{b'length':230,b'name':b'x'}})
        self.assertEqual(torrent_size(torrent),230)
    def test_multiple_files(self):
        torrent=enc({b'info':{b'files':[{b'length':20},{b'length':130}],b'name':b'x'}})
        self.assertEqual(torrent_size(torrent),150)
    def test_v2_only(self):
        torrent=enc({b'info':{b'file tree':{b'x.txt':{b'':{b'length':15}}}}})
        self.assertEqual(torrent_size(torrent),15)
    def test_reject_malformed(self):
        for data in (b'',b'not torrent',b'd4:infod6:lengthi-2eee',b'd4:infod6:lengthi4eeeEXTRA'):
            with self.assertRaises(TorrentMetadataError):torrent_size(data)

class DeleteTests(unittest.TestCase):
    def test_delete_api_always_removes_files(self):
        s=Mock();s.post.return_value=Mock(status_code=200)
        motor.delete_owned(s,{'qb_url':'http://127.0.0.1:8080'},'abcd')
        self.assertEqual(s.post.call_args.kwargs['data'],{'hashes':'abcd','deleteFiles':'true'})
    def test_prevents_unowned_or_renamed(self):
        rec={'hash':'abc','name':'Original'}
        self.assertFalse(motor._has_owned_torrent(rec,{'hash':'xyz','name':'Original'}))
        self.assertFalse(motor._has_owned_torrent(rec,{'hash':'abc','name':'Changed'}))
        self.assertTrue(motor._has_owned_torrent(rec,{'hash':'AbC','name':'original'}))
    def test_requires_two_complete_scans_before_delete(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)
            st={'1':{'hash':'abcdef','name':'Old','missing_scans':0}}
            torrent={'hash':'abcdef','name':'Old','save_path':str(target),'content_path':str(target/'Old')}
            listing=[torrent]
            deleted=[]
            def delete(_s,_c,h):
                deleted.append(h)
                listing.clear()
            c=policy.validate_settings({'max_managed_torrents':1,'mode':'full',
               'qb_save_path':str(target),'max_disk_usage_percent':70})
            with patch.object(motor,'collect_top_pages',return_value=[{'id':'2','name':'New','seeders':100}]),\
                 patch.object(motor,'qb_torrents',side_effect=lambda *_:list(listing)),\
                 patch.object(motor,'target_path',return_value=target),\
                 patch.object(motor,'disk_percent',return_value=10),\
                 patch.object(motor,'get_torrent_file',side_effect=RuntimeError('skip new')),\
                 patch.object(motor,'delete_owned',side_effect=delete),\
                 patch.object(motor,'STATE',target/'state.json'),\
                 patch.object(motor,'log'):
                motor.cycle(None,None,c,st)
                self.assertEqual(deleted,[])
                self.assertEqual(st['1']['missing_scans'],1)
                motor.cycle(None,None,c,st)
                self.assertEqual(deleted,['abcdef'])
                self.assertNotIn('1',st)
    def test_no_deletion_in_dry_mode_even_after_many_cycles(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)
            st={'1':{'hash':'abc','name':'Old','missing_scans':0}}
            listing=[{'hash':'abc','name':'Old','save_path':str(target)}]
            c=policy.validate_settings({'max_managed_torrents':1,'mode':'dry','qb_save_path':str(target)})
            with patch.object(motor,'collect_top_pages',return_value=[{'id':'2','name':'New','seeders':4}]),\
                 patch.object(motor,'qb_torrents',return_value=listing),\
                 patch.object(motor,'target_path',return_value=target),\
                 patch.object(motor,'disk_percent',return_value=15),\
                 patch.object(motor,'delete_owned') as deletion,\
                 patch.object(motor,'STATE',target/'state.json'),\
                 patch.object(motor,'log'):
                for _ in range(4):motor.cycle(None,None,c,st)
                deletion.assert_not_called()
                self.assertEqual(st['1']['missing_scans'],0)
    def test_incomplete_list_cannot_delete(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)
            st={'1':{'hash':'abc','name':'Old','missing_scans':1}}
            torrent={'hash':'abc','name':'Old','save_path':str(target)}
            c=policy.validate_settings({'max_managed_torrents':2,'mode':'full','qb_save_path':str(target)})
            with patch.object(motor,'collect_top_pages',return_value=[{'id':'2','name':'New','seeders':100}]),\
                 patch.object(motor,'qb_torrents',return_value=[torrent]),\
                 patch.object(motor,'target_path',return_value=target),\
                 patch.object(motor,'disk_percent',return_value=15),\
                 patch.object(motor,'delete_owned') as deletion,\
                 patch.object(motor,'STATE',target/'state.json'),\
                 patch.object(motor,'log'):
                motor.cycle(None,None,c,st)
                deletion.assert_not_called()
                self.assertEqual(st['1']['missing_scans'],0)

if __name__=='__main__': unittest.main()

class TopListParsingTests(unittest.TestCase):
    """A seeders értéket használjuk, nem a régi DLs oszlopot."""
    def test_parse_seeders_not_downloads(self):
        class Cell:
            def __init__(self,text):self.text=text
            def inner_text(self):return self.text
        class Cells:
            def __init__(self,texts):self.texts=texts
            def count(self):return len(self.texts)
            def all_text_contents(self):return self.texts
            def nth(self,index):return Cell(self.texts[index])
        class Anchor:
            def __init__(self,id,name):self.id=id;self.name=name
            def get_attribute(self,key):return f'details.php?id={self.id}' if key=='href' else self.name
            def inner_text(self):return self.name
        class Anchors:
            def __init__(self,anchor):self.anchor=anchor
            def count(self):return int(self.anchor is not None)
            @property
            def first(self):return self.anchor
        class Row:
            def __init__(self,texts,anchor=None):self.texts=texts;self.anchor=anchor
            def locator(self,selector):
                return Cells(self.texts) if selector.startswith(':scope') else Anchors(self.anchor)
        class Rows:
            def __init__(self,rows):self.rows=rows
            def count(self):return len(self.rows)
            def nth(self,index):return self.rows[index]
        class Table:
            def locator(self,selector):
                assert selector=='tr'
                return Rows([Row(['Név','Seeders','DLs']),
                    Row(['Torrent A','12','1000'],Anchor('101','A')),
                    Row(['Torrent B','90','1'],Anchor('102','B'))])
        class Tables:
            def all(self):return [Table()]
        class Page:
            def locator(self,selector):
                assert selector=='table'
                return Tables()
        result=motor.parse_list(Page(),policy.validate_settings({'max_managed_torrents':2}))
        self.assertEqual([x['id'] for x in result],['102','101'])
        self.assertEqual([x['seeders'] for x in result],[90,12])
