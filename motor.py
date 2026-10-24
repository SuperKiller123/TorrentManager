# -*- coding: utf-8 -*-
"""BitHuMen lista -> qBittorrent; alapból biztonságos próbaüzem."""
import json, os, re, time, shutil, logging, getpass
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import requests
from playwright.sync_api import sync_playwright

from paths import SETTINGS as CFG, STATE, PROFILE, LOG, DATA_DIR, migrate_old_data, find_playwright_browsers
DEFAULT={
 "qb_url":"http://127.0.0.1:8080",
 "qb_username":"admin",
 "qb_password":"",
 "qb_save_path":"",
 "check_minutes":5,
 "max_disk_usage_percent":70,
 "top_count":50,
 "max_managed_torrents":50,
 "browse_url":"https://bithumen.be/browse.php?sort=times_completed&d=DESC&type=legtobbet_letoltottek",
 "dry_run":True,
 "enable_additions":False,
 "enable_deletions":False,
 "delete_files":False,
 "minimum_valid_rows_for_deletion":50,
 "headless":False
}
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
 c={**DEFAULT,**read_json(CFG,{})}
 if not c.get("qb_save_path","").strip():
  raise ValueError("Válassz letöltési mappát a Beállításokban.")
 if c["enable_deletions"] and not c["enable_additions"]:
  log("Figyelmeztetés: a törlés aktív, hozzáadás nem.")
 return c
def qb_login(c):
 s=requests.Session()
 s.headers["Referer"]=c["qb_url"].rstrip("/")+"/"
 pw=c["qb_password"] or getpass.getpass("qBittorrent Web UI jelszó: ")
 r=s.post(c["qb_url"].rstrip("/")+"/api/v2/auth/login",
          data={"username":c["qb_username"],"password":pw},timeout=20)
 if not (r.status_code in (200,204) and r.text.strip().lower() in ("","ok.")):
  raise RuntimeError(f"qBittorrent bejelentkezés sikertelen: HTTP {r.status_code} {r.text[:100]}")
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
 # Csak a tényleges torrenttáblázat sorait értelmezzük, az ismétléseket ID szerint szűrjük.
 result={}
 for table in page.locator("table").all():
  rows=table.locator("tr")
  count=rows.count()
  dl_idx=None
  for i in range(min(count,8)):
   cells=rows.nth(i).locator(":scope > th, :scope > td")
   labels=[x.strip() for x in cells.all_text_contents()]
   for j,label in enumerate(labels):
    if label.casefold()=="dls":dl_idx=j;break
   if dl_idx is not None:break
  if dl_idx is None:continue
  for i in range(count):
   row=rows.nth(i)
   cells=row.locator(":scope > th, :scope > td")
   if cells.count()<=dl_idx:continue
   a=row.locator('a[href*="details.php?id="]')
   if a.count()==0:continue
   href=a.first.get_attribute("href") or ""
   tid=parse_qs(urlparse(urljoin("https://bithumen.be/",href)).query).get("id",[""])[0]
   if not tid.isdigit():continue
   name=(a.first.get_attribute("title") or a.first.inner_text()).strip()
   raw=cells.nth(dl_idx).inner_text().strip()
   if not re.fullmatch(r"[\d\s.,]+",raw):continue
   dls=int(re.sub(r"[^\d]","",raw))
   if tid not in result or dls>result[tid]["dls"]:
    result[tid]={"id":tid,"name":name,"dls":dls,
                 "url":urljoin("https://bithumen.be/",href)}
 return sorted(result.values(),key=lambda x:-x["dls"])[:int(c["top_count"])]
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
          data={"hashes":hash_,"deleteFiles":"true" if c["delete_files"] else "false"},
          timeout=45)
 r.raise_for_status()
def collect_top_pages(page,c):
 """Oldalanként legfeljebb 15 találat; a teljes listát összefésüljük."""
 base=c["browse_url"]
 parsed=urlparse(base)
 params=parse_qs(parsed.query,keep_blank_values=True)
 params.pop("page",None)
 limit=max(1,int(c["top_count"]))
 found={}
 previous_signature=None
 # 15 elem / oldal, plusz némi tartalék; nem végtelen ciklus.
 max_pages=min(30,(limit+14)//15+3)
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
  rows=parse_list(page,{**c,"top_count":limit})
  if not rows:
   if page_index==0:raise RuntimeError("Az első oldalon nincs feldolgozható torrent.")
   break
  signature=tuple(x["id"] for x in rows)
  if signature==previous_signature:
   raise RuntimeError("A lapozás ugyanazt az oldalt adta vissza; nem biztonságos a lista.")
  previous_signature=signature
  before=len(found)
  for item in rows:
   if item["id"] not in found or item["dls"]>found[item["id"]]["dls"]:
    found[item["id"]]=item
  log(f"Toplista {page_index+1}. oldal: {len(rows)} sor, összesen {len(found)} egyedi.")
  if len(found)>=limit:break
  if len(rows)<15:break
  if len(found)==before:
   raise RuntimeError("A lapozás nem hozott új torrenteket.")
 items=sorted(found.values(),key=lambda x:(-x["dls"],x["id"]))[:limit]
 return items

def wait_for_bithumen_login(page,c):
 """Wait for actual access to the torrent table, without interrupting the login form."""
 log("BitHuMen hozzáférés ellenőrzése. Ha kell, jelentkezz be a megnyílt böngészőben.")
 notified=False
 while True:
  current=urlparse(page.url)
  # Never navigate away while the user is filling in the login form.
  if current.path.endswith("/login.php"):
   if not notified:
    log("Bejelentkezés szükséges. A program megvárja a sikeres belépést.")
    notified=True
   page.wait_for_timeout(3000)
   continue
  try:
   page.goto(c["browse_url"],wait_until="domcontentloaded",timeout=45000)
   current=urlparse(page.url)
   if current.path.endswith("/login.php"):
    if not notified:
     log("A BitHuMen bejelentkezést kér; várakozás a böngészőben.")
     notified=True
    page.wait_for_timeout(3000)
    continue
   if current.path.endswith("/browse.php") and parse_list(page,{**c,"top_count":1}):
    log("BitHuMen bejelentkezés ellenőrizve; toplista elérhető.")
    return
   if not notified:
    log("A toplista még nem érhető el. Ellenőrizd a böngészőt.")
    notified=True
  except Exception as exc:
   if not notified:
    log(f"A toplista még nem elérhető: {exc}")
    notified=True
  page.wait_for_timeout(3000)

def cycle(page,s,c,state):
 items=collect_top_pages(page,c)
 log(f"Érvényes torrentek: {len(items)} (DLs szerint rendezve).")
 if not items:raise RuntimeError("Üres/hibás lista: sem hozzáadás, sem törlés nem történik.")
 # Csak akkor törlünk, ha valóban megvan a teljes top50, és nem egyetlen lap töredéke.
 valid_for_delete=(len(items)>=max(50,int(c["minimum_valid_rows_for_deletion"]))
                    and int(c["top_count"])>=50)
 top_ids={x["id"] for x in items}
 existing=qb_torrents(s,c)
 hashes={x.get("hash","").lower() for x in existing}
 names={x.get("name","").casefold() for x in existing}
 path=target_path(s,c)
 used=disk_percent(path)
 maximum=int(c.get("max_managed_torrents",50))
 total=len(existing)
 log(f"qBittorrent: {total} torrent | maximális összes torrent: {maximum}")
 log(f"Tárhely: {used:.1f}% | limit: {c['max_disk_usage_percent']}%")
 log(f"Üzemmód: próbaüzem={c['dry_run']}, hozzáadás engedélyezve={c['enable_additions']}")
 if c["dry_run"] or not c["enable_additions"]:
  log("FIGYELEM: A hozzáadás ki van kapcsolva. A Beállításokban kapcsold ki a Próbaüzemet és engedélyezd az új torrenteket.")
 for item in items:
  ident=item["id"]
  owned=state.get(ident,{})
  if owned.get("hash","").lower() in hashes and owned.get("hash"):
   continue
  if item["name"].casefold() in names:
   log(f"Már létezik név alapján: {item['name']}")
   continue
  # A darabszám a qBittorrent TELJES torrentlistájára vonatkozik.
  # Az új hozzáadásokat is beleszámoljuk, nem csak a nyilvántartottakat.
  if total>=maximum:
   log(f"Darabszámkorlát elérve: {total}/{maximum}; ebben a körben nincs több hozzáadás.")
   break
  if used>=float(c["max_disk_usage_percent"]):
   log("A tárhely elérte a korlátot; nincs új hozzáadás.")
   break
  if c["dry_run"] or not c["enable_additions"]:
   log(f"[PRÓBA - NEM TÖRTÉNT HOZZÁADÁS] {item['name']} (DLs {item['dls']})")
   continue
  try:
   data=get_torrent_file(page,item)
   log("Célmappa: "+c["qb_save_path"])
   status,h=add(s,c,data,item["name"])
   if status=="accepted":
    # Az API sikerjelzését csak a qBittorrent listájában való megjelenés
    # után tekintjük igazolt hozzáadásnak.
    verified=None
    for attempt in range(5):
     refreshed=qb_torrents(s,c)
     verified=next((x for x in refreshed
                    if (h and x.get("hash","").lower()==str(h).lower())
                    or x.get("name","").casefold()==item["name"].casefold()),None)
     if verified:break
     time.sleep(1)
    if not verified:
     log(f"Hozzáadási válasz érkezett, de a torrent nem ellenőrizhető a qBittorrentben: {item['name']}")
     # A következő ciklus majd ismét ellenőrzi, nem növeljük tévesen a számlálót.
     continue
    real_hash=verified.get("hash","")
    state[ident]={"name":item["name"],"hash":real_hash,"added_at":int(time.time())}
    write_json(STATE,state)
    existing=refreshed
    total=len(existing)
    hashes={x.get("hash","").lower() for x in existing}
    names={x.get("name","").casefold() for x in existing}
    log(f"Hozzáadva és ellenőrizve: {item['name']} | {total}/{maximum}")
   else:
    log(f"Nem igazolt hozzáadás ({status}): {item['name']}")
  except Exception as e:
   log(f"Hozzáadási hiba: {item['name']}: {e}")
  used=disk_percent(path)
 # NEM törölünk ismeretlen torrentet, és a lista 50-nél kevesebb eleme esetén sem.
 if not valid_for_delete:
  log("Törlés tiltva ebben a körben: nincs igazolt, teljes 50 elemű lista.")
 elif c["enable_deletions"]:
  for tid,rec in list(state.items()):
   if tid in top_ids:continue
   h=rec.get("hash","").lower()
   if not h or h not in hashes:
    log(f"Törlés kihagyva (nem igazolt torrentazonosító): {tid}")
    continue
   if c["dry_run"]:
    log(f"[PRÓBA] Törlés: {rec.get('name',tid)}")
    continue
   try:
    delete_owned(s,c,h)
    del state[tid]
    write_json(STATE,state)
    log(f"Eltávolítva: {rec.get('name',tid)} (fájlok törlése: {c['delete_files']})")
   except Exception as e:log(f"Törlési hiba: {tid}: {e}")
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
 s=qb_login(c)
 state=read_json(STATE,{})
 with sync_playwright() as p:
  context=p.chromium.launch_persistent_context(str(PROFILE),headless=bool(c["headless"]))
  page=context.pages[0] if context.pages else context.new_page()
  page.goto("https://bithumen.be/",wait_until="domcontentloaded")
  try:
   while True:
    try:
     wait_for_bithumen_login(page,c)
     cycle(page,s,c,state)
    except Exception as e:log(f"Ellenőrzési hiba (ebben a körben nincs törlés): {e}")
    log(f"Következő ellenőrzés {c['check_minutes']} perc múlva.")
    time.sleep(max(1,int(c["check_minutes"]))*60)
  except KeyboardInterrupt:log("Leállítva.")
  finally:context.close()
if __name__=="__main__":
 main()
