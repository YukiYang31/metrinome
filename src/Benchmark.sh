# Add paths to this list
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SRC${PYTHONPATH:+:$PYTHONPATH}"

paper_dict='{
   "1": "experiments/icse_experiment/files/files.txt",
   "2": "experiments/recursion/files/files.txt",
   "3": "experiments/function_calls/benchmark/benchmarkFiles.txt",
   "4": "tests/cFiles/C-master/CmasterFiles.txt",
   "5": "REPL"
   }'

# Add metrics to this list
apc_dict='"1" "2" "3" "4" "5"'

# Add papers below in chronological order :)
if command -v lolcat >/dev/null; then lolcat "$SRC/metrinome_ascii.txt"; else cat "$SRC/metrinome_ascii.txt"; fi
while :;do
   printf "PRESS THE CORRESPONDING NUMBER TO SEE THE BENCHMARKS FROM THAT PAPER.\n\
   1) ICSE 2021 PAPER\n\
   2) FormaliSE 2023 PAPER\n\
   3) ICSE 2024 POSTER\n\
   4) ISSTA 2024 PAPER
   5) I WANT THE REPLLL \n"
   while read paper_num; do
      # check if input in the list and is an integer
      if [[ $paper_dict == *"$paper_num"* && "$paper_num" =~ ^[0-9]+$ ]]; then
         if [[ $paper_num == 5 ]]; then
            python3 "$SRC/main.py"
            break
         fi
         printf "WHICH METRIC WOULD YOU LIKE TO COMPUTE? \n\
   1) APC-IP: Interprocedural APC\n\
   2) NAPC-IP: Naive Interprocedural APC\n\
   3) APC-R: Recursive APC\n\
   4) NPath Complexity\n\
   5) ALL METRICS\n"
         while read apc_num; do
            if [[ $apc_dict == *"$apc_num"* && "$apc_num" =~ ^[0-9]+$ ]]; then
               break
            else
               echo "Not a valid selection! Try Again :)"
               continue
            fi
         done
      else
         echo "Not a valid paper! Try Again :)"
         continue
      fi
      break
   done

   if [[ "$apc_num" == "1" || "$apc_num" == "5" ]]; then
      python3 "$SRC/experiments/function_calls/tests/test_getrgf.py" $paper_num "$paper_dict"
   fi

   if [[ "$apc_num" == "2" || "$apc_num" == "5" ]]; then
      python3 "$SRC/experiments/function_calls/tests/test_fcapc.py" $paper_num "$paper_dict"
   fi

   if [[ "$apc_num" == "3" || "$apc_num" == "5" ]]; then
      python3 "$SRC/experiments/function_calls/tests/test_rapc.py" $paper_num "$paper_dict"
   fi

   if [[ "$apc_num" == "4" || "$apc_num" == "5" ]]; then
      python3 "$SRC/experiments/function_calls/tests/test_npath.py" $paper_num "$paper_dict"
   fi

   if [[ "$apc_num" == "5" ]]; then
      python3 "$SRC/experiments/function_calls/tests/mergeData.py"
   fi

   printf "\n\nPRESS 1 TO COMPUTE ANOTHER METRIC. OTHERWISE PRESS ANYTHING ELSE TO EXIT.\n"

   read choice

   if [[ $choice == "1" ]]; then
      continue
   fi
   break
done
