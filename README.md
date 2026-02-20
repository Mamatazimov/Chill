Chill — bu Python tilida yozilgan, Git tizimiga o'xshash, ammo juda sodda ishlaydigan versiyalarni boshqarish vositasi. Bu loyiha murakkab buyruqlarsiz fayllaringizning holatlarini saqlash va kuzatib borish uchun mo'ljallangan.
Asosiy Imkoniyatlar

1. Loyihani boshlash (Init)
Yangi loyihada Chill tizimini ishga tushirish va kerakli konfiguratsiya fayllarini yaratish uchun ishlatiladi.
chill init

2. Holatni saqlash (Save)
Joriy o'zgarishlarni nusxalab, ularni ma'lum bir nom yoki izoh bilan saqlab qo'yadi.
chill save "birinchi versiya"

3. Saqlangan versiyalar ro'yxati (List)
Shu vaqtgacha saqlangan barcha "snapshot"larni va ularning qachon yaratilganini ko'rish imkonini beradi.
chill list

4. Dastur versiyasi (Version)
O'rnatilgan Chill dasturining joriy versiyasini tekshirish uchun.
chill --version
O'rnatish va Ishga tushirish

Loyiha Python muhitida va Click kutubxonasi yordamida ishlaydi. Uni ishga tushirish uchun quyidagi buyruqni bajaring:

pip install click
python main.py --help
