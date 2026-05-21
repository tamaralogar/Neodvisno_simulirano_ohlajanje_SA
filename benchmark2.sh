#!/bin/bash

# Nastavitve
CITIES=50
ITERS=500000
RUNS=3
CONFIGS=(1 2 4 8)
CSV_FILE="results.csv"

# Čiščenje okolja za stabilnost mpi4py + numpy
export OMP_NUM_THREADS=1

echo "=== SA-TSP Benchmark (Python + MPI) ==="
echo "Mesta: $CITIES | Iteracije/proc: $ITERS | Zagonov/konfiguracija: $RUNS"
date
echo ""

# Glava CSV datoteke
echo "procesi,zagon1_t,zagon2_t,zagon3_t,povprecje_t,zagon1_l,zagon2_l,zagon3_l,najboljsa_l" > $CSV_FILE

for p in "${CONFIGS[@]}"; do
    echo "--- Procesov: $p ---"
    
    times=()
    lengths=()
    
    for ((i=1; i<=RUNS; i++)); do
        echo -n "  Zagon $i/$RUNS ... "
        
        # Pognemo program in ulovimo vrstico BENCHMARK
        output=$(mpirun -np $p python3 tsp_sa.py $CITIES $ITERS 2>/dev/null | grep "BENCHMARK:")
        
        # Izluščimo čas in dolžino
        t_val=$(echo "$output" | sed -n 's/.*time=\([0-9.]*\).*/\1/p')
        l_val=$(echo "$output" | sed -n 's/.*length=\([0-9.]*\).*/\1/p')
        
        echo "${t_val}s | Pot: ${l_val}"
        
        times+=($t_val)
        lengths+=($l_val)
    done
    
    # Izračun povprečnika za čas (preko pythona, ker bash ne zna z decimalkami)
    avg_t=$(python3 -c "print(f'{(sum([float(x) for x in [${times[0]},${times[1]},${times[2]}]]) / 3):.6f}')")
    
    # Iskanje absolutno najboljše (najkrajše) poti izmed treh zagonov
    min_l=$(python3 -c "print(f'{min([float(x) for x in [${lengths[0]},${lengths[1]},${lengths[2]}]]):.4f}')")
    
    # Zapis v CSV vrstico
    echo "$p,${times[0]},${times[1]},${times[2]},$avg_t,${lengths[0]},${lengths[1]},${lengths[2]},$min_l" >> $CSV_FILE
    echo "  Povprečni čas: ${avg_t}s | Najboljša pot konfiguracije: ${min_l}"
    echo ""
done

echo "=== Rezultati shranjeni v $CSV_FILE ==="
