# Clipstack

ვიდეოს ჩამოტვირთვის საიტი ხარისხის არჩევითა და MP3 აუდიოთი.

**საიტი:** https://clipstack-video.vercel.app

კოდი: `website/`. Vercel-ის Root Directory: `website`.
საჭირო გარემოს ცვლადი: `DOWNLOAD_SECRET` — შემთხვევითი, მინიმუმ 32 სიმბოლო.

ადგილობრივად: `cd website`, `npm ci`, `pip install -r requirements.txt`.
API: `uvicorn api.index:app --port 8001`. საიტი: `npm run dev`.
აწყობა: `npm run build`.
ტესტები: `pip install httpx`, შემდეგ `python -m unittest discover -s tests -v`.

თითო საწყისი ნაკადის ლიმიტი: 64 MB. MP3 და ვიდეო/ხმის გაერთიანება ბრაუზერში სრულდება.
პლატფორმებმა შესაძლოა ჰოსტინგის მოთხოვნები დაბლოკონ. ყველა ვიდეოს მხარდაჭერა გარანტირებული არ არის.
