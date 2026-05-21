# analyze.py
import pandas as pd

try:
    df = pd.read_csv("results.csv")
except FileNotFoundError:
    print("Napaka: Datoteka results.csv ne obstaja. Najprej zaženi ./benchmark.sh")
    exit(1)

# Pridobi bazični čas na enem jedru (T1)
t1 = df.loc[df['procesi'] == 1, 'povprecje_t'].values[0]

pospeski = []
karp_flatt = []

# Izračun vzporednih metrik
for idx, row in df.iterrows():
    p = row['procesi']
    tp = row['povprecje_t']
    
    # Pospešek
    S = t1 / tp
    pospeski.append(S)
    
    # Karp-Flatt (e)
    if p == 1:
        e = 0.0
    else:
        e = ((1.0 / S) - (1.0 / p)) / (1.0 - (1.0 / p))
    karp_flatt.append(e)

df['pospesek'] = pospeski
df['karp_flatt_e'] = karp_flatt

# Izpis čudovite Markdown tabele, ki jo samo prekopiraš v Readme.md
print("\n=== REZULTATI ANALIZE ZMOGLJIVOSTI IN KVALITETE ===")
print("Kopiraj spodnjo tabelo direktno v Readme.md:\n")

print("| Procesi | Povprečni čas | Pospešek (Sp) | Karp-Flatt (e) | Najboljša pot (razdalja) |")
print("| :---: | :---: | :---: | :---: | :---: |")

for idx, row in df.iterrows():
    print(f"| **{int(row['procesi'])}** | "
          f"{row['povprecje_t']:.2f} s | "
          f"{row['pospesek']:.2f}x | "
          f"{row['karp_flatt_e']:.4f} | "
          f"{row['najboljsa_l']:.2f} |")
