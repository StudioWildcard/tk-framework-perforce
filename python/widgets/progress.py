import uuid


class ProgressTracker:
    def __init__(self, min=0, max=1, current=0, id=None):
        if not id:
            id = str(uuid.uuid4())
        self.id = id
        self.max = max
        self.current = current
        self.min = min

    @property
    def complete(self):
        if self.current >= self.max:
            return True
        return False

    @property
    def progress(self):
        # we translate to 0 for our min and bring down our max with it

        nmax = self.max - self.min
        ncur = self.current - self.min
        nmin = 0

        return float(ncur) / float(nmax)

    def iterate(self, val=1):
        self.current += val


class ProgressHandler:
    def __init__(self):
        """
        Register queues so that a universal progress solver can feed a progressbar

        Returns:
            _type_: _description_
        """

        self.queue = {}
        self.incr = -1

        self.format = ""
        self.message = "Progress: "

        self.meta_tracker = ProgressTracker()

    def tracker(self, id):
        return self.queue.get(id)

    def track_progress(self, items=1, id=None):
        tracker = ProgressTracker(max=items, id=id)
        self.queue[tracker.id] = tracker
        return tracker

    def iterate(self, id):
        self.queue.get(id).iterate()
        completed = sum([v.complete for i, v in self.queue.iteritems()]) + 1
        self.meta_tracker.current = completed
        self.meta_tracker.max = len(self.queue.iteritems())

    @property
    def progress(self):
        return sum([i.progress for i in self.queue.values()]) / float(len(self.queue))
