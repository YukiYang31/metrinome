#include <klee/klee.h>
#include "../../../../../experiments/recursion/files/hailstone-sequence-2.c"
#define SIZE 10
int main() {

	ulong n;
	klee_make_symbolic(&n, sizeof(n), "40e179d4ffeb4176855ecd62638a7581");
	return hailstone(n);
}
