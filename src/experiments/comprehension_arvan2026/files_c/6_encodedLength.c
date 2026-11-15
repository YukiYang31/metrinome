// Snippet 6 (Arvan et al., ASE 2026): manual C translation of Utf8.encodedLength (Guava).
// Control flow is unchanged. CharSequence -> UTF-16 code-unit array plus length; Java's `>>>` on int ->
// `>>` on uint32_t. `throw new IllegalArgumentException(...)` -> report via opaque extern, then exit the
// method (a throw leaves the method, as the Java CFG's edge to EXIT does).
#include <stdint.h>

extern int encodedLengthGeneral(const uint16_t *sequence, int sequence_length, int start);
extern void throw_illegal_argument(const char *message, int64_t value);

int encodedLength(const uint16_t *sequence, int sequence_length) {
    int utf16Length = sequence_length;
    int utf8Length = utf16Length;
    int i = 0;

    while (i < utf16Length && sequence[i] < 0x80) {
        i++;
    }

    for (; i < utf16Length; i++) {
        uint16_t c = sequence[i];
        if (c < 0x800) {
            utf8Length += ((uint32_t)(0x7f - c)) >> 31;
        } else {
            utf8Length += encodedLengthGeneral(sequence, sequence_length, i);
            break;
        }
    }

    if (utf8Length < utf16Length) {
        throw_illegal_argument("UTF-8 length does not fit in int: ", utf8Length + (1LL << 32));
        return -1;
    }
    return utf8Length;
}
