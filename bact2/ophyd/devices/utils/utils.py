from ophyd.status import SubscriptionStatus
def trigger_on_update(signal):
    def cb(**kwargs):
        return True
    status = SubscriptionStatus(signal, cb, run = False)
    return status
