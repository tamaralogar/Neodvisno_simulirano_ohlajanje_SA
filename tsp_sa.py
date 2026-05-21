#!/usr/bin/env python3
import sys
import math
import time
import numpy as np
from mpi4py import MPI

# ── Privzete konstante ──
DEFAULT_CITIES = 50
DEFAULT_ITERS = 500000
INITIAL_TEMP = 10000.0
COOLING_RATE = 0.99997

# ── MPI init ──
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# ── Argumenti ukazne vrstice ──
n_cities = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CITIES
n_iters = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_ITERS

if n_cities < 4:
    if rank == 0:
        print("Napaka: st_mest mora biti vsaj 4.", file=sys.stderr)
    MPI.Finalize()
    sys.exit(1)

# ── Globalne koordinate mest ──
city_x = np.zeros(n_cities, dtype=np.float64)
city_y = np.zeros(n_cities, dtype=np.float64)

# Master generira mesta in razpošlje vsem
if rank == 0:
    # Fiksno seme za generator 
    rng_master = np.random.default_rng(42)
    city_x[:] = rng_master.random(n_cities) * 1000.0
    city_y[:] = rng_master.random(n_cities) * 1000.0

# Sinhronizacija koordinat med vsemi procesi
comm.Bcast(city_x, root=0)
comm.Bcast(city_y, root=0)

# Precomputation: Izračun matrike razdalj 
D = np.zeros((n_cities, n_cities), dtype=np.float64)
for i in range(n_cities):
    for j in range(n_cities):
        dx = city_x[i] - city_x[j]
        dy = city_y[i] - city_y[j]
        D[i, j] = math.sqrt(dx * dx + dy * dy)

# ── Skupna dolžina poti ──
def path_length(path, D):
    total = 0.0
    n = len(path)
    for i in range(n - 1):
        total += D[path[i], path[i + 1]]
    total += D[path[-1], path[0]]
    return total

# ── Jedro SA – vrne dolžino najboljše najdene poti in pot samo ──
def simulated_annealing(n_cities, n_iters, seed, D):
    rng = np.random.default_rng(seed)
    
    # Naključna začetna pot 
    current = rng.permutation(n_cities)
    current_len = path_length(current, D)
    
    best_path = current.copy()
    best_len = current_len
    temp = INITIAL_TEMP

    for _ in range(n_iters):
        # Generiraj sosednje stanje s swap-om dveh naključnih mest
        candidate = current.copy()
        idx1, idx2 = rng.integers(0, n_cities, size=2)
        candidate[idx1], candidate[idx2] = candidate[idx2], candidate[idx1]
        
        candidate_len = path_length(candidate, D)
        delta = candidate_len - current_len

        # Metropolis kriterij sprejema
        if delta < 0.0 or rng.random() < math.exp(-delta / temp):
            current = candidate
            current_len = candidate_len

            if current_len < best_len:
                best_path = current.copy()
                best_len = current_len

        temp *= COOLING_RATE
        if temp < 1e-10: 
            temp = 1e-10  # Prepreči underflow

    return best_len, best_path

# ── Vsak proces dobi edinstveno deterministično seme ──
# Ustvarimo unikatno celo število na podlagi trenutnega časa in ranga procesa
base_seed = int(time.time()) & 0xFFFFFFFF
seed = (base_seed * (rank + 1) * 2654435761) & 0xFFFFFFFF

# ── Meritev časa ──
comm.Barrier()
t_start = MPI.Wtime()

# ── Neodvisni SA na vsakem procesu ──
local_len, local_path = simulated_annealing(n_cities, n_iters, seed, D)

comm.Barrier()
t_end = MPI.Wtime()

# ── MPI_Reduce z MINLOC: najdi globalno najboljšo pot ──
local_res = (local_len, rank)
global_res = comm.reduce(local_res, op=MPI.MINLOC, root=0)

# ── Razpošlji najboljšo pot od zmagovalnega procesa ──
# Najprej Master ugotovi, kdo je zmagal
best_rank = global_res[1] if rank == 0 else None
best_rank = comm.bcast(best_rank, root=0)

global_path = np.zeros(n_cities, dtype=np.int32)
if rank == best_rank:
    global_path[:] = local_path

# Zmagovalni proces razpošlje svojo pot vsem ostalim
comm.Bcast(global_path, root=best_rank)

# ── Izpis rezultatov (samo Master) ──
if rank == 0:
    elapsed = t_end - t_start
    global_best_len = global_res[0]
    
    print("=== SA-TSP Rezultati ===")
    print(f"Procesi       : {size}")
    print(f"Mesta         : {n_cities}")
    print(f"Iteracije/proc: {n_iters}")
    print(f"Najboljsa pot : {global_best_len:.4f}")
    print(f"Nasla proces  : {best_rank}")
    print(f"Cas izvajanja : {elapsed:.6f} s")

    # Za benchmark skripto
    print(f"BENCHMARK: processes={size} cities={n_cities} time={elapsed:.6f} length={global_best_len:.4f}")

    if n_cities <= 30:
        pot_str = " -> ".join(map(str, global_path))
        print(f"Pot           : {pot_str}")

MPI.Finalize()
