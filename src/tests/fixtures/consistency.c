/* C half of the cross-front-end consistency fixture; Consistency.java has the same functions.
 * Used by tests/test_frontends.py. */
int straight(int a, int b) {
    int c = a + b;
    c = c * 2;
    return c - 1;
}

int if_chain(int x) {
    int r;
    if (x < 0) {
        r = -1;
    } else if (x == 0) {
        r = 0;
    } else if (x < 10) {
        r = 1;
    } else {
        r = 2;
    }
    return r;
}

int for_loop(int n) {
    int s = 0;
    for (int i = 0; i < n; i++) {
        s += i;
    }
    return s;
}

int nested_loops(int n) {
    int s = 0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            s += i * j;
        }
    }
    return s;
}

int while_break(int n) {
    int i = 0;
    while (i < n) {
        if (i * i > n) {
            break;
        }
        i++;
    }
    return i;
}

int early_return(int x) {
    if (x < 0) {
        return -1;
    }
    if (x == 0) {
        return 0;
    }
    return 1;
}

int and_condition(int a, int b) {
    if (a > 0 && b > 0) {
        return 1;
    }
    return 0;
}

int ternary(int x) {
    return x > 0 ? x : -x;
}

int int_switch(int x) {
    int r;
    switch (x) {
    case 0:
        r = 10;
        break;
    case 1:
        r = 20;
        break;
    case 2:
        r = 30;
        break;
    default:
        r = -1;
        break;
    }
    return r;
}
