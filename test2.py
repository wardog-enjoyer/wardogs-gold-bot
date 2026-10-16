import urllib.request, re
from bs4 import BeautifulSoup

URL = 'https://metaforge.app/wardogs/market'
req = urllib.request.Request(
    URL,
    headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
)
html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', 'ignore')

with open('metaforge.html', 'w', encoding='utf-8') as f:
    f.write(html)

text = BeautifulSoup(html, 'html.parser').get_text(' ', strip=True)

# 1) Znajdź fragment wokół "Current"
print("=== FRAGMENT WOKOL 'Current' ===")
idx = text.find("Current")
if idx != -1:
    print(repr(text[max(0, idx-30):idx+100]))
else:
    print("BRAK slowa 'Current' w tekscie!")

print()
print("=== WSZYSTKIE LICZBY 4+ CYFR Z KONTEKSTEM ===")
for i, m in enumerate(re.finditer(r'[\d][\d,]{3,}', text)):
    start = max(0, m.start() - 60)
    end = min(len(text), m.end() + 20)
    print(f"--- Liczba #{i+1}: {m.group(0)} ---")
    print(repr(text[start:end]))
    if i > 15:
        print("... (wiecej pomijam)")
        break
