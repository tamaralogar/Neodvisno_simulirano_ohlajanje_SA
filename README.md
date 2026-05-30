# MPI Vzporedno Reševanje Problema Trgovskega Potnika (TSP) s simuliranim ohlajanjem (SA) 
Implementacija algoritma simuliranega ohlajanja (Simulated Annealing - SA) za reševanje problema trgovskega potnika (TSP), paraleliziranega s pomočjo knjižnice MPI (mpi4py).

## 0. OPIS PROBLEMA IN REŠITVE
   Cilj je najti najkrajšo pot, ki obišče vsa mesta točno enkrat in se vrne v začetno točko.

   Zasnova naloge: Vsak MPI proces neodvisno izvaja SA algoritem na svoji naključni začetni poti. Po končanem izvajanju Master proces s funkcijo MPI_Reduce zbere vse najdene poti in izbere globalno najboljšo.
   Za analizo se skupno število iteracij deli med procese (pri 500.000 iteracijah: 1 proces - vseh 500.000; 8 procesov - vsak 500.000/8=62.500), da bi ocenili pohitritev izvajanja.

## 1. NAVODILA ZA UPORABO
   
  Zahteve:
  
    * Python 3
    * MPI okolje (OpenMPI ali MPICH)
    * Knjižnice: mpi4py, numpy, pandas

  Zagon programa (Program sprejme dva argumenta: število mest in skupno število iteracij):

    mpirun -np <stevilo_procesov> python3 tsp_sa.py <stevilo_mest> <stevilo_iteracij>

  Primer za 4 procese, 50 mest in 500.000 iteracij:
  
      mpirun -np 4 python3 tsp_sa.py 50 500000

  Zagon testiranja (benchmark) - avtomatsko izvajanje meritev (1, 2, 4 in 8 procesov, vsak zagon 3x)
  
    ./benchmark2.sh

  Za generiranje rezultatov - po zagonu testiranja:
  
      python3 analyze2.py

## 2. REZULTATI MERITEV

   Meritve so bile izvedene na prenosnem računalniku z 8 jedri. Testiranje je potekalo znotraj virtualnega okolja Kali Linux, 
   ki so mu bila dodeljena vsa procesorska jedra (1 procesorsko gnezdo z 8 jedri).
   
   <img width="193" height="57" alt="Slika Racunalnik" src="https://github.com/user-attachments/assets/787ece18-917e-4e16-b9e1-68250303143b" />

   <img width="332" height="111" alt="Slika Kali" src="https://github.com/user-attachments/assets/75d80800-cd7e-4231-ae53-0b570b9557c6" />

   Meritve so bile izvedene za 50 mest in skupno 500.000 iteracij.

 Procesov: 1
 
    Zagon 1/3 ... 9.450003s | Pot: 6014.5239
    Zagon 2/3 ... 9.495096s | Pot: 5906.2729
    Zagon 3/3 ... 9.823605s | Pot: 6755.4214
    Povprečni čas: 9.589568s | Najboljša pot konfiguracije: 5906.2729

Procesov: 2

    Zagon 1/3 ... 4.913110s | Pot: 6043.7073
    Zagon 2/3 ... 4.818904s | Pot: 5934.6919
    Zagon 3/3 ... 4.839384s | Pot: 6287.3340
    Povprečni čas: 4.857133s | Najboljša pot konfiguracije: 5934.6919

Procesov: 4

    Zagon 1/3 ... 2.807408s | Pot: 11707.9139
    Zagon 2/3 ... 2.807482s | Pot: 12064.7582
    Zagon 3/3 ... 3.317124s | Pot: 12576.2720
    Povprečni čas: 2.977338s | Najboljša pot konfiguracije: 11707.9139

Procesov: 8 

    Zagon 1/3 ... 2.006338s | Pot: 17531.0453
    Zagon 2/3 ... 2.194689s | Pot: 17501.8913
    Zagon 3/3 ... 2.110744s | Pot: 17158.5733
     Povprečni čas: 2.103924s | Najboljša pot konfiguracije: 17158.5733

REZULTATI ANALIZE ZMOGLJIVOSTI IN KVALITETE
| Procesi | Povprečni čas | Pospešek (Sp) | Karp-Flatt (e) | Najboljša pot (razdalja) |
| :---: | :---: | :---: | :---: | :---: |
| **1** | 9.59 s | 1.00x | 0.0000 | 5906.27 |
| **2** | 4.86 s | 1.97x | 0.0130 | 5934.69 |
| **4** | 2.98 s | 3.22x | 0.0806 | 11707.91 |
| **8** | 2.10 s | 4.56x | 0.1079 | 17158.57 |


## 3.  INTERPRETACIJA REZULTATOV

### Pospešek:
  Čas izvajanja se z dodajanjem procesov zmanjšuje, ker se zmanjša število iteracij, ki jih posamezen proces izvede. 

 
   <img width="663" height="449" alt="Slika_pospesek" src="https://github.com/user-attachments/assets/1e918c40-2927-487e-98b4-4645c2d15c61" />

  
  Pri 8 procesih je bil pospešek 4.56x. 
  Odmik od idealnega linearnega pospeška (8x) je pričakovan, ker morajo vsi procesi opraviti nekatere operacije: 
  
    * Padci frekvence procesorja: pri obremenitvbi vseh procesorjev sistem preventivno zniža frekvenco vseh jeder
    * Tekmovanje za predpomnilnik (L3 Cache)
    * Režijski stroški virtualizacije: VMware porabi nekaj časa za koordinacijo 8 navideznih jeder na fizični strojni opremi

    
 ### Analiza trenda matrike Karp-Flatt (e):
  
  Karp-Flattova metrika (e) nam podaja eksperimentalni vpogled v učinkovitost.

   <img width="1150" height="869" alt="Slika_Karp_Flatt" src="https://github.com/user-attachments/assets/0ad8ab4c-f7cb-40fd-b819-00b8ba446fde" />

  
  Pri 2 procesih je vrednost nizka (0.0130). To pomeni, da je paralelizacija učinkovita.
  Z naraščanjem števila jeder vrednost naraste na 0.1079 (8 procesov). To kaže na to, da z večanjem števila jeder naraščajo režijski stroški operacijskega sistema (tekmovanje za procesorske vire).
  MPI komunikacija pa je v tem primeru minimalna.
    
  ### Identifikacija ozkih grl:
  
  Pri meritvah je prišlo do kompromisa med hitrostjo in kakovostjo rešitve. Pri uporabi večjega števila jeder (4 in 8) se kakovost najdene poti drastično poslabša.
  
  <img width="968" height="731" alt="Slika_kakovost_dolzine_poti" src="https://github.com/user-attachments/assets/95eac7f6-695e-4400-b5b6-2743c52f44ac" />

  Razlog je v zmanjšanem številu iteracij na proces (pri 8 procesih na samo 62.500), medtem ko je stopnja ohlajanja (COOLING_RATE) ostala nespremenjena. Algoritem se tako konča prehitro in se ujame v lokalni minimum, preden bi lahko našel boljšo rešitev.
  Za boljši preiskani prostor rešitev bi lahko dodali večje število iteracij na proces (s tem porabili več časa, ampak dobili boljši rezultat). Če bi vsi procesi imeli enako število iteracij, ne glede na to koliko procesov se izvaja, bi pri večjem številu izvajanih procesov prišli do krajše poti.

  Pri algoritmu, kot je SA, paralelizacija ni le vprašanje moči, ampak strategije iskanja. Za ohranitev kakovosti pri večjem številu jeder, bi bilo potrebno prilagoditi parametre ohlajanja ali povečati število iteracij na proces, kar pa bi ponovno podaljšalo čas izvajanja.
  

 
