SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SRC${PYTHONPATH:+:$PYTHONPATH}"

python3 "$SRC/experiments/function_calls/tests/test_getrgf.py" #with branching
# must run this in order for mergeTestResult to work

# python3 "$SRC/experiments/function_calls/tests/test_fcapc.py"

# python3 "$SRC/experiments/function_calls/tests/test_rapc.py"

# python3 "$SRC/experiments/function_calls/tests/test_npath.py"

# python3 "$SRC/experiments/function_calls/tests/mergeData.py"



### for apc vs branching apc, uncomment these and the first line ###
python3 "$SRC/experiments/branch_apc/tests/test_noBranching.py"

python3 "$SRC/experiments/branch_apc/tests/test_pythonBranch.py"

python3 "$SRC/experiments/branch_apc/tests/merge_branching_data.py"
##################################################################