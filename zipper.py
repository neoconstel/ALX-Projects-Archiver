from zipfile import ZipFile
import os


def zip_contents(directory, zip_output_file, selected_paths=[]):
    os.chdir(directory)
    archive_paths = []

    # make every filepath in selected_paths begin with "./" so a.txt would 
    # become ./a.txt
    selected_paths = list(map(lambda x: x if x.startswith("./") \
                                                else f"./{x}", selected_paths))

    if os.path.exists(zip_output_file):
        print("File with same name and path as output path already exists!")
        return

    with ZipFile(zip_output_file, "w") as archive:

        # ----operating on the FULL tree structure of given path------
        for dirpath, dirnames, filenames in os.walk("."):
            # operate on the files only
            for filename in filenames:
                path = os.path.join(dirpath, filename)

                # zip but don't zip the output file into the archive
                if os.path.join(dirpath, filename) != os.path.join(
                                                    dirpath, zip_output_file):
                    archive_paths.append(path)

            # operate on just the empty directories of given path
            if not dirnames and not filenames:
                archive_paths.append(dirpath)

        # now for the actual archiving on the paths
        for path in archive_paths:
            # if there is no selected_path (equivalent to "ZIP ALL")
            if (not selected_paths) \
                    or ( # or path is marked as selected_path
                        (path in selected_paths \
                        # or path is subdirectory of a selected_path
                        # (in other words there is a non-empty list of
                        # paths in selected paths for which adding a
                        # '/' suffix equals the value of current <path> 
                        # variable
                        or list(filter(lambda x: path.startswith(f"{x}/"), 
                        selected_paths)
                        )
                        )
                        ):
                print(path)
                archive.write(path)
                

