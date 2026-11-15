// Snippet 5 (Arvan et al., ASE 2026). Method body from study_materials/snippets_and_tasks.md with two
// Java 8 compatibility edits that do not change control flow (the CFG extractor reads Java 8 bytecode):
//   - removed the @Nullable parameter annotation
//   - `new SimpleFileVisitor<>()` -> `new SimpleFileVisitor<Path>()` (anonymous-class diamond needs Java 9)
import java.io.IOException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;

public class FileSystemUtils {
    public static boolean deleteRecursively(Path root) throws IOException {
        if (root == null) return false;
        if (!Files.exists(root)) return false;

        Files.walkFileTree(root, new SimpleFileVisitor<Path>() {
            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                Files.delete(file);
                return FileVisitResult.CONTINUE;
            }
            @Override
            public FileVisitResult postVisitDirectory(Path dir, IOException exc) throws IOException {
                Files.delete(dir);
                return FileVisitResult.CONTINUE;
            }
        });

        return true;
    }
}
