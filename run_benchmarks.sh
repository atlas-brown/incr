#!/bin/bash

base_dir=$(realpath $(dirname $0))
result_dir=./results/incr

mkdir -p ${result_dir}

# Remove results from previous runs 
rm -f "$result_dir"/*

bm_script="test.sh"

run_benchmark() {
	local benchmark_name="$1"
	local times=""
	
	for i in {1..1}; do
		echo "Running $script_path (Iteration $i)"
		time_output=$( { /usr/bin/time -f "%e" ./incr.sh $bm_script /users/jxia3/incr/cache > /users/jxia3/incr/out.txt; } 2>&1)
		times="$times,$time_output"
	done

	echo "$benchmark_name$times" >> $output_file
}

#export INCR_ISOLATION_MODE=try
#output_file=${result_dir}/"benchmark_results_try.csv"
#run_benchmark "eager"

export INCR_ISOLATION_MODE=docker
output_file=${result_dir}/"benchmark_results_docker.csv"
run_benchmark "eager"

#export INCR_ISOLATION_MODE=none
#output_file=${result_dir}/"benchmark_results_vanilla.csv"
#run_benchmark "eager"
