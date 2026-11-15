// Snippet 2 (Arvan et al., ASE 2026): manual C translation of HelpBuildUtils.isRemote (Ghidra).
// C has no switch on strings: `case "file": case "jar": return false; default: break;` becomes one
// if with the two string comparisons (same decision structure). URI accessors are opaque externs.
#include <stdbool.h>
#include <stddef.h>
#include <string.h>

extern bool isFilesystemPath(const char *uri);
extern const char *uri_get_scheme(const char *uri);

bool isRemote(const char *uri) {
    if (isFilesystemPath(uri)) {
        return false;
    }
    const char *scheme = uri_get_scheme(uri);
    if (scheme == NULL) {
        return false;
    }
    if (strcmp(scheme, "file") == 0 || strcmp(scheme, "jar") == 0) {
        return false;
    }
    return true;
}
