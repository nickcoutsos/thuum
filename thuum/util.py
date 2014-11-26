import tornado.concurrent

def combine_futures(*futures):
    pending = set(futures)
    all_complete = tornado.concurrent.Future()

    def future_complete(future):
        pending.discard(future)
        if len(pending) == 0:
            all_complete.set_result(None)

    for future in futures:
        future.add_done_callback(future_complete)

    return all_complete
