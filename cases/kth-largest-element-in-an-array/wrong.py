"""Two wrong answers to hunt. Run the check first; README.md explains both behind a fold."""
from heapq import heappop, heappush


def gut(nums, k):
    """Sort the distinct values and take the kth."""
    values = sorted(set(nums), reverse=True)
    return values[min(k, len(values)) - 1]


# A copy of fast.py with exactly one line changed. Find it.
def planted(nums, k):
    heap = []
    for x in nums:
        heappush(heap, x)
        if len(heap) > k + 1:
            heappop(heap)
    return heap[0]
