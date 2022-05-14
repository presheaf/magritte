from __future__ import annotations

import typing
import logging
import inspect
import string
from typing import List, Set, Tuple, Type, Callable, Annotated, Literal, Union

from magritte import SingleArgParser, ArgumentParser


# logging.getLogger().setLevel(logging.DEBUG)


def strtobool(s: str) -> bool:
    if s in {'y', 'yes', 't', 'true', 'on', '1'}:
        return True
    elif s in {'n', 'no', 'f', 'false', 'off', '0'}:
        return False
    else:
        raise ValueError


class ListParser(SingleArgParser[List]):
    def __init__(self, elttype, **kwargs):
        super().__init__(**kwargs)
        self.__type_str = repr(elttype)
        self.subparser = guess_parser(elttype)

    def parse_single_arg(self, arg_format, args, parser):
        log_prefix = f"ListParser[{self.__type_str}]"
        logging.debug(f"{log_prefix}: Parsing {args}")

        parsed_args = []
        num_parsed_args = 0
        while args:
            if parser.argstr_to_argname(args[0]) is not None:
                # Some other parser wants to start parsing now
                logging.debug(f"{log_prefix}: {args[0]} indicates a new arg")
                break
            try:
                nargs, argval = self.subparser(args[0], args, parser)
                logging.debug(f"{log_prefix}: parsed {nargs} args and got {argval}")
                parsed_args.append(argval)
                num_parsed_args += nargs
                args = args[nargs:]
            except ValueError as e:
                logging.debug(f"{e} on {args} - breaking")
                break
        logging.debug(f"Parsed {num_parsed_args} args and got {parsed_args}")
        return num_parsed_args, parsed_args


class SetParser(ListParser):
    def parse_single_arg(self, *args, **kwargs):
        nargs, parsed_val = super().parse_single_arg(*args, **kwargs)
        return nargs, set(parsed_val)


class TupleParser(SingleArgParser[Tuple]):
    def __init__(self, *elttypes, **kwargs):
        super().__init__(**kwargs)
        self.__type_str = repr(list(elttypes))
        self.subparsers = [guess_parser(t) for t in elttypes]

    def parse_single_arg(self, arg_format, args, parser):
        log_prefix = f"TupleParser[{self.__type_str}]"
        logging.debug(f"{log_prefix}: Parsing {args}")

        parsed_args = []
        num_parsed_args = 0
        for subparser in self.subparsers:  # first T1, then T2, etc
            # Note: If subparser ValueErrors, we fail to parse the thing by letting it bubble upwards
            nargs, argval = subparser(arg_format, args, parser)
            logging.debug(f"{log_prefix}: Subparser parsed {nargs} args and got {argval}")
            parsed_args.append(argval)
            num_parsed_args += nargs
            args = args[nargs:]
        logging.debug(f"{log_prefix}: Parsed {num_parsed_args} args and got {tuple(parsed_args)}")
        return num_parsed_args, tuple(parsed_args)


class UnionParser(SingleArgParser):
    def __init__(self, *union_types: Type, **kwargs):
        super().__init__(**kwargs)
        self.subparsers = [guess_parser(t) for t in union_types]
        self.__type_str = repr(list(union_types))

    def parse_single_arg(self, arg_format, args, parser: ArgumentParser):
        for subparser in self.subparsers:
            try:
                return subparser.parse_single_arg(arg_format, args, parser)
            except ValueError:
                pass
        raise ValueError(f"Couldn't parse {args} as Union{self.__type_str}")


class LiteralParser(SingleArgParser):
    def __init__(self, *literals, **kwargs):
        super().__init__(**kwargs)
        literal_types = {type(lit) for lit in literals}
        assert literal_types.issubset({int, str, type(None)}), "Only int, str, None literals supported"
        self.literals = literals
        self.__type_str = repr(list(self.literals))

    def parse_single_arg(self, arg_format, args, parser):
        log_prefix = f"TupleParser[{self.__type_str}]"
        logging.debug(f"{log_prefix}: Parsing {args}")
        for literal in self.literals:
            if str(literal) == args[0]:
                return 1, literal
        raise ValueError(f'{args[0]} unknown repr of Literal{self.__type_str}')


class IntParser(SingleArgParser[int]):
    def parse_single_arg(self, arg_format, args, parser):
        logging.debug(f"IntParser {args}")
        return 1, int(args[0])


class NoneParser(SingleArgParser[None]):
    def parse_single_arg(self, arg_format, args, parser):
        logging.debug(f"NoneParser {args}")
        if args[0] != 'None':
            raise ValueError
        return 1, None


class FloatParser(SingleArgParser[float]):
    def parse_single_arg(self, arg_format, args, parser):
        logging.debug(f"FloatParser {args}")
        return 1, float(args[0])


class StrParser(SingleArgParser[str]):
    def parse_single_arg(self, arg_format, args, parser):
        logging.debug(f"StrParser {args}")
        return 1, str(args[0])


class BoolParser(SingleArgParser[bool]):
    #   -should_log True/true/1/t/T   => True
    #   -should_log False/false/1/f/F => False
    #   --should_log                  => True
    #   --no-should_log               => False
    #   --not-should_log              => False
    #  Note: intentionally leaving out -s here
    
    def parse_single_arg(self, arg_format, args, parser: ArgumentParser):
        logging.debug(f"BoolParser {arg_format} {args}")
        argname = parser.argstr_to_argname(arg_format)
        if arg_format == f'-{argname}':
            return 1, strtobool(args[0])
        else:
            return 0, arg_format == f'--{argname}'

    def argname_representations(self, argname) -> List[str]:
        argname = argname.lower()
        assert argname and argname[0] in string.ascii_lowercase, f"Illegal argname: {repr(argname)}"

        return [f'-{argname}', f'--{argname}', f'--no-{argname}', f'--not-{argname}']


_special_types = {
    Annotated: lambda t, t_str: t
}

_all_the_parsers = {
    bool: BoolParser,
    int: IntParser,
    str: StrParser,
    type(None): NoneParser,
    tuple: TupleParser,
    Tuple: TupleParser,
    list: ListParser,
    List: ListParser,
    set: SetParser,
    Set: SetParser,
    Literal: LiteralParser,
    Union: UnionParser
}


def guess_parser(argtype: Type, default_value=inspect._empty):
    basetype, typeargs = typing.get_origin(argtype), typing.get_args(argtype)
    logging.info(f"Trying to guess parser for {argtype} -> {basetype}, {typeargs}")
    if basetype in _special_types:
        logging.info(f"Doing special transform of {argtype} -> {typeargs}")
        return guess_parser(_special_types[basetype](*typeargs), default_value)

    if argtype in _all_the_parsers:
        logging.info(f"Found parser for {argtype}!")
        return _all_the_parsers[argtype](default_value=default_value)

    if basetype in _all_the_parsers:
        logging.info(f"Found parser for {basetype}{list(typeargs)}!")
        return _all_the_parsers[basetype](*typeargs, default_value=default_value)
    else:
        logging.info(f"No parser found for {basetype}{list(typeargs)} - fallback to str")
        return _all_the_parsers[str](default_value=default_value)


def arg_description(argname: str, argtype: Type, default_value=inspect._empty):
    basetype, typeargs = typing.get_origin(argtype), typing.get_args(argtype)
    if basetype is Annotated:
        argtype, help_message = typeargs
    else:
        help_message = argname
    if argtype is inspect._empty:
        type_str = ""
    else:
        type_str = str(argtype)
        if type_str.startswith('typing.'):  # horrible hack...
            type_str = type_str[len('typing.'):]
    return help_message, type_str


def make_parser(func: Callable, **kwargs) -> ArgumentParser:
    # print(f.__name__)
    signature = inspect.signature(func, eval_str=True)
    parsers = {}
    arg_help = {}

    for param in signature.parameters.values():
        arg_help[param.name] = arg_description(param.name, param.annotation, param.default)
        parsers[param.name] = guess_parser(param.annotation, param.default)

    # TODO: check dict union for duplicate arguments here
    return ArgumentParser(parsers | kwargs, arg_help, func)
