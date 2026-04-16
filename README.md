## Chill — bu Python tilida yozilgan, Git tizimiga o'xshash, ammo juda sodda ishlaydigan versiyalarni boshqarish vositasi.
### Bu loyiha murakkab buyruqlarsiz fayllaringizning holatlarini saqlash va kuzatib borish uchun mo'ljallangan.
##### Asosiy Imkoniyatlar:

* Loyihani boshqarish __(Chill / Init)__\
Loyihani berilgan path asosida tekshiradi va mavjud bo‘lgan version yoki yangi projekt yaratadi:
```
chillbek -p /path/to/project
```

* Holatni saqlash __(Save)__\
Hozirgi loyiha holatini yangi versiya sifatida saqlaydi:
```
chillbek save
```
* Saqlangan versiyalar ro'yxati __(List)__\
Proyektning barcha flow va save’larini ko‘rsatadi:
```
chillbek list
```
* Flow yaratish va o‘zgartirish __(Flow)__\
Yangi flow yaratadi yoki mavjud flow’ni tanlaydi:
```
chillbek flow <flow_name>
```
* Eski versiyani tiklash __(Back)__\
Tanlangan save id asosida loyiha holatini tiklaydi:
```
chillbek back
```
* Terminal Ui ni ochish  __(Tui)__\
Gitdan farqli Chillda Tui bor bo'lib u tez va qulay bo'lgan Textual kutubxonasida yaratilgan:
```
chillbek tui
```

* __(Build)__ qilish uchun ushbu kamandani tering:\
```
uv tool install .
```
"." o'rnida loyha joylashgan path
