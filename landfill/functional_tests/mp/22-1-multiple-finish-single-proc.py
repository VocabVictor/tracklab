import tracklab

if __name__ == "__main__":
    with tracklab.init() as run:
        run.finish()
    run.finish()
