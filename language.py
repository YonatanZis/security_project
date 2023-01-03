import subprocess


def run_file(*args):
    try:
        subprocess.run([*args])
        return "success " + " ".join(args)
    except Exception as e:
        print("ERROR: could not run file. error: " + str(e))
        return "error " + " ".join(args)


def my_print(*args):
    print(" ".join(args))
    return "success " + " ".join(args)


commands = {"print": my_print, "run": run_file}
