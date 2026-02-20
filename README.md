Chill — bu Python tilida yozilgan, Git tizimiga o'xshash, ammo juda sodda ishlaydigan versiyalarni boshqarish vositasi. Bu loyiha murakkab buyruqlarsiz fayllaringizning holatlarini saqlash va kuzatib borish uchun mo'ljallangan.
Asosiy Imkoniyatlar

1. Loyihani boshlash (Init)
Loyhani oldin saqlangan version nomi va berilgan pathdan asosida loyhani izlab topadi va loyhani so'ralgan version asosida tahrirlaydi! 
[chill init path version]

2. Holatni saqlash (Save)
Path bilan berilgan loyhani version nomi asosida saqlab qo'yadi!
[chill save path version]

3. Saqlangan versiyalar ro'yxati (List)
Shu vaqtgacha saqlangan barcha "snapshot"larni va ularning "version"larini  ko'rish imkonini beradi.
[chill list]

4. Dastur versiyasi (Version)
Berilgan path asosida loyhani aniqlab undagi barcha pathlarni yozib chiqazadi!
[chill version path]

O'rnatish va Ishga tushirish:
Loyiha Python muhitida va Click kutubxonasi yordamida ishlaydi. Uni ishga tushirish uchun quyidagi buyruqni bajaring:

pip install click cryptocode cryptography
python main.py --help

