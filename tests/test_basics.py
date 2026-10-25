# -*- coding: utf-8 -*-
"""Egyszerű offline regressziós tesztek; nem igényel élő tracker-/qBittorrent-kapcsolatot."""
import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))

class SettingsTests(unittest.TestCase):
 def test_two_defaults_only(self):
  with tempfile.TemporaryDirectory() as td,patch.dict(os.environ,{'LOCALAPPDATA':td}):
   import paths, TorrentManager
   importlib.reload(paths)
   importlib.reload(TorrentManager)
   result=TorrentManager.read_settings()
   self.assertEqual(result['qb_url'],'http://127.0.0.1:8080')
   from policy import TOP_URL
   self.assertEqual(TOP_URL,"https://bithumen.be/browse.php?sort=seeders&d=DESC")
   self.assertNotIn('browse_url',result)
   self.assertEqual(result['qb_username'],'admin')
   self.assertEqual(result['qb_password'],'')
   self.assertEqual(result['check_minutes'],5)
   self.assertEqual(result['max_managed_torrents'],50)
   self.assertEqual(result['mode'],'dry')

 def test_saved_settings_take_precedence(self):
  with tempfile.TemporaryDirectory() as td,patch.dict(os.environ,{'LOCALAPPDATA':td}):
   import paths, TorrentManager
   importlib.reload(paths)
   importlib.reload(TorrentManager)
   paths.DATA_DIR.mkdir(exist_ok=True)
   paths.SETTINGS.write_text(json.dumps({'qb_url':'http://localhost:9999','qb_username':'me','max_managed_torrents':20}),encoding='utf-8')
   result=TorrentManager.read_settings()
   self.assertEqual(result['qb_url'],'http://localhost:9999')
   self.assertEqual(result['max_managed_torrents'],20)
   self.assertNotIn('browse_url',result)  # Nincs visszaállítás, ha felhasználó mentett.

 def test_migration_does_not_overwrite(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   old=root/'old';old.mkdir()
   new=root/'new'
   (old/'beallitasok.json').write_text('{"qb_url":"old"}',encoding='utf-8')
   (old/'kezelt_torrentek.json').write_text('{"1":{"hash":"abc"}}',encoding='utf-8')
   (old/'bithumen_bongeszo_profil').mkdir()
   (old/'bithumen_bongeszo_profil'/'session').write_text('cookie',encoding='utf-8')
   with patch.dict(os.environ,{'LOCALAPPDATA':str(new)}):
    import paths
    importlib.reload(paths)
    with patch.object(paths,'BASE',old):
     paths.migrate_old_data()
     self.assertEqual(json.loads(paths.SETTINGS.read_text(encoding='utf-8'))['qb_url'],'old')
     self.assertTrue((paths.PROFILE/'session').exists())
     paths.SETTINGS.write_text('{"qb_url":"new"}',encoding='utf-8')
     paths.migrate_old_data()
     self.assertEqual(json.loads(paths.SETTINGS.read_text(encoding='utf-8'))['qb_url'],'new')

 def test_add_transmits_save_path(self):
  from unittest.mock import Mock
  import motor
  response=Mock(status_code=200,text='Ok.')
  session=Mock()
  session.post.return_value=response
  cfg={'qb_url':'http://127.0.0.1:8080','qb_save_path':r'D:\\Torrentek'}
  status,_=motor.add(session,cfg,b'd4:info','test')
  self.assertEqual(status,'accepted')
  self.assertEqual(session.post.call_args.kwargs['data']['savepath'],r'D:\\Torrentek')

if __name__=='__main__': unittest.main()
