// Snippet 1 (Arvan et al., ASE 2026): manual C translation of NamingUtilities.isValidProjectName (Ghidra).
// Control flow is unchanged. name.length() -> name_length parameter; startsWith(".") -> name[0] == '.';
// Character.isLetterOrDigit -> isalnum; VALID_NAME_SET.contains(c) -> strchr on a character set.
#include <ctype.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>

#define MAX_NAME_LENGTH 10
static const char VALID_NAME_SET[] = ".-_ ";

bool isValidProjectName(const char *name, int name_length) {
    if (name == NULL) {
        return false;
    }
    if (name[0] == '.') {
        return false;
    }
    if ((name_length < 1) || (name_length > MAX_NAME_LENGTH)) {
        return false;
    }
    for (int i = 0; i < name_length; i++) {
        char c = name[i];
        if (!isalnum(c) && strchr(VALID_NAME_SET, c) == NULL) {
            return false;
        }
    }
    return true;
}
