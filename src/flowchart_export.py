import os
import tempfile
import subprocess


def mermaid_to_png(mermaid_code, output_png):

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".mmd",
        delete=False,
        encoding="utf-8"
    ) as temp_file:

        temp_file.write(mermaid_code)

        temp_mmd = temp_file.name

    try:

        subprocess.run(
            [
                r"C:\Users\Lenovo\AppData\Roaming\npm\mmdc.cmd",
                "-i",
                temp_mmd,
                "-o",
                output_png,
                "-b",
                "white",
                "-w",
                "2000",
                "-s",
                "3",
                "-t",
                "default"
            ],
            check=True
        )

        return output_png

    finally:

        if os.path.exists(temp_mmd):
            os.remove(temp_mmd)