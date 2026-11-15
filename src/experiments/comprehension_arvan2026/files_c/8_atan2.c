// Snippet 8 (Arvan et al., ASE 2026): manual C translation of MathUtils.atan2 (libGDX).
// Body is unchanged; atanUnchecked is an opaque extern. Named atan2 to match the Java method, which
// shadows the C library's double atan2(double, double) (clang warns; math.h is not included).
#define PI 3.14159265f
#define HALF_PI (PI / 2.0f)

extern float atanUnchecked(double i);

float atan2(float y, float x) {
    float n = y / x;
    if (n != n)
        n = (y == x ? 1.0f : -1.0f);
    else if (n - n != n - n)
        x = 0.0f;

    if (x > 0)
        return atanUnchecked(n);
    else if (x < 0) {
        if (y >= 0) return atanUnchecked(n) + PI;
        return atanUnchecked(n) - PI;
    } else if (y > 0)
        return x + HALF_PI;
    else if (y < 0)
        return x - HALF_PI;
    return x + y;
}
