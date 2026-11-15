// Snippet 4 (Arvan et al., ASE 2026): manual C translation of AsciiString.indexOfIgnoreCase (Netty).
// Control flow is unchanged. CharSequence.length() -> length parameters; regionMatches -> opaque extern.
#include <stdbool.h>
#include <stddef.h>

#define INDEX_NOT_FOUND (-1)

extern bool regionMatches(const char *cs, bool ignoreCase, int thisStart,
                          const char *substring, int start, int length);

int indexOfIgnoreCase(const char *str, int str_length, const char *searchStr, int searchStr_length,
                      int startPos) {
    if (str == NULL || searchStr == NULL) {
        return INDEX_NOT_FOUND;
    }
    if (startPos < 0) {
        startPos = 0;
    }
    int searchStrLen = searchStr_length;
    int endLimit = str_length - searchStrLen + 1;
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
