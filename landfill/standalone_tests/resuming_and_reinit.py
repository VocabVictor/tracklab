import sys
import time

import tracklab
from tracklab.sdk.lib import runid


def main(args):
    run_id = runid.generate_id()
    try:
        tracklab.init(project="resuming", resume="must", id=run_id)
    except tracklab.Error:
        print("Confirmed we can't resume a non-existent run with must")

    tracklab.init(project="resuming", resume="allow", id=run_id)
    print("Run start time: ", tracklab.run.start_time)
    for i in range(10):
        print(f"Logging step {i}")
        tracklab.log({"metric": i})
        time.sleep(1)
    tracklab.join()
    print("Run finished at: ", int(time.time()))

    print("Sleeping 5 seconds...")
    time.sleep(5)

    tracklab.init(project="resuming", resume="allow", id=run_id, reinit=True)
    print("Run starting step: ", tracklab.run.history._step)
    print("Run start time: ", int(tracklab.run.start_time))
    print("Time travel: ", int(time.time() - tracklab.run.start_time))
    for i in range(10):
        print("Resumed logging step %i" % i)
        tracklab.log({"metric": i})
        time.sleep(1)
    tracklab.join()

    try:
        tracklab.init(project="resuming", resume="never", id=run_id, reinit=True)
        raise ValueError("I was allowed to resume!")
    except tracklab.Error:
        print("Confirmed we can't resume run when never")

    api = tracklab.Api()
    run = api.run(f"resuming/{run_id}")

    # TODO: This is showing a beast bug, we're not syncing the last history row
    print("History")
    print(run.history())

    print("System Metrics")
    print(run.history(stream="system"))


if __name__ == "__main__":
    main(sys.argv)
