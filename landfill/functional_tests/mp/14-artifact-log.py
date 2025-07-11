#!/usr/bin/env python

import tracklab


def main():
    run = tracklab.init()
    run.log(dict(m1=1))
    run.log(dict(m2=2))

    with open("my-dataset.txt", "w") as fp:
        fp.write("this-is-data")
    artifact = tracklab.Artifact("my-dataset", type="dataset")
    table = tracklab.Table(columns=["a", "b", "c"], data=[[1, 2, 3]])
    artifact.add(table, "my_table")
    artifact.add_file("my-dataset.txt")
    art = run.log_artifact(artifact)
    art.wait()
    get_table = art.get("my_table")
    print("TABLE", get_table)
    run.finish()


if __name__ == "__main__":
    main()
