// Snippet 5 (Arvan et al., ASE 2026): manual C translation of FileSystemUtils.deleteRecursively (Spring).
// Files.exists/delete/walkFileTree -> opaque externs. The anonymous SimpleFileVisitor becomes a struct of
// function pointers to two static functions (its visitFile/postVisitDirectory methods).
#include <stdbool.h>
#include <stddef.h>

typedef enum { CONTINUE } FileVisitResult;
typedef struct {
    FileVisitResult (*visitFile)(const char *file);
    FileVisitResult (*postVisitDirectory)(const char *dir);
} FileVisitor;

extern bool files_exists(const char *path);
extern void files_delete(const char *path);
extern void files_walk_file_tree(const char *root, const FileVisitor *visitor);

static FileVisitResult visitFile(const char *file) {
    files_delete(file);
    return CONTINUE;
}

static FileVisitResult postVisitDirectory(const char *dir) {
    files_delete(dir);
    return CONTINUE;
}

bool deleteRecursively(const char *root) {
    if (root == NULL) return false;
    if (!files_exists(root)) return false;

    const FileVisitor visitor = {visitFile, postVisitDirectory};
    files_walk_file_tree(root, &visitor);

    return true;
}
