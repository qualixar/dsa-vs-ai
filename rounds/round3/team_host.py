"""Runs in the sandbox, in its own process, holding only the team's code. It answers the
judge's calls over two private pipes. Anything the team's code does here can only change
the team's own answers: the simulator and the scoring live in another process."""
import importlib
import json
import os
import sys
import traceback


def main():
    rfd, wfd, team = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    sys.dont_write_bytecode = True
    sys.path.insert(0, team)
    out = os.fdopen(wfd, "w", buffering=1)

    def send(obj):
        out.write(json.dumps(obj, default=repr) + "\n")
        out.flush()

    try:
        cls = importlib.import_module("dispatcher").Dispatcher
    except BaseException:
        send({"import_error": traceback.format_exc(limit=3)[-800:]})
        return
    send({"ok": True})
    d = None
    for line in os.fdopen(rfd):
        msg = json.loads(line)
        try:
            if msg["m"] == "__init__":
                d = cls(*msg["a"])
                reply = None
            else:
                reply = getattr(d, msg["m"])(*msg["a"])
                if msg["m"] != "step":
                    reply = None
                elif not isinstance(reply, list):
                    reply = "not a list: " + repr(reply)[:40]
            send({"r": reply})
        except BaseException as e:
            send({"e": f"{type(e).__name__}: {e}"[:300]})


main()
