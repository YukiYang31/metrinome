/* Pre-C99 code that clang 14 accepted with warnings but clang >= 16 rejects by default:
 *   - `helper` is called before any declaration (implicit function declaration);
 *   - `by_value` has the wrong signature for qsort's comparator (incompatible function pointer).
 * Used by tests/test_frontends.py. */
#include <stdlib.h>

static int by_value(int *a, int *b) {
    return *a - *b;
}

void sort_and_count(int *values, int n) {
    qsort(values, n, sizeof(int), by_value);
    helper(n);
}

int helper(int n) {
    int count = 0;
    while (n > 0) {
        n /= 2;
        count++;
    }
    return count;
}
