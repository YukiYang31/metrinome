/* A four-way switch plus default: the switch block has five distinct successors (LLVM record
 * ports :s0 .. :s4). Used by tests/test_frontends.py. */
int classify(int x) {
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
    case 3:
        r = 40;
        break;
    default:
        r = -1;
        break;
    }
    return r;
}
