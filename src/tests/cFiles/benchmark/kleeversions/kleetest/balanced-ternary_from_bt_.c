#include <klee/klee.h>
#include "../../../../../experiments/recursion/files/balanced-ternary.c"
#define SIZE 10
int main() {

	const char *a;
	klee_make_symbolic(&a, sizeof(a), "34738c636ac0493fa58ea269554d04ad");
	return from_bt(a);
}
