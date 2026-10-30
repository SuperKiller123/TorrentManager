# -*- coding: utf-8 -*-
"""BitHuMen lista -> qBittorrent; alapból biztonságos próbaüzem."""
import json, os, re, time, shutil, logging, getpass, sys
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import requests
from webui import webui_session
from playwright.sync_api import sync_playwright

from paths import SETTINGS as CFG, STATE, PROFILE, LOG, DATA_DIR, migrate_old_data, find_playwright_browsers
from policy import TOP_URL, DEFAULT, validate_settings, allowed_size
from metainfo import torrent_size, TorrentMetadataError

if hasattr(sys.stdout, 'reconfigure'):
 try:
  sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
 except (OSError, ValueError):
  pass

def log(msg):
 print(msg,flush=True)
 logging.info(msg)
def read_json(path,default):
 if not path.exists():return default
 with path.open(encoding="utf-8") as f:return json.load(f)
def write_json(path,obj):
 tmp=path.with_suffix(path.suffix+".tmp")
 tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
 tmp.replace(path)
def config():
 if not CFG.exists():
  write_json(CFG,DEFAULT)
  raise SystemExit("Létrehoztam: beallitasok.json. Állítsd be, majd indítsd újra.")
 c=validate_settings(read_json(CFG,{}))
 if not str(c.get("qb_save_path","")).strip():
  raise ValueError("Válassz letöltési mappát a Beállításokban.")
 if not c.get("qb_password"):
  raise ValueError("Hiányzik a qBittorrent jelszó a Beállításokban.")
 return c

def qb_login(c):
 s=webui_session(c['qb_url'])
 s.headers["Referer"]=c["qb_url"].rstrip("/")+"/"
 pw=c["qb_password"] or getpass.getpass("qBittorrent Web UI jelszó: ")
 try:
  r=s.post(c["qb_url"].rstrip("/")+"/api/v2/auth/login",
           data={"username":c["qb_username"],"password":pw},timeout=20)
 except requests.RequestException:
  s.close()
  raise
 if not (r.status_code in (200,204) and r.text.strip().lower() in ("","ok.")):
  s.close()
  raise RuntimeError(f"qBittorrent bejelentkezés sikertelen: HTTP {r.status_code}")
 return s
def api(s,c,method,path,**kwargs):
 r=s.request(method,c["qb_url"].rstrip("/")+"/api/v2/"+path,timeout=45,**kwargs)
 r.raise_for_status()
 return r
def qb_torrents(s,c):
 return api(s,c,"GET","torrents/info").json()
def target_path(s,c):
 if c["qb_save_path"]:
  return Path(c["qb_save_path"].strip())
 prefs=api(s,c,"GET","app/preferences").json()
 path=prefs.get("save_path") or prefs.get("save_path_history")
 if not path:raise RuntimeError("Nem található a letöltési mappa. Add meg a qb_save_path értékét.")
 return Path(path)
def disk_percent(path):
 if not path.exists():raise RuntimeError(f"A célmappa nem létezik: {path}")
 u=shutil.disk_usage(path)
 return u.used/u.total*100
def parse_list(page,c):
 """Torrenttáblázat seederek oszlopával; a sorrend a szerver szerinti seeders DESC."""
 result={}
 for table in page.locator("table").all():
  rows=table.locator("tr")
  count=rows.count()
  seed_idx=None
  for i in range(min(count,8)):
   cells=rows.nth(i).locator(":scope > th, :scope > td")
   labels=[re.sub(r"[^a-záéíóöőúüű]", "", t.casefold()) for t in cells.all_text_contents()]
   for j,label in enumerate(labels):
    if label in ("s", "seed", "seeds", "seeder", "seeders", "seedelő", "seedelők", "feltöltők"):
     seed_idx=j;break
   if seed_idx is not None:break
  if seed_idx is None:continue
  for i in range(count):
   row=rows.nth(i)
   cells=row.locator(":scope > th, :scope > td")
   if cells.count()<=seed_idx:continue
   a=row.locator('a[href*="details.php?id="]')
   if a.count()==0:continue
   href=a.first.get_attribute("href") or ""
   tid=parse_qs(urlparse(urljoin("https://bithumen.be/",href)).query).get("id",[""])[0]
   if not tid.isdigit():continue
   name=(a.first.get_attribute("title") or a.first.inner_text()).strip()
   raw=cells.nth(seed_idx).inner_text().strip()
   if not re.fullmatch(r"[\d\s.,]+",raw):continue
   seeds=int(re.sub(r"[^\d]","",raw))
   if tid not in result or seeds>result[tid]["seeders"]:
    result[tid]={"id":tid,"name":name,"seeders":seeds,"url":urljoin("https://bithumen.be/",href)}
 return sorted(result.values(),key=lambda x:(-x["seeders"],x["id"]))[:int(c["max_managed_torrents"])]

def get_torrent_file(page,item):
 # A letöltési link HTML-je oldalspecifikus; csak .torrent tartalmat fogadunk el.
 page.goto(item["url"],wait_until="domcontentloaded",timeout=45000)
 candidates=page.locator('a[href*="download.php"], a[href$=".torrent"], a[href*="download?id="]')
 for i in range(min(candidates.count(),20)):
  href=candidates.nth(i).get_attribute("href")
  if not href:continue
  url=urljoin(page.url,href)
  resp=page.request.get(url,timeout=45000)
  if not resp.ok:continue
  data=resp.body()
  if data.startswith(b"d") and b"4:info" in data[:4096]:
   return data
 raise RuntimeError("Nem található ellenőrizhető .torrent fájl az adatlapon.")
def add(s,c,data,name):
 payload={}
 if c.get("qb_save_path","").strip():
  payload["savepath"]=c["qb_save_path"].strip()
 r=s.post(c["qb_url"].rstrip("/")+"/api/v2/torrents/add",
          data=payload,
          files={"torrents":(name+".torrent",data,"application/x-bittorrent")},
          timeout=60)
 if r.status_code==409:return "conflict",None
 r.raise_for_status()
 body=r.text.strip()
 if body.lower() in ("","ok."):return "accepted",None
 try:
  j=r.json()
  if j.get("success_count",0)>0:
   ids=j.get("added_torrent_ids") or []
   return "accepted",ids[0] if ids else None
  if j.get("pending_count",0)>0:return "pending",None
 except (ValueError,AttributeError):pass
 raise RuntimeError("Sikertelen hozzáadás: "+body[:250])
def delete_owned(s,c,hash_):
 r=s.post(c["qb_url"].rstrip("/")+"/api/v2/torrents/delete",
          data={"hashes":hash_,"deleteFiles":"true"},
          timeout=45)
 r.raise_for_status()
def collect_top_pages(page,c):
 """Oldalanként legfeljebb 15 találat; a teljes listát összefésüljük."""
 base=TOP_URL
 parsed=urlparse(base)
 params=parse_qs(parsed.query,keep_blank_values=True)
 params.pop("page",None)
 limit=max(1,int(c["max_managed_torrents"]))
 found={}
 previous_signature=None
 # 15 elem / oldal, plusz némi tartalék; nem végtelen ciklus.
 max_pages=min(40,(limit+14)//15+3)
 for page_index in range(max_pages):
  query={k:v[-1] for k,v in params.items()}
  if page_index > 0:
   query["page"]=str(page_index)
  target=urlunparse(parsed._replace(query=urlencode(query)))
  page.goto(target,wait_until="domcontentloaded",timeout=45000)
  actual=urlparse(page.url)
  if actual.netloc.lower()!=parsed.netloc.lower() or not actual.path.endswith("browse.php"):
   raise RuntimeError(f"Váratlan átirányítás a toplistáról: {page.url}")
  actual_params=parse_qs(actual.query)
  # A beállított keresési szűrőnek végig változatlannak kell maradnia.
  for key in ("sort","d","type","search"):
   if key in params and actual_params.get(key)!=params[key]:
    raise RuntimeError(f"A lista szűrője megváltozott ({key}): {page.url}")
  rows=parse_list(page,c)
  if not rows:
   if page_index==0:raise RuntimeError("Az első oldalon nincs feldolgozható torrent.")
   break
  signature=tuple(x["id"] for x in rows)
  if signature==previous_signature:
   raise RuntimeError("A lapozás ugyanazt az oldalt adta vissza; nem biztonságos a lista.")
  previous_signature=signature
  before=len(found)
  for item in rows:
   if item["id"] not in found or item["seeders"]>found[item["id"]]["seeders"]:
    found[item["id"]]=item
  log(f"Toplista {page_index+1}. oldal: {len(rows)} sor, összesen {len(found)} egyedi.")
  if len(found)>=limit:break
  if len(rows)<15:break
  if len(found)==before:
   raise RuntimeError("A lapozás nem hozott új torrenteket.")
 items=sorted(found.values(),key=lambda x:(-x["seeders"],x["id"]))[:limit]
 return items

def wait_for_bithumen_login(page,c):
 """Wait for actual access to the torrent table, without interrupting the login form."""
 log("BitHuMen hozzáférés ellenőrzése (rejtett Chromium).")
 notified=False
 while True:
  current=urlparse(page.url)
  # Never navigate away while the user is filling in the login form.
  if current.path.endswith("/login.php"):
   raise RuntimeError("BitHuMen bejelentkezés szükséges: állítsd le az automatizálást, és a Beállításokban nyisd meg a kézi bejelentkezést.")
  try:
   page.goto(TOP_URL,wait_until="domcontentloaded",timeout=45000)
   current=urlparse(page.url)
   if current.path.endswith("/login.php"):
    raise RuntimeError("BitHuMen bejelentkezés szükséges: Beállítások > Bejelentkezés megnyitása.")
   if current.path.endswith("/browse.php") and parse_list(page,c):
    log("BitHuMen bejelentkezés ellenőrizve; toplista elérhető.")
    return
   if not notified:
    log("A toplista még nem érhető el. Ellenőrizd a böngészőt.")
    notified=True
  except Exception as exc:
   if "BitHuMen bejelentkezés szükséges" in str(exc):
    raise
   if not notified:
    log(f"A toplista még nem elérhető: {exc}")
    notified=True
  page.wait_for_timeout(3000)

def _has_owned_torrent(rec, torrent):
 """Soha ne töröljünk név-egyezés alapján: csak nyilvántartott hash + azonos név."""
 return (bool(rec.get("hash")) and
         rec["hash"].casefold()==str(torrent.get("hash","")).casefold() and
         rec.get("name","").casefold()==str(torrent.get("name","")).casefold())

def _in_target_folder(torrent, path):
 """Kétes/áthelyezett fájlokhoz nem nyúlunk."""
 try:
  actual=str(Path(torrent.get("save_path","")).resolve()).casefold()
  intended=str(path.resolve()).casefold()
  return bool(torrent.get("save_path")) and actual == intended
 except (OSError,ValueError):return False

def cycle(page,s,c,state):
 items=collect_top_pages(page,c)
 limit=int(c["max_managed_torrents"])
 log(f"Legtöbbet seedelt lista: {len(items)}/{limit} elem.")
 if not items:raise RuntimeError("Üres/hibás lista: nem történik módosítás.")
 valid_for_delete=len(items)>=limit and len({it["id"] for it in items})==len(items)
 top_ids={x["id"] for x in items}
 existing=qb_torrents(s,c)
 by_hash={x.get("hash","").casefold():x for x in existing if x.get("hash")}
 names={x.get("name","").casefold() for x in existing}
 target=target_path(s,c)
 used=disk_percent(target)
 maximum=limit
 total=len(existing)
 mode=c["mode"]
 if mode!="full" and any(isinstance(rec,dict) and rec.get("missing_scans",0) for rec in state.values()):
  for rec in state.values():
   if isinstance(rec,dict):rec["missing_scans"]=0
  write_json(STATE,state)
 log(f"qBittorrent: {total}/{maximum} torrent | tárhely: {used:.1f}% / {c['max_disk_usage_percent']}% | mód: {mode}")

 # Biztonságos törlés: teljes toplista + két EGYMÁST KÖVETŐ sikeres
 # kör + hash + név + célmappa + nincs megosztott tartalomútvonal.
 # Másik, kézzel hozzáadott torrentet soha nem törlünk.
 if valid_for_delete:
  for tid,rec in list(state.items()):
   if not isinstance(rec,dict):continue
   if tid in top_ids:
    if rec.get("missing_scans",0):
     rec["missing_scans"]=0
     write_json(STATE,state)
    continue
   torrent=by_hash.get(str(rec.get("hash","")).casefold())
   if not torrent or not _has_owned_torrent(rec,torrent):
    continue
   if not _in_target_folder(torrent,target):
    log(f"Törlés kihagyva (eltérő mentési mappa): {rec.get('name',tid)}")
    continue
   content=torrent.get("content_path","")
   if content and any(x.get("hash")!=torrent.get("hash") and x.get("content_path")==content for x in existing):
    log(f"Törlés kihagyva (megosztott tartalom): {rec.get('name',tid)}")
    continue
   if mode=="dry":
    log(f"[PRÓBA] Eltávolítaná a fájlokkal együtt: {rec.get('name',tid)}")
    continue
   if mode!="full":
    continue
   streak=int(rec.get("missing_scans",0))+1
   rec["missing_scans"]=streak
   write_json(STATE,state)
   if streak>=2:
    try:
     delete_owned(s,c,rec["hash"])
     # Az API választ követően győződjünk meg az eltávolításról.
     if rec["hash"].casefold() in {x.get("hash","").casefold() for x in qb_torrents(s,c)}:
      log(f"Törlési válasz érkezett, de a torrent még létezik: {rec.get('name',tid)}")
      continue
     del state[tid]
     write_json(STATE,state)
     log(f"Eltávolítva: {rec.get('name',tid)}")
     existing=qb_torrents(s,c)
     total=len(existing)
    except Exception as exc:
     log(f"Törlési hiba: {rec.get('name',tid)}: {exc}")
   elif mode=="full":
    log(f"Törlés előkészítve (megerősítés a következő körben): {rec.get('name',tid)}")
 else:
  # Hiányos toplista nem tekinthető megszakítás nélküli bizonyítéknak.
  for rec in state.values():
   if isinstance(rec,dict):rec["missing_scans"]=0
  write_json(STATE,state)
  log("Törlés tiltva: a kívánt hosszúságú, hiánytalan toplista nem igazolható.")

 # A rangsorban szereplő torrentek közül kizárólag a megadott méretűek kerülhetnek be.
 # A méretet a valódi .torrent metainfóból vizsgáljuk, nem a webes sor szövegéből.
 hashes={x.get("hash","").casefold() for x in existing}
 names={x.get("name","").casefold() for x in existing}
 for item in items:
  ident=item["id"]
  rec=state.get(ident,{})
  if isinstance(rec,dict) and rec.get("hash","").casefold() in hashes and rec.get("hash"):
   continue
  if item["name"].casefold() in names:
   log(f"Már létezik: {item['name']}")
   continue
  if total>=maximum:
   log(f"Darabszámkorlát elérve: {total}/{maximum}")
   break
  used=disk_percent(target)
  if used>=int(c["max_disk_usage_percent"]):
   log("Tárhelykorlát elérve; nincs több új torrent.")
   break
  try:
   data=get_torrent_file(page,item)
   size=torrent_size(data)
   if not allowed_size(size,c):
    log(f"Méretkorlát miatt kihagyva: {item['name']} ({size / 1000**3:.2f} GB)")
    continue
   disk=shutil.disk_usage(target)
   projected=(disk.used+size)/disk.total*100
   if size>disk.free or projected>int(c["max_disk_usage_percent"]):
    log(f"Tárhelykorlát miatt kihagyva: {item['name']} (várható telítettség {projected:.1f}%)")
    continue
   if mode=="dry":
    log(f"[PRÓBA] Letöltené: {item['name']} ({size / 1000**3:.2f} GB; seederek: {item['seeders']})")
    continue
   status,h=add(s,c,data,item["name"])
   if status!="accepted":
    log(f"Nem igazolt hozzáadás ({status}): {item['name']}")
    continue
   verified=None
   for _ in range(5):
    refreshed=qb_torrents(s,c)
    verified=next((x for x in refreshed if
                   (h and x.get("hash","").casefold()==str(h).casefold()) or
                   (x.get("name","").casefold()==item["name"].casefold() and
                    x.get("hash","").casefold() not in hashes)),None)
    if verified:break
    time.sleep(1)
   if not verified:
    log(f"A torrent hozzáadása még nem ellenőrizhető: {item['name']}")
    continue
   state[ident]={"name":verified.get("name",item["name"]),"hash":verified.get("hash",""),
                 "added_at":int(time.time()), "missing_scans":0}
   write_json(STATE,state)
   existing=refreshed
   total=len(existing)
   hashes={x.get("hash","").casefold() for x in existing}
   names={x.get("name","").casefold() for x in existing}
   log(f"Letöltve: {item['name']}")
  except Exception as exc:
   log(f"Hozzáadási hiba: {item['name']}: {exc}")

def main():
 # Közvetlen TorrentMotor.exe indításnál is helyes böngészőmappát keressünk.
 browser_dir = find_playwright_browsers()
 if browser_dir:
  os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browser_dir)
 migrate_old_data()
 DATA_DIR.mkdir(parents=True,exist_ok=True)
 logging.basicConfig(filename=LOG,level=logging.INFO,
                     format="%(asctime)s %(message)s",encoding="utf-8")
 c=config()
 s=None
 for retry in range(12):
  try:
   s=qb_login(c)
   break
  except requests.RequestException as exc:
   if retry==11:raise
   log(f"Várakozás a qBittorrentre ({retry+1}/12): {exc}")
   time.sleep(3)
 state=read_json(STATE,{})
 with sync_playwright() as p:
  context=p.chromium.launch_persistent_context(str(PROFILE),headless=True)
  page=context.pages[0] if context.pages else context.new_page()
  page.goto("https://bithumen.be/",wait_until="domcontentloaded")
  try:
   while True:
    try:
     s.close()
     s=qb_login(c)
     wait_for_bithumen_login(page,c)
     cycle(page,s,c,state)
    except Exception as e:
     for rec in state.values():
      if isinstance(rec,dict):rec["missing_scans"]=0
     write_json(STATE,state)
     log(f"Ellenőrzési hiba (ebben a körben nincs törlés): {e}")
    log(f"Következő ellenőrzés {c['check_minutes']} perc múlva.")
    time.sleep(max(1,int(c["check_minutes"]))*60)
  except KeyboardInterrupt:log("Leállítva.")
  finally:context.close()
if __name__=="__main__":
 main()
