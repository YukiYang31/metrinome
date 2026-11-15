#include <klee/klee.h>
#include "../../../../../experiments/recursion/files/mutual-recursion.c"
#define SIZE 10
int main() {

	const int n;
	klee_make_symbolic(&n, sizeof(n), "655c31540535457f9ffcf5ee51bce9ba");
	if ((n<-1) || (n>1024)) {
		 return 0;}
	return F(n);
}
