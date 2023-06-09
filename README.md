# Forfait

A concatenative, strongly-typed programming language implemented in Python.

The goal is to write a compiler for Forfait capable of generating binaries for the Z80 (and maybe other architectures).

## Overview of the language

The language is heavily inspired by [Forth](https://forth-standard.org/) and [Cat](https://github.com/cdiggins/cat-language). 

The syntax strives to be as minimal as possible without being too idealistic about it. 

An example program may be:

```
( define a function `square` that, given x, pushes x^2 )
: square    
  dup *8bit ;

( prints the first 10 squares; similar to a `for x in range(0,10) ...` )
0 10 [| square :s drop |] indexed-iter

( prints the current stack (it will be empty!) )
:s
```

## Few examples

### Fibonacci on-stack

```
: fibonacci (( n -- fact(n) ))
  1 1

    [| rot- dup 1 >=u8 |]  (( checks if n still >= 1 ))
    [| --u8 rot+           (( decrements n and puts it in third position ))
       over +u8 swap |]    (( fib(n-1) fib(n-2) -- fib(n) fib(n-1) ))
  while

  drop drop
;

8 fibonacci :s     (( will print [55] ))
```

## Architecture of the compiler

The canonical compiler architecture is used for Forfait:

- First, an input file is lexed and parsed
- The so-generated AST is typechecked
- _(not yet implemented)_ Few simple peephole optimizations are performed on the Forfait code
- The AST is then converted to Single-Static Assignment form ([SSA](https://en.wikipedia.org/wiki/Static_single-assignment_form)), translating the stack-based Forfait code to a register-based Intermediate Representation (IR).
- 

## Type system

(note: the following syntax about types is only for sake of clarity, it is not the actual syntax of the language)

Roughly, Forfait implements a classic Hindley-Milner type system with generics and row polymoprhism.

There are two types of generics: classic generics and "Row" (or stack) generics; the latter allow to remain generic over a row (i.e. an ordered list) of types, instead than on only one type. 

For example, the type signature of `swap` is the following :

```
swap :: (''S 'A 'B -> ''S 'B 'A)
```

`''S` is a _row_ type variable. It basically says: except for the two top-most positions (`'A` and `'B`), we don't care what is in the stack, and we call whatever it is `''S`.

`'A` and `'B` are normal generic type variables.

### What if I don't care about row generics?

Row generics are necessary if we want to correctly type `eval`-like functions. 

To see an example of this, let's first look at the type signature of a quotation.

#### Quotations (suspended computations)

Let's take the unquoted, builtin function `drop`:

`drop :: (''S 'T -> ''S)`

The signature means: `drop` accepts whatever stack `''S` that has an object with generic type `'T` on top. 

Quoting `drop` results in:

`[| drop |] :: (''R -> ''R (''S 'T -> ''S))`

The quotation (i.e. weird squared parenthesis) around `drop` wraps `drop` within a no-argument function: this is the way to delay the actual esecution of `drop` which, without the quotes, would be executed instantly. Note the existence of two different row generics at the same time, `''R` and `''S`!

#### `eval` function

`eval :: (''U (''U -> ''V) -> ''V)`

With `eval` we can evaluate these "suspended computation" at our convenience. So for example, if we manually typecheck `[| drop |] eval`:

```
[| drop |]      :: (''R -> ''R (''S 'T -> ''S))
eval            ::        (''U (''U    -> ''V)  -> ''V)
                           ^^^  ^^^^^^    ^^^  
            ---------------------------------------
[| drop |] eval :: (''R -> ''V)  which, after unification, becomes:
[| drop |] eval :: (''S 'T -> ''S)  (names may be different IRL)
```

## TODOs

- [ ] Typing for recursive functions
- [ ] Syntax for explicit type annotations
- [ ] Structure-like data types
- [ ] Macro `declare` for defining constructors and accessor to typed variables
  - [ ] Use `declare` inside a funcdef for "local" variables is impossible, because that would require the concept of "scope" and i don't want it >:|
- [ ] SSA
  - [ ] Test constant propagation on branching code (see if constants are actually propagated through CFGs)
  - [ ] Useless constant assignments can be deleted after propagation?