import os
import subprocess


def get_word_count(main_tex: os.PathLike, root_dir: os.PathLike) -> int:
    print("running with", main_tex)
    ps = subprocess.Popen(("detex", main_tex), stdout=subprocess.PIPE, cwd=root_dir)
    output = subprocess.check_output(("wc", "--w"), stdin=ps.stdout)
    ps.wait()
    return int(output)


def get_chapter_word_count(root_dir: os.PathLike):
    """Assumes that your chapters are given their own
    directory, and the main file for each chapter is named:
    `00-xxxx.tex`. See <https://github.com/Wheest/Glasgow-Thesis-Template>
    for an example.
    """
    word_count_dict = {}

    # Loop through each chapter directory
    for chapter_dir in os.listdir(root_dir):
        chapter_dirr = os.path.join(root_dir, chapter_dir)
        if os.path.isdir(chapter_dirr):
            word_count = 0

            # Loop through each tex file in the chapter directory
            for tex_file in os.listdir(chapter_dirr):
                if tex_file.endswith(".tex") and "00" in tex_file:
                    print("tex_file", tex_file)
                    # Use detex to get the word count of the tex file
                    word_count += get_word_count(
                        os.path.join(chapter_dirr, tex_file), root_dir
                    )

            # Store the word count in the dictionary
            if word_count == 0:
                continue
            word_count_dict[chapter_dir] = word_count

    # Print the word count for each chapter
    total = 0
    for chapter, count in word_count_dict.items():
        print(f"{chapter}: {count} words")
        total += count
    print("total count:", total)
    return word_count_dict


if __name__ == "__main__":
    get_chapter_word_count(
        "/home/pez/Dropbox/home/proj/phd/thesis/2023_PhD_Thesis_Perry_Gibson/"
    )
    root_dir = "/home/pez/Dropbox/home/proj/phd/thesis/2023_PhD_Thesis_Perry_Gibson/"
    print(get_word_count(os.path.join(root_dir, "01-header.tex"), root_dir))
