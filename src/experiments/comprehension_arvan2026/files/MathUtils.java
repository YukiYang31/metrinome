// Snippet 8 (Arvan et al., ASE 2026). Method body verbatim from study_materials/snippets_and_tasks.md.
public class MathUtils {
    // Stubs so the snippet compiles.
    static final float PI = (float) Math.PI;
    static final float HALF_PI = PI / 2f;
    static float atanUnchecked(double i) { return 0f; }

    public static float atan2(float y, float x) {
        float n = y / x;

        if (n != n)
            n = (y == x ? 1f : -1f);
        else if (n - n != n - n)
            x = 0f;

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
}
