// Snippet 2 (Arvan et al., ASE 2026). Method body verbatim from study_materials/snippets_and_tasks.md.
import java.net.URI;

public class HelpBuildUtils {
    // Stub so the snippet compiles.
    static boolean isFilesystemPath(URI uri) { return false; }

    public static boolean isRemote(URI uri) {
        if (isFilesystemPath(uri)) {
            return false;
        }
        String scheme = uri.getScheme();
        if (scheme == null) {
            return false;
        }
        switch (scheme) {
            case "file":
            case "jar":
                return false;
            default:
                break;
        }
        return true;
    }
}
