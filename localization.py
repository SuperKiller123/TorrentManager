# -*- coding: utf-8 -*-
"""Bundled UI translations: ten widely spoken languages plus Hungarian.
No network translations, and a missing entry falls back to Hungarian.
"""
LANGUAGES = {
    'en': 'English', 'zh': '中文（简体）', 'hi': 'हिन्दी',
    'es': 'Español', 'fr': 'Français', 'ar': 'العربية',
    'bn': 'বাংলা', 'pt': 'Português', 'ru': 'Русский',
    'ur': 'اردو', 'hu': 'Magyar', 'de': 'Deutsch',
}

# Common UI terminology; all versions use one installer, one application executable.
TEXT = {
'hu': {
 'home':'Kezdőlap','settings':'Beállítások','logs':'Napló és események','updates':'Frissítések',
 'start':'Indítás','stop':'Leállítás','running':'Fut','stopped':'Leállítva','waiting':'Várakozás a WebUI-ra…',
 'connected':'Kapcsolódva','connection':'Kapcsolatok','qb':'qBittorrent','webui':'WebUI',
 'space':'Tárhelyhasználat','limit':'Tárhelykorlát','mode':'Működési mód','dry':'Próbaüzem',
 'add':'Csak hozzáadás','full':'Hozzáadás és fájltörlés','total':'Torrentek száma',
 'interval':'Ellenőrzés','minsize':'Minimális méret','maxsize':'Maximális méret',
 'recent':'Legutóbbi események','safety':'Biztonság és működés','automation':'Automatizálás',
 'limits':'Aktuális korlátok','unavailable':'Nem érhető el','no_limit':'Nincs méretkorlát',
 'save':'Beállítások mentése','connection_settings':'qBittorrent kapcsolat',
 'url':'WebUI címe','user':'Felhasználónév','password':'Jelszó','path':'Letöltési mappa',
 'browse':'Tallózás','show':'Mutatás','hide':'Elrejtés','automation_limits':'Automatizálási korlátok',
 'interval_m':'Ellenőrzési időköz (perc)','total_n':'Torrentek száma (darab)',
 'limit_percent':'Tárhelykorlát (%)','min_gb':'Minimális torrentméret (GB)',
 'max_gb':'Maximális torrentméret (GB)','dry_full':'Próbaüzem (nincs módosítás)',
 'add_full':'Csak új torrentek hozzáadása','delete_full':'Hozzáadás és törlés fájlokkal együtt',
 'appearance':'Megjelenés és nyelv','theme':'Megjelenés','dark':'Sötét','light':'Világos',
 'system':'Windows szerint','language':'Nyelv','live_log':'Élő eseménynapló',
 'open_logs':'Naplómappa megnyitása','installed':'Telepített verzió',
 'latest':'Legújabb verzió','check':'Frissítés keresése','install':'Kiválasztott verzió telepítése',
 'versions':'Elérhető verziók','about':'A Torrent Managerről','github':'GitHub-projekt megnyitása',
 'download_note':'Kizárólag SHA-256 ellenőrzéssel ellátott Windows-telepítők használhatók.',
 'status':'Állapot','disk_info':'Felhasznált / korlát','next':'Következő ellenőrzés',
 'select_version':'Válassz verziót','check_qb':'WebUI ellenőrzése…',
 'saved':'Beállítások mentve.','update_ready':'Elérhető verziók betöltve.',
 'language_note':'A nyelv és a téma mentés után azonnal alkalmazódik.',
},
'en': {
 'home':'Dashboard','settings':'Settings','logs':'Log and events','updates':'Updates','start':'Start','stop':'Stop',
 'running':'Running','stopped':'Stopped','waiting':'Waiting for WebUI…','connected':'Connected',
 'connection':'Connections','qb':'qBittorrent','webui':'WebUI','space':'Disk usage','limit':'Disk limit','mode':'Operating mode','dry':'Dry run',
 'add':'Add only','full':'Add and delete files','total':'Torrent count','interval':'Interval',
 'minsize':'Minimum size','maxsize':'Maximum size','recent':'Recent events','safety':'Safety and operation',
 'automation':'Automation','limits':'Current limits','unavailable':'Unavailable','no_limit':'No size limit',
 'save':'Save settings','connection_settings':'qBittorrent connection','url':'WebUI URL',
 'user':'Username','password':'Password','path':'Download folder','browse':'Browse','show':'Show','hide':'Hide',
 'automation_limits':'Automation limits','interval_m':'Check interval (minutes)',
 'total_n':'Number of torrents','limit_percent':'Disk limit (%)',
 'min_gb':'Minimum torrent size (GB)','max_gb':'Maximum torrent size (GB)',
 'dry_full':'Dry run (no changes)','add_full':'Add new torrents only',
 'delete_full':'Add and delete torrents including files','appearance':'Appearance and language',
 'theme':'Theme','dark':'Dark','light':'Light','system':'Follow Windows','language':'Language',
 'live_log':'Live event log','open_logs':'Open log folder','installed':'Installed version',
 'latest':'Latest version','check':'Check for updates','install':'Install selected version',
 'versions':'Available versions','about':'About Torrent Manager','github':'Open GitHub project',
 'download_note':'Only Windows installers with verified SHA-256 checksums are allowed.',
 'status':'Status','disk_info':'Used / limit','next':'Next check','select_version':'Select version',
 'check_qb':'Checking WebUI…','saved':'Settings saved.','update_ready':'Available versions loaded.',
 'language_note':'Theme and language apply as soon as you save.',
},
'de': {
 'home':'Startseite','settings':'Einstellungen','logs':'Protokoll und Ereignisse','updates':'Updates',
 'start':'Starten','stop':'Stoppen','running':'Läuft','stopped':'Gestoppt','waiting':'Warte auf WebUI…',
 'connected':'Verbunden','connection':'Verbindungen','qb':'qBittorrent','webui':'WebUI','space':'Speichernutzung','limit':'Speicherlimit',
 'mode':'Betriebsmodus','dry':'Testlauf','add':'Nur hinzufügen','full':'Hinzufügen und löschen',
 'total':'Anzahl Torrents','interval':'Intervall','minsize':'Mindestgröße','maxsize':'Maximalgröße',
 'recent':'Letzte Ereignisse','safety':'Sicherheit und Betrieb','automation':'Automatisierung',
 'limits':'Aktuelle Grenzwerte','unavailable':'Nicht verfügbar','no_limit':'Keine Größenbegrenzung',
 'save':'Einstellungen speichern','connection_settings':'qBittorrent-Verbindung','url':'WebUI-Adresse',
 'user':'Benutzername','password':'Passwort','path':'Downloadordner','browse':'Durchsuchen',
 'show':'Anzeigen','hide':'Verbergen','automation_limits':'Automatisierungsgrenzen',
 'interval_m':'Prüfintervall (Minuten)','total_n':'Anzahl Torrents','limit_percent':'Speicherlimit (%)',
 'min_gb':'Mindestgröße (GB)','max_gb':'Maximalgröße (GB)','dry_full':'Testlauf (keine Änderungen)',
 'add_full':'Nur neue Torrents hinzufügen','delete_full':'Hinzufügen und Löschen mit Dateien',
 'appearance':'Darstellung und Sprache','theme':'Design','dark':'Dunkel','light':'Hell',
 'system':'Windows-Einstellung','language':'Sprache','live_log':'Live-Protokoll',
 'open_logs':'Protokollordner öffnen','installed':'Installierte Version','latest':'Neueste Version',
 'check':'Nach Updates suchen','install':'Ausgewählte Version installieren',
 'versions':'Verfügbare Versionen','about':'Über Torrent Manager','github':'GitHub-Projekt öffnen',
 'download_note':'Nur Windows-Installer mit geprüfter SHA-256-Prüfsumme.',
 'status':'Status','disk_info':'Belegt / Limit','next':'Nächste Prüfung',
 'select_version':'Version auswählen','check_qb':'WebUI wird geprüft…',
 'saved':'Einstellungen gespeichert.','update_ready':'Verfügbare Versionen geladen.',
 'language_note':'Sprache und Design werden nach dem Speichern übernommen.',
},
}

# Other major world languages. UI translation bundles are offline and small.
_EXTRA = {
'zh': '''首页|设置|日志与事件|更新|启动|停止|运行中|已停止|等待 WebUI…|已连接|连接|磁盘使用率|磁盘上限|运行模式|模拟运行|仅添加|添加并删除文件|种子数量|间隔|最小大小|最大大小|最近事件|安全与运行|自动化|当前限制|不可用|无限制|保存设置|qBittorrent 连接|WebUI 地址|用户名|密码|下载目录|浏览|显示|隐藏|自动化限制|检查间隔（分钟）|种子数量|磁盘限制 (%)|最小种子大小 (GB)|最大种子大小 (GB)|模拟运行（不修改）|仅添加新种子|添加并删除种子及文件|外观与语言|主题|深色|浅色|跟随 Windows|语言|实时事件日志|打开日志目录|已安装版本|最新版本|检查更新|安装所选版本|可用版本|关于 Torrent Manager|打开 GitHub 项目|仅允许经过 SHA-256 校验的 Windows 安装程序。|状态|已用 / 限制|下次检查|选择版本|检查 WebUI…|设置已保存。|已加载可用版本。|保存后立即应用语言和主题。''',
'hi': '''डैशबोर्ड|सेटिंग्स|लॉग और घटनाएँ|अपडेट|शुरू करें|रोकें|चल रहा है|बंद|WebUI की प्रतीक्षा…|कनेक्टेड|कनेक्शन|डिस्क उपयोग|डिस्क सीमा|कार्य मोड|परीक्षण मोड|केवल जोड़ें|जोड़ें और फ़ाइल हटाएँ|टोरेंट संख्या|अंतराल|न्यूनतम आकार|अधिकतम आकार|हाल की घटनाएँ|सुरक्षा और संचालन|स्वचालन|वर्तमान सीमाएँ|उपलब्ध नहीं|आकार सीमा नहीं|सेटिंग्स सहेजें|qBittorrent कनेक्शन|WebUI पता|उपयोगकर्ता नाम|पासवर्ड|डाउनलोड फ़ोल्डर|ब्राउज़ करें|दिखाएँ|छिपाएँ|स्वचालन सीमाएँ|जाँच अंतराल (मिनट)|टोरेंट संख्या|डिस्क सीमा (%)|न्यूनतम टोरेंट आकार (GB)|अधिकतम टोरेंट आकार (GB)|परीक्षण मोड (बदलाव नहीं)|केवल नए टोरेंट जोड़ें|टोरेंट और फ़ाइलें जोड़ें/हटाएँ|रूप और भाषा|थीम|डार्क|लाइट|Windows के अनुसार|भाषा|लाइव इवेंट लॉग|लॉग फ़ोल्डर खोलें|स्थापित संस्करण|नवीनतम संस्करण|अपडेट जाँचें|चयनित संस्करण इंस्टॉल करें|उपलब्ध संस्करण|Torrent Manager के बारे में|GitHub प्रोजेक्ट खोलें|केवल SHA-256 सत्यापित Windows इंस्टॉलर।|स्थिति|उपयोग / सीमा|अगली जाँच|संस्करण चुनें|WebUI जाँच…|सेटिंग्स सहेजी गईं।|संस्करण लोड हो गए।|सहेजने पर भाषा और थीम लागू होती हैं।''',
'es': '''Inicio|Configuración|Registro y eventos|Actualizaciones|Iniciar|Detener|En ejecución|Detenido|Esperando WebUI…|Conectado|Conexiones|Uso de disco|Límite de disco|Modo de operación|Simulación|Solo añadir|Añadir y borrar archivos|Número de torrents|Intervalo|Tamaño mínimo|Tamaño máximo|Eventos recientes|Seguridad y funcionamiento|Automatización|Límites actuales|No disponible|Sin límite de tamaño|Guardar configuración|Conexión qBittorrent|Dirección WebUI|Usuario|Contraseña|Carpeta de descargas|Examinar|Mostrar|Ocultar|Límites de automatización|Intervalo (minutos)|Número de torrents|Límite de disco (%)|Tamaño mínimo (GB)|Tamaño máximo (GB)|Simulación (sin cambios)|Solo añadir torrents nuevos|Añadir y borrar torrents con archivos|Aspecto e idioma|Tema|Oscuro|Claro|Según Windows|Idioma|Registro en vivo|Abrir carpeta de registros|Versión instalada|Última versión|Buscar actualizaciones|Instalar versión seleccionada|Versiones disponibles|Acerca de Torrent Manager|Abrir GitHub|Solo instaladores de Windows verificados por SHA-256.|Estado|Uso / límite|Próxima revisión|Seleccionar versión|Comprobando WebUI…|Configuración guardada.|Versiones cargadas.|El idioma y tema se aplican al guardar.''',
'fr': '''Accueil|Paramètres|Journal et événements|Mises à jour|Démarrer|Arrêter|En cours|Arrêté|En attente de WebUI…|Connecté|Connexions|Espace disque utilisé|Limite du disque|Mode de fonctionnement|Simulation|Ajout uniquement|Ajouter et supprimer|Nombre de torrents|Intervalle|Taille minimale|Taille maximale|Événements récents|Sécurité et fonctionnement|Automatisation|Limites actuelles|Indisponible|Sans limite de taille|Enregistrer les paramètres|Connexion qBittorrent|Adresse WebUI|Utilisateur|Mot de passe|Dossier de téléchargement|Parcourir|Afficher|Masquer|Limites d’automatisation|Intervalle (minutes)|Nombre de torrents|Limite du disque (%)|Taille minimale (Go)|Taille maximale (Go)|Simulation (aucun changement)|Ajouter de nouveaux torrents|Ajouter et supprimer avec fichiers|Apparence et langue|Thème|Sombre|Clair|Suivre Windows|Langue|Journal en direct|Ouvrir les journaux|Version installée|Dernière version|Rechercher des mises à jour|Installer la version choisie|Versions disponibles|À propos de Torrent Manager|Ouvrir GitHub|Seuls les installateurs Windows validés par SHA-256 sont autorisés.|État|Utilisé / limite|Prochaine vérification|Choisir la version|Vérification WebUI…|Paramètres enregistrés.|Versions chargées.|Langue et thème appliqués après l’enregistrement.''',
'ar': '''الرئيسية|الإعدادات|السجل والأحداث|التحديثات|بدء|إيقاف|يعمل|متوقف|انتظار WebUI…|متصل|الاتصالات|استخدام القرص|حد القرص|وضع التشغيل|تجريبي|إضافة فقط|إضافة وحذف الملفات|عدد التورنت|الفاصل|الحد الأدنى للحجم|الحد الأقصى للحجم|الأحداث الأخيرة|الأمان والتشغيل|الأتمتة|الحدود الحالية|غير متاح|بدون حد للحجم|حفظ الإعدادات|اتصال qBittorrent|عنوان WebUI|اسم المستخدم|كلمة المرور|مجلد التنزيل|استعراض|إظهار|إخفاء|حدود الأتمتة|الفاصل بالدقائق|عدد التورنت|حد القرص (%)|أصغر تورنت (GB)|أكبر تورنت (GB)|وضع تجريبي دون تغييرات|إضافة ملفات التورنت الجديدة فقط|إضافة وحذف التورنت وملفاته|المظهر واللغة|السمة|داكن|فاتح|حسب Windows|اللغة|سجل الأحداث المباشر|فتح مجلد السجل|الإصدار المثبت|أحدث إصدار|التحقق من التحديثات|تثبيت الإصدار المحدد|الإصدارات المتاحة|حول Torrent Manager|فتح GitHub|يُسمح فقط بمثبتات Windows الموثقة بـ SHA-256.|الحالة|المستخدم / الحد|الفحص التالي|اختر الإصدار|فحص WebUI…|تم حفظ الإعدادات.|تم تحميل الإصدارات.|يتم تطبيق اللغة والسمة بعد الحفظ.''',
'bn': '''ড্যাশবোর্ড|সেটিংস|লগ ও ঘটনা|আপডেট|শুরু|বন্ধ|চলছে|বন্ধ আছে|WebUI এর অপেক্ষা…|সংযুক্ত|সংযোগ|ডিস্ক ব্যবহার|ডিস্ক সীমা|চালনার ধরন|পরীক্ষামূলক|শুধু যোগ|যোগ ও ফাইল মুছুন|টরেন্ট সংখ্যা|বিরতি|সর্বনিম্ন আকার|সর্বোচ্চ আকার|সাম্প্রতিক ঘটনা|নিরাপত্তা ও কার্যক্রম|স্বয়ংক্রিয়তা|বর্তমান সীমা|পাওয়া যাচ্ছে না|আকারের সীমা নেই|সেটিংস সংরক্ষণ|qBittorrent সংযোগ|WebUI ঠিকানা|ব্যবহারকারীর নাম|পাসওয়ার্ড|ডাউনলোড ফোল্ডার|ব্রাউজ|দেখান|লুকান|স্বয়ংক্রিয়তার সীমা|পরীক্ষার বিরতি (মিনিট)|টরেন্ট সংখ্যা|ডিস্ক সীমা (%)|সর্বনিম্ন টরেন্ট (GB)|সর্বোচ্চ টরেন্ট (GB)|পরীক্ষামূলক (পরিবর্তন নয়)|শুধু নতুন টরেন্ট যোগ|ফাইলসহ যোগ ও মুছুন|রূপ ও ভাষা|থিম|গাঢ়|হালকা|Windows অনুসরণ|ভাষা|লাইভ লগ|লগ ফোল্ডার খুলুন|ইনস্টল করা সংস্করণ|সর্বশেষ সংস্করণ|আপডেট দেখুন|নির্বাচিত সংস্করণ ইনস্টল|উপলব্ধ সংস্করণ|Torrent Manager সম্পর্কে|GitHub খুলুন|কেবল SHA-256 যাচাইকৃত Windows ইনস্টলার।|অবস্থা|ব্যবহৃত / সীমা|পরের পরীক্ষা|সংস্করণ নির্বাচন|WebUI পরীক্ষা…|সেটিংস সংরক্ষিত।|সংস্করণ লোড হয়েছে।|সংরক্ষণের পর ভাষা ও থিম কার্যকর হয়।''',
'pt': '''Início|Configurações|Registro e eventos|Atualizações|Iniciar|Parar|Executando|Parado|Aguardando WebUI…|Conectado|Conexões|Uso do disco|Limite de disco|Modo de operação|Simulação|Apenas adicionar|Adicionar e excluir arquivos|Número de torrents|Intervalo|Tamanho mínimo|Tamanho máximo|Eventos recentes|Segurança e operação|Automação|Limites atuais|Indisponível|Sem limite de tamanho|Salvar configurações|Conexão qBittorrent|Endereço WebUI|Usuário|Senha|Pasta de downloads|Procurar|Mostrar|Ocultar|Limites de automação|Intervalo (minutos)|Número de torrents|Limite do disco (%)|Tamanho mínimo (GB)|Tamanho máximo (GB)|Simulação (sem alterações)|Adicionar apenas torrents novos|Adicionar e excluir com arquivos|Aparência e idioma|Tema|Escuro|Claro|Seguir Windows|Idioma|Registro ao vivo|Abrir pasta de logs|Versão instalada|Última versão|Verificar atualizações|Instalar versão selecionada|Versões disponíveis|Sobre o Torrent Manager|Abrir projeto GitHub|Somente instaladores Windows com SHA-256 verificado.|Status|Usado / limite|Próxima verificação|Selecionar versão|Verificando WebUI…|Configurações salvas.|Versões carregadas.|Idioma e tema aplicados após salvar.''',
'ru': '''Главная|Настройки|Журнал и события|Обновления|Запуск|Стоп|Работает|Остановлено|Ожидание WebUI…|Подключено|Соединения|Использование диска|Лимит диска|Режим работы|Пробный запуск|Только добавление|Добавление и удаление файлов|Количество торрентов|Интервал|Мин. размер|Макс. размер|Последние события|Безопасность и работа|Автоматизация|Текущие ограничения|Недоступно|Без ограничения размера|Сохранить настройки|Подключение qBittorrent|Адрес WebUI|Имя пользователя|Пароль|Папка загрузок|Обзор|Показать|Скрыть|Ограничения автоматизации|Интервал (мин.)|Количество торрентов|Лимит диска (%)|Мин. размер торрента (ГБ)|Макс. размер торрента (ГБ)|Пробный запуск (без изменений)|Только добавление новых торрентов|Добавление и удаление с файлами|Тема и язык|Тема|Тёмная|Светлая|Как в Windows|Язык|Журнал событий|Открыть папку журнала|Установленная версия|Последняя версия|Проверить обновления|Установить выбранную версию|Доступные версии|О Torrent Manager|Открыть GitHub|Только установщики Windows с проверкой SHA-256.|Статус|Занято / лимит|Следующая проверка|Выбрать версию|Проверка WebUI…|Настройки сохранены.|Версии загружены.|Язык и тема применяются после сохранения.''',
'ur': '''ڈیش بورڈ|ترتیبات|لاگ اور واقعات|اپ ڈیٹس|شروع|بند کریں|چل رہا ہے|بند ہے|WebUI کا انتظار…|منسلک|کنکشن|ڈسک استعمال|ڈسک کی حد|کام کا طریقہ|آزمائشی|صرف شامل|فائلیں شامل اور حذف|ٹورینٹ تعداد|وقفہ|کم از کم حجم|زیادہ سے زیادہ حجم|حالیہ واقعات|حفاظت اور عمل|خودکار نظام|موجودہ حدود|دستیاب نہیں|حجم کی حد نہیں|ترتیبات محفوظ کریں|qBittorrent کنکشن|WebUI پتہ|صارف نام|پاس ورڈ|ڈاؤن لوڈ فولڈر|براؤز|دکھائیں|چھپائیں|خودکار حدود|جانچ کا وقفہ (منٹ)|ٹورینٹ تعداد|ڈسک کی حد (%)|کم از کم ٹورینٹ (GB)|زیادہ سے زیادہ ٹورینٹ (GB)|آزمائشی (تبدیلی نہیں)|صرف نئے ٹورینٹ شامل|فائلوں کے ساتھ شامل اور حذف|ظاہری شکل اور زبان|تھیم|گہرا|ہلکا|Windows کے مطابق|زبان|براہ راست لاگ|لاگ فولڈر کھولیں|نصب شدہ ورژن|تازہ ترین ورژن|اپ ڈیٹ چیک کریں|منتخب ورژن نصب کریں|دستیاب ورژن|Torrent Manager کے بارے میں|GitHub کھولیں|صرف SHA-256 تصدیق شدہ Windows انسٹالر۔|حالت|استعمال / حد|اگلی جانچ|ورژن منتخب کریں|WebUI جانچ…|ترتیبات محفوظ ہوئیں۔|ورژن لوڈ ہوئے۔|محفوظ کرنے کے بعد زبان اور تھیم لاگو ہوں گے۔''',
}
_KEYS = list(TEXT['hu'])
for _language, _text in _EXTRA.items():
    _translated = _text.split('|')
    _translated[11:11] = ['qBittorrent', 'WebUI']
    if len(_translated) != len(_KEYS):
        raise ValueError(f'{_language}: {len(_translated)} translations, expected {len(_KEYS)}')
    TEXT[_language] = dict(zip(_KEYS, _translated))

def tr(code, key):
    return TEXT.get(code, TEXT['hu']).get(key, TEXT['hu'].get(key, key))

# Status and BitHuMen authorization UI. Technical engine messages are retained
# in their original language inside the audit log.
STATUS_TEXT = {
'hu': ('Hiányzó WebUI bejelentkezés','Hibás WebUI hozzáférés','Hibás WebUI-cím',
       'BitHuMen – egyszeri bejelentkezés','Bejelentkezés megnyitása',
       'A Torrent Manager a BitHuMen seederek szerint rendezett toplistáját figyeli, és a qBittorrent WebUI-val automatikusan kezeli a torrenteket. Beállítható a torrentszám, a méretkorlát és a tárhelyhatár. Próbaüzem, csak hozzáadás és ellenőrzött törlés választható. A működés eseménynaplóban követhető, és a program lehetővé teszi a korábbi verziók biztonságos telepítését.'),
'en': ('Missing WebUI credentials','Incorrect WebUI credentials','Invalid WebUI address',
       'BitHuMen – manual sign-in','Open sign-in browser',
       'Torrent Manager monitors BitHuMen torrents sorted by seeders and automates qBittorrent through its WebUI. You can set torrent count, size limits and a disk usage cap. Choose dry run, add only, or controlled removal. The event log tracks all operations, and previous releases can be installed after integrity verification.'),
'de': ('WebUI-Zugangsdaten fehlen','Ungültige WebUI-Zugangsdaten','Ungültige WebUI-Adresse',
       'BitHuMen – manuelle Anmeldung','Anmeldung öffnen',
       'Torrent Manager überwacht die nach Seedern sortierte BitHuMen-Liste und automatisiert qBittorrent über die WebUI. Anzahl, Größenlimits und Speichergrenze sind einstellbar. Zur Auswahl stehen Testlauf, nur Hinzufügen und kontrolliertes Löschen. Ereignisse werden protokolliert und ältere Versionen können geprüft installiert werden.'),
'zh': ('缺少 WebUI 凭据','WebUI 凭据无效','WebUI 地址无效',
       'BitHuMen – 手动登录','打开登录窗口',
       'Torrent Manager 监控按做种人数排序的 BitHuMen 列表，并通过 qBittorrent WebUI 自动管理种子。可以设置种子数量、大小限制和磁盘使用阈值。支持模拟运行、仅添加和受控删除。日志记录操作，并可安全安装已验证的旧版本。'),
'hi': ('WebUI लॉगिन जानकारी नहीं है','WebUI लॉगिन गलत है','WebUI पता गलत है',
       'BitHuMen – मैनुअल लॉगिन','लॉगिन खोलें',
       'Torrent Manager BitHuMen की सीडर सूची पर नज़र रखता है और qBittorrent WebUI के ज़रिए टोरेंट प्रबंधित करता है। टोरेंट संख्या, आकार और डिस्क सीमा तय की जा सकती है। परीक्षण मोड, केवल जोड़ना और नियंत्रित हटाना उपलब्ध हैं। गतिविधि लॉग और सत्यापित पुराने संस्करण भी समर्थित हैं।'),
'es': ('Faltan credenciales WebUI','Credenciales WebUI incorrectas','Dirección WebUI no válida',
       'BitHuMen – inicio de sesión manual','Abrir inicio de sesión',
       'Torrent Manager supervisa la lista de BitHuMen ordenada por semillas y gestiona torrents con qBittorrent WebUI. Se pueden configurar número, tamaño y límite de disco. Ofrece simulación, solo agregar y eliminación controlada. Registra las actividades y permite instalar versiones anteriores verificadas.'),
'fr': ('Identifiants WebUI manquants','Identifiants WebUI incorrects','Adresse WebUI invalide',
       'BitHuMen – connexion manuelle','Ouvrir la connexion',
       'Torrent Manager surveille la liste BitHuMen classée par seeders et automatise qBittorrent via WebUI. Définissez le nombre de torrents, leurs tailles et la limite de stockage. Les modes simulation, ajout seul et suppression contrôlée sont disponibles. Les actions sont journalisées, et les anciennes versions vérifiées peuvent être installées.'),
'ar': ('بيانات WebUI مفقودة','بيانات WebUI غير صحيحة','عنوان WebUI غير صالح',
       'BitHuMen – تسجيل الدخول اليدوي','فتح تسجيل الدخول',
       'يراقب Torrent Manager قائمة BitHuMen المرتبة حسب عدد المشاركين، ويدير التورنت عبر qBittorrent WebUI. يمكنك ضبط العدد والحد الأدنى والأقصى للحجم وسعة القرص. تتوفر أوضاع التجربة والإضافة فقط والحذف المتحكم به. تُسجل العمليات ويمكن تثبيت الإصدارات السابقة المتحقق منها.'),
'bn': ('WebUI লগইন তথ্য নেই','WebUI লগইন ভুল','WebUI ঠিকানা ভুল',
       'BitHuMen – ম্যানুয়াল লগইন','লগইন খুলুন',
       'Torrent Manager BitHuMen-এর সিডার অনুযায়ী সাজানো তালিকা দেখে এবং qBittorrent WebUI দিয়ে টরেন্ট পরিচালনা করে। সংখ্যা, আকার ও ডিস্ক সীমা নির্ধারণ করা যায়। পরীক্ষামূলক, শুধু যোগ এবং নিয়ন্ত্রিত মুছে ফেলা মোড আছে। কাজের লগ রাখা হয় এবং যাচাইকৃত পুরোনো সংস্করণ ইনস্টল করা যায়।'),
'pt': ('Credenciais WebUI ausentes','Credenciais WebUI incorretas','Endereço WebUI inválido',
       'BitHuMen – login manual','Abrir login',
       'Torrent Manager monitora a lista de BitHuMen por seeders e automatiza o qBittorrent via WebUI. É possível definir quantidade, tamanhos e limite de disco. Há simulação, somente adição e remoção controlada. As ações são registradas e versões anteriores verificadas podem ser instaladas.'),
'ru': ('Нет данных для WebUI','Неверные данные WebUI','Неверный адрес WebUI',
       'BitHuMen – ручной вход','Открыть окно входа',
       'Torrent Manager отслеживает список BitHuMen, отсортированный по сидерам, и управляет торрентами через qBittorrent WebUI. Можно задать количество, размеры и лимит диска. Доступны пробный запуск, только добавление и контролируемое удаление. Действия записываются, а старые версии устанавливаются после проверки.'),
'ur': ('WebUI لاگ ان موجود نہیں','WebUI کی معلومات غلط ہیں','WebUI پتہ غلط ہے',
       'BitHuMen – دستی لاگ ان','لاگ ان کھولیں',
       'Torrent Manager سیڈرز کے مطابق BitHuMen فہرست کی نگرانی کرتا ہے اور qBittorrent WebUI سے ٹورینٹ سنبھالتا ہے۔ تعداد، سائز اور ڈسک کی حد طے کی جا سکتی ہے۔ آزمائشی، صرف شامل کرنے اور محتاط حذف کرنے کے طریقے موجود ہیں۔ کارروائیاں لاگ میں محفوظ ہوتی ہیں اور پرانے تصدیق شدہ ورژن نصب کیے جا سکتے ہیں۔'),
}
STATUS_KEYS = ('missing_credentials','bad_credentials','invalid_url','login_title','login_open','about_description')
for _code, _values in STATUS_TEXT.items():
    if len(_values) != len(STATUS_KEYS):
        raise ValueError(_code)
    TEXT[_code].update(dict(zip(STATUS_KEYS, _values)))

# v0.7 setup and Windows options. Additional help falls back to English.
V07_EN = {
 'transfer':'Transfer speed', 'setup_close_browser':'Close the login browser before continuing.',
 'setup_title':'First setup',
 'setup_intro':'Configure the connection and limits. Save is enabled only after a successful WebUI connection test.',
 'setup_finish':'Test connection and save', 'setup_login':'After setup, use the BitHuMen login button in Settings to sign in through the browser.',
 'startup':'Start with Windows', 'close_to_tray':'Close window to notification area', 'desktopicon':'Desktop shortcut', 'exit':'Exit',
 'help_qb_url':'Enter the qBittorrent WebUI address, including http:// or https://.',
 'help_qb_username':'Use the username configured in qBittorrent WebUI.',
 'help_qb_password':'Use your WebUI password, not your tracker password.',
 'help_qb_save_path':'Choose an existing folder for downloaded torrent content.',
 'help_check_minutes':'The tracker is checked at this interval in minutes (1–1440).',
 'help_max_managed_torrents':'Maximum number of torrents managed by this application (1–500).',
 'help_max_disk_usage_percent':'Set the maximum allowed disk usage percentage (1–99).',
 'help_min_size_gb':'Optional minimum torrent size in decimal GB; leave blank for no minimum.',
 'help_max_size_gb':'Optional maximum torrent size in decimal GB; leave blank for no maximum.',
 'help_startup':'Launch the installed application automatically when you sign in to Windows.',
 'help_close_to_tray':'The notification area menu lets you restore or exit the application.',
 'help_desktopicon':'Create or remove your personal desktop shortcut.',
}
V07_HU = {
 'transfer':'Átviteli sebesség', 'setup_close_browser':'A folytatás előtt zárd be a bejelentkezési böngészőt.',
 'setup_title':'Első beállítás',
 'setup_intro':'Állítsd be a kapcsolatot és a korlátokat. A mentéshez sikeres WebUI-kapcsolatteszt szükséges.',
 'setup_finish':'Kapcsolat tesztelése és mentés', 'setup_login':'A beállítás után a Beállítások BitHuMen-bejelentkezés gombjával jelentkezhetsz be a böngészőben.',
 'startup':'Indítás a Windowszal', 'close_to_tray':'Bezáráskor futás az értesítési területen', 'desktopicon':'Asztali parancsikon', 'exit':'Kilépés',
 'help_qb_url':'A qBittorrent WebUI címe http:// vagy https:// előtaggal.',
 'help_qb_username':'A qBittorrent WebUI-ban beállított felhasználónév.',
 'help_qb_password':'A WebUI-jelszót add meg, ne a trackerhez használt jelszavadat.',
 'help_qb_save_path':'Válassz létező mappát a torrentek letöltött tartalmának.',
 'help_check_minutes':'A toplista ellenőrzése ilyen időközönként történik, percben (1–1440).',
 'help_max_managed_torrents':'Az alkalmazás által kezelt torrentek legnagyobb száma (1–500).',
 'help_max_disk_usage_percent':'A megengedett legnagyobb tárhelyhasználat százalékban (1–99).',
 'help_min_size_gb':'Opcionális alsó mérethatár decimális GB-ban; üresen nincs alsó korlát.',
 'help_max_size_gb':'Opcionális felső mérethatár decimális GB-ban; üresen nincs felső korlát.',
 'help_startup':'A telepített alkalmazás automatikusan elindul a Windows-bejelentkezéskor.',
 'help_close_to_tray':'Az értesítési terület ikonjának menüjéből visszaállítható és bezárható az alkalmazás.',
 'help_desktopicon':'A személyes asztali parancsikon létrehozása vagy eltávolítása.',
}
for _code in LANGUAGES:
    TEXT[_code].update(V07_HU if _code == 'hu' else V07_EN)
TEXT['hu']['about_description'] = ('A Torrent Manager a BitHuMen seederek szerint rendezett toplistáját figyeli. '
 'A qBittorrenthez a WebUI-n keresztül kapcsolódik. Az első indításkor külön beállítófelület segít a konfigurálásban. '
 'Megadható a kezelt torrentek száma. A torrentméret alsó és felső határa decimális GB-ban állítható. '
 'A tárhelyhasználatnak külön korlát szabható. A próbaüzem módosítás nélkül mutatja a tervezett műveleteket. '
 'A csak hozzáadás mód nem töröl torrenteket. A teljes mód kizárólag a program által nyilvántartott torrenteket kezelheti és törölheti. '
 'Az események UTF-8 naplóba kerülnek. A felület sötét és világos témát támogat. '
 'A kiadáslista automatikusan betöltődik, a telepítők letöltését SHA-256 ellenőrzés követi.')
TEXT['en']['about_description'] = ('Torrent Manager monitors the BitHuMen list ordered by seeders. '
 'It connects to qBittorrent through WebUI. First-run setup helps configure the connection. '
 'You can limit the number of managed torrents. Minimum and maximum sizes use decimal GB. '
 'A separate limit controls disk usage. Dry run previews actions without changing torrents. '
 'Add-only mode never deletes torrents. Full mode can delete only torrents recorded as owned by this application. '
 'Events are written to a UTF-8 log. Dark and light themes are available. '
 'Release lists load automatically and downloaded installers require SHA-256 verification.')

from localization_v07 import extend as _extend_v07
_extend_v07(TEXT)
from localization_v07 import ABOUT as _ABOUT_V07
for _code, _description in _ABOUT_V07.items():
    TEXT[_code]['about_description'] = _description
