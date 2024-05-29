from pythonning.benchmark import timeit


def test__timeit():
    messages = []

    def callback(msg):
        messages.append(msg)

    fib = lambda n: n if n < 2 else fib(n - 1) + fib(n - 2)
    with timeit("process took ", callback):
        result = fib(27)

    messages = messages[0].split(".")
    assert messages[0] == "process took 0"
    # we cannot verify exactly how much time it take so we just verify rounding
    assert len(messages[1]) == 3
