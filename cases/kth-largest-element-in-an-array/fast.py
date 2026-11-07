from heapq import heappop, heappush


def solve(nums, k):
    heap = []
    for x in nums:
        heappush(heap, x)
        if len(heap) > k:
            heappop(heap)
    return heap[0]
