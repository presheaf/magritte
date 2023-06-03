# `magritte` - an experiment in arg parsing

This was a PoC to see whether it'd be feasible to automagically make a CLI from a Python function, given its function annotation. It can be installed by e.g. `pip install .`

It was inspired by the `argh` library, which uses heuristics to Do What You Mean, meaning the following often suffices to give your script a simple CLI:

```
if __name__ == '__main__':
    argh.dispatch_commands([func1, func2])
```

Of course, argh sometimes needs to be told the types of your arguments to e.g. know that you want the strings you pass in to be converted to numbers. I sometimes like to annotate my functions so `mypy` can typecheck them anyway, which raised the question of whether I could kill two birds with one stone here. For simple types like `str` and `int`, all that's really needed is a simple type conversion, and I have a PR implementing this in (a fork of) `argh`. 

However, the Python type system also permits the expression of more complex types, such as `list[tuple[str, int]]`. Although we can't expect to parse everything, several of the builtin generics have natural enough interpretations in a CLI. For example, if an argument is typed `list[int]`, reasonable behavior would be that that argument could take any number of integers, whereas if it is typed as `tuple[int, int]`, you'd expect it to take exactly two. `list[tuple[str, int]]` might be a tad esoteric, but the reasonable expectation seems to be a list of an even amount of strings/integers, alternating. A type such as `Literal['apple', 'banana']` tells you that the argument should either be apple or banana.

Anyway, this made me curious enough to take a stab of it. And it kind of works - see `example.py` for example usage. I tried to make the parser design extensible enough that adding custom behavior for your own types would be possible (e.g. a type for non-directory files, which could also check that they exist) too, so there are lots of low-hanging fruits for parsers related to `pathlib.Path`.


# Why I dropped it after the PoC
After writing `magritte`, someone told me `typer` already exists. It might not do exactly what I wanted, but the utilities is has for checking whether a `pathlib.Path` exists and/or is writable is way more useful than being able to parse a `list[tuple[list[...]]]` nested mess. Also, someone else maintains it. :)

A secondary reason is that there are several ambiguities that would need resolving. For example, given the type `list[Union[tuple[int, int], tuple[int, int, int]]]`, how should the argument list `1 2 3 4 5 6` be parsed? Probably the most sane approach is to refuse to guess a parser for 'ambiguous' types in the first place, so we'd need to ensure our design permits checking for this. I don't think this is totally insurmountable, but using `typer` seemed the easier option.
