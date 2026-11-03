# Project Directory Structure

**Last Updated:** Phase A (Automated)

---

## Current Active Tree

```text
kids_game/
├── build
│   └── MotionController
│       ├── localpycs
│       │   ├── pyimod01_archive.pyc
│       │   ├── pyimod02_importers.pyc
│       │   ├── pyimod03_ctypes.pyc
│       │   ├── pyimod04_pywin32.pyc
│       │   └── struct.pyc
│       ├── Analysis-00.toc
│       ├── base_library.zip
│       ├── COLLECT-00.toc
│       ├── EXE-00.toc
│       ├── MotionController.exe
│       ├── MotionController.pkg
│       ├── PKG-00.toc
│       ├── PYZ-00.pyz
│       ├── PYZ-00.toc
│       ├── warn-MotionController.txt
│       └── xref-MotionController.html
├── core
│   ├── __init__.py
│   ├── config.py
│   ├── event_bus.py
│   ├── events.py
│   ├── input_keyboard.py
│   └── logger.py
├── dist
│   └── MotionController
│       ├── _internal
│       │   ├── _sounddevice_data
│       │   │   └── portaudio-binaries
│       │   │       ├── libportaudio.dylib
│       │   │       ├── libportaudio32bit-asio.dll
│       │   │       ├── libportaudio32bit.dll
│       │   │       ├── libportaudio64bit-asio.dll
│       │   │       ├── libportaudio64bit.dll
│       │   │       ├── libportaudioarm64-asio.dll
│       │   │       ├── libportaudioarm64.dll
│       │   │       └── README.md
│       │   ├── _tcl_data
│       │   │   ├── encoding
│       │   │   │   ├── ascii.enc
│       │   │   │   ├── big5.enc
│       │   │   │   ├── cns11643.enc
│       │   │   │   ├── cp1250.enc
│       │   │   │   ├── cp1251.enc
│       │   │   │   ├── cp1252.enc
│       │   │   │   ├── cp1253.enc
│       │   │   │   ├── cp1254.enc
│       │   │   │   ├── cp1255.enc
│       │   │   │   ├── cp1256.enc
│       │   │   │   ├── cp1257.enc
│       │   │   │   ├── cp1258.enc
│       │   │   │   ├── cp437.enc
│       │   │   │   ├── cp737.enc
│       │   │   │   ├── cp775.enc
│       │   │   │   ├── cp850.enc
│       │   │   │   ├── cp852.enc
│       │   │   │   ├── cp855.enc
│       │   │   │   ├── cp857.enc
│       │   │   │   ├── cp860.enc
│       │   │   │   ├── cp861.enc
│       │   │   │   ├── cp862.enc
│       │   │   │   ├── cp863.enc
│       │   │   │   ├── cp864.enc
│       │   │   │   ├── cp865.enc
│       │   │   │   ├── cp866.enc
│       │   │   │   ├── cp869.enc
│       │   │   │   ├── cp874.enc
│       │   │   │   ├── cp932.enc
│       │   │   │   ├── cp936.enc
│       │   │   │   ├── cp949.enc
│       │   │   │   ├── cp950.enc
│       │   │   │   ├── dingbats.enc
│       │   │   │   ├── ebcdic.enc
│       │   │   │   ├── euc-cn.enc
│       │   │   │   ├── euc-jp.enc
│       │   │   │   ├── euc-kr.enc
│       │   │   │   ├── gb12345.enc
│       │   │   │   ├── gb1988.enc
│       │   │   │   ├── gb2312-raw.enc
│       │   │   │   ├── gb2312.enc
│       │   │   │   ├── iso2022-jp.enc
│       │   │   │   ├── iso2022-kr.enc
│       │   │   │   ├── iso2022.enc
│       │   │   │   ├── iso8859-1.enc
│       │   │   │   ├── iso8859-10.enc
│       │   │   │   ├── iso8859-11.enc
│       │   │   │   ├── iso8859-13.enc
│       │   │   │   ├── iso8859-14.enc
│       │   │   │   ├── iso8859-15.enc
│       │   │   │   ├── iso8859-16.enc
│       │   │   │   ├── iso8859-2.enc
│       │   │   │   ├── iso8859-3.enc
│       │   │   │   ├── iso8859-4.enc
│       │   │   │   ├── iso8859-5.enc
│       │   │   │   ├── iso8859-6.enc
│       │   │   │   ├── iso8859-7.enc
│       │   │   │   ├── iso8859-8.enc
│       │   │   │   ├── iso8859-9.enc
│       │   │   │   ├── jis0201.enc
│       │   │   │   ├── jis0208.enc
│       │   │   │   ├── jis0212.enc
│       │   │   │   ├── koi8-r.enc
│       │   │   │   ├── koi8-ru.enc
│       │   │   │   ├── koi8-t.enc
│       │   │   │   ├── koi8-u.enc
│       │   │   │   ├── ksc5601.enc
│       │   │   │   ├── macCentEuro.enc
│       │   │   │   ├── macCroatian.enc
│       │   │   │   ├── macCyrillic.enc
│       │   │   │   ├── macDingbats.enc
│       │   │   │   ├── macGreek.enc
│       │   │   │   ├── macIceland.enc
│       │   │   │   ├── macJapan.enc
│       │   │   │   ├── macRoman.enc
│       │   │   │   ├── macRomania.enc
│       │   │   │   ├── macThai.enc
│       │   │   │   ├── macTurkish.enc
│       │   │   │   ├── macUkraine.enc
│       │   │   │   ├── shiftjis.enc
│       │   │   │   ├── symbol.enc
│       │   │   │   └── tis-620.enc
│       │   │   ├── http1.0
│       │   │   │   ├── http.tcl
│       │   │   │   └── pkgIndex.tcl
│       │   │   ├── msgs
│       │   │   │   ├── af.msg
│       │   │   │   ├── af_za.msg
│       │   │   │   ├── ar.msg
│       │   │   │   ├── ar_in.msg
│       │   │   │   ├── ar_jo.msg
│       │   │   │   ├── ar_lb.msg
│       │   │   │   ├── ar_sy.msg
│       │   │   │   ├── be.msg
│       │   │   │   ├── bg.msg
│       │   │   │   ├── bn.msg
│       │   │   │   ├── bn_in.msg
│       │   │   │   ├── ca.msg
│       │   │   │   ├── cs.msg
│       │   │   │   ├── da.msg
│       │   │   │   ├── de.msg
│       │   │   │   ├── de_at.msg
│       │   │   │   ├── de_be.msg
│       │   │   │   ├── el.msg
│       │   │   │   ├── en_au.msg
│       │   │   │   ├── en_be.msg
│       │   │   │   ├── en_bw.msg
│       │   │   │   ├── en_ca.msg
│       │   │   │   ├── en_gb.msg
│       │   │   │   ├── en_hk.msg
│       │   │   │   ├── en_ie.msg
│       │   │   │   ├── en_in.msg
│       │   │   │   ├── en_nz.msg
│       │   │   │   ├── en_ph.msg
│       │   │   │   ├── en_sg.msg
│       │   │   │   ├── en_za.msg
│       │   │   │   ├── en_zw.msg
│       │   │   │   ├── eo.msg
│       │   │   │   ├── es.msg
│       │   │   │   ├── es_ar.msg
│       │   │   │   ├── es_bo.msg
│       │   │   │   ├── es_cl.msg
│       │   │   │   ├── es_co.msg
│       │   │   │   ├── es_cr.msg
│       │   │   │   ├── es_do.msg
│       │   │   │   ├── es_ec.msg
│       │   │   │   ├── es_gt.msg
│       │   │   │   ├── es_hn.msg
│       │   │   │   ├── es_mx.msg
│       │   │   │   ├── es_ni.msg
│       │   │   │   ├── es_pa.msg
│       │   │   │   ├── es_pe.msg
│       │   │   │   ├── es_pr.msg
│       │   │   │   ├── es_py.msg
│       │   │   │   ├── es_sv.msg
│       │   │   │   ├── es_uy.msg
│       │   │   │   ├── es_ve.msg
│       │   │   │   ├── et.msg
│       │   │   │   ├── eu.msg
│       │   │   │   ├── eu_es.msg
│       │   │   │   ├── fa.msg
│       │   │   │   ├── fa_in.msg
│       │   │   │   ├── fa_ir.msg
│       │   │   │   ├── fi.msg
│       │   │   │   ├── fo.msg
│       │   │   │   ├── fo_fo.msg
│       │   │   │   ├── fr.msg
│       │   │   │   ├── fr_be.msg
│       │   │   │   ├── fr_ca.msg
│       │   │   │   ├── fr_ch.msg
│       │   │   │   ├── ga.msg
│       │   │   │   ├── ga_ie.msg
│       │   │   │   ├── gl.msg
│       │   │   │   ├── gl_es.msg
│       │   │   │   ├── gv.msg
│       │   │   │   ├── gv_gb.msg
│       │   │   │   ├── he.msg
│       │   │   │   ├── hi.msg
│       │   │   │   ├── hi_in.msg
│       │   │   │   ├── hr.msg
│       │   │   │   ├── hu.msg
│       │   │   │   ├── id.msg
│       │   │   │   ├── id_id.msg
│       │   │   │   ├── is.msg
│       │   │   │   ├── it.msg
│       │   │   │   ├── it_ch.msg
│       │   │   │   ├── ja.msg
│       │   │   │   ├── kl.msg
│       │   │   │   ├── kl_gl.msg
│       │   │   │   ├── ko.msg
│       │   │   │   ├── ko_kr.msg
│       │   │   │   ├── kok.msg
│       │   │   │   ├── kok_in.msg
│       │   │   │   ├── kw.msg
│       │   │   │   ├── kw_gb.msg
│       │   │   │   ├── lt.msg
│       │   │   │   ├── lv.msg
│       │   │   │   ├── mk.msg
│       │   │   │   ├── mr.msg
│       │   │   │   ├── mr_in.msg
│       │   │   │   ├── ms.msg
│       │   │   │   ├── ms_my.msg
│       │   │   │   ├── mt.msg
│       │   │   │   ├── nb.msg
│       │   │   │   ├── nl.msg
│       │   │   │   ├── nl_be.msg
│       │   │   │   ├── nn.msg
│       │   │   │   ├── pl.msg
│       │   │   │   ├── pt.msg
│       │   │   │   ├── pt_br.msg
│       │   │   │   ├── ro.msg
│       │   │   │   ├── ru.msg
│       │   │   │   ├── ru_ua.msg
│       │   │   │   ├── sh.msg
│       │   │   │   ├── sk.msg
│       │   │   │   ├── sl.msg
│       │   │   │   ├── sq.msg
│       │   │   │   ├── sr.msg
│       │   │   │   ├── sv.msg
│       │   │   │   ├── sw.msg
│       │   │   │   ├── ta.msg
│       │   │   │   ├── ta_in.msg
│       │   │   │   ├── te.msg
│       │   │   │   ├── te_in.msg
│       │   │   │   ├── th.msg
│       │   │   │   ├── tr.msg
│       │   │   │   ├── uk.msg
│       │   │   │   ├── vi.msg
│       │   │   │   ├── zh.msg
│       │   │   │   ├── zh_cn.msg
│       │   │   │   ├── zh_hk.msg
│       │   │   │   ├── zh_sg.msg
│       │   │   │   └── zh_tw.msg
│       │   │   ├── opt0.4
│       │   │   │   ├── optparse.tcl
│       │   │   │   └── pkgIndex.tcl
│       │   │   ├── tzdata
│       │   │   │   ├── Africa
│       │   │   │   │   ├── Abidjan
│       │   │   │   │   ├── Accra
│       │   │   │   │   ├── Addis_Ababa
│       │   │   │   │   ├── Algiers
│       │   │   │   │   ├── Asmara
│       │   │   │   │   ├── Asmera
│       │   │   │   │   ├── Bamako
│       │   │   │   │   ├── Bangui
│       │   │   │   │   ├── Banjul
│       │   │   │   │   ├── Bissau
│       │   │   │   │   ├── Blantyre
│       │   │   │   │   ├── Brazzaville
│       │   │   │   │   ├── Bujumbura
│       │   │   │   │   ├── Cairo
│       │   │   │   │   ├── Casablanca
│       │   │   │   │   ├── Ceuta
│       │   │   │   │   ├── Conakry
│       │   │   │   │   ├── Dakar
│       │   │   │   │   ├── Dar_es_Salaam
│       │   │   │   │   ├── Djibouti
│       │   │   │   │   ├── Douala
│       │   │   │   │   ├── El_Aaiun
│       │   │   │   │   ├── Freetown
│       │   │   │   │   ├── Gaborone
│       │   │   │   │   ├── Harare
│       │   │   │   │   ├── Johannesburg
│       │   │   │   │   ├── Juba
│       │   │   │   │   ├── Kampala
│       │   │   │   │   ├── Khartoum
│       │   │   │   │   ├── Kigali
│       │   │   │   │   ├── Kinshasa
│       │   │   │   │   ├── Lagos
│       │   │   │   │   ├── Libreville
│       │   │   │   │   ├── Lome
│       │   │   │   │   ├── Luanda
│       │   │   │   │   ├── Lubumbashi
│       │   │   │   │   ├── Lusaka
│       │   │   │   │   ├── Malabo
│       │   │   │   │   ├── Maputo
│       │   │   │   │   ├── Maseru
│       │   │   │   │   ├── Mbabane
│       │   │   │   │   ├── Mogadishu
│       │   │   │   │   ├── Monrovia
│       │   │   │   │   ├── Nairobi
│       │   │   │   │   ├── Ndjamena
│       │   │   │   │   ├── Niamey
│       │   │   │   │   ├── Nouakchott
│       │   │   │   │   ├── Ouagadougou
│       │   │   │   │   ├── Porto-Novo
│       │   │   │   │   ├── Sao_Tome
│       │   │   │   │   ├── Timbuktu
│       │   │   │   │   ├── Tripoli
│       │   │   │   │   ├── Tunis
│       │   │   │   │   └── Windhoek
│       │   │   │   ├── America
│       │   │   │   │   ├── Argentina
│       │   │   │   │   │   ├── Buenos_Aires
│       │   │   │   │   │   ├── Catamarca
│       │   │   │   │   │   ├── ComodRivadavia
│       │   │   │   │   │   ├── Cordoba
│       │   │   │   │   │   ├── Jujuy
│       │   │   │   │   │   ├── La_Rioja
│       │   │   │   │   │   ├── Mendoza
│       │   │   │   │   │   ├── Rio_Gallegos
│       │   │   │   │   │   ├── Salta
│       │   │   │   │   │   ├── San_Juan
│       │   │   │   │   │   ├── San_Luis
│       │   │   │   │   │   ├── Tucuman
│       │   │   │   │   │   └── Ushuaia
│       │   │   │   │   ├── Indiana
│       │   │   │   │   │   ├── Indianapolis
│       │   │   │   │   │   ├── Knox
│       │   │   │   │   │   ├── Marengo
│       │   │   │   │   │   ├── Petersburg
│       │   │   │   │   │   ├── Tell_City
│       │   │   │   │   │   ├── Vevay
│       │   │   │   │   │   ├── Vincennes
│       │   │   │   │   │   └── Winamac
│       │   │   │   │   ├── Kentucky
│       │   │   │   │   │   ├── Louisville
│       │   │   │   │   │   └── Monticello
│       │   │   │   │   ├── North_Dakota
│       │   │   │   │   │   ├── Beulah
│       │   │   │   │   │   ├── Center
│       │   │   │   │   │   └── New_Salem
│       │   │   │   │   ├── Adak
│       │   │   │   │   ├── Anchorage
│       │   │   │   │   ├── Anguilla
│       │   │   │   │   ├── Antigua
│       │   │   │   │   ├── Araguaina
│       │   │   │   │   ├── Aruba
│       │   │   │   │   ├── Asuncion
│       │   │   │   │   ├── Atikokan
│       │   │   │   │   ├── Atka
│       │   │   │   │   ├── Bahia
│       │   │   │   │   ├── Bahia_Banderas
│       │   │   │   │   ├── Barbados
│       │   │   │   │   ├── Belem
│       │   │   │   │   ├── Belize
│       │   │   │   │   ├── Blanc-Sablon
│       │   │   │   │   ├── Boa_Vista
│       │   │   │   │   ├── Bogota
│       │   │   │   │   ├── Boise
│       │   │   │   │   ├── Buenos_Aires
│       │   │   │   │   ├── Cambridge_Bay
│       │   │   │   │   ├── Campo_Grande
│       │   │   │   │   ├── Cancun
│       │   │   │   │   ├── Caracas
│       │   │   │   │   ├── Catamarca
│       │   │   │   │   ├── Cayenne
│       │   │   │   │   ├── Cayman
│       │   │   │   │   ├── Chicago
│       │   │   │   │   ├── Chihuahua
│       │   │   │   │   ├── Ciudad_Juarez
│       │   │   │   │   ├── Coral_Harbour
│       │   │   │   │   ├── Cordoba
│       │   │   │   │   ├── Costa_Rica
│       │   │   │   │   ├── Creston
│       │   │   │   │   ├── Cuiaba
│       │   │   │   │   ├── Curacao
│       │   │   │   │   ├── Danmarkshavn
│       │   │   │   │   ├── Dawson
│       │   │   │   │   ├── Dawson_Creek
│       │   │   │   │   ├── Denver
│       │   │   │   │   ├── Detroit
│       │   │   │   │   ├── Dominica
│       │   │   │   │   ├── Edmonton
│       │   │   │   │   ├── Eirunepe
│       │   │   │   │   ├── El_Salvador
│       │   │   │   │   ├── Ensenada
│       │   │   │   │   ├── Fort_Nelson
│       │   │   │   │   ├── Fort_Wayne
│       │   │   │   │   ├── Fortaleza
│       │   │   │   │   ├── Glace_Bay
│       │   │   │   │   ├── Godthab
│       │   │   │   │   ├── Goose_Bay
│       │   │   │   │   ├── Grand_Turk
│       │   │   │   │   ├── Grenada
│       │   │   │   │   ├── Guadeloupe
│       │   │   │   │   ├── Guatemala
│       │   │   │   │   ├── Guayaquil
│       │   │   │   │   ├── Guyana
│       │   │   │   │   ├── Halifax
│       │   │   │   │   ├── Havana
│       │   │   │   │   ├── Hermosillo
│       │   │   │   │   ├── Indianapolis
│       │   │   │   │   ├── Inuvik
│       │   │   │   │   ├── Iqaluit
│       │   │   │   │   ├── Jamaica
│       │   │   │   │   ├── Jujuy
│       │   │   │   │   ├── Juneau
│       │   │   │   │   ├── Knox_IN
│       │   │   │   │   ├── Kralendijk
│       │   │   │   │   ├── La_Paz
│       │   │   │   │   ├── Lima
│       │   │   │   │   ├── Los_Angeles
│       │   │   │   │   ├── Louisville
│       │   │   │   │   ├── Lower_Princes
│       │   │   │   │   ├── Maceio
│       │   │   │   │   ├── Managua
│       │   │   │   │   ├── Manaus
│       │   │   │   │   ├── Marigot
│       │   │   │   │   ├── Martinique
│       │   │   │   │   ├── Matamoros
│       │   │   │   │   ├── Mazatlan
│       │   │   │   │   ├── Mendoza
│       │   │   │   │   ├── Menominee
│       │   │   │   │   ├── Merida
│       │   │   │   │   ├── Metlakatla
│       │   │   │   │   ├── Mexico_City
│       │   │   │   │   ├── Miquelon
│       │   │   │   │   ├── Moncton
│       │   │   │   │   ├── Monterrey
│       │   │   │   │   ├── Montevideo
│       │   │   │   │   ├── Montreal
│       │   │   │   │   ├── Montserrat
│       │   │   │   │   ├── Nassau
│       │   │   │   │   ├── New_York
│       │   │   │   │   ├── Nipigon
│       │   │   │   │   ├── Nome
│       │   │   │   │   ├── Noronha
│       │   │   │   │   ├── Nuuk
│       │   │   │   │   ├── Ojinaga
│       │   │   │   │   ├── Panama
│       │   │   │   │   ├── Pangnirtung
│       │   │   │   │   ├── Paramaribo
│       │   │   │   │   ├── Phoenix
│       │   │   │   │   ├── Port-au-Prince
│       │   │   │   │   ├── Port_of_Spain
│       │   │   │   │   ├── Porto_Acre
│       │   │   │   │   ├── Porto_Velho
│       │   │   │   │   ├── Puerto_Rico
│       │   │   │   │   ├── Punta_Arenas
│       │   │   │   │   ├── Rainy_River
│       │   │   │   │   ├── Rankin_Inlet
│       │   │   │   │   ├── Recife
│       │   │   │   │   ├── Regina
│       │   │   │   │   ├── Resolute
│       │   │   │   │   ├── Rio_Branco
│       │   │   │   │   ├── Rosario
│       │   │   │   │   ├── Santa_Isabel
│       │   │   │   │   ├── Santarem
│       │   │   │   │   ├── Santiago
│       │   │   │   │   ├── Santo_Domingo
│       │   │   │   │   ├── Sao_Paulo
│       │   │   │   │   ├── Scoresbysund
│       │   │   │   │   ├── Shiprock
│       │   │   │   │   ├── Sitka
│       │   │   │   │   ├── St_Barthelemy
│       │   │   │   │   ├── St_Johns
│       │   │   │   │   ├── St_Kitts
│       │   │   │   │   ├── St_Lucia
│       │   │   │   │   ├── St_Thomas
│       │   │   │   │   ├── St_Vincent
│       │   │   │   │   ├── Swift_Current
│       │   │   │   │   ├── Tegucigalpa
│       │   │   │   │   ├── Thule
│       │   │   │   │   ├── Thunder_Bay
│       │   │   │   │   ├── Tijuana
│       │   │   │   │   ├── Toronto
│       │   │   │   │   ├── Tortola
│       │   │   │   │   ├── Vancouver
│       │   │   │   │   ├── Virgin
│       │   │   │   │   ├── Whitehorse
│       │   │   │   │   ├── Winnipeg
│       │   │   │   │   ├── Yakutat
│       │   │   │   │   └── Yellowknife
│       │   │   │   ├── Antarctica
│       │   │   │   │   ├── Casey
│       │   │   │   │   ├── Davis
│       │   │   │   │   ├── DumontDUrville
│       │   │   │   │   ├── Macquarie
│       │   │   │   │   ├── Mawson
│       │   │   │   │   ├── McMurdo
│       │   │   │   │   ├── Palmer
│       │   │   │   │   ├── Rothera
│       │   │   │   │   ├── South_Pole
│       │   │   │   │   ├── Syowa
│       │   │   │   │   ├── Troll
│       │   │   │   │   └── Vostok
│       │   │   │   ├── Arctic
│       │   │   │   │   └── Longyearbyen
│       │   │   │   ├── Asia
│       │   │   │   │   ├── Aden
│       │   │   │   │   ├── Almaty
│       │   │   │   │   ├── Amman
│       │   │   │   │   ├── Anadyr
│       │   │   │   │   ├── Aqtau
│       │   │   │   │   ├── Aqtobe
│       │   │   │   │   ├── Ashgabat
│       │   │   │   │   ├── Ashkhabad
│       │   │   │   │   ├── Atyrau
│       │   │   │   │   ├── Baghdad
│       │   │   │   │   ├── Bahrain
│       │   │   │   │   ├── Baku
│       │   │   │   │   ├── Bangkok
│       │   │   │   │   ├── Barnaul
│       │   │   │   │   ├── Beirut
│       │   │   │   │   ├── Bishkek
│       │   │   │   │   ├── Brunei
│       │   │   │   │   ├── Calcutta
│       │   │   │   │   ├── Chita
│       │   │   │   │   ├── Choibalsan
│       │   │   │   │   ├── Chongqing
│       │   │   │   │   ├── Chungking
│       │   │   │   │   ├── Colombo
│       │   │   │   │   ├── Dacca
│       │   │   │   │   ├── Damascus
│       │   │   │   │   ├── Dhaka
│       │   │   │   │   ├── Dili
│       │   │   │   │   ├── Dubai
│       │   │   │   │   ├── Dushanbe
│       │   │   │   │   ├── Famagusta
│       │   │   │   │   ├── Gaza
│       │   │   │   │   ├── Harbin
│       │   │   │   │   ├── Hebron
│       │   │   │   │   ├── Ho_Chi_Minh
│       │   │   │   │   ├── Hong_Kong
│       │   │   │   │   ├── Hovd
│       │   │   │   │   ├── Irkutsk
│       │   │   │   │   ├── Istanbul
│       │   │   │   │   ├── Jakarta
│       │   │   │   │   ├── Jayapura
│       │   │   │   │   ├── Jerusalem
│       │   │   │   │   ├── Kabul
│       │   │   │   │   ├── Kamchatka
│       │   │   │   │   ├── Karachi
│       │   │   │   │   ├── Kashgar
│       │   │   │   │   ├── Kathmandu
│       │   │   │   │   ├── Katmandu
│       │   │   │   │   ├── Khandyga
│       │   │   │   │   ├── Kolkata
│       │   │   │   │   ├── Krasnoyarsk
│       │   │   │   │   ├── Kuala_Lumpur
│       │   │   │   │   ├── Kuching
│       │   │   │   │   ├── Kuwait
│       │   │   │   │   ├── Macao
│       │   │   │   │   ├── Macau
│       │   │   │   │   ├── Magadan
│       │   │   │   │   ├── Makassar
│       │   │   │   │   ├── Manila
│       │   │   │   │   ├── Muscat
│       │   │   │   │   ├── Nicosia
│       │   │   │   │   ├── Novokuznetsk
│       │   │   │   │   ├── Novosibirsk
│       │   │   │   │   ├── Omsk
│       │   │   │   │   ├── Oral
│       │   │   │   │   ├── Phnom_Penh
│       │   │   │   │   ├── Pontianak
│       │   │   │   │   ├── Pyongyang
│       │   │   │   │   ├── Qatar
│       │   │   │   │   ├── Qostanay
│       │   │   │   │   ├── Qyzylorda
│       │   │   │   │   ├── Rangoon
│       │   │   │   │   ├── Riyadh
│       │   │   │   │   ├── Saigon
│       │   │   │   │   ├── Sakhalin
│       │   │   │   │   ├── Samarkand
│       │   │   │   │   ├── Seoul
│       │   │   │   │   ├── Shanghai
│       │   │   │   │   ├── Singapore
│       │   │   │   │   ├── Srednekolymsk
│       │   │   │   │   ├── Taipei
│       │   │   │   │   ├── Tashkent
│       │   │   │   │   ├── Tbilisi
│       │   │   │   │   ├── Tehran
│       │   │   │   │   ├── Tel_Aviv
│       │   │   │   │   ├── Thimbu
│       │   │   │   │   ├── Thimphu
│       │   │   │   │   ├── Tokyo
│       │   │   │   │   ├── Tomsk
│       │   │   │   │   ├── Ujung_Pandang
│       │   │   │   │   ├── Ulaanbaatar
│       │   │   │   │   ├── Ulan_Bator
│       │   │   │   │   ├── Urumqi
│       │   │   │   │   ├── Ust-Nera
│       │   │   │   │   ├── Vientiane
│       │   │   │   │   ├── Vladivostok
│       │   │   │   │   ├── Yakutsk
│       │   │   │   │   ├── Yangon
│       │   │   │   │   ├── Yekaterinburg
│       │   │   │   │   └── Yerevan
│       │   │   │   ├── Atlantic
│       │   │   │   │   ├── Azores
│       │   │   │   │   ├── Bermuda
│       │   │   │   │   ├── Canary
│       │   │   │   │   ├── Cape_Verde
│       │   │   │   │   ├── Faeroe
│       │   │   │   │   ├── Faroe
│       │   │   │   │   ├── Jan_Mayen
│       │   │   │   │   ├── Madeira
│       │   │   │   │   ├── Reykjavik
│       │   │   │   │   ├── South_Georgia
│       │   │   │   │   ├── St_Helena
│       │   │   │   │   └── Stanley
│       │   │   │   ├── Australia
│       │   │   │   │   ├── ACT
│       │   │   │   │   ├── Adelaide
│       │   │   │   │   ├── Brisbane
│       │   │   │   │   ├── Broken_Hill
│       │   │   │   │   ├── Canberra
│       │   │   │   │   ├── Currie
│       │   │   │   │   ├── Darwin
│       │   │   │   │   ├── Eucla
│       │   │   │   │   ├── Hobart
│       │   │   │   │   ├── LHI
│       │   │   │   │   ├── Lindeman
│       │   │   │   │   ├── Lord_Howe
│       │   │   │   │   ├── Melbourne
│       │   │   │   │   ├── North
│       │   │   │   │   ├── NSW
│       │   │   │   │   ├── Perth
│       │   │   │   │   ├── Queensland
│       │   │   │   │   ├── South
│       │   │   │   │   ├── Sydney
│       │   │   │   │   ├── Tasmania
│       │   │   │   │   ├── Victoria
│       │   │   │   │   ├── West
│       │   │   │   │   └── Yancowinna
│       │   │   │   ├── Brazil
│       │   │   │   │   ├── Acre
│       │   │   │   │   ├── DeNoronha
│       │   │   │   │   ├── East
│       │   │   │   │   └── West
│       │   │   │   ├── Canada
│       │   │   │   │   ├── Atlantic
│       │   │   │   │   ├── Central
│       │   │   │   │   ├── Eastern
│       │   │   │   │   ├── Mountain
│       │   │   │   │   ├── Newfoundland
│       │   │   │   │   ├── Pacific
│       │   │   │   │   ├── Saskatchewan
│       │   │   │   │   └── Yukon
│       │   │   │   ├── Chile
│       │   │   │   │   ├── Continental
│       │   │   │   │   └── EasterIsland
│       │   │   │   ├── Etc
│       │   │   │   │   ├── GMT
│       │   │   │   │   ├── GMT+0
│       │   │   │   │   ├── GMT+1
│       │   │   │   │   ├── GMT+10
│       │   │   │   │   ├── GMT+11
│       │   │   │   │   ├── GMT+12
│       │   │   │   │   ├── GMT+2
│       │   │   │   │   ├── GMT+3
│       │   │   │   │   ├── GMT+4
│       │   │   │   │   ├── GMT+5
│       │   │   │   │   ├── GMT+6
│       │   │   │   │   ├── GMT+7
│       │   │   │   │   ├── GMT+8
│       │   │   │   │   ├── GMT+9
│       │   │   │   │   ├── GMT-0
│       │   │   │   │   ├── GMT-1
│       │   │   │   │   ├── GMT-10
│       │   │   │   │   ├── GMT-11
│       │   │   │   │   ├── GMT-12
│       │   │   │   │   ├── GMT-13
│       │   │   │   │   ├── GMT-14
│       │   │   │   │   ├── GMT-2
│       │   │   │   │   ├── GMT-3
│       │   │   │   │   ├── GMT-4
│       │   │   │   │   ├── GMT-5
│       │   │   │   │   ├── GMT-6
│       │   │   │   │   ├── GMT-7
│       │   │   │   │   ├── GMT-8
│       │   │   │   │   ├── GMT-9
│       │   │   │   │   ├── GMT0
│       │   │   │   │   ├── Greenwich
│       │   │   │   │   ├── UCT
│       │   │   │   │   ├── Universal
│       │   │   │   │   ├── UTC
│       │   │   │   │   └── Zulu
│       │   │   │   ├── Europe
│       │   │   │   │   ├── Amsterdam
│       │   │   │   │   ├── Andorra
│       │   │   │   │   ├── Astrakhan
│       │   │   │   │   ├── Athens
│       │   │   │   │   ├── Belfast
│       │   │   │   │   ├── Belgrade
│       │   │   │   │   ├── Berlin
│       │   │   │   │   ├── Bratislava
│       │   │   │   │   ├── Brussels
│       │   │   │   │   ├── Bucharest
│       │   │   │   │   ├── Budapest
│       │   │   │   │   ├── Busingen
│       │   │   │   │   ├── Chisinau
│       │   │   │   │   ├── Copenhagen
│       │   │   │   │   ├── Dublin
│       │   │   │   │   ├── Gibraltar
│       │   │   │   │   ├── Guernsey
│       │   │   │   │   ├── Helsinki
│       │   │   │   │   ├── Isle_of_Man
│       │   │   │   │   ├── Istanbul
│       │   │   │   │   ├── Jersey
│       │   │   │   │   ├── Kaliningrad
│       │   │   │   │   ├── Kiev
│       │   │   │   │   ├── Kirov
│       │   │   │   │   ├── Kyiv
│       │   │   │   │   ├── Lisbon
│       │   │   │   │   ├── Ljubljana
│       │   │   │   │   ├── London
│       │   │   │   │   ├── Luxembourg
│       │   │   │   │   ├── Madrid
│       │   │   │   │   ├── Malta
│       │   │   │   │   ├── Mariehamn
│       │   │   │   │   ├── Minsk
│       │   │   │   │   ├── Monaco
│       │   │   │   │   ├── Moscow
│       │   │   │   │   ├── Nicosia
│       │   │   │   │   ├── Oslo
│       │   │   │   │   ├── Paris
│       │   │   │   │   ├── Podgorica
│       │   │   │   │   ├── Prague
│       │   │   │   │   ├── Riga
│       │   │   │   │   ├── Rome
│       │   │   │   │   ├── Samara
│       │   │   │   │   ├── San_Marino
│       │   │   │   │   ├── Sarajevo
│       │   │   │   │   ├── Saratov
│       │   │   │   │   ├── Simferopol
│       │   │   │   │   ├── Skopje
│       │   │   │   │   ├── Sofia
│       │   │   │   │   ├── Stockholm
│       │   │   │   │   ├── Tallinn
│       │   │   │   │   ├── Tirane
│       │   │   │   │   ├── Tiraspol
│       │   │   │   │   ├── Ulyanovsk
│       │   │   │   │   ├── Uzhgorod
│       │   │   │   │   ├── Vaduz
│       │   │   │   │   ├── Vatican
│       │   │   │   │   ├── Vienna
│       │   │   │   │   ├── Vilnius
│       │   │   │   │   ├── Volgograd
│       │   │   │   │   ├── Warsaw
│       │   │   │   │   ├── Zagreb
│       │   │   │   │   ├── Zaporozhye
│       │   │   │   │   └── Zurich
│       │   │   │   ├── Indian
│       │   │   │   │   ├── Antananarivo
│       │   │   │   │   ├── Chagos
│       │   │   │   │   ├── Christmas
│       │   │   │   │   ├── Cocos
│       │   │   │   │   ├── Comoro
│       │   │   │   │   ├── Kerguelen
│       │   │   │   │   ├── Mahe
│       │   │   │   │   ├── Maldives
│       │   │   │   │   ├── Mauritius
│       │   │   │   │   ├── Mayotte
│       │   │   │   │   └── Reunion
│       │   │   │   ├── Mexico
│       │   │   │   │   ├── BajaNorte
│       │   │   │   │   ├── BajaSur
│       │   │   │   │   └── General
│       │   │   │   ├── Pacific
│       │   │   │   │   ├── Apia
│       │   │   │   │   ├── Auckland
│       │   │   │   │   ├── Bougainville
│       │   │   │   │   ├── Chatham
│       │   │   │   │   ├── Chuuk
│       │   │   │   │   ├── Easter
│       │   │   │   │   ├── Efate
│       │   │   │   │   ├── Enderbury
│       │   │   │   │   ├── Fakaofo
│       │   │   │   │   ├── Fiji
│       │   │   │   │   ├── Funafuti
│       │   │   │   │   ├── Galapagos
│       │   │   │   │   ├── Gambier
│       │   │   │   │   ├── Guadalcanal
│       │   │   │   │   ├── Guam
│       │   │   │   │   ├── Honolulu
│       │   │   │   │   ├── Johnston
│       │   │   │   │   ├── Kanton
│       │   │   │   │   ├── Kiritimati
│       │   │   │   │   ├── Kosrae
│       │   │   │   │   ├── Kwajalein
│       │   │   │   │   ├── Majuro
│       │   │   │   │   ├── Marquesas
│       │   │   │   │   ├── Midway
│       │   │   │   │   ├── Nauru
│       │   │   │   │   ├── Niue
│       │   │   │   │   ├── Norfolk
│       │   │   │   │   ├── Noumea
│       │   │   │   │   ├── Pago_Pago
│       │   │   │   │   ├── Palau
│       │   │   │   │   ├── Pitcairn
│       │   │   │   │   ├── Pohnpei
│       │   │   │   │   ├── Ponape
│       │   │   │   │   ├── Port_Moresby
│       │   │   │   │   ├── Rarotonga
│       │   │   │   │   ├── Saipan
│       │   │   │   │   ├── Samoa
│       │   │   │   │   ├── Tahiti
│       │   │   │   │   ├── Tarawa
│       │   │   │   │   ├── Tongatapu
│       │   │   │   │   ├── Truk
│       │   │   │   │   ├── Wake
│       │   │   │   │   ├── Wallis
│       │   │   │   │   └── Yap
│       │   │   │   ├── SystemV
│       │   │   │   │   ├── AST4
│       │   │   │   │   ├── AST4ADT
│       │   │   │   │   ├── CST6
│       │   │   │   │   ├── CST6CDT
│       │   │   │   │   ├── EST5
│       │   │   │   │   ├── EST5EDT
│       │   │   │   │   ├── HST10
│       │   │   │   │   ├── MST7
│       │   │   │   │   ├── MST7MDT
│       │   │   │   │   ├── PST8
│       │   │   │   │   ├── PST8PDT
│       │   │   │   │   ├── YST9
│       │   │   │   │   └── YST9YDT
│       │   │   │   ├── US
│       │   │   │   │   ├── Alaska
│       │   │   │   │   ├── Aleutian
│       │   │   │   │   ├── Arizona
│       │   │   │   │   ├── Central
│       │   │   │   │   ├── East-Indiana
│       │   │   │   │   ├── Eastern
│       │   │   │   │   ├── Hawaii
│       │   │   │   │   ├── Indiana-Starke
│       │   │   │   │   ├── Michigan
│       │   │   │   │   ├── Mountain
│       │   │   │   │   ├── Pacific
│       │   │   │   │   └── Samoa
│       │   │   │   ├── CET
│       │   │   │   ├── CST6CDT
│       │   │   │   ├── Cuba
│       │   │   │   ├── EET
│       │   │   │   ├── Egypt
│       │   │   │   ├── Eire
│       │   │   │   ├── EST
│       │   │   │   ├── EST5EDT
│       │   │   │   ├── GB
│       │   │   │   ├── GB-Eire
│       │   │   │   ├── GMT
│       │   │   │   ├── GMT+0
│       │   │   │   ├── GMT-0
│       │   │   │   ├── GMT0
│       │   │   │   ├── Greenwich
│       │   │   │   ├── Hongkong
│       │   │   │   ├── HST
│       │   │   │   ├── Iceland
│       │   │   │   ├── Iran
│       │   │   │   ├── Israel
│       │   │   │   ├── Jamaica
│       │   │   │   ├── Japan
│       │   │   │   ├── Kwajalein
│       │   │   │   ├── Libya
│       │   │   │   ├── MET
│       │   │   │   ├── MST
│       │   │   │   ├── MST7MDT
│       │   │   │   ├── Navajo
│       │   │   │   ├── NZ
│       │   │   │   ├── NZ-CHAT
│       │   │   │   ├── Poland
│       │   │   │   ├── Portugal
│       │   │   │   ├── PRC
│       │   │   │   ├── PST8PDT
│       │   │   │   ├── ROC
│       │   │   │   ├── ROK
│       │   │   │   ├── Singapore
│       │   │   │   ├── Turkey
│       │   │   │   ├── UCT
│       │   │   │   ├── Universal
│       │   │   │   ├── UTC
│       │   │   │   ├── W-SU
│       │   │   │   ├── WET
│       │   │   │   └── Zulu
│       │   │   ├── auto.tcl
│       │   │   ├── clock.tcl
│       │   │   ├── history.tcl
│       │   │   ├── init.tcl
│       │   │   ├── package.tcl
│       │   │   ├── parray.tcl
│       │   │   ├── safe.tcl
│       │   │   ├── tclIndex
│       │   │   ├── tm.tcl
│       │   │   └── word.tcl
│       │   ├── _tk_data
│       │   │   ├── images
│       │   │   │   ├── logo.eps
│       │   │   │   ├── logo100.gif
│       │   │   │   ├── logo64.gif
│       │   │   │   ├── logoLarge.gif
│       │   │   │   ├── logoMed.gif
│       │   │   │   ├── pwrdLogo.eps
│       │   │   │   ├── pwrdLogo100.gif
│       │   │   │   ├── pwrdLogo150.gif
│       │   │   │   ├── pwrdLogo175.gif
│       │   │   │   ├── pwrdLogo200.gif
│       │   │   │   ├── pwrdLogo75.gif
│       │   │   │   ├── README
│       │   │   │   └── tai-ku.gif
│       │   │   ├── msgs
│       │   │   │   ├── cs.msg
│       │   │   │   ├── da.msg
│       │   │   │   ├── de.msg
│       │   │   │   ├── el.msg
│       │   │   │   ├── en.msg
│       │   │   │   ├── en_gb.msg
│       │   │   │   ├── eo.msg
│       │   │   │   ├── es.msg
│       │   │   │   ├── fi.msg
│       │   │   │   ├── fr.msg
│       │   │   │   ├── hu.msg
│       │   │   │   ├── it.msg
│       │   │   │   ├── nl.msg
│       │   │   │   ├── pl.msg
│       │   │   │   ├── pt.msg
│       │   │   │   ├── ru.msg
│       │   │   │   ├── sv.msg
│       │   │   │   └── zh_cn.msg
│       │   │   ├── ttk
│       │   │   │   ├── altTheme.tcl
│       │   │   │   ├── aquaTheme.tcl
│       │   │   │   ├── button.tcl
│       │   │   │   ├── clamTheme.tcl
│       │   │   │   ├── classicTheme.tcl
│       │   │   │   ├── combobox.tcl
│       │   │   │   ├── cursors.tcl
│       │   │   │   ├── defaults.tcl
│       │   │   │   ├── entry.tcl
│       │   │   │   ├── fonts.tcl
│       │   │   │   ├── menubutton.tcl
│       │   │   │   ├── notebook.tcl
│       │   │   │   ├── panedwindow.tcl
│       │   │   │   ├── progress.tcl
│       │   │   │   ├── scale.tcl
│       │   │   │   ├── scrollbar.tcl
│       │   │   │   ├── sizegrip.tcl
│       │   │   │   ├── spinbox.tcl
│       │   │   │   ├── treeview.tcl
│       │   │   │   ├── ttk.tcl
│       │   │   │   ├── utils.tcl
│       │   │   │   ├── vistaTheme.tcl
│       │   │   │   ├── winTheme.tcl
│       │   │   │   └── xpTheme.tcl
│       │   │   ├── bgerror.tcl
│       │   │   ├── button.tcl
│       │   │   ├── choosedir.tcl
│       │   │   ├── clrpick.tcl
│       │   │   ├── comdlg.tcl
│       │   │   ├── console.tcl
│       │   │   ├── dialog.tcl
│       │   │   ├── entry.tcl
│       │   │   ├── focus.tcl
│       │   │   ├── fontchooser.tcl
│       │   │   ├── iconlist.tcl
│       │   │   ├── icons.tcl
│       │   │   ├── license.terms
│       │   │   ├── listbox.tcl
│       │   │   ├── megawidget.tcl
│       │   │   ├── menu.tcl
│       │   │   ├── mkpsenc.tcl
│       │   │   ├── msgbox.tcl
│       │   │   ├── obsolete.tcl
│       │   │   ├── optMenu.tcl
│       │   │   ├── palette.tcl
│       │   │   ├── panedwindow.tcl
│       │   │   ├── pkgIndex.tcl
│       │   │   ├── safetk.tcl
│       │   │   ├── scale.tcl
│       │   │   ├── scrlbar.tcl
│       │   │   ├── spinbox.tcl
│       │   │   ├── tclIndex
│       │   │   ├── tearoff.tcl
│       │   │   ├── text.tcl
│       │   │   ├── tk.tcl
│       │   │   ├── tkfbox.tcl
│       │   │   ├── unsupported.tcl
│       │   │   └── xmfbox.tcl
│       │   ├── attrs-26.1.0.dist-info
│       │   │   ├── licenses
│       │   │   │   └── LICENSE
│       │   │   ├── INSTALLER
│       │   │   ├── METADATA
│       │   │   ├── RECORD
│       │   │   └── WHEEL
│       │   ├── certifi
│       │   │   ├── cacert.pem
│       │   │   └── py.typed
│       │   ├── contourpy
│       │   │   └── _contourpy.cp312-win_amd64.pyd
│       │   ├── cv2
│       │   │   ├── data
│       │   │   │   └── __init__.py
│       │   │   ├── mat_wrapper
│       │   │   │   └── __init__.py
│       │   │   ├── misc
│       │   │   │   ├── __init__.py
│       │   │   │   └── version.py
│       │   │   ├── typing
│       │   │   │   └── __init__.py
│       │   │   ├── utils
│       │   │   │   └── __init__.py
│       │   │   ├── __init__.py
│       │   │   ├── config-3.py
│       │   │   ├── config.py
│       │   │   ├── cv2.pyd
│       │   │   ├── load_config_py3.py
│       │   │   ├── opencv_videoio_ffmpeg500_64.dll
│       │   │   └── version.py
│       │   ├── google
│       │   │   └── _upb
│       │   │       └── _message.pyd
│       │   ├── kiwisolver
│       │   │   └── _cext.cp312-win_amd64.pyd
│       │   ├── matplotlib
│       │   │   ├── backends
│       │   │   │   ├── _backend_agg.cp312-win_amd64.pyd
│       │   │   │   └── _tkagg.cp312-win_amd64.pyd
│       │   │   ├── mpl-data
│       │   │   │   ├── fonts
│       │   │   │   │   ├── afm
│       │   │   │   │   │   ├── cmex10.afm
│       │   │   │   │   │   ├── cmmi10.afm
│       │   │   │   │   │   ├── cmr10.afm
│       │   │   │   │   │   ├── cmsy10.afm
│       │   │   │   │   │   ├── cmti10.afm
│       │   │   │   │   │   ├── cmtt10.afm
│       │   │   │   │   │   ├── pagd8a.afm
│       │   │   │   │   │   ├── pagdo8a.afm
│       │   │   │   │   │   ├── pagk8a.afm
│       │   │   │   │   │   ├── pagko8a.afm
│       │   │   │   │   │   ├── pbkd8a.afm
│       │   │   │   │   │   ├── pbkdi8a.afm
│       │   │   │   │   │   ├── pbkl8a.afm
│       │   │   │   │   │   ├── pbkli8a.afm
│       │   │   │   │   │   ├── pcrb8a.afm
│       │   │   │   │   │   ├── pcrbo8a.afm
│       │   │   │   │   │   ├── pcrr8a.afm
│       │   │   │   │   │   ├── pcrro8a.afm
│       │   │   │   │   │   ├── phvb8a.afm
│       │   │   │   │   │   ├── phvb8an.afm
│       │   │   │   │   │   ├── phvbo8a.afm
│       │   │   │   │   │   ├── phvbo8an.afm
│       │   │   │   │   │   ├── phvl8a.afm
│       │   │   │   │   │   ├── phvlo8a.afm
│       │   │   │   │   │   ├── phvr8a.afm
│       │   │   │   │   │   ├── phvr8an.afm
│       │   │   │   │   │   ├── phvro8a.afm
│       │   │   │   │   │   ├── phvro8an.afm
│       │   │   │   │   │   ├── pncb8a.afm
│       │   │   │   │   │   ├── pncbi8a.afm
│       │   │   │   │   │   ├── pncr8a.afm
│       │   │   │   │   │   ├── pncri8a.afm
│       │   │   │   │   │   ├── pplb8a.afm
│       │   │   │   │   │   ├── pplbi8a.afm
│       │   │   │   │   │   ├── pplr8a.afm
│       │   │   │   │   │   ├── pplri8a.afm
│       │   │   │   │   │   ├── psyr.afm
│       │   │   │   │   │   ├── ptmb8a.afm
│       │   │   │   │   │   ├── ptmbi8a.afm
│       │   │   │   │   │   ├── ptmr8a.afm
│       │   │   │   │   │   ├── ptmri8a.afm
│       │   │   │   │   │   ├── putb8a.afm
│       │   │   │   │   │   ├── putbi8a.afm
│       │   │   │   │   │   ├── putr8a.afm
│       │   │   │   │   │   ├── putri8a.afm
│       │   │   │   │   │   ├── pzcmi8a.afm
│       │   │   │   │   │   └── pzdr.afm
│       │   │   │   │   ├── pdfcorefonts
│       │   │   │   │   │   ├── Courier-Bold.afm
│       │   │   │   │   │   ├── Courier-BoldOblique.afm
│       │   │   │   │   │   ├── Courier-Oblique.afm
│       │   │   │   │   │   ├── Courier.afm
│       │   │   │   │   │   ├── Helvetica-Bold.afm
│       │   │   │   │   │   ├── Helvetica-BoldOblique.afm
│       │   │   │   │   │   ├── Helvetica-Oblique.afm
│       │   │   │   │   │   ├── Helvetica.afm
│       │   │   │   │   │   ├── readme.txt
│       │   │   │   │   │   ├── Symbol.afm
│       │   │   │   │   │   ├── Times-Bold.afm
│       │   │   │   │   │   ├── Times-BoldItalic.afm
│       │   │   │   │   │   ├── Times-Italic.afm
│       │   │   │   │   │   ├── Times-Roman.afm
│       │   │   │   │   │   └── ZapfDingbats.afm
│       │   │   │   │   └── ttf
│       │   │   │   │       ├── cmb10.ttf
│       │   │   │   │       ├── cmex10.ttf
│       │   │   │   │       ├── cmmi10.ttf
│       │   │   │   │       ├── cmr10.ttf
│       │   │   │   │       ├── cmss10.ttf
│       │   │   │   │       ├── cmsy10.ttf
│       │   │   │   │       ├── cmti10.ttf
│       │   │   │   │       ├── cmtt10.ttf
│       │   │   │   │       ├── DejaVuSans-Bold.ttf
│       │   │   │   │       ├── DejaVuSans-BoldOblique.ttf
│       │   │   │   │       ├── DejaVuSans-Oblique.ttf
│       │   │   │   │       ├── DejaVuSans.ttf
│       │   │   │   │       ├── DejaVuSansDisplay.ttf
│       │   │   │   │       ├── DejaVuSansMono-Bold.ttf
│       │   │   │   │       ├── DejaVuSansMono-BoldOblique.ttf
│       │   │   │   │       ├── DejaVuSansMono-Oblique.ttf
│       │   │   │   │       ├── DejaVuSansMono.ttf
│       │   │   │   │       ├── DejaVuSerif-Bold.ttf
│       │   │   │   │       ├── DejaVuSerif-BoldItalic.ttf
│       │   │   │   │       ├── DejaVuSerif-Italic.ttf
│       │   │   │   │       ├── DejaVuSerif.ttf
│       │   │   │   │       ├── DejaVuSerifDisplay.ttf
│       │   │   │   │       ├── LastResortHE-Regular.ttf
│       │   │   │   │       ├── LICENSE_DEJAVU
│       │   │   │   │       ├── LICENSE_STIX
│       │   │   │   │       ├── STIXGeneral.ttf
│       │   │   │   │       ├── STIXGeneralBol.ttf
│       │   │   │   │       ├── STIXGeneralBolIta.ttf
│       │   │   │   │       ├── STIXGeneralItalic.ttf
│       │   │   │   │       ├── STIXNonUni.ttf
│       │   │   │   │       ├── STIXNonUniBol.ttf
│       │   │   │   │       ├── STIXNonUniBolIta.ttf
│       │   │   │   │       ├── STIXNonUniIta.ttf
│       │   │   │   │       ├── STIXSizFiveSymReg.ttf
│       │   │   │   │       ├── STIXSizFourSymBol.ttf
│       │   │   │   │       ├── STIXSizFourSymReg.ttf
│       │   │   │   │       ├── STIXSizOneSymBol.ttf
│       │   │   │   │       ├── STIXSizOneSymReg.ttf
│       │   │   │   │       ├── STIXSizThreeSymBol.ttf
│       │   │   │   │       ├── STIXSizThreeSymReg.ttf
│       │   │   │   │       ├── STIXSizTwoSymBol.ttf
│       │   │   │   │       └── STIXSizTwoSymReg.ttf
│       │   │   │   ├── images
│       │   │   │   │   ├── back-symbolic.svg
│       │   │   │   │   ├── back.pdf
│       │   │   │   │   ├── back.png
│       │   │   │   │   ├── back.svg
│       │   │   │   │   ├── back_large.png
│       │   │   │   │   ├── filesave-symbolic.svg
│       │   │   │   │   ├── filesave.pdf
│       │   │   │   │   ├── filesave.png
│       │   │   │   │   ├── filesave.svg
│       │   │   │   │   ├── filesave_large.png
│       │   │   │   │   ├── forward-symbolic.svg
│       │   │   │   │   ├── forward.pdf
│       │   │   │   │   ├── forward.png
│       │   │   │   │   ├── forward.svg
│       │   │   │   │   ├── forward_large.png
│       │   │   │   │   ├── hand.pdf
│       │   │   │   │   ├── hand.png
│       │   │   │   │   ├── hand.svg
│       │   │   │   │   ├── help-symbolic.svg
│       │   │   │   │   ├── help.pdf
│       │   │   │   │   ├── help.png
│       │   │   │   │   ├── help.svg
│       │   │   │   │   ├── help_large.png
│       │   │   │   │   ├── home-symbolic.svg
│       │   │   │   │   ├── home.pdf
│       │   │   │   │   ├── home.png
│       │   │   │   │   ├── home.svg
│       │   │   │   │   ├── home_large.png
│       │   │   │   │   ├── matplotlib.pdf
│       │   │   │   │   ├── matplotlib.png
│       │   │   │   │   ├── matplotlib.svg
│       │   │   │   │   ├── matplotlib_large.png
│       │   │   │   │   ├── move-symbolic.svg
│       │   │   │   │   ├── move.pdf
│       │   │   │   │   ├── move.png
│       │   │   │   │   ├── move.svg
│       │   │   │   │   ├── move_large.png
│       │   │   │   │   ├── qt4_editor_options.pdf
│       │   │   │   │   ├── qt4_editor_options.png
│       │   │   │   │   ├── qt4_editor_options.svg
│       │   │   │   │   ├── qt4_editor_options_large.png
│       │   │   │   │   ├── subplots-symbolic.svg
│       │   │   │   │   ├── subplots.pdf
│       │   │   │   │   ├── subplots.png
│       │   │   │   │   ├── subplots.svg
│       │   │   │   │   ├── subplots_large.png
│       │   │   │   │   ├── zoom_to_rect-symbolic.svg
│       │   │   │   │   ├── zoom_to_rect.pdf
│       │   │   │   │   ├── zoom_to_rect.png
│       │   │   │   │   ├── zoom_to_rect.svg
│       │   │   │   │   └── zoom_to_rect_large.png
│       │   │   │   ├── plot_directive
│       │   │   │   │   └── plot_directive.css
│       │   │   │   ├── sample_data
│       │   │   │   │   ├── axes_grid
│       │   │   │   │   │   └── bivariate_normal.npy
│       │   │   │   │   ├── data_x_x2_x3.csv
│       │   │   │   │   ├── eeg.dat
│       │   │   │   │   ├── embedding_in_wx3.xrc
│       │   │   │   │   ├── goog.npz
│       │   │   │   │   ├── grace_hopper.jpg
│       │   │   │   │   ├── jacksboro_fault_dem.npz
│       │   │   │   │   ├── logo2.png
│       │   │   │   │   ├── membrane.dat
│       │   │   │   │   ├── Minduka_Present_Blue_Pack.png
│       │   │   │   │   ├── msft.csv
│       │   │   │   │   ├── README.txt
│       │   │   │   │   ├── s1045.ima.gz
│       │   │   │   │   ├── Stocks.csv
│       │   │   │   │   └── topobathy.npz
│       │   │   │   ├── stylelib
│       │   │   │   │   ├── _classic_test_patch.mplstyle
│       │   │   │   │   ├── _mpl-gallery-nogrid.mplstyle
│       │   │   │   │   ├── _mpl-gallery.mplstyle
│       │   │   │   │   ├── bmh.mplstyle
│       │   │   │   │   ├── classic.mplstyle
│       │   │   │   │   ├── dark_background.mplstyle
│       │   │   │   │   ├── fast.mplstyle
│       │   │   │   │   ├── fivethirtyeight.mplstyle
│       │   │   │   │   ├── ggplot.mplstyle
│       │   │   │   │   ├── grayscale.mplstyle
│       │   │   │   │   ├── petroff10.mplstyle
│       │   │   │   │   ├── petroff6.mplstyle
│       │   │   │   │   ├── petroff8.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-bright.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-colorblind.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-dark-palette.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-dark.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-darkgrid.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-deep.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-muted.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-notebook.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-paper.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-pastel.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-poster.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-talk.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-ticks.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-white.mplstyle
│       │   │   │   │   ├── seaborn-v0_8-whitegrid.mplstyle
│       │   │   │   │   ├── seaborn-v0_8.mplstyle
│       │   │   │   │   ├── Solarize_Light2.mplstyle
│       │   │   │   │   └── tableau-colorblind10.mplstyle
│       │   │   │   ├── kpsewhich.lua
│       │   │   │   └── matplotlibrc
│       │   │   ├── _c_internal_utils.cp312-win_amd64.pyd
│       │   │   ├── _image.cp312-win_amd64.pyd
│       │   │   ├── _path.cp312-win_amd64.pyd
│       │   │   ├── _qhull.cp312-win_amd64.pyd
│       │   │   ├── _tri.cp312-win_amd64.pyd
│       │   │   └── ft2font.cp312-win_amd64.pyd
│       │   ├── mediapipe
│       │   │   └── python
│       │   │       ├── _framework_bindings.cp312-win_amd64.pyd
│       │   │       └── opencv_world3410.dll
│       │   ├── numpy
│       │   │   ├── _core
│       │   │   │   ├── _multiarray_tests.cp312-win_amd64.pyd
│       │   │   │   └── _multiarray_umath.cp312-win_amd64.pyd
│       │   │   ├── fft
│       │   │   │   └── _pocketfft_umath.cp312-win_amd64.pyd
│       │   │   ├── linalg
│       │   │   │   └── _umath_linalg.cp312-win_amd64.pyd
│       │   │   └── random
│       │   │       ├── _bounded_integers.cp312-win_amd64.pyd
│       │   │       ├── _common.cp312-win_amd64.pyd
│       │   │       ├── _generator.cp312-win_amd64.pyd
│       │   │       ├── _mt19937.cp312-win_amd64.pyd
│       │   │       ├── _pcg64.cp312-win_amd64.pyd
│       │   │       ├── _philox.cp312-win_amd64.pyd
│       │   │       ├── _sfc64.cp312-win_amd64.pyd
│       │   │       ├── bit_generator.cp312-win_amd64.pyd
│       │   │       └── mtrand.cp312-win_amd64.pyd
│       │   ├── numpy-2.5.4.dist-info
│       │   │   ├── licenses
│       │   │   │   ├── numpy
│       │   │   │   │   ├── _core
│       │   │   │   │   │   ├── include
│       │   │   │   │   │   │   └── numpy
│       │   │   │   │   │   │       └── libdivide
│       │   │   │   │   │   │           └── LICENSE.txt
│       │   │   │   │   │   └── src
│       │   │   │   │   │       ├── common
│       │   │   │   │   │       │   └── pythoncapi-compat
│       │   │   │   │   │       │       └── COPYING
│       │   │   │   │   │       ├── highway
│       │   │   │   │   │       │   └── LICENSE
│       │   │   │   │   │       ├── multiarray
│       │   │   │   │   │       │   └── dragon4_LICENSE.txt
│       │   │   │   │   │       ├── npysort
│       │   │   │   │   │       │   └── x86-simd-sort
│       │   │   │   │   │       │       └── LICENSE.md
│       │   │   │   │   │       └── umath
│       │   │   │   │   │           └── svml
│       │   │   │   │   │               └── LICENSE
│       │   │   │   │   ├── fft
│       │   │   │   │   │   └── pocketfft
│       │   │   │   │   │       └── LICENSE.md
│       │   │   │   │   ├── linalg
│       │   │   │   │   │   └── lapack_lite
│       │   │   │   │   │       └── LICENSE.txt
│       │   │   │   │   ├── ma
│       │   │   │   │   │   └── LICENSE
│       │   │   │   │   └── random
│       │   │   │   │       ├── src
│       │   │   │   │       │   ├── distributions
│       │   │   │   │       │   │   └── LICENSE.md
│       │   │   │   │       │   ├── mt19937
│       │   │   │   │       │   │   └── LICENSE.md
│       │   │   │   │       │   ├── pcg64
│       │   │   │   │       │   │   └── LICENSE.md
│       │   │   │   │       │   ├── philox
│       │   │   │   │       │   │   └── LICENSE.md
│       │   │   │   │       │   ├── sfc64
│       │   │   │   │       │   │   └── LICENSE.md
│       │   │   │   │       │   └── splitmix64
│       │   │   │   │       │       └── LICENSE.md
│       │   │   │   │       └── LICENSE.md
│       │   │   │   └── LICENSE.txt
│       │   │   ├── DELVEWHEEL
│       │   │   ├── entry_points.txt
│       │   │   ├── INSTALLER
│       │   │   ├── METADATA
│       │   │   ├── RECORD
│       │   │   └── WHEEL
│       │   ├── numpy.libs
│       │   │   ├── libscipy_openblas64_-ed4f167a5330424524f45258e7ca2c8d.dll
│       │   │   └── msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll
│       │   ├── PIL
│       │   │   ├── _avif.cp312-win_amd64.pyd
│       │   │   ├── _imaging.cp312-win_amd64.pyd
│       │   │   ├── _imagingcms.cp312-win_amd64.pyd
│       │   │   ├── _imagingtk.cp312-win_amd64.pyd
│       │   │   └── _webp.cp312-win_amd64.pyd
│       │   ├── pygame
│       │   │   ├── _freetype.cp312-win_amd64.pyd
│       │   │   ├── base.cp312-win_amd64.pyd
│       │   │   ├── bufferproxy.cp312-win_amd64.pyd
│       │   │   ├── color.cp312-win_amd64.pyd
│       │   │   ├── constants.cp312-win_amd64.pyd
│       │   │   ├── display.cp312-win_amd64.pyd
│       │   │   ├── draw.cp312-win_amd64.pyd
│       │   │   ├── event.cp312-win_amd64.pyd
│       │   │   ├── font.cp312-win_amd64.pyd
│       │   │   ├── freesansbold.ttf
│       │   │   ├── freetype.dll
│       │   │   ├── image.cp312-win_amd64.pyd
│       │   │   ├── imageext.cp312-win_amd64.pyd
│       │   │   ├── joystick.cp312-win_amd64.pyd
│       │   │   ├── key.cp312-win_amd64.pyd
│       │   │   ├── libjpeg-9.dll
│       │   │   ├── libogg-0.dll
│       │   │   ├── libopus-0.dll
│       │   │   ├── libpng16-16.dll
│       │   │   ├── mask.cp312-win_amd64.pyd
│       │   │   ├── math.cp312-win_amd64.pyd
│       │   │   ├── mixer.cp312-win_amd64.pyd
│       │   │   ├── mixer_music.cp312-win_amd64.pyd
│       │   │   ├── mouse.cp312-win_amd64.pyd
│       │   │   ├── pixelarray.cp312-win_amd64.pyd
│       │   │   ├── pixelcopy.cp312-win_amd64.pyd
│       │   │   ├── pygame_icon.bmp
│       │   │   ├── rect.cp312-win_amd64.pyd
│       │   │   ├── rwobject.cp312-win_amd64.pyd
│       │   │   ├── scrap.cp312-win_amd64.pyd
│       │   │   ├── SDL2.dll
│       │   │   ├── SDL2_image.dll
│       │   │   ├── SDL2_mixer.dll
│       │   │   ├── SDL2_ttf.dll
│       │   │   ├── surface.cp312-win_amd64.pyd
│       │   │   ├── surflock.cp312-win_amd64.pyd
│       │   │   ├── time.cp312-win_amd64.pyd
│       │   │   ├── transform.cp312-win_amd64.pyd
│       │   │   └── zlib1.dll
│       │   ├── tcl8
│       │   │   ├── 8.4
│       │   │   │   ├── platform
│       │   │   │   │   └── shell-1.1.4.tm
│       │   │   │   └── platform-1.0.19.tm
│       │   │   ├── 8.5
│       │   │   │   ├── msgcat-1.6.1.tm
│       │   │   │   └── tcltest-2.5.8.tm
│       │   │   └── 8.6
│       │   │       └── http-2.9.8.tm
│       │   ├── tzdata
│       │   │   ├── zoneinfo
│       │   │   │   ├── Africa
│       │   │   │   │   ├── Abidjan
│       │   │   │   │   ├── Accra
│       │   │   │   │   ├── Addis_Ababa
│       │   │   │   │   ├── Algiers
│       │   │   │   │   ├── Asmara
│       │   │   │   │   ├── Asmera
│       │   │   │   │   ├── Bamako
│       │   │   │   │   ├── Bangui
│       │   │   │   │   ├── Banjul
│       │   │   │   │   ├── Bissau
│       │   │   │   │   ├── Blantyre
│       │   │   │   │   ├── Brazzaville
│       │   │   │   │   ├── Bujumbura
│       │   │   │   │   ├── Cairo
│       │   │   │   │   ├── Casablanca
│       │   │   │   │   ├── Ceuta
│       │   │   │   │   ├── Conakry
│       │   │   │   │   ├── Dakar
│       │   │   │   │   ├── Dar_es_Salaam
│       │   │   │   │   ├── Djibouti
│       │   │   │   │   ├── Douala
│       │   │   │   │   ├── El_Aaiun
│       │   │   │   │   ├── Freetown
│       │   │   │   │   ├── Gaborone
│       │   │   │   │   ├── Harare
│       │   │   │   │   ├── Johannesburg
│       │   │   │   │   ├── Juba
│       │   │   │   │   ├── Kampala
│       │   │   │   │   ├── Khartoum
│       │   │   │   │   ├── Kigali
│       │   │   │   │   ├── Kinshasa
│       │   │   │   │   ├── Lagos
│       │   │   │   │   ├── Libreville
│       │   │   │   │   ├── Lome
│       │   │   │   │   ├── Luanda
│       │   │   │   │   ├── Lubumbashi
│       │   │   │   │   ├── Lusaka
│       │   │   │   │   ├── Malabo
│       │   │   │   │   ├── Maputo
│       │   │   │   │   ├── Maseru
│       │   │   │   │   ├── Mbabane
│       │   │   │   │   ├── Mogadishu
│       │   │   │   │   ├── Monrovia
│       │   │   │   │   ├── Nairobi
│       │   │   │   │   ├── Ndjamena
│       │   │   │   │   ├── Niamey
│       │   │   │   │   ├── Nouakchott
│       │   │   │   │   ├── Ouagadougou
│       │   │   │   │   ├── Porto-Novo
│       │   │   │   │   ├── Sao_Tome
│       │   │   │   │   ├── Timbuktu
│       │   │   │   │   ├── Tripoli
│       │   │   │   │   ├── Tunis
│       │   │   │   │   └── Windhoek
│       │   │   │   ├── America
│       │   │   │   │   ├── Argentina
│       │   │   │   │   │   ├── Buenos_Aires
│       │   │   │   │   │   ├── Catamarca
│       │   │   │   │   │   ├── ComodRivadavia
│       │   │   │   │   │   ├── Cordoba
│       │   │   │   │   │   ├── Jujuy
│       │   │   │   │   │   ├── La_Rioja
│       │   │   │   │   │   ├── Mendoza
│       │   │   │   │   │   ├── Rio_Gallegos
│       │   │   │   │   │   ├── Salta
│       │   │   │   │   │   ├── San_Juan
│       │   │   │   │   │   ├── San_Luis
│       │   │   │   │   │   ├── Tucuman
│       │   │   │   │   │   └── Ushuaia
│       │   │   │   │   ├── Indiana
│       │   │   │   │   │   ├── Indianapolis
│       │   │   │   │   │   ├── Knox
│       │   │   │   │   │   ├── Marengo
│       │   │   │   │   │   ├── Petersburg
│       │   │   │   │   │   ├── Tell_City
│       │   │   │   │   │   ├── Vevay
│       │   │   │   │   │   ├── Vincennes
│       │   │   │   │   │   └── Winamac
│       │   │   │   │   ├── Kentucky
│       │   │   │   │   │   ├── Louisville
│       │   │   │   │   │   └── Monticello
│       │   │   │   │   ├── North_Dakota
│       │   │   │   │   │   ├── Beulah
│       │   │   │   │   │   ├── Center
│       │   │   │   │   │   └── New_Salem
│       │   │   │   │   ├── Adak
│       │   │   │   │   ├── Anchorage
│       │   │   │   │   ├── Anguilla
│       │   │   │   │   ├── Antigua
│       │   │   │   │   ├── Araguaina
│       │   │   │   │   ├── Aruba
│       │   │   │   │   ├── Asuncion
│       │   │   │   │   ├── Atikokan
│       │   │   │   │   ├── Atka
│       │   │   │   │   ├── Bahia
│       │   │   │   │   ├── Bahia_Banderas
│       │   │   │   │   ├── Barbados
│       │   │   │   │   ├── Belem
│       │   │   │   │   ├── Belize
│       │   │   │   │   ├── Blanc-Sablon
│       │   │   │   │   ├── Boa_Vista
│       │   │   │   │   ├── Bogota
│       │   │   │   │   ├── Boise
│       │   │   │   │   ├── Buenos_Aires
│       │   │   │   │   ├── Cambridge_Bay
│       │   │   │   │   ├── Campo_Grande
│       │   │   │   │   ├── Cancun
│       │   │   │   │   ├── Caracas
│       │   │   │   │   ├── Catamarca
│       │   │   │   │   ├── Cayenne
│       │   │   │   │   ├── Cayman
│       │   │   │   │   ├── Chicago
│       │   │   │   │   ├── Chihuahua
│       │   │   │   │   ├── Ciudad_Juarez
│       │   │   │   │   ├── Coral_Harbour
│       │   │   │   │   ├── Cordoba
│       │   │   │   │   ├── Costa_Rica
│       │   │   │   │   ├── Coyhaique
│       │   │   │   │   ├── Creston
│       │   │   │   │   ├── Cuiaba
│       │   │   │   │   ├── Curacao
│       │   │   │   │   ├── Danmarkshavn
│       │   │   │   │   ├── Dawson
│       │   │   │   │   ├── Dawson_Creek
│       │   │   │   │   ├── Denver
│       │   │   │   │   ├── Detroit
│       │   │   │   │   ├── Dominica
│       │   │   │   │   ├── Edmonton
│       │   │   │   │   ├── Eirunepe
│       │   │   │   │   ├── El_Salvador
│       │   │   │   │   ├── Ensenada
│       │   │   │   │   ├── Fort_Nelson
│       │   │   │   │   ├── Fort_Wayne
│       │   │   │   │   ├── Fortaleza
│       │   │   │   │   ├── Glace_Bay
│       │   │   │   │   ├── Godthab
│       │   │   │   │   ├── Goose_Bay
│       │   │   │   │   ├── Grand_Turk
│       │   │   │   │   ├── Grenada
│       │   │   │   │   ├── Guadeloupe
│       │   │   │   │   ├── Guatemala
│       │   │   │   │   ├── Guayaquil
│       │   │   │   │   ├── Guyana
│       │   │   │   │   ├── Halifax
│       │   │   │   │   ├── Havana
│       │   │   │   │   ├── Hermosillo
│       │   │   │   │   ├── Indianapolis
│       │   │   │   │   ├── Inuvik
│       │   │   │   │   ├── Iqaluit
│       │   │   │   │   ├── Jamaica
│       │   │   │   │   ├── Jujuy
│       │   │   │   │   ├── Juneau
│       │   │   │   │   ├── Knox_IN
│       │   │   │   │   ├── Kralendijk
│       │   │   │   │   ├── La_Paz
│       │   │   │   │   ├── Lima
│       │   │   │   │   ├── Los_Angeles
│       │   │   │   │   ├── Louisville
│       │   │   │   │   ├── Lower_Princes
│       │   │   │   │   ├── Maceio
│       │   │   │   │   ├── Managua
│       │   │   │   │   ├── Manaus
│       │   │   │   │   ├── Marigot
│       │   │   │   │   ├── Martinique
│       │   │   │   │   ├── Matamoros
│       │   │   │   │   ├── Mazatlan
│       │   │   │   │   ├── Mendoza
│       │   │   │   │   ├── Menominee
│       │   │   │   │   ├── Merida
│       │   │   │   │   ├── Metlakatla
│       │   │   │   │   ├── Mexico_City
│       │   │   │   │   ├── Miquelon
│       │   │   │   │   ├── Moncton
│       │   │   │   │   ├── Monterrey
│       │   │   │   │   ├── Montevideo
│       │   │   │   │   ├── Montreal
│       │   │   │   │   ├── Montserrat
│       │   │   │   │   ├── Nassau
│       │   │   │   │   ├── New_York
│       │   │   │   │   ├── Nipigon
│       │   │   │   │   ├── Nome
│       │   │   │   │   ├── Noronha
│       │   │   │   │   ├── Nuuk
│       │   │   │   │   ├── Ojinaga
│       │   │   │   │   ├── Panama
│       │   │   │   │   ├── Pangnirtung
│       │   │   │   │   ├── Paramaribo
│       │   │   │   │   ├── Phoenix
│       │   │   │   │   ├── Port-au-Prince
│       │   │   │   │   ├── Port_of_Spain
│       │   │   │   │   ├── Porto_Acre
│       │   │   │   │   ├── Porto_Velho
│       │   │   │   │   ├── Puerto_Rico
│       │   │   │   │   ├── Punta_Arenas
│       │   │   │   │   ├── Rainy_River
│       │   │   │   │   ├── Rankin_Inlet
│       │   │   │   │   ├── Recife
│       │   │   │   │   ├── Regina
│       │   │   │   │   ├── Resolute
│       │   │   │   │   ├── Rio_Branco
│       │   │   │   │   ├── Rosario
│       │   │   │   │   ├── Santa_Isabel
│       │   │   │   │   ├── Santarem
│       │   │   │   │   ├── Santiago
│       │   │   │   │   ├── Santo_Domingo
│       │   │   │   │   ├── Sao_Paulo
│       │   │   │   │   ├── Scoresbysund
│       │   │   │   │   ├── Shiprock
│       │   │   │   │   ├── Sitka
│       │   │   │   │   ├── St_Barthelemy
│       │   │   │   │   ├── St_Johns
│       │   │   │   │   ├── St_Kitts
│       │   │   │   │   ├── St_Lucia
│       │   │   │   │   ├── St_Thomas
│       │   │   │   │   ├── St_Vincent
│       │   │   │   │   ├── Swift_Current
│       │   │   │   │   ├── Tegucigalpa
│       │   │   │   │   ├── Thule
│       │   │   │   │   ├── Thunder_Bay
│       │   │   │   │   ├── Tijuana
│       │   │   │   │   ├── Toronto
│       │   │   │   │   ├── Tortola
│       │   │   │   │   ├── Vancouver
│       │   │   │   │   ├── Virgin
│       │   │   │   │   ├── Whitehorse
│       │   │   │   │   ├── Winnipeg
│       │   │   │   │   ├── Yakutat
│       │   │   │   │   └── Yellowknife
│       │   │   │   ├── Antarctica
│       │   │   │   │   ├── Casey
│       │   │   │   │   ├── Davis
│       │   │   │   │   ├── DumontDUrville
│       │   │   │   │   ├── Macquarie
│       │   │   │   │   ├── Mawson
│       │   │   │   │   ├── McMurdo
│       │   │   │   │   ├── Palmer
│       │   │   │   │   ├── Rothera
│       │   │   │   │   ├── South_Pole
│       │   │   │   │   ├── Syowa
│       │   │   │   │   ├── Troll
│       │   │   │   │   └── Vostok
│       │   │   │   ├── Arctic
│       │   │   │   │   └── Longyearbyen
│       │   │   │   ├── Asia
│       │   │   │   │   ├── Aden
│       │   │   │   │   ├── Almaty
│       │   │   │   │   ├── Amman
│       │   │   │   │   ├── Anadyr
│       │   │   │   │   ├── Aqtau
│       │   │   │   │   ├── Aqtobe
│       │   │   │   │   ├── Ashgabat
│       │   │   │   │   ├── Ashkhabad
│       │   │   │   │   ├── Atyrau
│       │   │   │   │   ├── Baghdad
│       │   │   │   │   ├── Bahrain
│       │   │   │   │   ├── Baku
│       │   │   │   │   ├── Bangkok
│       │   │   │   │   ├── Barnaul
│       │   │   │   │   ├── Beirut
│       │   │   │   │   ├── Bishkek
│       │   │   │   │   ├── Brunei
│       │   │   │   │   ├── Calcutta
│       │   │   │   │   ├── Chita
│       │   │   │   │   ├── Choibalsan
│       │   │   │   │   ├── Chongqing
│       │   │   │   │   ├── Chungking
│       │   │   │   │   ├── Colombo
│       │   │   │   │   ├── Dacca
│       │   │   │   │   ├── Damascus
│       │   │   │   │   ├── Dhaka
│       │   │   │   │   ├── Dili
│       │   │   │   │   ├── Dubai
│       │   │   │   │   ├── Dushanbe
│       │   │   │   │   ├── Famagusta
│       │   │   │   │   ├── Gaza
│       │   │   │   │   ├── Harbin
│       │   │   │   │   ├── Hebron
│       │   │   │   │   ├── Ho_Chi_Minh
│       │   │   │   │   ├── Hong_Kong
│       │   │   │   │   ├── Hovd
│       │   │   │   │   ├── Irkutsk
│       │   │   │   │   ├── Istanbul
│       │   │   │   │   ├── Jakarta
│       │   │   │   │   ├── Jayapura
│       │   │   │   │   ├── Jerusalem
│       │   │   │   │   ├── Kabul
│       │   │   │   │   ├── Kamchatka
│       │   │   │   │   ├── Karachi
│       │   │   │   │   ├── Kashgar
│       │   │   │   │   ├── Kathmandu
│       │   │   │   │   ├── Katmandu
│       │   │   │   │   ├── Khandyga
│       │   │   │   │   ├── Kolkata
│       │   │   │   │   ├── Krasnoyarsk
│       │   │   │   │   ├── Kuala_Lumpur
│       │   │   │   │   ├── Kuching
│       │   │   │   │   ├── Kuwait
│       │   │   │   │   ├── Macao
│       │   │   │   │   ├── Macau
│       │   │   │   │   ├── Magadan
│       │   │   │   │   ├── Makassar
│       │   │   │   │   ├── Manila
│       │   │   │   │   ├── Muscat
│       │   │   │   │   ├── Nicosia
│       │   │   │   │   ├── Novokuznetsk
│       │   │   │   │   ├── Novosibirsk
│       │   │   │   │   ├── Omsk
│       │   │   │   │   ├── Oral
│       │   │   │   │   ├── Phnom_Penh
│       │   │   │   │   ├── Pontianak
│       │   │   │   │   ├── Pyongyang
│       │   │   │   │   ├── Qatar
│       │   │   │   │   ├── Qostanay
│       │   │   │   │   ├── Qyzylorda
│       │   │   │   │   ├── Rangoon
│       │   │   │   │   ├── Riyadh
│       │   │   │   │   ├── Saigon
│       │   │   │   │   ├── Sakhalin
│       │   │   │   │   ├── Samarkand
│       │   │   │   │   ├── Seoul
│       │   │   │   │   ├── Shanghai
│       │   │   │   │   ├── Singapore
│       │   │   │   │   ├── Srednekolymsk
│       │   │   │   │   ├── Taipei
│       │   │   │   │   ├── Tashkent
│       │   │   │   │   ├── Tbilisi
│       │   │   │   │   ├── Tehran
│       │   │   │   │   ├── Tel_Aviv
│       │   │   │   │   ├── Thimbu
│       │   │   │   │   ├── Thimphu
│       │   │   │   │   ├── Tokyo
│       │   │   │   │   ├── Tomsk
│       │   │   │   │   ├── Ujung_Pandang
│       │   │   │   │   ├── Ulaanbaatar
│       │   │   │   │   ├── Ulan_Bator
│       │   │   │   │   ├── Urumqi
│       │   │   │   │   ├── Ust-Nera
│       │   │   │   │   ├── Vientiane
│       │   │   │   │   ├── Vladivostok
│       │   │   │   │   ├── Yakutsk
│       │   │   │   │   ├── Yangon
│       │   │   │   │   ├── Yekaterinburg
│       │   │   │   │   └── Yerevan
│       │   │   │   ├── Atlantic
│       │   │   │   │   ├── Azores
│       │   │   │   │   ├── Bermuda
│       │   │   │   │   ├── Canary
│       │   │   │   │   ├── Cape_Verde
│       │   │   │   │   ├── Faeroe
│       │   │   │   │   ├── Faroe
│       │   │   │   │   ├── Jan_Mayen
│       │   │   │   │   ├── Madeira
│       │   │   │   │   ├── Reykjavik
│       │   │   │   │   ├── South_Georgia
│       │   │   │   │   ├── St_Helena
│       │   │   │   │   └── Stanley
│       │   │   │   ├── Australia
│       │   │   │   │   ├── ACT
│       │   │   │   │   ├── Adelaide
│       │   │   │   │   ├── Brisbane
│       │   │   │   │   ├── Broken_Hill
│       │   │   │   │   ├── Canberra
│       │   │   │   │   ├── Currie
│       │   │   │   │   ├── Darwin
│       │   │   │   │   ├── Eucla
│       │   │   │   │   ├── Hobart
│       │   │   │   │   ├── LHI
│       │   │   │   │   ├── Lindeman
│       │   │   │   │   ├── Lord_Howe
│       │   │   │   │   ├── Melbourne
│       │   │   │   │   ├── North
│       │   │   │   │   ├── NSW
│       │   │   │   │   ├── Perth
│       │   │   │   │   ├── Queensland
│       │   │   │   │   ├── South
│       │   │   │   │   ├── Sydney
│       │   │   │   │   ├── Tasmania
│       │   │   │   │   ├── Victoria
│       │   │   │   │   ├── West
│       │   │   │   │   └── Yancowinna
│       │   │   │   ├── Brazil
│       │   │   │   │   ├── Acre
│       │   │   │   │   ├── DeNoronha
│       │   │   │   │   ├── East
│       │   │   │   │   └── West
│       │   │   │   ├── Canada
│       │   │   │   │   ├── Atlantic
│       │   │   │   │   ├── Central
│       │   │   │   │   ├── Eastern
│       │   │   │   │   ├── Mountain
│       │   │   │   │   ├── Newfoundland
│       │   │   │   │   ├── Pacific
│       │   │   │   │   ├── Saskatchewan
│       │   │   │   │   └── Yukon
│       │   │   │   ├── Chile
│       │   │   │   │   ├── Continental
│       │   │   │   │   └── EasterIsland
│       │   │   │   ├── Etc
│       │   │   │   │   ├── GMT
│       │   │   │   │   ├── GMT+0
│       │   │   │   │   ├── GMT+1
│       │   │   │   │   ├── GMT+10
│       │   │   │   │   ├── GMT+11
│       │   │   │   │   ├── GMT+12
│       │   │   │   │   ├── GMT+2
│       │   │   │   │   ├── GMT+3
│       │   │   │   │   ├── GMT+4
│       │   │   │   │   ├── GMT+5
│       │   │   │   │   ├── GMT+6
│       │   │   │   │   ├── GMT+7
│       │   │   │   │   ├── GMT+8
│       │   │   │   │   ├── GMT+9
│       │   │   │   │   ├── GMT-0
│       │   │   │   │   ├── GMT-1
│       │   │   │   │   ├── GMT-10
│       │   │   │   │   ├── GMT-11
│       │   │   │   │   ├── GMT-12
│       │   │   │   │   ├── GMT-13
│       │   │   │   │   ├── GMT-14
│       │   │   │   │   ├── GMT-2
│       │   │   │   │   ├── GMT-3
│       │   │   │   │   ├── GMT-4
│       │   │   │   │   ├── GMT-5
│       │   │   │   │   ├── GMT-6
│       │   │   │   │   ├── GMT-7
│       │   │   │   │   ├── GMT-8
│       │   │   │   │   ├── GMT-9
│       │   │   │   │   ├── GMT0
│       │   │   │   │   ├── Greenwich
│       │   │   │   │   ├── UCT
│       │   │   │   │   ├── Universal
│       │   │   │   │   ├── UTC
│       │   │   │   │   └── Zulu
│       │   │   │   ├── Europe
│       │   │   │   │   ├── Amsterdam
│       │   │   │   │   ├── Andorra
│       │   │   │   │   ├── Astrakhan
│       │   │   │   │   ├── Athens
│       │   │   │   │   ├── Belfast
│       │   │   │   │   ├── Belgrade
│       │   │   │   │   ├── Berlin
│       │   │   │   │   ├── Bratislava
│       │   │   │   │   ├── Brussels
│       │   │   │   │   ├── Bucharest
│       │   │   │   │   ├── Budapest
│       │   │   │   │   ├── Busingen
│       │   │   │   │   ├── Chisinau
│       │   │   │   │   ├── Copenhagen
│       │   │   │   │   ├── Dublin
│       │   │   │   │   ├── Gibraltar
│       │   │   │   │   ├── Guernsey
│       │   │   │   │   ├── Helsinki
│       │   │   │   │   ├── Isle_of_Man
│       │   │   │   │   ├── Istanbul
│       │   │   │   │   ├── Jersey
│       │   │   │   │   ├── Kaliningrad
│       │   │   │   │   ├── Kiev
│       │   │   │   │   ├── Kirov
│       │   │   │   │   ├── Kyiv
│       │   │   │   │   ├── Lisbon
│       │   │   │   │   ├── Ljubljana
│       │   │   │   │   ├── London
│       │   │   │   │   ├── Luxembourg
│       │   │   │   │   ├── Madrid
│       │   │   │   │   ├── Malta
│       │   │   │   │   ├── Mariehamn
│       │   │   │   │   ├── Minsk
│       │   │   │   │   ├── Monaco
│       │   │   │   │   ├── Moscow
│       │   │   │   │   ├── Nicosia
│       │   │   │   │   ├── Oslo
│       │   │   │   │   ├── Paris
│       │   │   │   │   ├── Podgorica
│       │   │   │   │   ├── Prague
│       │   │   │   │   ├── Riga
│       │   │   │   │   ├── Rome
│       │   │   │   │   ├── Samara
│       │   │   │   │   ├── San_Marino
│       │   │   │   │   ├── Sarajevo
│       │   │   │   │   ├── Saratov
│       │   │   │   │   ├── Simferopol
│       │   │   │   │   ├── Skopje
│       │   │   │   │   ├── Sofia
│       │   │   │   │   ├── Stockholm
│       │   │   │   │   ├── Tallinn
│       │   │   │   │   ├── Tirane
│       │   │   │   │   ├── Tiraspol
│       │   │   │   │   ├── Ulyanovsk
│       │   │   │   │   ├── Uzhgorod
│       │   │   │   │   ├── Vaduz
│       │   │   │   │   ├── Vatican
│       │   │   │   │   ├── Vienna
│       │   │   │   │   ├── Vilnius
│       │   │   │   │   ├── Volgograd
│       │   │   │   │   ├── Warsaw
│       │   │   │   │   ├── Zagreb
│       │   │   │   │   ├── Zaporozhye
│       │   │   │   │   └── Zurich
│       │   │   │   ├── Indian
│       │   │   │   │   ├── Antananarivo
│       │   │   │   │   ├── Chagos
│       │   │   │   │   ├── Christmas
│       │   │   │   │   ├── Cocos
│       │   │   │   │   ├── Comoro
│       │   │   │   │   ├── Kerguelen
│       │   │   │   │   ├── Mahe
│       │   │   │   │   ├── Maldives
│       │   │   │   │   ├── Mauritius
│       │   │   │   │   ├── Mayotte
│       │   │   │   │   └── Reunion
│       │   │   │   ├── Mexico
│       │   │   │   │   ├── BajaNorte
│       │   │   │   │   ├── BajaSur
│       │   │   │   │   └── General
│       │   │   │   ├── Pacific
│       │   │   │   │   ├── Apia
│       │   │   │   │   ├── Auckland
│       │   │   │   │   ├── Bougainville
│       │   │   │   │   ├── Chatham
│       │   │   │   │   ├── Chuuk
│       │   │   │   │   ├── Easter
│       │   │   │   │   ├── Efate
│       │   │   │   │   ├── Enderbury
│       │   │   │   │   ├── Fakaofo
│       │   │   │   │   ├── Fiji
│       │   │   │   │   ├── Funafuti
│       │   │   │   │   ├── Galapagos
│       │   │   │   │   ├── Gambier
│       │   │   │   │   ├── Guadalcanal
│       │   │   │   │   ├── Guam
│       │   │   │   │   ├── Honolulu
│       │   │   │   │   ├── Johnston
│       │   │   │   │   ├── Kanton
│       │   │   │   │   ├── Kiritimati
│       │   │   │   │   ├── Kosrae
│       │   │   │   │   ├── Kwajalein
│       │   │   │   │   ├── Majuro
│       │   │   │   │   ├── Marquesas
│       │   │   │   │   ├── Midway
│       │   │   │   │   ├── Nauru
│       │   │   │   │   ├── Niue
│       │   │   │   │   ├── Norfolk
│       │   │   │   │   ├── Noumea
│       │   │   │   │   ├── Pago_Pago
│       │   │   │   │   ├── Palau
│       │   │   │   │   ├── Pitcairn
│       │   │   │   │   ├── Pohnpei
│       │   │   │   │   ├── Ponape
│       │   │   │   │   ├── Port_Moresby
│       │   │   │   │   ├── Rarotonga
│       │   │   │   │   ├── Saipan
│       │   │   │   │   ├── Samoa
│       │   │   │   │   ├── Tahiti
│       │   │   │   │   ├── Tarawa
│       │   │   │   │   ├── Tongatapu
│       │   │   │   │   ├── Truk
│       │   │   │   │   ├── Wake
│       │   │   │   │   ├── Wallis
│       │   │   │   │   └── Yap
│       │   │   │   ├── US
│       │   │   │   │   ├── Alaska
│       │   │   │   │   ├── Aleutian
│       │   │   │   │   ├── Arizona
│       │   │   │   │   ├── Central
│       │   │   │   │   ├── East-Indiana
│       │   │   │   │   ├── Eastern
│       │   │   │   │   ├── Hawaii
│       │   │   │   │   ├── Indiana-Starke
│       │   │   │   │   ├── Michigan
│       │   │   │   │   ├── Mountain
│       │   │   │   │   ├── Pacific
│       │   │   │   │   └── Samoa
│       │   │   │   ├── CET
│       │   │   │   ├── CST6CDT
│       │   │   │   ├── Cuba
│       │   │   │   ├── EET
│       │   │   │   ├── Egypt
│       │   │   │   ├── Eire
│       │   │   │   ├── EST
│       │   │   │   ├── EST5EDT
│       │   │   │   ├── Factory
│       │   │   │   ├── GB
│       │   │   │   ├── GB-Eire
│       │   │   │   ├── GMT
│       │   │   │   ├── GMT+0
│       │   │   │   ├── GMT-0
│       │   │   │   ├── GMT0
│       │   │   │   ├── Greenwich
│       │   │   │   ├── Hongkong
│       │   │   │   ├── HST
│       │   │   │   ├── Iceland
│       │   │   │   ├── Iran
│       │   │   │   ├── iso3166.tab
│       │   │   │   ├── Israel
│       │   │   │   ├── Jamaica
│       │   │   │   ├── Japan
│       │   │   │   ├── Kwajalein
│       │   │   │   ├── leapseconds
│       │   │   │   ├── Libya
│       │   │   │   ├── MET
│       │   │   │   ├── MST
│       │   │   │   ├── MST7MDT
│       │   │   │   ├── Navajo
│       │   │   │   ├── NZ
│       │   │   │   ├── NZ-CHAT
│       │   │   │   ├── Poland
│       │   │   │   ├── Portugal
│       │   │   │   ├── PRC
│       │   │   │   ├── PST8PDT
│       │   │   │   ├── ROC
│       │   │   │   ├── ROK
│       │   │   │   ├── Singapore
│       │   │   │   ├── Turkey
│       │   │   │   ├── tzdata.zi
│       │   │   │   ├── UCT
│       │   │   │   ├── Universal
│       │   │   │   ├── UTC
│       │   │   │   ├── W-SU
│       │   │   │   ├── WET
│       │   │   │   ├── zone.tab
│       │   │   │   ├── zone1970.tab
│       │   │   │   ├── zonenow.tab
│       │   │   │   └── Zulu
│       │   │   └── zones
│       │   ├── _asyncio.pyd
│       │   ├── _bz2.pyd
│       │   ├── _cffi_backend.cp312-win_amd64.pyd
│       │   ├── _ctypes.pyd
│       │   ├── _decimal.pyd
│       │   ├── _elementtree.pyd
│       │   ├── _hashlib.pyd
│       │   ├── _lzma.pyd
│       │   ├── _multiprocessing.pyd
│       │   ├── _overlapped.pyd
│       │   ├── _queue.pyd
│       │   ├── _socket.pyd
│       │   ├── _ssl.pyd
│       │   ├── _tkinter.pyd
│       │   ├── _uuid.pyd
│       │   ├── _wmi.pyd
│       │   ├── _zoneinfo.pyd
│       │   ├── base_library.zip
│       │   ├── CONCRT140.dll
│       │   ├── config.json
│       │   ├── freetype.dll
│       │   ├── libcrypto-3.dll
│       │   ├── libffi-8.dll
│       │   ├── libjpeg-9.dll
│       │   ├── libmodplug-1.dll
│       │   ├── libogg-0.dll
│       │   ├── libopus-0.dll
│       │   ├── libopusfile-0.dll
│       │   ├── libpng16-16.dll
│       │   ├── libssl-3.dll
│       │   ├── libtiff-5.dll
│       │   ├── libwebp-7.dll
│       │   ├── MSVCP140.dll
│       │   ├── portmidi.dll
│       │   ├── pyexpat.pyd
│       │   ├── python3.dll
│       │   ├── python312.dll
│       │   ├── SDL2.dll
│       │   ├── SDL2_image.dll
│       │   ├── SDL2_mixer.dll
│       │   ├── SDL2_ttf.dll
│       │   ├── select.pyd
│       │   ├── tcl86t.dll
│       │   ├── tk86t.dll
│       │   ├── unicodedata.pyd
│       │   ├── VCRUNTIME140.dll
│       │   ├── VCRUNTIME140_1.dll
│       │   └── zlib1.dll
│       └── MotionController.exe
├── docs
│   ├── AI_START_HERE.md
│   ├── change.md
│   ├── event_contracts.md
│   ├── full_game_plan.md
│   ├── GEMINI_CODE_ASSIST_GUIDE.md
│   ├── git_commits.md
│   ├── issues_and_resolutions.md
│   ├── master_ai_handoff.md
│   ├── progress_tracker.md
│   ├── project_directory_structure.md
│   ├── project_graph.md
│   └── use_case_catalogue.md
├── engine
│   ├── games
│   ├── mechanics
│   │   ├── __init__.py
│   │   ├── entities.py
│   │   └── manager.py
│   ├── __init__.py
│   ├── audio.py
│   ├── display.py
│   ├── event_pump.py
│   ├── game_engine.py
│   ├── motion_bridge.py
│   └── tutorial_ui.py
├── identity
│   ├── __init__.py
│   ├── measurement_capture.py
│   ├── profile_manager.py
│   └── shop_manager.py
├── logs
├── projection
│   └── projector_manager.py
├── reports
├── tests
│   ├── __init__.py
│   ├── test_action_detector.py
│   ├── test_audio.py
│   ├── test_camera_manager.py
│   ├── test_camera_supervisor.py
│   ├── test_config.py
│   ├── test_debug_tools.py
│   ├── test_display.py
│   ├── test_event_bus.py
│   ├── test_event_pump.py
│   ├── test_game_engine.py
│   ├── test_input_keyboard.py
│   ├── test_logger.py
│   ├── test_measurement_capture.py
│   ├── test_mechanics.py
│   ├── test_motion_bridge.py
│   ├── test_player_lock.py
│   ├── test_pose_tracker.py
│   ├── test_profile_manager.py
│   ├── test_projector_manager.py
│   ├── test_shop_manager.py
│   ├── test_tutorial_ui.py
│   └── test_zone_calibration.py
├── tools
│   ├── build_controller_exe.py
│   ├── build_exe.py
│   ├── calibrate_session.py
│   ├── extract_module.py
│   ├── generate_graph.py
│   ├── inspect_cameras.py
│   ├── make_session_diff.py
│   ├── motion_controller_app.py
│   ├── show_tree.py
│   └── update_git_commits.py
├── user_data
│   ├── custom_assets
│   │   ├── actions
│   │   ├── monsters
│   │   ├── photos
│   │   └── powerups
│   ├── catalog.json
│   ├── profiles.json
│   └── profiles.json.bak
├── vision
│   ├── __init__.py
│   ├── action_detector.py
│   ├── camera_manager.py
│   ├── camera_supervisor.py
│   ├── debug_tools.py
│   ├── player_lock.py
│   ├── pose_tracker.py
│   └── zone_calibration.py
├── .geminiignore
├── .gitignore
├── .gitingestignore
├── config.json
├── Launch_Motion_Controller.bat
├── main.py
├── module_10_spec.md
├── MotionController.spec
├── Play_Kids_Game.bat
├── requirements.txt
└── session_diff.txt
```

---

## Target Project Tree (Full Build Roadmap)

```text
kids_game/
├── core/                          # Architecture foundation (Phase A)
│   ├── logger.py                  # Module 1: Logging
│   ├── config.py                  # Module 1: Settings
│   ├── events.py                  # Module 2: Event catalogue & dataclass
│   ├── event_bus.py               # Module 2: Pub/Sub message broker
│   └── input_keyboard.py          # Module 3: Keyboard input adapter
├── engine/                        # Game Engine & Mechanics (Phase B)
│   ├── display.py                 # Module 4: Pygame second-screen display & HUD
│   ├── audio.py                   # Module 5: Sound & music manager
│   ├── game_engine.py             # Module 6: State machine & fixed timestep loop
│   ├── mechanics/                 # Module 7: Reusable gameplay blocks
│   └── games/                     # Module 8 & 18: Runner, Lane Switch, Freeze Dance
├── vision/                        # Computer Vision & Tracking (Phase C & E)
├── identity/                      # Player Profiles & Calibration (Phase D)
├── projection/                    # Projector Output (Phase E)
├── assets/                        # Art, sounds and fonts
├── docs/                          # Comprehensive documentation & logs
├── tests/                         # Module unit tests
└── main.py                        # Game startup script
```
