#include <klee/klee.h>
#include "lina.c"
#define SIZE 10
int main() {

  dVector N;
	klee_make_symbolic(&N, sizeof(N), "53ce1833a88f4d3badbed4100e614ea3");
	max(N);
  return 0;
}
