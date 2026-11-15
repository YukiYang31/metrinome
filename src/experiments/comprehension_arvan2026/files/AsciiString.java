// Snippet 4 (Arvan et al., ASE 2026). Method body verbatim from study_materials/snippets_and_tasks.md.
public class AsciiString {
    // Stubs so the snippet compiles.
    static final int INDEX_NOT_FOUND = -1;
    static boolean regionMatches(CharSequence cs, boolean ignoreCase, int thisStart,
                                 CharSequence substring, int start, int length) { return false; }

    public static int indexOfIgnoreCase(CharSequence str, CharSequence searchStr, int startPos) {
        if (str == null || searchStr == null) {
            return INDEX_NOT_FOUND;
        }
        if (startPos < 0) {
            startPos = 0;
        }
        int searchStrLen = searchStr.length();
        int endLimit = str.length() - searchStrLen + 1;
        if (startPos > endLimit) {
            return INDEX_NOT_FOUND;
        }
        if (searchStrLen == 0) {
            return startPos;
        }
        for (int i = startPos; i < endLimit; i++) {
            if (regionMatches(str, true, i, searchStr, 0, searchStrLen)) {
                return i;
            }
        }
        return INDEX_NOT_FOUND;
    }
}
