// Snippet 7 (Arvan et al., ASE 2026): manual C translation of GeometryUtils.lowestPositiveRoot (libGDX).
// Body is unchanged apart from Float.NaN -> NAN.
#include <math.h>

float lowestPositiveRoot(float a, float b, float c) {
    float det = b * b - 4 * a * c;
    if (det < 0) return NAN;

    float sqrtD = (float)sqrt(det);
    float invA = 1 / (2 * a);

    float r1 = (-b - sqrtD) * invA;
    float r2 = (-b + sqrtD) * invA;

    if (r1 > r2) {
        float tmp = r2;
        r2 = r1;
        r1 = tmp;
    }

    if (r1 > 0) return r1;
    if (r2 > 0) return r2;
    return NAN;
}
