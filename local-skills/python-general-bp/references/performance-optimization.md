# Performance Optimization

## Profiling

### Profile with cProfile

```python
import cProfile
import pstats
from pstats import SortKey

def slow_function():
    """Example function to profile."""
    result = []
    for i in range(10000):
        result.append(i ** 2)
    return result

# Profile and save results
cProfile.run('slow_function()', 'profile_stats')

# Analyze results
p = pstats.Stats('profile_stats')
p.strip_dirs()
p.sort_stats(SortKey.CUMULATIVE)
p.print_stats(10)  # Top 10 functions


# Profile decorator
from functools import wraps
import cProfile

def profile(func):
    """Decorator to profile a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        profiler.print_stats(sort='cumulative')
        return result
    return wrapper

@profile
def my_function():
    """Function to profile."""
    # Code here
    pass
```

### Line Profiler

```python
# Install: pip install line_profiler
# Use decorator from line_profiler

from line_profiler import profile

@profile
def process_data(data: list[int]) -> list[int]:
    """Process data line by line profiling."""
    result = []
    for item in data:
        if item % 2 == 0:
            result.append(item ** 2)
    return result

# Run with: kernprof -l -v script.py
```

### Memory Profiling

```python
# Install: pip install memory_profiler

from memory_profiler import profile

@profile
def memory_intensive():
    """Function with memory profiling."""
    large_list = [i for i in range(1000000)]
    return sum(large_list)

# Run with: python -m memory_profiler script.py
```

## Data Structures

### Choose Right Data Structure

```python
# List: Ordered, mutable, allows duplicates - O(1) append, O(n) search
names: list[str] = ['Alice', 'Bob', 'Charlie']

# Tuple: Ordered, immutable, allows duplicates - Memory efficient
coords: tuple[float, float] = (10.5, 20.3)

# Set: Unordered, mutable, unique items - O(1) search, add, remove
unique_ids: set[int] = {1, 2, 3, 4, 5}

# Dict: Key-value pairs - O(1) lookup, insert, delete
user_map: dict[int, str] = {1: 'Alice', 2: 'Bob'}

# Deque: Double-ended queue - O(1) append/pop on both ends
from collections import deque
queue: deque[str] = deque(['a', 'b', 'c'])
queue.appendleft('z')  # O(1)
queue.pop()  # O(1)

# Counter: Count hashable objects
from collections import Counter
word_counts = Counter(['apple', 'banana', 'apple'])
# Counter({'apple': 2, 'banana': 1})

# DefaultDict: Dict with default values
from collections import defaultdict
groups: defaultdict[str, list[int]] = defaultdict(list)
groups['even'].append(2)
groups['even'].append(4)
```

### Efficient Lookups

```python
# DON'T: Linear search in list
def has_item_slow(items: list[str], target: str) -> bool:
    return target in items  # O(n)

# DO: Use set for membership testing
def has_item_fast(items: set[str], target: str) -> bool:
    return target in items  # O(1)


# DON'T: Multiple lookups in list
users = [
    {'id': 1, 'name': 'Alice'},
    {'id': 2, 'name': 'Bob'},
]
for user_id in [1, 5, 2]:
    for user in users:  # O(n) per lookup
        if user['id'] == user_id:
            print(user['name'])

# DO: Create dict for O(1) lookup
user_dict = {user['id']: user for user in users}
for user_id in [1, 5, 2]:
    user = user_dict.get(user_id)  # O(1)
    if user:
        print(user['name'])
```

## List Operations

### List Comprehensions vs Loops

```python
# Faster: List comprehension
squares = [x**2 for x in range(1000)]

# Slower: Append in loop
squares = []
for x in range(1000):
    squares.append(x**2)


# Faster: Generator for large data
def large_squares():
    return (x**2 for x in range(1000000))

# Use generator
for square in large_squares():
    if square > 1000:
        break
```

### Avoid Repeated Concatenation

```python
# DON'T: String concatenation in loop
result = ''
for word in ['hello', 'world', 'python']:
    result += word + ' '  # Creates new string each time - O(n^2)

# DO: Use join
words = ['hello', 'world', 'python']
result = ' '.join(words)  # O(n)


# DON'T: List concatenation in loop
result = []
for chunk in chunks:
    result = result + chunk  # Creates new list each time

# DO: Extend or use itertools
result = []
for chunk in chunks:
    result.extend(chunk)

# OR: Use itertools.chain
from itertools import chain
result = list(chain.from_iterable(chunks))
```

## Function Optimization

### Avoid Function Call Overhead

```python
# Slow: Function call in tight loop
def square(x):
    return x * x

result = [square(x) for x in range(10000)]

# Faster: Inline calculation
result = [x * x for x in range(10000)]


# Slow: Repeated method lookups
items = []
for i in range(1000):
    items.append(i)  # Lookup .append each time

# Faster: Cache method reference
items = []
append = items.append
for i in range(1000):
    append(i)
```

### Memoization and Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    """Cached fibonacci calculation."""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# First call calculates
print(fibonacci(100))  # Slow first time
# Subsequent calls use cache
print(fibonacci(100))  # Instant


# Custom cache with timeout
import time
from functools import wraps

def timed_cache(seconds: int):
    """Cache with expiration."""
    cache = {}

    def decorator(func):
        @wraps(func)
        def wrapper(*args):
            now = time.time()
            if args in cache:
                result, timestamp = cache[args]
                if now - timestamp < seconds:
                    return result

            result = func(*args)
            cache[args] = (result, now)
            return result
        return wrapper
    return decorator

@timed_cache(seconds=60)
def expensive_api_call(url: str) -> dict:
    """Cache API results for 60 seconds."""
    # Make API call
    return {'data': 'result'}
```

## Iterator and Generator Optimization

### Generators for Memory Efficiency

```python
# Memory inefficient: Load all into memory
def read_file_lines(path: str) -> list[str]:
    with open(path) as f:
        return [line.strip() for line in f]

# Processes all at once
for line in read_file_lines('huge.txt'):
    process(line)


# Memory efficient: Generator
def read_file_lines_gen(path: str):
    with open(path) as f:
        for line in f:
            yield line.strip()

# Processes one at a time
for line in read_file_lines_gen('huge.txt'):
    process(line)
```

### itertools for Efficient Iteration

```python
import itertools

# Chain multiple iterables without creating intermediate list
combined = itertools.chain(list1, list2, list3)

# Take first n items efficiently
first_10 = itertools.islice(huge_sequence, 10)

# Group consecutive items
data = [1, 1, 2, 2, 2, 3, 3]
for key, group in itertools.groupby(data):
    print(f"{key}: {list(group)}")

# Pairwise iteration
def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

# Efficient combinations
for pair in itertools.combinations(range(5), 2):
    print(pair)
```

## String Operations

### String Building

```python
# Slow: Repeated concatenation
result = ''
for i in range(10000):
    result += str(i)

# Fast: Join list
parts = [str(i) for i in range(10000)]
result = ''.join(parts)

# Fast: io.StringIO for incremental building
from io import StringIO

buffer = StringIO()
for i in range(10000):
    buffer.write(str(i))
result = buffer.getvalue()
```

### String Formatting

```python
# Fastest: f-strings (Python 3.6+)
name, age = 'Alice', 30
message = f'{name} is {age} years old'

# Slower: % formatting
message = '%s is %d years old' % (name, age)

# Slower: str.format()
message = '{} is {} years old'.format(name, age)
```

## Comprehensions and Map/Filter

### List/Dict/Set Comprehensions

```python
# Fast: List comprehension
squares = [x**2 for x in range(100)]

# Slower: map + list
squares = list(map(lambda x: x**2, range(100)))


# Fast: Dict comprehension
word_lengths = {word: len(word) for word in words}

# Slower: Dict from zip
word_lengths = dict(zip(words, map(len, words)))


# Fast: Set comprehension
unique_squares = {x**2 for x in range(100)}

# Slower: Set from map
unique_squares = set(map(lambda x: x**2, range(100)))
```

### Filter with Comprehensions

```python
# Fast: List comprehension with condition
evens = [x for x in range(100) if x % 2 == 0]

# Slower: filter + list
evens = list(filter(lambda x: x % 2 == 0, range(100)))
```

## Class Optimization

### __slots__ for Memory

```python
# Without slots: ~400 bytes per instance
class PointNormal:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

# With slots: ~200 bytes per instance
class PointSlots:
    __slots__ = ('x', 'y')

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

# Significant savings with many instances
points = [PointSlots(i, i) for i in range(10000)]
```

### Property Caching

```python
class DataProcessor:
    """Process data with cached property."""

    def __init__(self, data: list[int]):
        self._data = data
        self._sum_cache: int | None = None

    @property
    def sum(self) -> int:
        """Cached sum calculation."""
        if self._sum_cache is None:
            self._sum_cache = sum(self._data)
        return self._sum_cache

    def add_item(self, item: int) -> None:
        """Add item and invalidate cache."""
        self._data.append(item)
        self._sum_cache = None


# Or use functools.cached_property (Python 3.8+)
from functools import cached_property

class DataProcessorAuto:
    """Process data with auto-cached property."""

    def __init__(self, data: list[int]):
        self._data = data

    @cached_property
    def sum(self) -> int:
        """Auto-cached sum calculation."""
        return sum(self._data)
```

## Numpy for Numerical Operations

```python
import numpy as np

# Slow: Pure Python
data = list(range(1000000))
result = [x * 2 for x in data]

# Fast: NumPy vectorized
data = np.arange(1000000)
result = data * 2  # 10-100x faster


# Slow: Python loop for calculations
total = 0
for x in data:
    total += x * x

# Fast: NumPy operations
total = np.sum(data * data)
```

## Multiprocessing and Threading

### CPU-Bound: multiprocessing

```python
from multiprocessing import Pool
from typing import Callable

def cpu_intensive(n: int) -> int:
    """CPU-intensive calculation."""
    return sum(i * i for i in range(n))

# Sequential
results = [cpu_intensive(n) for n in range(10)]

# Parallel
with Pool(processes=4) as pool:
    results = pool.map(cpu_intensive, range(10))
```

### I/O-Bound: Threading

```python
import concurrent.futures
import requests

def fetch_url(url: str) -> str:
    """Fetch URL content."""
    response = requests.get(url)
    return response.text

urls = ['http://example.com'] * 10

# Sequential
results = [fetch_url(url) for url in urls]

# Concurrent
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(fetch_url, urls))
```

### Async for I/O

```python
import asyncio
import aiohttp

async def fetch_async(url: str) -> str:
    """Async fetch."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

async def fetch_all(urls: list[str]) -> list[str]:
    """Fetch all URLs concurrently."""
    tasks = [fetch_async(url) for url in urls]
    return await asyncio.gather(*tasks)

# Run
urls = ['http://example.com'] * 10
results = asyncio.run(fetch_all(urls))
```

## Best Practices Summary

1. **Profile first**: Don't optimize without measuring
2. **Use appropriate data structures**: Set for membership, dict for lookup
3. **Generators for large data**: Memory efficiency over speed sometimes
4. **Avoid premature optimization**: Clear code first, optimize bottlenecks
5. **Cache expensive calculations**: lru_cache, cached_property
6. **Comprehensions over loops**: Usually faster and more readable
7. **NumPy for numerical work**: Vectorized operations are much faster
8. **__slots__ for many instances**: Significant memory savings
9. **Multiprocessing for CPU**: Threading for I/O, async for I/O-heavy
10. **Batch operations**: Reduce function call overhead
